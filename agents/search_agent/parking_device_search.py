#!/usr/bin/env python3
"""
סוכן חיפוש מתקני חניה בפרוטוקולי ועדות תכנון.
שלב 1: סריקה מהירה עם PyMuPDF - חיפוש מילות מפתח
שלב 2: חילוץ מידע עם Claude API

הרצה:
    python parking_device_search.py --input-dir <dir> --output <results.json>
    python parking_device_search.py --input-dir <dir> --scan-only
"""
import sys, os, json, re, argparse, time
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1, encoding='utf-8')

import fitz  # PyMuPDF
from dotenv import load_dotenv

# Try multiple env paths
for env_candidate in [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'env', '.env'),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'env', '.env'),
    'c:/Users/boaze/Ai-Projects/env/.env',
]:
    if os.path.exists(env_candidate):
        load_dotenv(env_candidate)
        break

PARKING_KEYWORDS = [
    'מתקן רובוטי', 'מתקן אוטומטי', 'מתקני חניה', 'מתקן חניה',
    'מתקני חנייה', 'מתקן חנייה', 'מכפילי חניה', 'מכפילי חנייה',
    'מכפילים', 'מכפיל חניה', 'מכפיל חנייה', 'חניה רובוטית',
    'חנייה רובוטית', 'חניה אוטומטית', 'חנייה אוטומטית',
    'חניה מכנית', 'חנייה מכנית', 'מתקן חצי אוטומטי',
    'מתקן רכבים', 'מגדל חניה', 'מגדל חנייה',
]

KEYWORD_PATTERN = re.compile('|'.join(re.escape(kw) for kw in PARKING_KEYWORDS))


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using PyMuPDF."""
    pages = []
    try:
        doc = fitz.open(pdf_path)
        for i, page in enumerate(doc):
            text = page.get_text()
            if text and len(text.strip()) > 10:
                pages.append((i + 1, text))
        doc.close()
    except:
        pass
    return pages


def scan_pdf_for_keywords(pdf_path):
    pages = extract_text_from_pdf(pdf_path)
    if not pages:
        return False, [], []
    matching_pages = []
    for page_num, text in pages:
        if KEYWORD_PATTERN.search(text):
            matching_pages.append((page_num, text))
    return len(matching_pages) > 0, matching_pages, pages


def extract_info_with_claude(filename, matching_pages, all_pages):
    import anthropic
    api_key = os.getenv('ANTHROPIC_API_KEY')
    model = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-20250514')
    if not api_key:
        return None

    client = anthropic.Anthropic(api_key=api_key)

    # Send each matching page separately to avoid context limits
    all_buildings = []

    # Group matching pages by building (consecutive pages often belong to same building)
    # Send all matching pages together but limit total context
    context = f"שם הקובץ: {filename}\n\n"
    for pn, text in matching_pages:
        context += f"--- עמוד {pn} ---\n{text}\n\n"

    if len(context) > 15000:
        context = context[:15000]

    prompt = f"""{context}

---

הפרוטוקול לעיל הוא מפרוטוקול ועדת תכנון ובנייה בתל אביב. נמצאו בו אזכורים של מתקני חניה.

חלץ את כל הפרויקטים/בניינים שבהם מוזכר שימוש במתקן חניה (מתקן רובוטי, מכפילים, מתקן אוטומטי, מתקן חניה מכנית וכו').

עבור כל פרויקט, החזר JSON array:

[{{
  "gush": "מספר גוש (אם מוזכר, אחרת null)",
  "helka": "מספר חלקה (אם מוזכר, אחרת null)",
  "address": "כתובת הבניין (אם מוזכרת, אחרת null)",
  "date": "תאריך הפרוטוקול/הישיבה (DD/MM/YYYY, אחרת null)",
  "description": "סיכום קצר (1-2 משפטים) של הפרויקט ותיאור מתקן החניה",
  "parking_count": "מספר מקומות חניה במתקן (מספר, אחרת null)",
  "device_type": "סוג המתקן (מכפיל/רובוטי/אוטומטי/חצי אוטומטי/מכני/אחר)"
}}]

חשוב: חלץ רק פרויקטים שבהם מתואר מתקן חניה מכני/אוטומטי/רובוטי/מכפיל - לא חניה רגילה.
אם אין פרויקטים כאלה, החזר [].
החזר רק JSON, ללא טקסט נוסף."""

    try:
        response = client.messages.create(
            model=model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        # Remove markdown code blocks if present
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'\s*```$', '', text)

        if text.startswith('['):
            return json.loads(text)
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return []
    except Exception as e:
        print(f"    Claude API error: {type(e).__name__}: {str(e)[:200]}")
        return None


def scan_directory(input_dir, scan_only=False):
    results = []
    pdf_files = []
    for root, dirs, files in os.walk(input_dir):
        for f in files:
            if f.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, f))

    print(f"Found {len(pdf_files)} PDFs to scan")

    # Phase 1: Quick keyword scan
    print("\n--- Phase 1: Keyword Scan ---")
    matches = []
    for i, pdf_path in enumerate(pdf_files):
        has_match, matching_pages, all_pages = scan_pdf_for_keywords(pdf_path)
        if has_match:
            matches.append({
                'path': pdf_path,
                'filename': os.path.basename(pdf_path),
                'matching_pages': matching_pages,
                'all_pages': all_pages,
            })
            keywords_found = set()
            for _, text in matching_pages:
                for kw in PARKING_KEYWORDS:
                    if kw in text:
                        keywords_found.add(kw)
            print(f"  MATCH [{i+1}]: {os.path.basename(pdf_path)} ({len(matching_pages)} pages, {', '.join(keywords_found)})")

        if (i + 1) % 50 == 0:
            print(f"  Scanned [{i+1}/{len(pdf_files)}] - {len(matches)} matches so far")

    print(f"\nPhase 1 complete: {len(matches)} PDFs with parking keywords out of {len(pdf_files)}")

    if scan_only:
        return matches, []

    if not matches:
        return matches, []

    # Phase 2: Claude API extraction
    print(f"\n--- Phase 2: AI Extraction ({len(matches)} PDFs) ---")
    all_buildings = []

    for i, match in enumerate(matches):
        print(f"  [{i+1}/{len(matches)}] {match['filename']}...")

        extracted = extract_info_with_claude(
            match['filename'],
            match['matching_pages'],
            match['all_pages'],
        )

        if extracted is None:
            print(f"    API error, skipping")
            continue

        if not extracted:
            print(f"    No parking devices (false positive)")
            continue

        for building in extracted:
            building['source_file'] = match['filename']
            all_buildings.append(building)

        print(f"    Found {len(extracted)} building(s)")
        time.sleep(1)

    return matches, all_buildings


def main():
    parser = argparse.ArgumentParser(description='Parking Device Search Agent')
    parser.add_argument('--input-dir', type=str, required=True)
    parser.add_argument('--output', type=str, default=None)
    parser.add_argument('--scan-only', action='store_true')
    args = parser.parse_args()

    if not args.output:
        args.output = os.path.join(
            os.path.dirname(__file__), '..', '..', 'data', 'parking_devices_search_results.json'
        )

    print("=" * 60)
    print("  Parking Device Search Agent")
    print(f"  Input: {args.input_dir}")
    print(f"  Mode: {'Scan only' if args.scan_only else 'Full extraction'}")
    print("=" * 60)

    matches, buildings = scan_directory(args.input_dir, args.scan_only)

    output_data = {
        'search_date': datetime.now().isoformat(),
        'input_dir': args.input_dir,
        'total_pdfs_scanned': sum(1 for _ in Path(args.input_dir).rglob('*.pdf')),
        'pdfs_with_keywords': len(matches),
        'matched_files': [m['filename'] for m in matches],
        'buildings': buildings,
        'total_buildings': len(buildings),
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"  PDFs scanned: {output_data['total_pdfs_scanned']}")
    print(f"  PDFs with parking keywords: {len(matches)}")
    print(f"  Buildings with parking devices: {len(buildings)}")
    print(f"  Results saved to: {args.output}")

    if buildings:
        print(f"\n  Buildings found:")
        for b in buildings:
            addr = b.get('address') or '?'
            gush = b.get('gush') or '?'
            helka = b.get('helka') or '?'
            count = b.get('parking_count') or '?'
            device = b.get('device_type') or '?'
            date = b.get('date') or '?'
            print(f"    {addr} | גוש {gush} חלקה {helka} | {count} חניות | {device} | {date}")


if __name__ == '__main__':
    main()
