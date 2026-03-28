#!/usr/bin/env python3
"""
סקריפט להורדת פרוטוקולים מועדת התכנון והבנייה של תל אביב-יפו.
אתר העירייה מבוסס SharePoint ומארח פרוטוקולים ב-DocLib.

מבנה ה-URL של פרוטוקולים:
    https://www.tel-aviv.gov.il/Residents/Development/DocLib/{filename}.pdf
    https://www.tel-aviv.gov.il/Transparency/DocLib3/{filename}.pdf

התקנה:
    pip install requests beautifulsoup4

הרצה:
    python3 telaviv_scraper.py --start-year 2015 --end-year 2026
    python3 telaviv_scraper.py --count-only

פרמטרים:
    --start-year    שנה ראשונה (ברירת מחדל: 2015)
    --end-year      שנה אחרונה (ברירת מחדל: 2026)
    --output-dir    תיקיית פלט (ברירת מחדל: output)
    --no-download   רק חילוץ קישורים
    --count-only    רק ספירה
"""

import os
import sys
import json
import time
import re
import argparse
import requests
from urllib.parse import urljoin, unquote, quote
from datetime import datetime

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("Warning: beautifulsoup4 not installed. pip install beautifulsoup4")


BASE_URL = "https://www.tel-aviv.gov.il"

# Known protocol page URLs
PROTOCOL_PAGES = [
    "/Residents/Development/Pages/protocols.aspx",
    "/Transparency/Pages/Protocols.aspx",
]

# SharePoint document library paths where protocols are stored
DOC_LIBRARIES = [
    "/Residents/Development/DocLib",
    "/Transparency/DocLib3",
]

# Committee types on the Tel Aviv site
COMMITTEE_TYPES = [
    'ועדת משנה לתכנון ובניה',
    'מליאת הועדה',
    'רשות רישוי',
    'ועדת ערר',
]


def sanitize(name):
    for c in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        name = name.replace(c, '_')
    return name.strip()


class TelAvivScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7',
        })

    def fetch_page(self, url):
        try:
            resp = self.session.get(url, timeout=30, allow_redirects=True)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            print(f"    ERROR fetching {url}: {e}")
            return None

    def extract_pdf_links_from_page(self, html_text, base_url):
        links = []
        if not html_text:
            return links

        if HAS_BS4:
            soup = BeautifulSoup(html_text, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                text = a.get_text(strip=True)
                if href.lower().endswith('.pdf'):
                    full_url = urljoin(base_url, href)
                    links.append({
                        'url': full_url,
                        'text': text,
                        'filename': unquote(href.split('/')[-1]),
                    })
        else:
            for match in re.finditer(r'href=["\']([^"\']+\.pdf)["\']', html_text, re.IGNORECASE):
                href = match.group(1)
                full_url = urljoin(base_url, href)
                links.append({
                    'url': full_url,
                    'text': '',
                    'filename': unquote(href.split('/')[-1]),
                })
        return links

    def try_sharepoint_list_api(self, doc_lib_path):
        """Try SharePoint REST API to enumerate documents in a library."""
        # SharePoint 2013+ REST API for listing files in a folder
        encoded_path = quote(doc_lib_path, safe='/')
        api_url = f"{BASE_URL}/_api/web/GetFolderByServerRelativeUrl('{encoded_path}')/Files"

        headers = {
            'Accept': 'application/json;odata=verbose',
        }

        try:
            resp = self.session.get(api_url, headers=headers, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get('d', {}).get('results', [])
                files = []
                for item in results:
                    name = item.get('Name', '')
                    url = item.get('ServerRelativeUrl', '')
                    if name.lower().endswith('.pdf'):
                        files.append({
                            'url': urljoin(BASE_URL, url),
                            'text': name,
                            'filename': name,
                            'modified': item.get('TimeLastModified', ''),
                        })
                return files
        except:
            pass

        # Try subfolder enumeration
        folders_url = f"{BASE_URL}/_api/web/GetFolderByServerRelativeUrl('{encoded_path}')/Folders"
        try:
            resp = self.session.get(folders_url, headers=headers, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                folders = data.get('d', {}).get('results', [])
                all_files = []
                for folder in folders:
                    folder_url = folder.get('ServerRelativeUrl', '')
                    folder_files = self.try_sharepoint_list_api(folder_url)
                    if folder_files:
                        all_files.extend(folder_files)
                return all_files
        except:
            pass

        return None

    def scrape_protocol_pages(self):
        """Scrape main protocol listing pages."""
        all_docs = []

        for page_path in PROTOCOL_PAGES:
            url = BASE_URL + page_path
            print(f"    Fetching: {page_path}")
            html = self.fetch_page(url)
            if not html:
                continue

            pdfs = self.extract_pdf_links_from_page(html, BASE_URL)
            for pdf in pdfs:
                pdf['source'] = page_path
            all_docs.extend(pdfs)
            print(f"      Found {len(pdfs)} PDF links")

            # Look for sub-pages / tabs / year filters
            if HAS_BS4:
                soup = BeautifulSoup(html, 'html.parser')
                # Find links to year-specific pages or filtered views
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    text = a.get_text(strip=True)
                    if ('protocol' in href.lower() or 'פרוטוקול' in text) and href != page_path:
                        sub_url = urljoin(BASE_URL, href)
                        if sub_url.startswith(BASE_URL) and sub_url not in [BASE_URL + p for p in PROTOCOL_PAGES]:
                            sub_html = self.fetch_page(sub_url)
                            if sub_html:
                                sub_pdfs = self.extract_pdf_links_from_page(sub_html, BASE_URL)
                                for pdf in sub_pdfs:
                                    pdf['source'] = href
                                all_docs.extend(sub_pdfs)
                            time.sleep(0.3)

        return all_docs

    def scrape_doc_libraries(self):
        """Try to enumerate documents from SharePoint document libraries."""
        all_docs = []

        for lib_path in DOC_LIBRARIES:
            print(f"    Trying SharePoint API for: {lib_path}")
            sp_files = self.try_sharepoint_list_api(lib_path)
            if sp_files:
                for f in sp_files:
                    f['source'] = f'SP_API:{lib_path}'
                all_docs.extend(sp_files)
                print(f"      Found {len(sp_files)} files via SharePoint API")
            else:
                # Try direct HTTP access to the library
                url = BASE_URL + lib_path
                html = self.fetch_page(url)
                if html:
                    pdfs = self.extract_pdf_links_from_page(html, BASE_URL)
                    for pdf in pdfs:
                        pdf['source'] = lib_path
                    all_docs.extend(pdfs)
                    print(f"      Found {len(pdfs)} PDF links via HTML")

        return all_docs

    def scrape_all(self, start_year, end_year):
        """Main scraping entry point."""
        print("  Step 1: Scraping protocol pages...")
        page_docs = self.scrape_protocol_pages()

        print(f"\n  Step 2: Trying SharePoint document libraries...")
        lib_docs = self.scrape_doc_libraries()

        # Combine and deduplicate
        all_docs = page_docs + lib_docs
        seen_urls = set()
        unique_docs = []
        for doc in all_docs:
            if doc['url'] not in seen_urls:
                seen_urls.add(doc['url'])
                unique_docs.append(doc)

        # Filter to protocols only
        protocol_docs = []
        for doc in unique_docs:
            text = (doc.get('text', '') + ' ' + doc.get('filename', '')).lower()
            if any(w in text for w in ['פרוטוקול', 'protocol', 'פרוט', 'החלט']):
                protocol_docs.append(doc)

        # Extract year from filename
        for doc in protocol_docs:
            filename = doc.get('filename', '') + doc.get('url', '')
            year_match = re.search(r'20[12]\d', filename)
            if year_match:
                doc['year'] = int(year_match.group())
            else:
                doc['year'] = 0

        # Filter by year range
        filtered = [d for d in protocol_docs
                   if d['year'] == 0 or (start_year <= d['year'] <= end_year)]

        return filtered


def download_files(documents, output_dir, session):
    os.makedirs(output_dir, exist_ok=True)
    success = 0
    errors = 0

    for i, doc in enumerate(documents):
        url = doc['url']
        filename = sanitize(doc.get('filename', f"doc_{i}.pdf"))
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'

        # Organize by year
        year = doc.get('year', 0)
        if year > 0:
            year_dir = os.path.join(output_dir, str(year))
            os.makedirs(year_dir, exist_ok=True)
            filepath = os.path.join(year_dir, filename)
        else:
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
    parser = argparse.ArgumentParser(description='Tel Aviv Protocol Scraper')
    parser.add_argument('--start-year', type=int, default=2015)
    parser.add_argument('--end-year', type=int, default=2026)
    parser.add_argument('--output-dir', type=str, default='output')
    parser.add_argument('--no-download', action='store_true')
    parser.add_argument('--count-only', action='store_true')
    args = parser.parse_args()

    city_output = os.path.join(args.output_dir, 'תל_אביב_יפו')

    print("=" * 60)
    print("Tel Aviv-Yafo Protocol Scraper")
    print(f"Years: {args.start_year}-{args.end_year}")
    print("=" * 60)

    scraper = TelAvivScraper()
    documents = scraper.scrape_all(args.start_year, args.end_year)

    print(f"\n  Total protocol documents found: {len(documents)}")

    counts = {}
    for doc in documents:
        year = doc.get('year', 0)
        counts[year] = counts.get(year, 0) + 1

    print(f"\n  Protocols by year:")
    for year in sorted(counts.keys()):
        print(f"    {year}: {counts[year]}")

    os.makedirs(city_output, exist_ok=True)
    json_path = os.path.join(city_output, 'תל_אביב_יפו_data.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'city': 'תל אביב-יפו',
            'platform': 'tel-aviv.gov.il',
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
