#!/usr/bin/env python3
"""
סקריפט אוטומטי מלא להורדת כל הפרוטוקולים וההחלטות
מאתר הוועדה המקומית לתכנון ובניה יוקנעם עילית
https://vaada.yoqneam.org.il/

הסקריפט משתמש ב-API ישיר של המערכת (GetMeetingDocs / GetMeetingByDate)
ללא צורך ב-Playwright או דפדפן. עובד עם requests בלבד.

התקנה:
    pip install requests lxml

הרצה:
    python3 yokneam_scraper_auto.py

פרמטרים אופציונליים:
    --start-year 2020    # שנה ראשונה (ברירת מחדל: 2020)
    --end-year 2026      # שנה אחרונה (ברירת מחדל: 2026)
    --protocols-only     # רק פרוטוקולים (בלי סדרי יום)
    --output-dir DIR     # תיקיית פלט (ברירת מחדל: yokneam_protocols)
    --no-download        # רק חילוץ קישורים, בלי הורדה
"""

import os
import sys
import json
import time
import csv
import re
import argparse
import requests
from pathlib import Path
from datetime import datetime

try:
    from lxml import html as lxml_html
    USE_LXML = True
except ImportError:
    from html.parser import HTMLParser
    USE_LXML = False
    print("Note: lxml not installed, using built-in HTML parser (pip install lxml for better parsing)")


# API Configuration
API_BASE = "https://handasi.complot.co.il/magicscripts/mgrqispi.dll"
SITE_ID = 63

COMMITTEE_FOLDER_NAMES = {
    "1": "01_רשות_רישוי_מקומית",
    "2": "02_ועדת_משנה",
    "3": "03_מליאת_הועדה",
    "4": "04_ועדת_שימור",
}


def sanitize_filename(name):
    for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        name = name.replace(char, '_')
    return name.strip()


def parse_archive_links(html_text):
    """Extract archive.gis-net links from HTML response"""
    links = []
    if USE_LXML:
        doc = lxml_html.fromstring(html_text)
        for a in doc.xpath('//a[contains(@href, "archive.gis-net")]'):
            href = a.get('href', '')
            text = (a.text or '').strip()
            if href:
                links.append({'text': text, 'url': href})
    else:
        pattern = r'<a[^>]+href="(https?://archive\.gis-net[^"]+)"[^>]*>([^<]*)</a>'
        for match in re.finditer(pattern, html_text):
            links.append({'text': match.group(2).strip(), 'url': match.group(1)})
    return links


def parse_meeting_links(html_text):
    """Extract getMeeting(type, number) links from search results HTML"""
    meetings = []
    if USE_LXML:
        doc = lxml_html.fromstring(html_text)
        rows = doc.xpath('//table[@id="results-table"]//tbody//tr')
        for row in rows:
            links = row.xpath('.//a[contains(@href, "getMeeting")]')
            for link in links:
                href = link.get('href', '')
                match = re.search(r'getMeeting\((\d+),(\d+)\)', href)
                if match:
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
    else:
        pattern = r'getMeeting\((\d+),(\d+)\)'
        seen = set()
        for match in re.finditer(pattern, html_text):
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


def get_meetings_by_year(session, year):
    """Fetch all meetings for a given year using GetMeetingByDate API"""
    url = (f"{API_BASE}?appname=cixpa&prgname=GetMeetingByDate"
           f"&siteid={SITE_ID}&v=0&fd=01/01/{year}&td=31/12/{year}"
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


def get_meeting_docs(session, committee_type, meeting_number):
    """Fetch document links for a specific meeting using GetMeetingDocs API"""
    url = (f"{API_BASE}?appname=cixpa&prgname=GetMeetingDocs"
           f"&siteid={SITE_ID}&v={committee_type}&n={meeting_number}"
           f"&arguments=siteid,v,n")

    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        return parse_archive_links(resp.text)
    except Exception as e:
        print(f"  ERROR fetching docs for meeting {committee_type}/{meeting_number}: {e}")
        return []


def extract_all_data(start_year, end_year):
    """Extract all meeting data using the API directly"""
    all_meetings = []
    all_documents = []

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
    })

    for year in range(start_year, end_year + 1):
        print(f"\nSearching meetings in {year}...")
        meetings = get_meetings_by_year(session, year)

        for m in meetings:
            if not any(existing['type'] == m['type'] and existing['number'] == m['number']
                       for existing in all_meetings):
                all_meetings.append(m)

        print(f"  Found {len(meetings)} meetings in {year} ({len(all_meetings)} total unique)")

    print(f"\nTotal unique meetings: {len(all_meetings)}")
    print(f"\nExtracting document links from each meeting...")

    for i, meeting in enumerate(all_meetings):
        progress = f"[{i+1}/{len(all_meetings)}]"

        docs = get_meeting_docs(session, meeting['type'], meeting['number'])

        for doc in docs:
            url = doc['url']
            parts = url.split('/')
            all_documents.append({
                'meetingNumber': meeting['number'],
                'committeeType': meeting['type'],
                'committee': meeting['committee'],
                'date': meeting['date'],
                'year': meeting['year'],
                'docType': doc['text'],
                'url': url,
                'folder': parts[-2] if len(parts) >= 2 else '',
                'guid': parts[-1].replace('.pdf', '') if parts else ''
            })

        if docs:
            print(f"  {progress} {meeting.get('date', '?')} | {meeting.get('committee', '?')[:30]} | {len(docs)} docs")
        else:
            print(f"  {progress} {meeting.get('date', '?')} | {meeting.get('committee', '?')[:30]} | no docs")

        time.sleep(0.15)

    return all_meetings, all_documents


def download_files(documents, output_dir, protocols_only=False):
    """Download all documents"""
    if protocols_only:
        documents = [d for d in documents
                     if 'פרוטוקול' in d['docType'] or 'תמליל' in d['docType']]
        print(f"\nDownloading {len(documents)} protocols only")
    else:
        print(f"\nDownloading all {len(documents)} documents")

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    for doc in documents:
        comm_dir = COMMITTEE_FOLDER_NAMES.get(doc['committeeType'], "99_אחר")
        year_dir = output_path / comm_dir / str(doc['year'])
        year_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_path / "documents_index.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([
            "meeting_number", "committee_type", "committee",
            "date", "year", "doc_type", "url", "local_file",
            "success", "size_bytes"
        ])

    total = len(documents)
    success = 0
    failed = 0
    total_size = 0
    start_time = time.time()

    for i, doc in enumerate(documents):
        comm_dir = COMMITTEE_FOLDER_NAMES.get(doc['committeeType'], "99_אחר")
        date_str = doc['date'].replace('/', '-')
        doc_type_clean = sanitize_filename(doc['docType'])
        filename = f"{date_str}_{doc['meetingNumber']}_{doc_type_clean}.pdf"
        filepath = output_path / comm_dir / str(doc['year']) / filename

        if filepath.exists() and filepath.stat().st_size > 1000:
            print(f"[{i+1}/{total}] Cached: {filename}")
            success += 1
            total_size += filepath.stat().st_size
            with open(csv_path, 'a', newline='', encoding='utf-8-sig') as f:
                csv.writer(f).writerow([
                    doc['meetingNumber'], doc['committeeType'], doc['committee'],
                    doc['date'], doc['year'], doc['docType'], doc['url'],
                    str(filepath), "cached", filepath.stat().st_size
                ])
            continue

        print(f"[{i+1}/{total}] {date_str} | {doc_type_clean[:30]:30s} | ", end='', flush=True)

        try:
            resp = requests.get(doc['url'], timeout=30)
            resp.raise_for_status()
            filepath.write_bytes(resp.content)
            size = len(resp.content)
            success += 1
            total_size += size
            print(f"OK ({size:,} bytes)")
            status = "yes"
        except Exception as e:
            failed += 1
            size = 0
            print(f"FAILED: {e}")
            status = "no"

        with open(csv_path, 'a', newline='', encoding='utf-8-sig') as f:
            csv.writer(f).writerow([
                doc['meetingNumber'], doc['committeeType'], doc['committee'],
                doc['date'], doc['year'], doc['docType'], doc['url'],
                str(filepath), status, size
            ])

        time.sleep(0.3)

    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"  Done!")
    print(f"  Downloaded: {success}/{total}")
    print(f"  Failed: {failed}")
    print(f"  Total size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
    print(f"  Time: {elapsed:.0f} seconds")
    print(f"  Index: {csv_path}")
    print(f"  Folder: {output_path.absolute()}")
    print("=" * 70)


def main():
    sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='Download protocols from Yokneam Illit Planning Committee')
    parser.add_argument('--start-year', type=int, default=2020,
                        help='First year to scrape (default: 2020)')
    parser.add_argument('--end-year', type=int, default=2026,
                        help='Last year to scrape (default: 2026)')
    parser.add_argument('--protocols-only', action='store_true',
                        help='Download only protocols (skip agendas)')
    parser.add_argument('--output-dir', default=None,
                        help='Output directory')
    parser.add_argument('--no-download', action='store_true',
                        help='Only extract URLs, do not download files')

    args = parser.parse_args()

    if args.output_dir is None:
        args.output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'yokneam_protocols')

    print("=" * 70)
    print("  Yokneam Illit Planning Committee - Protocol Scraper")
    print(f"  Period: {args.start_year} - {args.end_year}")
    print(f"  API: GetMeetingDocs (direct, no browser needed)")
    print("=" * 70)

    meetings, documents = extract_all_data(args.start_year, args.end_year)

    json_path = Path(args.output_dir) / f"yokneam_data_{args.start_year}_{args.end_year}.json"
    json_path.parent.mkdir(exist_ok=True)

    protocols = [d for d in documents
                 if 'פרוטוקול' in d['docType'] or 'תמליל' in d['docType']]

    output_json = {
        'metadata': {
            'source': 'https://vaada.yoqneam.org.il',
            'committee': 'הוועדה המקומית לתכנון ובניה יקנעם עילית',
            'dateRange': f'{args.start_year}-{args.end_year}',
            'extractedAt': datetime.now().isoformat(),
            'totalMeetings': len(meetings),
            'totalDocuments': len(documents),
            'totalProtocols': len(protocols),
            'apiEndpoint': f'{API_BASE}?appname=cixpa&prgname=GetMeetingDocs'
        },
        'meetings': meetings,
        'documents': documents
    }

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output_json, f, ensure_ascii=False, indent=2)

    print(f"\nData saved to: {json_path}")
    print(f"Total meetings: {len(meetings)}")
    print(f"Total documents: {len(documents)}")
    print(f"Total protocols: {len(protocols)}")

    if not args.no_download:
        download_files(documents, args.output_dir, args.protocols_only)
    else:
        print("\n--no-download flag set. Skipping downloads.")


if __name__ == "__main__":
    main()
