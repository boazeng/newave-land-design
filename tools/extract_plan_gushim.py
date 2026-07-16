"""
Fill in a plan's gushim/helkot from its הוראות PDF.

Most plan records already carry `gushim`, but some were scraped without it. The
data is in the PDF's "גושים וחלקות בתכנית" table (section 1.5.5), which PyMuPDF
can read directly.

PDF text comes out in visual order, so Hebrew arrives reversed ('שוג רפסמ' is
'מספר גוש'). Columns are matched by header text rather than position, since the
column order is not guaranteed across plans.

Usage:
  python tools/extract_plan_gushim.py 457-0434621 --dry-run
  python tools/extract_plan_gushim.py 457-0434621            # writes to the plans DB
  python tools/extract_plan_gushim.py --missing --dry-run    # every plan lacking gushim
"""
import sys
import os
import re
import json
import tempfile

import requests
import fitz

sys.stdout.reconfigure(encoding='utf-8')  # Hebrew output dies on the default cp1252 console

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, 'backend'))

from services.projects_service import find_plan, sharepoint_folder  # noqa: E402
from services.sharepoint_pdf_service import get_pdf_url  # noqa: E402

DATA_DIR = os.path.join(REPO, 'data')

HEADER_GUSH = 'מספר גוש'
HEADER_FULL = 'בשלמותן'
HEADER_PARTIAL = 'בחלקן'
# Print-counter watermark that bleeds into cells ('מונה' in visual order)
NOISE = 'הנומ'


def _logical(text):
    """PDF text is visual order; reverse each line to read Hebrew logically."""
    return '\n'.join(line[::-1] for line in (text or '').split('\n'))


def _clean_helkot(cell):
    """A helkot cell is numbers, ranges and commas. Drop watermark noise."""
    if not cell:
        return ''
    cell = cell.replace(NOISE, ' ')
    parts = [p.strip() for p in re.split(r'[\n,]', cell) if p.strip()]
    kept = [p for p in parts if re.fullmatch(r'\d+(\s*-\s*\d+)?', p)]
    return ', '.join(kept)


def _find_gushim_table(doc):
    """The 1.5.5 table, identified by its header rather than a page number."""
    for page in doc:
        for table in page.find_tables().tables:
            rows = table.extract()
            if not rows:
                continue
            header = [_logical(c or '') for c in rows[0]]
            if any(HEADER_GUSH in h for h in header):
                return header, rows[1:]
    return None, None


def extract_gushim(pdf_path):
    """-> [{'gush': int, 'helkot_full': str, 'helkot_partial': str}]"""
    doc = fitz.open(pdf_path)
    header, rows = _find_gushim_table(doc)
    if not header:
        return []

    def col(match):
        for i, h in enumerate(header):
            if match in h:
                return i
        return None

    i_gush, i_full, i_partial = col(HEADER_GUSH), col(HEADER_FULL), col(HEADER_PARTIAL)
    if i_gush is None:
        return []

    out = []
    for row in rows:
        raw = (row[i_gush] or '').strip()
        if not raw.isdigit():
            continue  # skip stray/continuation rows
        out.append({
            'gush': int(raw),
            'helkot_full': _clean_helkot(row[i_full]) if i_full is not None else '',
            'helkot_partial': _clean_helkot(row[i_partial]) if i_partial is not None else '',
        })
    return out


def fetch_pdf(plan):
    """Download the plan's הוראות PDF from SharePoint to a temp file."""
    files = [f for f in (plan.get('downloaded_files') or []) if 'הוראות' in f]
    if not files:
        return None
    folder = sharepoint_folder(plan)
    if not folder:
        return None
    url = get_pdf_url(files[0], [folder])
    if not url:
        return None
    resp = requests.get(url, timeout=180)
    if resp.status_code != 200:
        return None
    fd, path = tempfile.mkstemp(suffix='.pdf')
    with os.fdopen(fd, 'wb') as f:
        f.write(resp.content)
    return path


def save_gushim(db_name, plan_number, gushim):
    path = os.path.join(DATA_DIR, f'{db_name}.json')
    with open(path, encoding='utf-8') as f:
        db = json.load(f)
    plans = db['plans'] if isinstance(db, dict) else db
    for p in plans:
        if p['plan_number'] == plan_number:
            p['gushim'] = gushim
            break
    else:
        return False
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    return True


def process(plan_number, dry_run):
    plan, db_name = find_plan(plan_number)
    if not plan:
        print(f'  {plan_number}: plan not found')
        return False
    if plan.get('gushim'):
        print(f'  {plan_number}: already has {len(plan["gushim"])} gushim, skipping')
        return False

    pdf = fetch_pdf(plan)
    if not pdf:
        print(f'  {plan_number}: no הוראות PDF reachable')
        return False
    try:
        gushim = extract_gushim(pdf)
    finally:
        os.unlink(pdf)

    if not gushim:
        print(f'  {plan_number}: no gushim table found in PDF')
        return False

    total = sum(len(g['helkot_full'].split(',')) + len(g['helkot_partial'].split(','))
                for g in gushim)
    print(f'  {plan_number} ({db_name}): {len(gushim)} gushim, ~{total} helka entries')
    for g in gushim:
        print(f"    גוש {g['gush']}: בשלמותן [{g['helkot_full']}] בחלקן [{g['helkot_partial']}]")
    if dry_run:
        return True
    return save_gushim(db_name, plan_number, gushim)


def plans_missing_gushim():
    out = []
    for fname in os.listdir(DATA_DIR):
        if not (fname.startswith('plans_') and fname.endswith('.json')):
            continue
        with open(os.path.join(DATA_DIR, fname), encoding='utf-8') as f:
            db = json.load(f)
        plans = db.get('plans', []) if isinstance(db, dict) else db
        for p in plans:
            if isinstance(p, dict) and p.get('plan_number') and not p.get('gushim'):
                if p.get('downloaded_files'):
                    out.append(p['plan_number'])
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry_run = '--dry-run' in sys.argv

    if '--missing' in sys.argv:
        targets = plans_missing_gushim()
        print(f'{len(targets)} plans missing gushim (with a PDF available)')
    elif args:
        targets = args
    else:
        print(__doc__)
        return 1

    ok = 0
    for t in targets:
        if process(t, dry_run):
            ok += 1
    print(f"\n{'[dry-run] ' if dry_run else ''}{ok}/{len(targets)} extracted")
    return 0


if __name__ == '__main__':
    sys.exit(main())
