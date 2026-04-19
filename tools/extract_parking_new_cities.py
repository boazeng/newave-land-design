#!/usr/bin/env python3
"""
Extract parking device buildings from Givatayim and Bat Yam protocols.
Uses PyMuPDF to find relevant PDFs, Claude Haiku to extract structured data,
and Nominatim for geocoding.

Usage:
  py extract_parking_new_cities.py givatayim
  py extract_parking_new_cities.py batya
  py extract_parking_new_cities.py all
"""
import sys, os, json, re, time, glob, requests
sys.stdout.reconfigure(encoding='utf-8')

# Load API key from .env
_ENV_PATH = r'C:/Users/boaze/Ai-Projects/env/.env'
if os.path.exists(_ENV_PATH):
    for _line in open(_ENV_PATH, encoding='utf-8'):
        _line = _line.strip()
        if _line.startswith('ANTHROPIC_API_KEY='):
            os.environ['ANTHROPIC_API_KEY'] = _line.split('=', 1)[1].strip().strip('"\'')
            break

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
CACHE_FILE = os.path.join(DATA_DIR, 'geocode_cache.json')
PROGRESS_DIR = os.path.dirname(__file__)

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

PARKING_KEYWORDS = [
    'מתקן חניה', 'מתקן חנייה', 'חניה מכנית', 'חנייה מכנית',
    'חניה אוטומטית', 'חנייה אוטומטית', 'חניה רובוטית', 'חנייה רובוטית',
    'מכפיל חניה', 'מגדל חניה', 'חניון מכני', 'מעלית חניה',
    'פלטפורמת חניה', 'parking device', 'automated parking',
]

CITY_CONFIG = {
    'givatayim': {
        'name': 'גבעתיים',
        'pdf_dir': os.path.join(DATA_DIR, 'protocols_search', 'גבעתיים'),
        'output': os.path.join(DATA_DIR, 'parking_protocols_givatayim.json'),
        'progress': os.path.join(PROGRESS_DIR, 'parking_givatayim_progress.json'),
    },
    'batya': {
        'name': 'בת ים',
        'pdf_dir': os.path.join(DATA_DIR, 'protocols_search', 'בת_ים'),
        'output': os.path.join(DATA_DIR, 'parking_protocols_batya.json'),
        'progress': os.path.join(PROGRESS_DIR, 'parking_batya_progress.json'),
    },
    'rishon': {
        'name': 'ראשון לציון',
        'pdf_dir': os.path.join(DATA_DIR, 'protocols_search', 'ראשון_לציון'),
        'output': os.path.join(DATA_DIR, 'parking_protocols_rishon.json'),
        'progress': os.path.join(PROGRESS_DIR, 'parking_rishon_progress.json'),
    },
    'netanya': {
        'name': 'נתניה',
        'pdf_dir': os.path.join(DATA_DIR, 'protocols_search', 'נתניה'),
        'output': os.path.join(DATA_DIR, 'parking_protocols_netanya.json'),
        'progress': os.path.join(PROGRESS_DIR, 'parking_netanya_progress.json'),
    },
}


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def geocode(address, city, cache):
    key = f"{address}, {city}"
    if key in cache:
        return cache[key]
    query = f"{address} {city} ישראל"
    try:
        resp = requests.get(NOMINATIM_URL, params={
            "q": query, "format": "json", "limit": 1, "countrycodes": "il",
        }, headers={"User-Agent": "NewaveLandDesign/1.0"}, timeout=10)
        if resp.status_code == 200:
            results = resp.json()
            if results:
                coords = {"lat": float(results[0]["lat"]), "lng": float(results[0]["lon"])}
                cache[key] = coords
                save_cache(cache)
                return coords
    except Exception:
        pass
    cache[key] = None
    save_cache(cache)
    return None


def extract_text_from_pdf(pdf_path):
    try:
        import fitz
        doc = fitz.open(pdf_path)
        text = ''
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        return ''


def has_parking_keywords(text):
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in PARKING_KEYWORDS)


def fix_json_strings(s):
    result_chars = []
    in_string = False
    escaped = False
    for i, ch in enumerate(s):
        if escaped:
            result_chars.append(ch); escaped = False
        elif ch == '\\':
            result_chars.append(ch); escaped = True
        elif ch == '"' and not in_string:
            in_string = True; result_chars.append(ch)
        elif ch == '"' and in_string:
            rest = s[i+1:].lstrip()
            if rest and rest[0] in ':,}]':
                in_string = False; result_chars.append(ch)
            else:
                result_chars.append('\\"')
        else:
            result_chars.append(ch)
    return ''.join(result_chars)


def extract_relevant_text(text, max_chars=8000):
    """Extract text focused on keyword-matching regions rather than just the start."""
    text_lower = text.lower()
    positions = []
    for kw in PARKING_KEYWORDS:
        idx = 0
        while True:
            pos = text_lower.find(kw.lower(), idx)
            if pos == -1:
                break
            positions.append(pos)
            idx = pos + 1

    if not positions:
        return text[:max_chars]

    # Build excerpts around each keyword hit (2000 chars context each)
    excerpts = []
    seen_ranges = []
    for pos in sorted(set(positions)):
        start = max(0, pos - 800)
        end = min(len(text), pos + 1200)
        # Merge overlapping ranges
        merged = False
        for i, (s, e) in enumerate(seen_ranges):
            if start <= e and end >= s:
                seen_ranges[i] = (min(s, start), max(e, end))
                merged = True
                break
        if not merged:
            seen_ranges.append((start, end))

    chunks = [text[s:e] for s, e in seen_ranges]
    combined = '\n---\n'.join(chunks)
    return combined[:max_chars]


def extract_parking_with_claude(text, filename, city_name):
    if not ANTHROPIC_API_KEY:
        return []

    text_truncated = extract_relevant_text(text, max_chars=8000)
    prompt = f"""אתה מנתח פרוטוקולי ועדת תכנון ובניה. מצא בטקסט הבא כל הבניינים שבהם מאושר או מוזכר מתקן חניה מכני/אוטומטי/רובוטי/מכפיל.

עבור כל בניין החזר JSON עם השדות:
- address: כתובת המלאה (רחוב + מספר)
- gush: מספר גוש (אם קיים)
- helka: מספר חלקה (אם קיים)
- device_types: סוג המתקן (אוטומטי/רובוטי/מכפיל/מגדל/אחר)
- parking_count: מספר מקומות חניה במתקן (מספר שלם בלבד, 0 אם לא ידוע)
- description: תיאור קצר של הפרויקט (עד 200 תווים)
- date: תאריך הפרוטוקול אם מוזכר (DD/MM/YYYY)

החזר ONLY מערך JSON תקין. אם אין מתקני חניה מכניים — החזר [].

טקסט מתוך הקובץ {filename}:
{text_truncated}"""

    try:
        resp = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': ANTHROPIC_API_KEY,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
            },
            json={
                'model': 'claude-haiku-4-5-20251001',
                'max_tokens': 1024,
                'messages': [{'role': 'user', 'content': prompt}],
            },
            timeout=30,
        )
        if resp.status_code != 200:
            return []

        raw = resp.json()['content'][0]['text'].strip()
        raw = raw.replace('בע"מ', 'בע״מ')

        # Extract JSON array
        m = re.search(r'\[.*\]', raw, re.DOTALL)
        if not m:
            return []

        json_str = fix_json_strings(m.group(0))
        items = json.loads(json_str)
        if not isinstance(items, list):
            return []

        # Add source file
        for item in items:
            item['source_files'] = [os.path.basename(filename)]
            item['city'] = city_name
        return items

    except Exception as e:
        return []


def load_progress(progress_file):
    if os.path.exists(progress_file):
        with open(progress_file, encoding='utf-8') as f:
            return json.load(f)
    return {'processed': [], 'buildings': []}


def save_progress(progress_file, data):
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def process_city(city_key):
    config = CITY_CONFIG[city_key]
    city_name = config['name']
    pdf_dir = config['pdf_dir']
    output_file = config['output']
    progress_file = config['progress']

    print(f'\n=== Processing {city_name} ===')

    if not os.path.exists(pdf_dir):
        print(f'ERROR: PDF dir not found: {pdf_dir}')
        return

    # Find all PDFs
    all_pdfs = glob.glob(os.path.join(pdf_dir, '**', '*.pdf'), recursive=True)
    print(f'Found {len(all_pdfs)} PDFs')

    # Load progress
    progress = load_progress(progress_file)
    processed_set = set(progress['processed'])
    buildings = progress['buildings']

    # Filter to only ועדת_משנה PDFs (most relevant)
    relevant_pdfs = [p for p in all_pdfs if 'ועדת_משנה' in p or 'ועדה' in p.lower()]
    if not relevant_pdfs:
        relevant_pdfs = all_pdfs
    print(f'Relevant PDFs (ועדת משנה): {len(relevant_pdfs)}')

    todo = [p for p in relevant_pdfs if p not in processed_set]
    print(f'To process: {len(todo)} (already done: {len(processed_set)})')

    keyword_matches = 0
    new_buildings = 0

    for i, pdf_path in enumerate(todo):
        filename = os.path.basename(pdf_path)
        text = extract_text_from_pdf(pdf_path)

        if not has_parking_keywords(text):
            processed_set.add(pdf_path)
            if (i + 1) % 50 == 0:
                print(f'  [{i+1}/{len(todo)}] scanned, {keyword_matches} matches so far')
            continue

        keyword_matches += 1
        print(f'  [{i+1}/{len(todo)}] MATCH: {filename}')

        items = extract_parking_with_claude(text, filename, city_name)
        if items:
            buildings.extend(items)
            new_buildings += len(items)
            print(f'    -> {len(items)} buildings extracted')
        else:
            print(f'    -> no buildings found')

        processed_set.add(pdf_path)

        # Save progress every 10 matches
        if keyword_matches % 10 == 0:
            progress['processed'] = list(processed_set)
            progress['buildings'] = buildings
            save_progress(progress_file, progress)

        time.sleep(0.5)

    # Final save
    progress['processed'] = list(processed_set)
    progress['buildings'] = buildings
    save_progress(progress_file, progress)

    print(f'\nScan complete: {keyword_matches} PDFs matched, {new_buildings} new buildings extracted')
    print(f'Total buildings: {len(buildings)}')

    # Geocode and build final output
    print('\nGeocoding addresses...')
    cache = load_cache()
    from collections import defaultdict

    by_address = defaultdict(list)
    for b in buildings:
        addr = (b.get('address') or '').strip()
        if addr:
            by_address[addr].append(b)

    print(f'Unique addresses: {len(by_address)}')
    sites = []
    geocoded_count = 0

    for j, (address, bldgs) in enumerate(sorted(by_address.items())):
        device_types = list({b.get('device_types', b.get('device_type', '')) for b in bldgs if b.get('device_types') or b.get('device_type')})
        total_parking = sum(int(b.get('parking_count', 0) or 0) for b in bldgs)
        gushes = sorted({str(b['gush']) for b in bldgs if b.get('gush')})
        helkas = sorted({str(b['helka']) for b in bldgs if b.get('helka')})
        dates = sorted({b['date'] for b in bldgs if b.get('date')})
        descriptions = [b['description'] for b in bldgs if b.get('description')]
        source_files = list({f for b in bldgs for f in (b.get('source_files') or [])})

        # Clean address for geocoding
        cleaned = re.sub(r'^רחוב\s+', '', address)
        cleaned = re.split(r'[,/]', cleaned)[0].strip()
        cleaned = re.sub(r'\(.*?\)', '', cleaned).strip()

        coords = geocode(cleaned, city_name, cache)
        if not coords and cleaned != address:
            coords = geocode(address, city_name, cache)
        if coords:
            geocoded_count += 1

        if (j + 1) % 20 == 0:
            print(f'  [{j+1}/{len(by_address)}] geocoded: {geocoded_count}')

        time.sleep(1.1)

        sites.append({
            'id': j + 1,
            'address': address,
            'city': city_name,
            'city_key': city_key,
            'device_types': ' | '.join(filter(None, device_types)),
            'parking_count': total_parking or None,
            'gush': ', '.join(gushes),
            'helka': ', '.join(helkas),
            'dates': ', '.join(dates),
            'record_count': len(bldgs),
            'description': descriptions[0][:200] if descriptions else '',
            'source_files': source_files[:3],
            'lat': coords['lat'] if coords else None,
            'lng': coords['lng'] if coords else None,
        })

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sites, f, ensure_ascii=False, indent=2)

    no_coords = sum(1 for s in sites if not s.get('lat'))
    print(f'\nSaved {len(sites)} buildings to {output_file}')
    print(f'Geocoded: {geocoded_count}/{len(by_address)} | Without coords: {no_coords}')


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else 'all'

    if arg == 'all':
        for key in CITY_CONFIG:
            process_city(key)
    elif arg in CITY_CONFIG:
        process_city(arg)
    else:
        print(f'Unknown city: {arg}. Use: {" / ".join(CITY_CONFIG.keys())} / all')
        sys.exit(1)


if __name__ == '__main__':
    main()
