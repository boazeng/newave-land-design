#!/usr/bin/env python3
"""
סקריפט לאיתור Site IDs של ועדות תכנון במערכת Complot.
סורק IDs 1-200 ומזהה את שם העיר לכל ID פעיל.

הרצה:
    python3 find_complot_ids.py

פלט:
    complot_site_ids.json - מיפוי של כל ה-IDs הפעילים לשמות ערים
"""

import requests
import json
import re
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

API_BASE = "https://handasi.complot.co.il/magicscripts/mgrqispi.dll"

KNOWN_IDS = {
    3: "רמת גן",
    34: "חולון",
    63: "יוקנעם עילית",
}

def check_site_id(session, site_id):
    """Check if a site ID has meetings and try to identify the city."""
    url = (f"{API_BASE}?appname=cixpa&prgname=GetMeetingByDate"
           f"&siteid={site_id}&v=0&fd=01/01/2020&td=31/12/2025"
           f"&l=true&arguments=siteid,v,fd,td,l")
    try:
        resp = session.get(url, timeout=15)
        if resp.status_code != 200:
            return None
        text = resp.text
        matches = re.findall(r'getMeeting\((\d+),(\d+)\)', text)
        if not matches:
            return None

        city_name = identify_city(session, site_id, matches[0][0], matches[0][1])
        return {
            'site_id': site_id,
            'meetings_found': len(matches),
            'city': city_name or f'unknown_site_{site_id}'
        }
    except Exception as e:
        return None


def identify_city(session, site_id, committee_type, meeting_number):
    """Try to identify city name from archive URL in meeting docs."""
    url = (f"{API_BASE}?appname=cixpa&prgname=GetMeetingDocs"
           f"&siteid={site_id}&v={committee_type}&n={meeting_number}"
           f"&arguments=siteid,v,n")
    try:
        resp = session.get(url, timeout=15)
        archive_match = re.search(r'archive\.gis-net\.co\.il/([^/]+)/', resp.text)
        if archive_match:
            return archive_match.group(1)
        return None
    except:
        return None


def scan_all_ids(max_id=200):
    """Scan all site IDs from 1 to max_id."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
    })

    results = {}
    for sid, city in KNOWN_IDS.items():
        results[sid] = {'site_id': sid, 'city': city, 'meetings_found': -1, 'source': 'known'}

    ids_to_scan = [i for i in range(1, max_id + 1) if i not in KNOWN_IDS]
    total = len(ids_to_scan)
    found = 0

    print(f"Scanning {total} site IDs (1-{max_id}, skipping {len(KNOWN_IDS)} known)...")
    print(f"Known sites: {KNOWN_IDS}")
    print()

    for i, site_id in enumerate(ids_to_scan):
        result = check_site_id(session, site_id)
        if result:
            found += 1
            results[site_id] = result
            print(f"  [{i+1}/{total}] ID {site_id}: ✅ {result['city']} ({result['meetings_found']} meetings)")
        else:
            if (i + 1) % 20 == 0:
                print(f"  [{i+1}/{total}] Scanned up to ID {site_id}... ({found} found so far)")
        time.sleep(0.3)

    return results


def main():
    print("=" * 60)
    print("Complot Site ID Scanner")
    print("=" * 60)

    results = scan_all_ids(200)

    print(f"\n{'=' * 60}")
    print(f"Scan complete! Found {len(results)} active sites:")
    print(f"{'=' * 60}")

    for sid in sorted(results.keys()):
        r = results[sid]
        print(f"  Site ID {sid:3d}: {r['city']}")

    output = {str(k): v for k, v in sorted(results.items())}
    with open('complot_site_ids.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to complot_site_ids.json")

    # Highlight Tel Aviv district cities we're looking for
    target_cities = ['BatYam', 'batyam', 'bat-yam', 'bat_yam',
                     'OYehuda', 'oryehuda', 'or-yehuda', 'or_yehuda',
                     'RamatHasharon', 'ramathasharon', 'ramat-hasharon', 'ramat_hasharon',
                     'Herzliya', 'herzliya', 'herzlia',
                     'RamatGan', 'ramatgan', 'ramat-gan',
                     'Holon', 'holon']

    print(f"\n{'=' * 60}")
    print("Tel Aviv district matches:")
    print(f"{'=' * 60}")
    for sid in sorted(results.keys()):
        city = results[sid].get('city', '')
        city_lower = city.lower().replace(' ', '')
        for target in target_cities:
            if target.lower() in city_lower or city_lower in target.lower():
                print(f"  ✅ Site ID {sid}: {city}")
                break


if __name__ == '__main__':
    main()
