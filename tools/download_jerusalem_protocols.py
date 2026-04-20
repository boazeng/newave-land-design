#!/usr/bin/env python3
"""
Download Jerusalem planning committee protocol PDFs.
Scrapes www-mgmt.jerusalem.muni.il council archive pages.

Usage:
  py tools/download_jerusalem_protocols.py
"""
import os, sys, time, json, re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = 'https://www-mgmt.jerusalem.muni.il'
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'protocols_search', 'ירושלים')
INDEX_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'protocols_search', 'ירושלים', '_index.json')

# Council terms and their relevant committee IDs
COUNCILS = [
    {
        'id': '35',
        'name': 'מועצה 14',
        'committees': [
            {'comId': '45', 'name': 'משנה לתכנון ובנייה - היתרים'},
        ],
    },
    {
        'id': '86',
        'name': 'מועצה 15',
        'committees': [
            {'comId': '45', 'name': 'משנה לתכנון ובנייה - היתרים'},
            {'comId': '115', 'name': 'רשות רישוי מקומית'},
        ],
    },
    {
        'id': 'd375bb1d-cf11-ea11-a811-000d3ab87c51',
        'name': 'מועצה 16',
        'committees': [
            {'comId': '471793c7-4c14-ea11-a811-000d3ab8764f', 'name': 'משנה לתכנון ובנייה - היתרים'},
        ],
    },
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; NewaveLandDesign/1.0)',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'he,en;q=0.9',
    'Referer': BASE_URL,
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def fetch_html(url, retries=3):
    for attempt in range(retries):
        try:
            resp = SESSION.get(url, timeout=30)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f'  ERROR fetching {url}: {e}')
                return None


def get_meeting_links(council_id, com_id):
    """Scrape CouncilCommitteeArchive to get all meeting convId values."""
    url = f'{BASE_URL}/he/city/council/CouncilArchive/CouncilCommitteeArchive?id={council_id}&comId={com_id}'
    html = fetch_html(url)
    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    meetings = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'CouncilMeetingArchive' in href:
            qs = parse_qs(urlparse(href).query)
            conv_id = qs.get('convId', [None])[0]
            if conv_id:
                text = a.get_text(strip=True)
                meetings.append({'convId': conv_id, 'title': text})

    return meetings


def get_pdf_links(council_id, conv_id):
    """Scrape CouncilMeetingArchive to get all PDF blob URLs."""
    url = f'{BASE_URL}/he/city/council/CouncilArchive/CouncilMeetingArchive?id={council_id}&convId={conv_id}'
    html = fetch_html(url)
    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    pdfs = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'jerintsvcblob.blob.core.windows.net' in href and '.pdf' in href.lower():
            label = a.get_text(strip=True)
            pdfs.append({'url': href, 'label': label})

    return pdfs


def download_pdf(url, dest_path):
    if os.path.exists(dest_path):
        return True
    try:
        resp = SESSION.get(url, timeout=60, stream=True)
        resp.raise_for_status()
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, 'wb') as f:
            for chunk in resp.iter_content(65536):
                f.write(chunk)
        return True
    except Exception as e:
        print(f'  DOWNLOAD ERROR {os.path.basename(dest_path)}: {e}')
        return False


def load_index():
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {'downloaded': [], 'meetings': {}}


def save_index(index):
    os.makedirs(os.path.dirname(INDEX_FILE), exist_ok=True)
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def safe_filename(name):
    return re.sub(r'[\\/:*?"<>|]', '_', name)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    index = load_index()
    downloaded_set = set(index['downloaded'])

    total_meetings = 0
    total_pdfs = 0
    total_downloaded = 0

    for council in COUNCILS:
        council_id = council['id']
        council_name = council['name']

        for committee in council['committees']:
            com_id = committee['comId']
            com_name = committee['name']

            print(f'\n=== {council_name} / {com_name} ===')
            meetings = get_meeting_links(council_id, com_id)
            print(f'  Found {len(meetings)} meetings')
            total_meetings += len(meetings)

            for meeting in meetings:
                conv_id = meeting['convId']
                meeting_title = safe_filename(meeting['title'])
                meeting_key = f'{council_id}_{conv_id}'

                pdfs = get_pdf_links(council_id, conv_id)
                if not pdfs:
                    time.sleep(0.5)
                    continue

                # Store meeting info
                index['meetings'][meeting_key] = {
                    'council': council_name,
                    'committee': com_name,
                    'title': meeting['title'],
                    'pdf_count': len(pdfs),
                }

                for pdf in pdfs:
                    pdf_url = pdf['url']
                    if pdf_url in downloaded_set:
                        continue

                    # Derive filename from URL
                    path_part = urlparse(pdf_url).path
                    filename = os.path.basename(path_part)
                    if not filename.lower().endswith('.pdf'):
                        filename += '.pdf'

                    # Organize under committee folder
                    com_folder = safe_filename(com_name)
                    dest = os.path.join(OUTPUT_DIR, com_folder, filename)

                    if download_pdf(pdf_url, dest):
                        total_downloaded += 1
                        downloaded_set.add(pdf_url)
                        total_pdfs += 1
                        print(f'  + {filename}')
                    else:
                        total_pdfs += 1

                    time.sleep(0.3)

                index['downloaded'] = list(downloaded_set)
                save_index(index)
                time.sleep(0.5)

    print(f'\n=== Done ===')
    print(f'Meetings scanned: {total_meetings}')
    print(f'PDFs found: {total_pdfs}')
    print(f'PDFs downloaded: {total_downloaded}')
    print(f'Output dir: {OUTPUT_DIR}')


if __name__ == '__main__':
    main()
