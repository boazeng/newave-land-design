#!/usr/bin/env python3
"""
סקריפט להורדת פרוטוקולים מועדות תכנון במערכת Bartech.
עובד עם כל ועדה שמשתמשת בפלטפורמת bartech-net.co.il.

Bartech sites have a /SearchMeetings page and a REST API.

התקנה:
    pip install requests beautifulsoup4

הרצה:
    python3 bartech_scraper.py --city-code ono --city-name "קרית_אונו" --start-year 2015 --end-year 2026 --protocols-only
    python3 bartech_scraper.py --city-code azr --city-name "אזור" --start-year 2015 --end-year 2026 --protocols-only

פרמטרים:
    --city-code     קוד העיר ב-bartech (למשל: ono, azr) (חובה)
    --city-name     שם העיר לתיקיית הפלט (חובה)
    --start-year    שנה ראשונה (ברירת מחדל: 2015)
    --end-year      שנה אחרונה (ברירת מחדל: 2026)
    --protocols-only רק פרוטוקולים
    --output-dir    תיקיית פלט (ברירת מחדל: output)
    --no-download   רק חילוץ קישורים
    --count-only    רק ספירת פרוטוקולים לפי שנה
"""

import os
import sys
import json
import time
import re
import argparse
import requests
from datetime import datetime
from urllib.parse import urljoin, quote

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("Warning: beautifulsoup4 not installed. Install with: pip install beautifulsoup4")


def sanitize(name):
    for c in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        name = name.replace(c, '_')
    return name.strip()


class BartechScraper:
    """Scraper for Bartech planning committee websites."""

    def __init__(self, city_code, city_name):
        self.city_code = city_code
        self.city_name = city_name
        self.base_url = f"https://{city_code}.bartech-net.co.il"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7',
        })

    def get_meetings_page(self):
        """Fetch the SearchMeetings page to understand the structure."""
        url = f"{self.base_url}/SearchMeetings"
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            print(f"  ERROR fetching SearchMeetings: {e}")
            # Try alternative URLs
            alternatives = [
                f"{self.base_url}/Meetings",
                f"{self.base_url}/meetings",
                f"{self.base_url}/ישיבות",
            ]
            for alt_url in alternatives:
                try:
                    resp = self.session.get(alt_url, timeout=15)
                    if resp.status_code == 200:
                        return resp.text
                except:
                    continue
            return None

    def search_meetings_api(self, start_date, end_date, committee_type=0):
        """Search meetings via Bartech API.

        Bartech typically uses POST to /SearchMeetings or /api/meetings
        with form data or JSON body.
        """
        # Try multiple API patterns used by different Bartech sites
        apis = [
            # Pattern 1: Form POST to SearchMeetings
            {
                'method': 'POST',
                'url': f"{self.base_url}/SearchMeetings",
                'data': {
                    'FromDate': start_date,
                    'ToDate': end_date,
                    'CommitteeType': str(committee_type),
                },
                'type': 'form'
            },
            # Pattern 2: GET with query params
            {
                'method': 'GET',
                'url': f"{self.base_url}/SearchMeetings",
                'params': {
                    'fromDate': start_date,
                    'toDate': end_date,
                    'committeeType': str(committee_type),
                },
                'type': 'get'
            },
            # Pattern 3: API endpoint
            {
                'method': 'POST',
                'url': f"{self.base_url}/api/Meetings/Search",
                'json': {
                    'FromDate': start_date,
                    'ToDate': end_date,
                    'CommitteeType': committee_type,
                },
                'type': 'json'
            },
            # Pattern 4: REST endpoint with dates in URL
            {
                'method': 'GET',
                'url': f"{self.base_url}/api/Meetings",
                'params': {
                    'from': start_date,
                    'to': end_date,
                },
                'type': 'get'
            },
        ]

        for api in apis:
            try:
                if api['method'] == 'POST':
                    if api['type'] == 'json':
                        resp = self.session.post(api['url'], json=api.get('json', {}), timeout=30)
                    else:
                        resp = self.session.post(api['url'], data=api.get('data', {}), timeout=30)
                else:
                    resp = self.session.get(api['url'], params=api.get('params', {}), timeout=30)

                if resp.status_code == 200 and len(resp.text) > 100:
                    return resp.text, api['type']
            except:
                continue

        return None, None

    def parse_meetings_html(self, html_text):
        """Parse meeting links from HTML page."""
        meetings = []

        if HAS_BS4:
            soup = BeautifulSoup(html_text, 'html.parser')

            # Look for meeting links - various patterns
            for a in soup.find_all('a', href=True):
                href = a['href']
                text = a.get_text(strip=True)

                # Pattern: /Meeting/123 or /MeetingDetails/123
                match = re.search(r'/(?:Meeting|MeetingDetails|meeting)/(\d+)', href)
                if match:
                    meetings.append({
                        'id': match.group(1),
                        'url': urljoin(self.base_url, href),
                        'text': text,
                    })
                    continue

                # Pattern: ?meetingId=123
                match = re.search(r'meetingId=(\d+)', href)
                if match:
                    meetings.append({
                        'id': match.group(1),
                        'url': urljoin(self.base_url, href),
                        'text': text,
                    })

            # Also look for table rows with meeting data
            for row in soup.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 3:
                    link = row.find('a', href=True)
                    if link:
                        href = link['href']
                        match = re.search(r'/(?:Meeting|MeetingDetails|meeting)/(\d+)', href)
                        if not match:
                            match = re.search(r'meetingId=(\d+)', href)
                        if match:
                            date_text = cells[0].get_text(strip=True) if cells else ''
                            committee_text = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                            meetings.append({
                                'id': match.group(1),
                                'url': urljoin(self.base_url, href),
                                'date': date_text,
                                'committee': committee_text,
                                'text': link.get_text(strip=True),
                            })
        else:
            # Regex fallback
            for match in re.finditer(r'href=["\']([^"\']*(?:Meeting|meeting)[^"\']*?(\d+)[^"\']*)["\']', html_text):
                meetings.append({
                    'id': match.group(2),
                    'url': urljoin(self.base_url, match.group(1)),
                    'text': '',
                })

        # Deduplicate
        seen = set()
        unique = []
        for m in meetings:
            if m['id'] not in seen:
                seen.add(m['id'])
                unique.append(m)

        return unique

    def get_meeting_docs(self, meeting_id):
        """Get document links for a specific meeting."""
        docs = []

        # Try multiple URL patterns
        urls_to_try = [
            f"{self.base_url}/Meeting/{meeting_id}",
            f"{self.base_url}/MeetingDetails/{meeting_id}",
            f"{self.base_url}/api/Meeting/{meeting_id}/Documents",
            f"{self.base_url}/api/Meetings/{meeting_id}/files",
        ]

        for url in urls_to_try:
            try:
                resp = self.session.get(url, timeout=30)
                if resp.status_code != 200:
                    continue

                # Try JSON first
                try:
                    data = resp.json()
                    if isinstance(data, list):
                        for item in data:
                            if 'url' in item or 'Url' in item or 'fileUrl' in item:
                                file_url = item.get('url') or item.get('Url') or item.get('fileUrl')
                                docs.append({
                                    'url': urljoin(self.base_url, file_url),
                                    'text': item.get('name', '') or item.get('Name', '') or item.get('fileName', ''),
                                    'type': item.get('type', '') or item.get('Type', ''),
                                })
                    elif isinstance(data, dict) and 'files' in data:
                        for item in data['files']:
                            file_url = item.get('url') or item.get('Url') or item.get('fileUrl')
                            if file_url:
                                docs.append({
                                    'url': urljoin(self.base_url, file_url),
                                    'text': item.get('name', ''),
                                    'type': item.get('type', ''),
                                })
                    if docs:
                        return docs
                except:
                    pass

                # Parse HTML
                if HAS_BS4:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        text = a.get_text(strip=True)
                        if href.lower().endswith('.pdf') or 'download' in href.lower() or 'file' in href.lower():
                            docs.append({
                                'url': urljoin(self.base_url, href),
                                'text': text,
                                'type': 'pdf' if href.lower().endswith('.pdf') else 'unknown',
                            })
                else:
                    for match in re.finditer(r'href=["\']([^"\']+\.pdf)["\']', resp.text, re.IGNORECASE):
                        docs.append({
                            'url': urljoin(self.base_url, match.group(1)),
                            'text': '',
                            'type': 'pdf',
                        })

                if docs:
                    return docs

            except Exception as e:
                continue

        return docs

    def extract_all(self, start_year, end_year, protocols_only=False):
        """Extract all meetings and documents."""
        all_meetings = []
        all_documents = []

        # First fetch the initial page to get cookies/tokens
        print(f"  Fetching initial page...")
        initial = self.get_meetings_page()
        if not initial:
            print(f"  WARNING: Could not access {self.base_url}")
            print(f"  This site may require a different approach.")
            return [], []

        # Extract any CSRF token or anti-forgery token
        if HAS_BS4:
            soup = BeautifulSoup(initial, 'html.parser')
            token_input = soup.find('input', {'name': '__RequestVerificationToken'})
            if token_input:
                self.session.headers['X-RequestVerificationToken'] = token_input.get('value', '')

        # Search by year
        for year in range(start_year, end_year + 1):
            print(f"  Searching {year}...")
            start_date = f"01/01/{year}"
            end_date = f"31/12/{year}"

            html, api_type = self.search_meetings_api(start_date, end_date)
            if not html:
                # Try with the initial page content if it's the current year
                print(f"    No results from API for {year}")
                continue

            # Try JSON parsing first
            try:
                data = json.loads(html)
                if isinstance(data, list):
                    for item in data:
                        mid = str(item.get('id', '') or item.get('Id', '') or item.get('MeetingId', ''))
                        if mid:
                            all_meetings.append({
                                'id': mid,
                                'url': f"{self.base_url}/Meeting/{mid}",
                                'date': item.get('date', '') or item.get('Date', '') or item.get('MeetingDate', ''),
                                'committee': item.get('committee', '') or item.get('Committee', '') or item.get('CommitteeType', ''),
                                'year': year,
                            })
                    print(f"    Found {len(data)} meetings (JSON)")
                    continue
                elif isinstance(data, dict) and 'meetings' in data:
                    for item in data['meetings']:
                        mid = str(item.get('id', '') or item.get('Id', ''))
                        if mid:
                            all_meetings.append({
                                'id': mid,
                                'url': f"{self.base_url}/Meeting/{mid}",
                                'date': item.get('date', ''),
                                'committee': item.get('committee', ''),
                                'year': year,
                            })
                    print(f"    Found {len(data['meetings'])} meetings (JSON)")
                    continue
            except:
                pass

            # Parse HTML
            meetings = self.parse_meetings_html(html)
            for m in meetings:
                m['year'] = year
            all_meetings.extend(meetings)
            print(f"    Found {len(meetings)} meetings (HTML)")

        # Deduplicate meetings
        seen = set()
        unique_meetings = []
        for m in all_meetings:
            if m['id'] not in seen:
                seen.add(m['id'])
                unique_meetings.append(m)

        print(f"\n  Total unique meetings: {len(unique_meetings)}")
        print(f"  Extracting document links...")

        for i, meeting in enumerate(unique_meetings):
            docs = self.get_meeting_docs(meeting['id'])
            for doc in docs:
                entry = {
                    'meetingId': meeting['id'],
                    'date': meeting.get('date', ''),
                    'committee': meeting.get('committee', ''),
                    'year': meeting.get('year', 0),
                    'docType': doc.get('text', ''),
                    'url': doc['url'],
                    'fileType': doc.get('type', ''),
                }

                if protocols_only:
                    text = (doc.get('text', '') + doc.get('type', '')).lower()
                    if 'פרוטוקול' not in text and 'protocol' not in text and 'החלט' not in text:
                        url_lower = doc['url'].lower()
                        if 'protocol' not in url_lower and 'prot' not in url_lower:
                            continue

                all_documents.append(entry)

            if (i + 1) % 10 == 0:
                print(f"    [{i+1}/{len(unique_meetings)}] {len(all_documents)} docs")
            time.sleep(0.3)

        return unique_meetings, all_documents


def download_files(documents, output_dir, session):
    os.makedirs(output_dir, exist_ok=True)
    success = 0
    errors = 0

    for i, doc in enumerate(documents):
        url = doc['url']
        date_str = sanitize(doc.get('date', 'unknown'))
        doc_type = sanitize(doc.get('docType', 'protocol'))
        meeting_id = doc.get('meetingId', '0')

        filename = f"{date_str}_{meeting_id}_{doc_type}.pdf"
        filepath = os.path.join(output_dir, filename)

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
            if errors <= 5:
                print(f"    ERROR: {url}: {e}")

        if (i + 1) % 10 == 0:
            print(f"    [{i+1}/{len(documents)}] ({success} ok, {errors} errors)")
        time.sleep(0.3)

    return success, errors


def main():
    parser = argparse.ArgumentParser(description='Bartech Protocol Scraper')
    parser.add_argument('--city-code', type=str, required=True, help='Bartech city code (e.g., ono, azr)')
    parser.add_argument('--city-name', type=str, required=True, help='City name for output folder')
    parser.add_argument('--start-year', type=int, default=2015)
    parser.add_argument('--end-year', type=int, default=2026)
    parser.add_argument('--protocols-only', action='store_true')
    parser.add_argument('--output-dir', type=str, default='output')
    parser.add_argument('--no-download', action='store_true')
    parser.add_argument('--count-only', action='store_true')
    args = parser.parse_args()

    city = sanitize(args.city_name)
    city_output = os.path.join(args.output_dir, city)

    print("=" * 60)
    print(f"Bartech Protocol Scraper - {args.city_name}")
    print(f"Site: {args.city_code}.bartech-net.co.il")
    print(f"Years: {args.start_year}-{args.end_year}")
    print("=" * 60)

    scraper = BartechScraper(args.city_code, args.city_name)
    meetings, documents = scraper.extract_all(
        args.start_year, args.end_year, args.protocols_only
    )

    print(f"\n  Total documents found: {len(documents)}")

    counts = {}
    for doc in documents:
        year = doc.get('year', 0)
        counts[year] = counts.get(year, 0) + 1

    print(f"\n  Protocols by year:")
    for year in sorted(counts.keys()):
        print(f"    {year}: {counts[year]}")

    os.makedirs(city_output, exist_ok=True)
    json_path = os.path.join(city_output, f'{city}_data.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'city': args.city_name,
            'platform': 'bartech',
            'city_code': args.city_code,
            'total_meetings': len(meetings),
            'total_documents': len(documents),
            'counts_by_year': counts,
            'documents': documents
        }, f, ensure_ascii=False, indent=2)
    print(f"\n  Data saved to {json_path}")

    if args.count_only or args.no_download:
        return counts

    print(f"\n  Downloading {len(documents)} files...")
    success, errors = download_files(documents, city_output, scraper.session)
    print(f"  Download complete: {success} success, {errors} errors")

    return counts


if __name__ == '__main__':
    main()
