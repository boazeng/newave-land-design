#!/usr/bin/env python3
"""
סקריפט גנרי להורדת פרוטוקולים מועדות תכנון במערכת Complot.
עובד עם כל ועדה שמשתמשת בפלטפורמת Complot (API ישיר, ללא דפדפן).

התקנה:
    pip install requests lxml

הרצה:
    python3 complot_scraper.py --site-id 3 --city-name "רמת_גן" --start-year 2015 --end-year 2026 --protocols-only
    python3 complot_scraper.py --site-id 34 --city-name "חולון" --start-year 2015 --end-year 2026 --protocols-only

פרמטרים:
    --site-id       מזהה האתר במערכת Complot (חובה)
    --city-name     שם העיר לתיקיית הפלט (חובה)
    --start-year    שנה ראשונה (ברירת מחדל: 2015)
    --end-year      שנה אחרונה (ברירת מחדל: 2026)
    --protocols-only רק פרוטוקולים (תיקיה 775/778)
    --output-dir    תיקיית פלט ראשית (ברירת מחדל: output)
    --no-download   רק חילוץ קישורים, בלי הורדה
    --count-only    רק ספירת פרוטוקולים לפי שנה (בלי הורדה)
"""

import os
import sys
import json
import time
import re
import argparse
import requests
from pathlib import Path
from datetime import datetime

try:
    from lxml import html as lxml_html
    USE_LXML = True
except ImportError:
    USE_LXML = False

API_BASE = "https://handasi.complot.co.il/magicscripts/mgrqispi.dll"

COMMITTEE_NAMES = {
    "1": "רשות_רישוי_מקומית",
    "2": "ועדת_משנה",
    "3": "מליאת_הועדה",
    "4": "ועדת_שימור",
}

# Folders 775 and 778 contain protocols
PROTOCOL_FOLDERS = {'775', '778'}


def sanitize(name):
    for c in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        name = name.replace(c, '_')
    return name.strip()


def parse_archive_links(html_text):
    links = []
    if USE_LXML:
        try:
            doc = lxml_html.fromstring(html_text)
            for a in doc.xpath('//a[contains(@href, "archive.gis-net")]'):
                href = a.get('href', '')
                text = (a.text or '').strip()
                if href:
                    links.append({'text': text, 'url': href})
        except:
            pass
    if not links:
        pattern = r'<a[^>]+href=["\']?(https?://archive\.gis-net[^"\'>\s]+)["\']?[^>]*>([^<]*)</a>'
        for match in re.finditer(pattern, html_text, re.IGNORECASE):
            links.append({'text': match.group(2).strip(), 'url': match.group(1)})
    return links


def parse_meeting_links(html_text):
    meetings = []
    seen = set()

    if USE_LXML:
        try:
            doc = lxml_html.fromstring(html_text)
            rows = doc.xpath('//table[@id="results-table"]//tbody//tr')
            for row in rows:
                for link in row.xpath('.//a[contains(@href, "getMeeting")]'):
                    href = link.get('href', '')
                    match = re.search(r'getMeeting\((\d+),(\d+)\)', href)
                    if match:
                        key = (match.group(1), match.group(2))
                        if key not in seen:
                            seen.add(key)
                            cells = row.xpath('.//td')
                            committee = cells[2].text_content().strip() if len(cells) > 2 else ''
                            date = cells[3].text_content().strip() if len(cells) > 3 else ''
                            meetings.append({
                                'type': match.group(1),
                                'number': match.group(2),
                                'committee': committee,
                                'date': date
                            })
                        break
        except:
            pass

    if not meetings:
        for match in re.finditer(r'getMeeting\((\d+),(\d+)\)', html_text):
            key = (match.group(1), match.group(2))
            if key not in seen:
                seen.add(key)
                meetings.append({
                    'type': match.group(1),
                    'number': match.group(2),
                    'committee': '',
                    'date': ''
                })
    return meetings


def get_meetings_by_year(session, site_id, year):
    url = (f"{API_BASE}?appname=cixpa&prgname=GetMeetingByDate"
           f"&siteid={site_id}&v=0&fd=01/01/{year}&td=31/12/{year}"
           f"&l=true&arguments=siteid,v,fd,td,l")
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        meetings = parse_meeting_links(resp.text)
        for m in meetings:
            m['year'] = year
        return meetings
    except Exception as e:
        print(f"  ERROR fetching meetings for {year}: {e}")
        return []


def get_meeting_docs(session, site_id, committee_type, meeting_number):
    url = (f"{API_BASE}?appname=cixpa&prgname=GetMeetingDocs"
           f"&siteid={site_id}&v={committee_type}&n={meeting_number}"
           f"&arguments=siteid,v,n")
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        return parse_archive_links(resp.text)
    except Exception as e:
        print(f"  ERROR fetching docs for {committee_type}/{meeting_number}: {e}")
        return []


def is_protocol(doc):
    url = doc.get('url', '')
    parts = url.split('/')
    folder = parts[-2] if len(parts) >= 2 else ''
    if folder in PROTOCOL_FOLDERS:
        return True
    text = doc.get('text', '').lower()
    return 'פרוטוקול' in text or 'protocol' in text


def extract_all_data(site_id, start_year, end_year, protocols_only=False):
    all_meetings = []
    all_documents = []

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
    })

    for year in range(start_year, end_year + 1):
        print(f"  Searching {year}...")
        meetings = get_meetings_by_year(session, site_id, year)
        for m in meetings:
            if not any(e['type'] == m['type'] and e['number'] == m['number'] for e in all_meetings):
                all_meetings.append(m)
        print(f"    Found {len(meetings)} meetings ({len(all_meetings)} total unique)")

    print(f"\n  Total unique meetings: {len(all_meetings)}")
    print(f"  Extracting document links...")

    for i, meeting in enumerate(all_meetings):
        docs = get_meeting_docs(session, site_id, meeting['type'], meeting['number'])
        for doc in docs:
            url = doc['url']
            parts = url.split('/')
            entry = {
                'meetingNumber': meeting['number'],
                'committeeType': meeting['type'],
                'committee': meeting.get('committee', ''),
                'date': meeting.get('date', ''),
                'year': meeting.get('year', 0),
                'docType': doc['text'],
                'url': url,
                'folder': parts[-2] if len(parts) >= 2 else '',
                'guid': parts[-1].replace('.pdf', '') if parts else ''
            }

            if protocols_only and not is_protocol(entry):
                continue
            all_documents.append(entry)

        if (i + 1) % 20 == 0 or i == len(all_meetings) - 1:
            print(f"    [{i+1}/{len(all_meetings)}] {len(all_documents)} docs so far")
        time.sleep(0.2)

    return all_meetings, all_documents


def count_protocols_by_year(documents):
    counts = {}
    for doc in documents:
        year = doc.get('year', 0)
        if year not in counts:
            counts[year] = 0
        counts[year] += 1
    return counts


def download_files(documents, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
    })

    success = 0
    errors = 0

    for i, doc in enumerate(documents):
        url = doc['url']
        committee = COMMITTEE_NAMES.get(doc['committeeType'], f"type_{doc['committeeType']}")
        date_str = sanitize(doc.get('date', 'unknown'))
        doc_type = sanitize(doc.get('docType', 'doc'))
        meeting_num = doc.get('meetingNumber', '0')

        folder = os.path.join(output_dir, committee)
        os.makedirs(folder, exist_ok=True)

        # Use GUID from URL to ensure unique filenames
        guid = doc.get('guid', '')[:8] or str(i)
        filename = f"{date_str}_{meeting_num}_{doc_type}_{guid}.pdf"
        filepath = os.path.join(folder, filename)

        if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
            success += 1
            continue

        try:
            resp = session.get(url, timeout=60)
            resp.raise_for_status()
            with open(filepath, 'wb') as f:
                f.write(resp.content)
            success += 1
        except Exception as e:
            errors += 1
            print(f"    ERROR downloading {url}: {e}")

        if (i + 1) % 10 == 0:
            print(f"    Downloaded [{i+1}/{len(documents)}] ({success} ok, {errors} errors)")
        time.sleep(0.3)

    return success, errors


def main():
    parser = argparse.ArgumentParser(description='Complot Protocol Scraper')
    parser.add_argument('--site-id', type=int, required=True, help='Complot site ID')
    parser.add_argument('--city-name', type=str, required=True, help='City name for output folder')
    parser.add_argument('--start-year', type=int, default=2015)
    parser.add_argument('--end-year', type=int, default=2026)
    parser.add_argument('--protocols-only', action='store_true', help='Only download protocols')
    parser.add_argument('--output-dir', type=str, default='output')
    parser.add_argument('--no-download', action='store_true', help='Extract links only')
    parser.add_argument('--count-only', action='store_true', help='Only count protocols per year')
    args = parser.parse_args()

    city = sanitize(args.city_name)
    city_output = os.path.join(args.output_dir, city)

    print("=" * 60)
    print(f"Complot Protocol Scraper - {args.city_name}")
    print(f"Site ID: {args.site_id} | Years: {args.start_year}-{args.end_year}")
    print(f"Protocols only: {args.protocols_only}")
    print("=" * 60)

    meetings, documents = extract_all_data(
        args.site_id, args.start_year, args.end_year, args.protocols_only
    )

    print(f"\n  Total documents found: {len(documents)}")

    counts = count_protocols_by_year(documents)
    print(f"\n  Protocols by year:")
    for year in sorted(counts.keys()):
        print(f"    {year}: {counts[year]}")

    # Save JSON
    os.makedirs(city_output, exist_ok=True)
    json_path = os.path.join(city_output, f'{city}_data.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'city': args.city_name,
            'site_id': args.site_id,
            'start_year': args.start_year,
            'end_year': args.end_year,
            'total_meetings': len(meetings),
            'total_documents': len(documents),
            'counts_by_year': counts,
            'documents': documents
        }, f, ensure_ascii=False, indent=2)
    print(f"\n  Data saved to {json_path}")

    if args.count_only:
        print("\n  Count-only mode, skipping download.")
        return counts

    if args.no_download:
        print("\n  No-download mode, links saved to JSON.")
        return counts

    print(f"\n  Downloading {len(documents)} files to {city_output}...")
    success, errors = download_files(documents, city_output)
    print(f"\n  Download complete: {success} success, {errors} errors")

    return counts


if __name__ == '__main__':
    main()
