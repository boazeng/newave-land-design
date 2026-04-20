#!/usr/bin/env python3
"""
Download planning committee protocols for Haifa (חיפה) - siteid=16
Uses the complot.co.il API system (handasi.complot.co.il).
Committee IDs change over time; all are saved as type_{v} folders.
"""
import sys, os, re, time, json, requests
sys.stdout.reconfigure(encoding='utf-8')

SITE_ID = 16
CITY_NAME = 'חיפה'
BASE_API = 'https://handasi.complot.co.il/magicscripts/mgrqispi.dll'
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'protocols_search', 'חיפה')
INDEX_FILE = os.path.join(OUTPUT_DIR, 'index.json')

# Haifa committee IDs shift over years - map known ones, fallback to type_{v}
COMMITTEE_NAMES = {
    '2': 'מליאת_הועדה',     # 2024+
    '3': 'ועדת_משנה',       # 2024+
    '4': 'type_4',
    '5': 'ועדת_שימור',
    '7': 'רשות_רישוי',
    '332': 'מליאת_הועדה',   # 2015-2016
    '333': 'ועדת_משנה',     # 2015-2016
    '342': 'מליאת_הועדה',   # 2021-2023
    '343': 'ועדת_משנה',     # 2021-2023
}

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
s.verify = False


def get_meetings_for_year(year):
    url = (f'{BASE_API}?appname=cixpa&prgname=GetMeetingByDate'
           f'&siteid={SITE_ID}&v=0&fd=01/01/{year}&td=31/12/{year}'
           f'&l=true&arguments=siteid,v,fd,td,l')
    r = s.get(url, timeout=30)
    r.raise_for_status()
    meetings = re.findall(r'getMeeting\((\d+),(\d+)\)', r.text)
    seen = set()
    unique = []
    for m in meetings:
        if m not in seen:
            seen.add(m)
            unique.append(m)
    return unique


def get_meetings(start_year=2015, end_year=2026):
    all_meetings = []
    seen = set()
    for year in range(start_year, end_year + 1):
        try:
            year_meetings = get_meetings_for_year(year)
            for m in year_meetings:
                if m not in seen:
                    seen.add(m)
                    all_meetings.append(m)
            print(f'  {year}: {len(year_meetings)} meetings')
            time.sleep(0.5)
        except Exception as e:
            print(f'  {year}: ERROR - {e}')
    return all_meetings


def get_meeting_docs(v, n):
    url = (f'{BASE_API}?appname=cixpa&prgname=GetMeetingDocs'
           f'&siteid={SITE_ID}&v={v}&n={n}&arguments=siteid,v,n')
    r = s.get(url, timeout=30)
    r.raise_for_status()
    links = re.findall(r'href="(https://archive\.gis-net[^"]+\.pdf)"', r.text, re.IGNORECASE)
    texts = re.findall(r'href="https://archive\.gis-net[^"]+\.pdf"[^>]*>([^<]+)<', r.text)
    dates = re.findall(r'(\d{2}/\d{2}/\d{4})', r.text)
    date = dates[0] if dates else ''
    return links, texts, date


def download_file(url, filepath):
    if os.path.exists(filepath):
        return True, os.path.getsize(filepath), 'skipped'
    try:
        r = s.get(url, timeout=60)
        r.raise_for_status()
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            f.write(r.content)
        return True, len(r.content), 'downloaded'
    except Exception as e:
        return False, 0, str(e)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f'=== Downloading {CITY_NAME} protocols (siteid={SITE_ID}) ===')
    print('Fetching meetings year by year...')
    meetings = get_meetings(2015, 2026)
    print(f'Found {len(meetings)} unique meetings total')

    index = []
    total_downloaded = 0
    total_skipped = 0
    total_failed = 0

    for i, (v, n) in enumerate(meetings):
        committee_dir = COMMITTEE_NAMES.get(v, f'type_{v}')
        os.makedirs(os.path.join(OUTPUT_DIR, committee_dir), exist_ok=True)

        try:
            links, texts, date = get_meeting_docs(v, n)
        except Exception as e:
            print(f'  [{i+1}/{len(meetings)}] meeting v={v} n={n}: ERROR fetching docs: {e}')
            time.sleep(1)
            continue

        date_str = date.replace('/', '-') if date else 'unknown'
        print(f'[{i+1}/{len(meetings)}] v={v} n={n} date={date} -> {len(links)} docs')

        for j, url in enumerate(links):
            doc_text = texts[j].strip() if j < len(texts) else f'doc_{j+1}'
            doc_text_clean = re.sub(r'[<>:"/\\|?*]', '_', doc_text)[:60]
            filename = f'{date_str}_{n}_{doc_text_clean}.pdf'
            filepath = os.path.join(OUTPUT_DIR, committee_dir, filename)

            ok, size, status = download_file(url, filepath)
            entry = {
                'committee_type': v,
                'committee_name': committee_dir,
                'meeting_num': n,
                'date': date,
                'doc_type': doc_text,
                'url': url,
                'local_file': filepath,
                'filename': filename,
                'success': ok,
                'size': size,
                'status': status,
            }
            index.append(entry)

            if ok and status == 'downloaded':
                total_downloaded += 1
                print(f'  OK {filename} ({size:,} bytes)')
            elif ok and status == 'skipped':
                total_skipped += 1
            else:
                total_failed += 1
                print(f'  FAIL {url}: {status}')

            time.sleep(0.2)

        time.sleep(0.3)

    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print('=' * 60)
    print(f'Done! Downloaded: {total_downloaded}, Skipped: {total_skipped}, Failed: {total_failed}')
    print(f'Index: {INDEX_FILE}')
    print(f'Total docs on disk: {total_downloaded + total_skipped}')


if __name__ == '__main__':
    main()
