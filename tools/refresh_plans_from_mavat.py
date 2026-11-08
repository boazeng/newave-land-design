"""
Refresh the plans databases (data/plans_*.json) from MAVAT (mavat.iplan.gov.il).

MAVAT blocks plain HTTP clients and needs a fresh reCAPTCHA v3 token on every API
call, so this runs a headless Chromium on a MAVAT page and calls the site's own
REST API from inside it (grecaptcha.execute -> fetch), several tabs in parallel.

Two phases:
  fetch  - download each plan's SV4 JSON into output/mavat_cache/<mid>.json
           (resumable: plans already cached are skipped unless --refetch)
  apply  - update status / dates / milestones in the plans JSON files from the
           cache and write a change report to output/mavat_refresh_report.csv

Usage:
  python tools/refresh_plans_from_mavat.py fetch [--tabs 3] [--refetch]
  python tools/refresh_plans_from_mavat.py apply
"""
import argparse
import asyncio
import csv
import json
import os
import re
import sys
from datetime import datetime

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(ROOT, 'data')
CACHE_DIR = os.path.join(ROOT, 'output', 'mavat_cache')
REPORT = os.path.join(ROOT, 'output', 'mavat_refresh_report.csv')
DBS = ['plans_bdika_tichnunit', 'plans_milui_tnaim', 'plans_tanai_saf']

SITE_KEY = '6LeUKkMoAAAAAH4UacB4zewg4ult8Rcriv-ce0Db'
START_URL = 'https://mavat.iplan.gov.il/SV3'

JS_SV4 = """async (mid) => {
  const t = await grecaptcha.execute('%s', {action: 'homepage'});
  const r = await fetch('/rest/api/SV4/1?mid=' + mid + '&guid=0',
                        {headers: {authorization: t, accept: 'application/json, text/plain, */*'}});
  return [r.status, await r.text()];
}""" % SITE_KEY

JS_SEARCH = """async (text) => {
  const t = await grecaptcha.execute('%s', {action: 'homepage'});
  const body = {freeSearchLut: {DESCRIPTION: 'הכל', CODE: -1}, searchName: '', favored: false,
                code: -1, text: text, fromResult: 1, toResult: 20, _page: 1, token: t};
  const r = await fetch('/rest/api/sv3/Search', {method: 'POST',
                        headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
  return [r.status, await r.text()];
}""" % SITE_KEY


def load_db(name):
    with open(os.path.join(DATA_DIR, name + '.json'), encoding='utf-8') as f:
        return json.load(f)


def save_db(name, db):
    path = os.path.join(DATA_DIR, name + '.json')
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def plan_mid(plan):
    m = re.search(r'SV4/1/(\d+)', str(plan.get('mavat_url') or ''))
    return m.group(1) if m else None


def cache_path(key):
    return os.path.join(CACHE_DIR, re.sub(r'[^\w\-]', '_', key) + '.json')


# ---------------------------------------------------------------- fetch

async def _new_page(browser):
    """Open a MAVAT page with reCAPTCHA ready, retrying through network drops."""
    for attempt in range(10):
        page = await browser.new_page()
        try:
            await page.goto(START_URL, timeout=90000)
            await page.wait_for_function('() => window.grecaptcha && grecaptcha.execute', timeout=60000)
            await page.wait_for_timeout(1500)
            return page
        except Exception as e:
            print(f'  page open failed ({e.__class__.__name__}), retry {attempt + 1}/10', flush=True)
            await page.close()
            await asyncio.sleep(min(30 * (attempt + 1), 300))
    raise RuntimeError('MAVAT unreachable')


async def _resolve_mid(page, plan_number):
    """Find a plan's MAVAT id by searching its exact number."""
    status, text = await page.evaluate(JS_SEARCH, plan_number)
    if status != 200:
        raise RuntimeError(f'search HTTP {status}')
    for block in json.loads(text):
        for row in (block.get('result') or {}).get('dtResults') or []:
            if (row.get('ENTITY_NUMBER') or '').strip() == plan_number.strip() and row.get('MP_ID'):
                return str(int(row['MP_ID']))
    return None


async def _worker(name, browser, queue, stats, refetch):
    page = await _new_page(browser)
    while True:
        try:
            plan_number, mid = queue.get_nowait()
        except asyncio.QueueEmpty:
            break
        for attempt in range(3):
            try:
                if not mid:
                    mid = await _resolve_mid(page, plan_number)
                    if not mid:
                        stats['not_found'] += 1
                        _write(cache_path(plan_number), {'_not_found': True, '_plan_number': plan_number})
                        break
                status, text = await page.evaluate(JS_SV4, mid)
                if status != 200:
                    raise RuntimeError(f'SV4 HTTP {status}')
                data = json.loads(text)
                data['_mid'] = mid
                data['_fetched_at'] = datetime.now().isoformat(timespec='seconds')
                _write(cache_path(plan_number), data)
                stats['ok'] += 1
                break
            except Exception as e:
                if attempt == 2:
                    stats['failed'] += 1
                    print(f'  [{name}] FAILED {plan_number}: {e}', flush=True)
                else:
                    await asyncio.sleep(5 * (attempt + 1))
                    try:
                        await page.close()
                    except Exception:
                        pass
                    page = await _new_page(browser)
        done = stats['ok'] + stats['failed'] + stats['not_found']
        if done % 50 == 0:
            print(f'  {done}/{stats["total"]}  ok={stats["ok"]} failed={stats["failed"]} '
                  f'not_found={stats["not_found"]}', flush=True)
    await page.close()


def _write(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)


async def fetch(tabs, refetch):
    from playwright.async_api import async_playwright
    os.makedirs(CACHE_DIR, exist_ok=True)
    todo = {}
    for name in DBS:
        for p in load_db(name)['plans']:
            num = p['plan_number']
            if num in todo:
                continue
            if not refetch and os.path.exists(cache_path(num)):
                continue
            todo[num] = plan_mid(p)
    print(f'{len(todo)} plans to fetch with {tabs} tabs', flush=True)
    queue = asyncio.Queue()
    for item in todo.items():
        queue.put_nowait(item)
    stats = {'ok': 0, 'failed': 0, 'not_found': 0, 'total': len(todo)}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        await asyncio.gather(*[_worker(f't{i}', browser, queue, stats, refetch) for i in range(tabs)])
        await browser.close()
    print(f'done: {stats}', flush=True)


# ---------------------------------------------------------------- apply

def _to_date(s):
    m = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', str(s or ''))
    return datetime(int(m[3]), int(m[2]), int(m[1])) if m else None


def apply():
    rows = []
    now = datetime.now().isoformat(timespec='seconds')
    for name in DBS:
        db = load_db(name)
        changed = 0
        for p in db['plans']:
            path = cache_path(p['plan_number'])
            if not os.path.exists(path):
                continue
            with open(path, encoding='utf-8') as f:
                d = json.load(f)
            if d.get('_not_found'):
                continue
            det = d.get('planDetails') or {}
            loc = (d.get('rsLocation') or [{}])[0]
            # Plans managed outside MAVAT's new system come back as "(חסר)" - not a real status.
            new_status = d.get('unifiedStatus')
            if not new_status or new_status.strip() in ('(חסר)', 'חסר'):
                new_status = p.get('status')
            old_status = p.get('status')

            if not plan_mid(p) and d.get('_mid'):
                p['mavat_url'] = f'https://mavat.iplan.gov.il/SV4/1/{d["_mid"]}/310'
            for field, value in (('district', loc.get('DISTRICT_AREA')),
                                 ('planning_area', loc.get('PLAN_AREA')),
                                 ('municipality', loc.get('JURST_AREA')),
                                 ('plan_type', det.get('ENTITY_SUBTYPE')),
                                 ('area_dunam', d.get('decAreaDunam'))):
                if value not in (None, '') and p.get(field) in (None, '', 'None'):
                    p[field] = value

            milestones = [{'status': m.get('LIS_DESC'), 'date': m.get('EIS_DATE')}
                          for m in (d.get('rsInternet') or []) if m.get('LIS_DESC')]
            milestones.sort(key=lambda m: _to_date(m['date']) or datetime.min)
            p['mavat_milestones'] = milestones
            p['main_status'] = d.get('mainStatus')
            p['status_date'] = d.get('statusDate')
            if det.get('LAST_UPDATE_DATE'):
                p['last_update'] = det['LAST_UPDATE_DATE']
            p['mavat_refreshed_at'] = d.get('_fetched_at') or now

            if new_status and new_status != old_status:
                p['previous_status'] = old_status
                p['status'] = new_status
                stages = p.get('processing_stages')
                if isinstance(stages, list):
                    stages.append({'status': new_status, 'date': d.get('statusDate')})
                changed += 1

            last_ms = milestones[-1] if milestones else {}
            rows.append({
                'db': name, 'plan_number': p['plan_number'], 'plan_name': p.get('plan_name'),
                'authority': p.get('authority'), 'district': p.get('district'),
                'old_status': old_status, 'new_status': p.get('status'),
                'status_changed': 'כן' if new_status and new_status != old_status else '',
                'status_date': d.get('statusDate'),
                'last_milestone': last_ms.get('status'), 'last_milestone_date': last_ms.get('date'),
            })
        db.setdefault('metadata', {})['mavat_refreshed_at'] = now
        save_db(name, db)
        print(f'{name}: {changed} status changes')

    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f'report: {REPORT} ({len(rows)} rows)')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('phase', choices=['fetch', 'apply'])
    ap.add_argument('--tabs', type=int, default=3)
    ap.add_argument('--refetch', action='store_true')
    a = ap.parse_args()
    if a.phase == 'fetch':
        asyncio.run(fetch(a.tabs, a.refetch))
    else:
        apply()


if __name__ == '__main__':
    sys.exit(main())
