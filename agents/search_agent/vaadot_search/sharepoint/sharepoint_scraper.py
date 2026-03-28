#!/usr/bin/env python3
"""
סקריפט להורדת פרוטוקולים מאתרי עיריות המבוססים על SharePoint / muni.il.
עובד עם: בני ברק, גבעתיים, הרצליה, רמת השרון.

כל אתר עירוני מבוסס SharePoint חושף document library שניתן לגשת אליו
דרך SharePoint REST API או דרך scraping של דפי HTML.

התקנה:
    pip install requests beautifulsoup4

הרצה:
    python3 sharepoint_scraper.py --city bnei-brak --start-year 2015 --end-year 2026
    python3 sharepoint_scraper.py --city givatayim --start-year 2015 --end-year 2026
    python3 sharepoint_scraper.py --city herzliya --start-year 2015 --end-year 2026
    python3 sharepoint_scraper.py --city ramat-hasharon --start-year 2015 --end-year 2026

פרמטרים:
    --city          שם העיר (bnei-brak/givatayim/herzliya/ramat-hasharon) (חובה)
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
from urllib.parse import urljoin, quote, unquote
from datetime import datetime

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("Warning: beautifulsoup4 not installed. pip install beautifulsoup4")

# City configurations - URLs for protocol pages and document libraries
CITY_CONFIGS = {
    'bnei-brak': {
        'name': 'בני_ברק',
        'name_heb': 'בני ברק',
        'base_url': 'https://www.bnei-brak.muni.il',
        'protocol_pages': [
            '/Service/Pages/protocol_handasa.aspx',
            '/Service/eng/pages/yeshiva.aspx',
        ],
        'doc_library_patterns': [
            '/Service/Documents/פרוטוקולים של וועדת תכנון ובנייה/',
            '/Service/Documents/',
        ],
        'sharepoint_api': True,
    },
    'givatayim': {
        'name': 'גבעתיים',
        'name_heb': 'גבעתיים',
        'base_url': 'https://www.givatayim.muni.il',
        'protocol_pages': [
            '/Services/handasa/Pages/protocols.aspx',
            '/162/',
            '/ישיבות-ועדה/',
        ],
        'doc_library_patterns': [],
        'sharepoint_api': True,
    },
    'herzliya': {
        'name': 'הרצליה',
        'name_heb': 'הרצליה',
        'base_url': 'https://www.herzliya.muni.il',
        'protocol_pages': [
            '/protocols/',
            '/ועדות-עירוניות/',
        ],
        'engineering_url': 'https://handasa.herzliya.muni.il',
        'engineering_pages': [
            '/yad9/licenscommit/',
        ],
        'doc_library_patterns': [],
        'sharepoint_api': False,
        # Herzliya also has a Complot site - try that too
        'complot_subdomain': 'herzliya',
    },
    'ramat-hasharon': {
        'name': 'רמת_השרון',
        'name_heb': 'רמת השרון',
        'base_url': 'https://ramat-hasharon.muni.il',
        'protocol_pages': [
            '/פרוטוקולים-ועדות-העירייה/',
            '/פרוטוקולים-ועדות-העירייה/פרוטוקולים-ישיבות-מועצה/',
        ],
        'doc_library_patterns': [],
        'sharepoint_api': False,
        # Ramat HaSharon has a Complot site
        'complot_subdomain': 'ramathasharon',
    },
}


def sanitize(name):
    for c in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        name = name.replace(c, '_')
    return name.strip()


class SharePointScraper:
    def __init__(self, city_key):
        if city_key not in CITY_CONFIGS:
            raise ValueError(f"Unknown city: {city_key}. Valid: {list(CITY_CONFIGS.keys())}")
        self.config = CITY_CONFIGS[city_key]
        self.city_key = city_key
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

    def extract_pdf_links(self, html_text, base_url):
        """Extract all PDF links from HTML page."""
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

    def extract_subpage_links(self, html_text, base_url):
        """Extract links to sub-pages that might contain more protocols."""
        links = []
        if not html_text or not HAS_BS4:
            return links

        soup = BeautifulSoup(html_text, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text(strip=True)
            # Look for links that contain year numbers or protocol-related words
            if re.search(r'20[12]\d', href) or any(w in text for w in ['פרוטוקול', 'ישיב', 'ועד', 'protocol']):
                full_url = urljoin(base_url, href)
                if full_url.startswith(base_url) or full_url.startswith(self.config.get('engineering_url', '')):
                    links.append({'url': full_url, 'text': text})

        return links

    def try_sharepoint_api(self, base_url, doc_lib_path):
        """Try SharePoint REST API to list documents."""
        # SharePoint 2013+ REST API
        api_url = f"{base_url}/_api/web/GetFolderByServerRelativeUrl('{doc_lib_path}')/Files"
        headers = {
            'Accept': 'application/json;odata=verbose',
        }
        try:
            resp = self.session.get(api_url, headers=headers, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get('d', {}).get('results', [])
                links = []
                for item in results:
                    url = item.get('ServerRelativeUrl', '')
                    name = item.get('Name', '')
                    if name.lower().endswith('.pdf'):
                        links.append({
                            'url': urljoin(base_url, url),
                            'text': name,
                            'filename': name,
                        })
                return links
        except:
            pass
        return None

    def scrape_protocols(self, start_year, end_year, protocols_only=True):
        """Main scraping logic."""
        all_documents = []
        visited_urls = set()

        base_url = self.config['base_url']

        # Step 1: Visit main protocol pages
        print(f"  Scanning protocol pages...")
        for page_path in self.config['protocol_pages']:
            url = base_url + page_path
            if url in visited_urls:
                continue
            visited_urls.add(url)

            print(f"    Fetching: {page_path}")
            html = self.fetch_page(url)
            if not html:
                continue

            # Extract PDFs directly
            pdfs = self.extract_pdf_links(html, base_url)
            for pdf in pdfs:
                pdf['source_page'] = page_path
                all_documents.append(pdf)

            # Extract sub-page links and follow them
            subpages = self.extract_subpage_links(html, base_url)
            for sp in subpages[:50]:  # Limit to prevent infinite crawling
                if sp['url'] in visited_urls:
                    continue
                visited_urls.add(sp['url'])

                sub_html = self.fetch_page(sp['url'])
                if sub_html:
                    sub_pdfs = self.extract_pdf_links(sub_html, base_url)
                    for pdf in sub_pdfs:
                        pdf['source_page'] = sp['url']
                        all_documents.append(pdf)
                time.sleep(0.3)

        # Step 2: Try SharePoint document library paths
        for doc_path in self.config.get('doc_library_patterns', []):
            print(f"    Trying doc library: {doc_path}")
            # Try SharePoint API
            sp_docs = self.try_sharepoint_api(base_url, doc_path)
            if sp_docs:
                for doc in sp_docs:
                    doc['source_page'] = f'SP_API:{doc_path}'
                    all_documents.append(doc)
                print(f"      Found {len(sp_docs)} docs via SharePoint API")
            else:
                # Try direct HTTP listing
                url = base_url + doc_path
                html = self.fetch_page(url)
                if html:
                    pdfs = self.extract_pdf_links(html, base_url)
                    for pdf in pdfs:
                        pdf['source_page'] = doc_path
                        all_documents.append(pdf)

        # Step 3: Try engineering sub-site if configured
        eng_url = self.config.get('engineering_url')
        if eng_url:
            print(f"  Scanning engineering site: {eng_url}")
            for page_path in self.config.get('engineering_pages', []):
                url = eng_url + page_path
                html = self.fetch_page(url)
                if html:
                    pdfs = self.extract_pdf_links(html, eng_url)
                    for pdf in pdfs:
                        pdf['source_page'] = f'eng:{page_path}'
                        all_documents.append(pdf)

                    subpages = self.extract_subpage_links(html, eng_url)
                    for sp in subpages[:30]:
                        if sp['url'] in visited_urls:
                            continue
                        visited_urls.add(sp['url'])
                        sub_html = self.fetch_page(sp['url'])
                        if sub_html:
                            sub_pdfs = self.extract_pdf_links(sub_html, eng_url)
                            for pdf in sub_pdfs:
                                pdf['source_page'] = sp['url']
                                all_documents.append(pdf)
                        time.sleep(0.3)

        # Deduplicate
        seen_urls = set()
        unique_docs = []
        for doc in all_documents:
            if doc['url'] not in seen_urls:
                seen_urls.add(doc['url'])
                unique_docs.append(doc)

        # Filter by protocol keywords
        if protocols_only:
            protocol_docs = []
            for doc in unique_docs:
                text = (doc.get('text', '') + ' ' + doc.get('filename', '')).lower()
                if any(w in text for w in ['פרוטוקול', 'protocol', 'פרוט', 'החלט']):
                    protocol_docs.append(doc)
            unique_docs = protocol_docs

        # Try to extract year from filename/URL
        for doc in unique_docs:
            filename = doc.get('filename', '') + doc.get('url', '')
            year_match = re.search(r'20[12]\d', filename)
            if year_match:
                doc['year'] = int(year_match.group())
            else:
                doc['year'] = 0

        # Filter by year range
        filtered = [d for d in unique_docs
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
        filepath = os.path.join(output_dir, filename)

        if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
            success += 1
            continue

        try:
            resp = session.get(url, timeout=60)
            resp.raise_for_status()
            content_type = resp.headers.get('Content-Type', '')
            if 'pdf' in content_type or 'octet' in content_type or len(resp.content) > 5000:
                with open(filepath, 'wb') as f:
                    f.write(resp.content)
                success += 1
            else:
                errors += 1
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"    ERROR: {url}: {e}")

        if (i + 1) % 10 == 0:
            print(f"    [{i+1}/{len(documents)}] ({success} ok, {errors} errors)")
        time.sleep(0.3)

    return success, errors


def main():
    parser = argparse.ArgumentParser(description='SharePoint/muni.il Protocol Scraper')
    parser.add_argument('--city', type=str, required=True,
                       choices=list(CITY_CONFIGS.keys()),
                       help='City to scrape')
    parser.add_argument('--start-year', type=int, default=2015)
    parser.add_argument('--end-year', type=int, default=2026)
    parser.add_argument('--output-dir', type=str, default='output')
    parser.add_argument('--no-download', action='store_true')
    parser.add_argument('--count-only', action='store_true')
    args = parser.parse_args()

    config = CITY_CONFIGS[args.city]
    city = config['name']
    city_output = os.path.join(args.output_dir, city)

    print("=" * 60)
    print(f"SharePoint/muni.il Scraper - {config['name_heb']}")
    print(f"Base URL: {config['base_url']}")
    print(f"Years: {args.start_year}-{args.end_year}")
    print("=" * 60)

    scraper = SharePointScraper(args.city)
    documents = scraper.scrape_protocols(args.start_year, args.end_year, protocols_only=True)

    print(f"\n  Total protocol documents found: {len(documents)}")

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
            'city': config['name_heb'],
            'platform': 'sharepoint/muni.il',
            'base_url': config['base_url'],
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
