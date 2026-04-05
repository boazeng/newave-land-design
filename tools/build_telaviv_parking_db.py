"""
Build a database of parking devices from Tel Aviv committee protocols.
Merges results from 3 source files, deduplicates by address,
geocodes addresses, and saves as parking_protocols_telaviv.json
for display on the map.
"""
import json
import os
import sys
import time
import requests
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
CACHE_FILE = os.path.join(DATA_DIR, 'geocode_cache.json')
OUTPUT = os.path.join(DATA_DIR, 'parking_protocols_telaviv.json')

SOURCE_FILES = [
    'parking_results_vaada_mishne.json',
    'parking_results_vaada_old.json',
    'parking_results_vaada_rishui.json',
]

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def geocode(address, cache):
    """Geocode an address in Tel Aviv."""
    key = address + ", תל אביב"
    if key in cache:
        return cache[key]

    query = f"{address} תל אביב ישראל"
    try:
        resp = requests.get(NOMINATIM_URL, params={
            "q": query,
            "format": "json",
            "limit": 1,
            "countrycodes": "il",
        }, headers={
            "User-Agent": "NewaveLandDesign/1.0",
        }, timeout=10)
        if resp.status_code == 200:
            results = resp.json()
            if results:
                coords = {
                    "lat": float(results[0]["lat"]),
                    "lng": float(results[0]["lon"]),
                }
                cache[key] = coords
                save_cache(cache)
                return coords
    except Exception as e:
        print(f"  Geocode error for '{address}': {e}")

    cache[key] = None
    save_cache(cache)
    return None


def main():
    # Load all buildings
    all_buildings = []
    for f in SOURCE_FILES:
        path = os.path.join(DATA_DIR, f)
        if not os.path.exists(path):
            print(f"Skip: {f} not found")
            continue
        with open(path, encoding='utf-8') as fh:
            data = json.load(fh)
        all_buildings.extend(data.get('buildings', []))
    print(f"Loaded {len(all_buildings)} buildings from {len(SOURCE_FILES)} files")

    # Group by address (one entry per building)
    by_address = defaultdict(list)
    for b in all_buildings:
        addr = (b.get('address') or '').strip()
        if addr:
            by_address[addr].append(b)

    print(f"Unique addresses: {len(by_address)}")

    # Load geocode cache
    cache = load_cache()
    print(f"Geocode cache: {len(cache)} entries")

    # Build output
    sites = []
    geocoded = 0
    total = len(by_address)

    for i, (address, buildings) in enumerate(sorted(by_address.items())):
        # Aggregate data from all records for this address
        device_types = []
        total_parking = 0
        gushes = set()
        helkas = set()
        dates = set()
        descriptions = []
        source_files = set()

        for b in buildings:
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
            if b.get('source_file'):
                source_files.add(b['source_file'])

        # Geocode
        coords = geocode(address, cache)
        if coords:
            geocoded += 1
            if i % 20 == 0:
                print(f"  [{i+1}/{total}] {address} -> {coords['lat']:.4f},{coords['lng']:.4f}")
            time.sleep(1.1)  # Rate limit

        sites.append({
            'id': i + 1,
            'address': address,
            'city': 'תל אביב-יפו',
            'device_types': ' | '.join(device_types),
            'parking_count': total_parking,
            'gush': ', '.join(sorted(gushes)),
            'helka': ', '.join(sorted(helkas)),
            'dates': ', '.join(sorted(dates)),
            'record_count': len(buildings),
            'description': (descriptions[0][:200] if descriptions else ''),
            'lat': coords['lat'] if coords else None,
            'lng': coords['lng'] if coords else None,
            'source_files': list(source_files),
        })

    # Save
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(sites, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(sites)} sites to {OUTPUT}")
    print(f"Geocoded: {geocoded}/{total}")


if __name__ == "__main__":
    main()
