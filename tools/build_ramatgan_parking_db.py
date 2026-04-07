"""
Build parking devices database for Ramat Gan with geocoding.
Groups by address, geocodes, and saves for map display.
"""
import json
import os
import sys
import re
import time
import requests
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
CACHE_FILE = os.path.join(DATA_DIR, 'geocode_cache.json')
OUTPUT = os.path.join(DATA_DIR, 'parking_protocols_ramatgan.json')
SOURCE = os.path.join(DATA_DIR, 'parking_results_ramat_gan.json')

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def clean_address(addr):
    """Clean address for better geocoding."""
    addr = addr.strip()
    # Remove "רחוב" prefix
    addr = re.sub(r'^רחוב\s+', '', addr)
    # Take first address if intersection
    parts = re.split(r'[,/]', addr)
    addr = parts[0].strip()
    # Remove parenthetical
    addr = re.sub(r'\(.*?\)', '', addr).strip()
    return addr


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


def main():
    with open(SOURCE, encoding='utf-8') as f:
        data = json.load(f)
    buildings = data.get('buildings', [])
    print(f"Loaded {len(buildings)} buildings")

    # Group by address
    by_address = defaultdict(list)
    skipped = 0
    for b in buildings:
        addr = (b.get('address') or '').strip()
        if not addr:
            skipped += 1
            continue
        by_address[addr].append(b)

    print(f"Unique addresses: {len(by_address)} (skipped {skipped} without address)")

    cache = load_cache()
    sites = []
    geocoded = 0
    total = len(by_address)

    for i, (address, bldgs) in enumerate(sorted(by_address.items())):
        device_types = []
        total_parking = 0
        gushes = set()
        helkas = set()
        dates = set()
        descriptions = []

        for b in bldgs:
            dt = b.get('device_type', '')
            if dt and dt not in device_types:
                device_types.append(dt)
            try:
                total_parking += int(b.get('parking_count', 0) or 0)
            except (ValueError, TypeError):
                pass
            if b.get('gush'):
                gushes.add(str(b['gush']))
            if b.get('helka'):
                helkas.add(str(b['helka']))
            if b.get('date'):
                dates.add(b['date'])
            if b.get('description'):
                descriptions.append(b['description'])

        cleaned = clean_address(address)
        coords = geocode(cleaned, 'רמת גן', cache)

        if not coords and cleaned != address:
            # Try original
            coords = geocode(address, 'רמת גן', cache)

        if coords:
            geocoded += 1

        if (i + 1) % 20 == 0:
            print(f"  [{i+1}/{total}] geocoded so far: {geocoded}")

        time.sleep(1.1)

        sites.append({
            'id': i + 1,
            'address': address,
            'city': 'רמת גן',
            'device_types': ' | '.join(device_types),
            'parking_count': total_parking,
            'gush': ', '.join(sorted(gushes)),
            'helka': ', '.join(sorted(helkas)),
            'dates': ', '.join(sorted(dates)),
            'record_count': len(bldgs),
            'description': (descriptions[0][:200] if descriptions else ''),
            'lat': coords['lat'] if coords else None,
            'lng': coords['lng'] if coords else None,
        })

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(sites, f, ensure_ascii=False, indent=2)

    remaining = sum(1 for s in sites if not s.get('lat') or not s.get('lng'))
    print(f"\nSaved {len(sites)} sites to {OUTPUT}")
    print(f"Geocoded: {geocoded}/{total}")
    print(f"Without coords: {remaining}")


if __name__ == "__main__":
    main()
