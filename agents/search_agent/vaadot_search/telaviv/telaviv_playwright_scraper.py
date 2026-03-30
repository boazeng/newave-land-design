#!/usr/bin/env python3
"""
Tel Aviv protocol scraper using Playwright with browser restart to avoid crashes.
"""
import sys, os, json, time, re, argparse, requests
from urllib.parse import unquote
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

URL = 'https://www.tel-aviv.gov.il/Transparency/Pages/Protocols.aspx'
BATCH_SIZE = 200  # SharePoint Search limit is ~200 pages


def sanitize(name):
    for c in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        name = name.replace(c, '_')
    return name.strip()


def extract_year(text):
    m = re.search(r'20[12]\d', text)
    return int(m.group()) if m else 0


def classify_committee(text):
    if 'רשות רישוי' in text or 'רישוי' in text.lower():
        return 'רשות_רישוי'
    if 'מליאת' in text or 'מליאה' in text:
        return 'מליאת_הועדה'
    if 'משנה' in text:
        if 'רישוי עסקים' in text:
            return 'ועדת_משנה_רישוי_עסקים'
        return 'ועדת_משנה'
    if 'נכסים' in text:
        return 'ועדת_נכסים'
    return 'אחר'


def scrape_batch(pw, start_page, all_pdfs, seen_urls):
    """Scrape a batch of pages with a fresh browser. Returns (last_page, found_new)."""
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto(URL, timeout=60000)
    page.wait_for_timeout(3000)

    # Navigate to start_page by clicking the right offset
    if start_page > 1:
        target_offset = (start_page - 1) * 15 + 1
        # Click through pages to get to target
        try:
            page.evaluate(f'$getClientControl(document.querySelector("[onclick*=\'.page(\']")).page({target_offset})')
            page.wait_for_timeout(3000)
        except:
            # Fallback: click sequential pages
            current = 1
            while current < start_page:
                next_offset = current * 15 + 1
                btn = page.query_selector(f'a[onclick*="page({next_offset})"]')
                if not btn:
                    # Try to find any higher offset
                    try:
                        btns = page.evaluate('''() => Array.from(document.querySelectorAll('a[onclick*=".page("]')).map(e => {
                            let m = e.getAttribute("onclick").match(/page\\((\\d+)\\)/);
                            return m ? parseInt(m[1]) : 0;
                        }).filter(x => x > 0).sort((a,b) => a-b)''')
                        higher = [b for b in btns if b > (current - 1) * 15 + 1]
                        if not higher:
                            break
                        target = higher[0]
                        btn = page.query_selector(f'a[onclick*="page({target})"]')
                        if btn:
                            btn.click()
                            page.wait_for_timeout(2000)
                            current = (target - 1) // 15 + 1
                            continue
                    except:
                        pass
                    break
                btn.click()
                page.wait_for_timeout(2000)
                current += 1

    found_new_total = 0
    current_page = start_page
    pages_in_batch = 0

    while pages_in_batch < BATCH_SIZE:
        print(f"  Page {current_page}...")

        try:
            page.wait_for_timeout(1500)
            links = page.eval_on_selector_all('a[href*=".pdf"]', '''els => els.map(e => ({
                href: e.href,
                text: e.textContent.trim()
            }))''')
        except:
            print(f"    Error reading page, stopping batch.")
            break

        new_count = 0
        for link in links:
            url = link['href']
            if url not in seen_urls:
                seen_urls.add(url)
                decoded = unquote(url)
                filename = decoded.split('/')[-1]
                all_pdfs.append({
                    'url': url,
                    'text': link['text'],
                    'filename': filename,
                    'committee': classify_committee(link['text'] or filename),
                    'year': extract_year(filename),
                })
                new_count += 1

        found_new_total += new_count
        print(f"    {new_count} new ({len(all_pdfs)} total)")

        if new_count == 0 and current_page > start_page:
            print("    No new PDFs, stopping.")
            break

        # Click next page
        next_offset = current_page * 15 + 1
        try:
            btn = page.query_selector(f'a[onclick*="page({next_offset})"]')
            if not btn:
                btns = page.evaluate('''() => Array.from(document.querySelectorAll('a[onclick*=".page("]')).map(e => {
                    let m = e.getAttribute("onclick").match(/page\\((\\d+)\\)/);
                    return m ? parseInt(m[1]) : 0;
                }).filter(x => x > 0)''')
                current_max = (current_page - 1) * 15 + 1
                higher = sorted([b for b in btns if b > current_max])
                if not higher:
                    print("    No more pages.")
                    break
                btn = page.query_selector(f'a[onclick*="page({higher[0]})"]')

            if btn:
                btn.click()
                page.wait_for_timeout(2500)
                current_page += 1
                pages_in_batch += 1
            else:
                print("    No next button.")
                break
        except Exception as e:
            print(f"    Navigation error: {e}")
            break

    browser.close()
    return current_page, found_new_total > 0


def download_files(documents, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'})

    success = 0
    errors = 0

    for i, doc in enumerate(documents):
        committee = sanitize(doc['committee'])
        filename = sanitize(doc['filename'])
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'

        folder = os.path.join(output_dir, committee)
        os.makedirs(folder, exist_ok=True)
        filepath = os.path.join(folder, filename)

        if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
            success += 1
            continue

        try:
            resp = session.get(doc['url'], timeout=60)
            resp.raise_for_status()
            with open(filepath, 'wb') as f:
                f.write(resp.content)
            success += 1
        except Exception as e:
            errors += 1
            if errors <= 10:
                print(f"    ERROR: {filename}: {e}")

        if (i + 1) % 50 == 0 or i == len(documents) - 1:
            print(f"    [{i+1}/{len(documents)}] ({success} ok, {errors} errors)")
        time.sleep(0.2)

    return success, errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', default='output')
    parser.add_argument('--count-only', action='store_true')
    parser.add_argument('--no-download', action='store_true')
    args = parser.parse_args()

    city_output = os.path.join(args.output_dir, 'תל_אביב_יפו')

    print("=" * 60)
    print("Tel Aviv-Yafo Protocol Scraper (Playwright)")
    print("=" * 60)

    all_pdfs = []
    seen_urls = set()

    with sync_playwright() as pw:
        print(f"\n--- Scanning pages ---")
        scrape_batch(pw, 1, all_pdfs, seen_urls)

    print(f"\nTotal documents found: {len(all_pdfs)}")

    counts = {}
    for doc in all_pdfs:
        y = doc['year']
        counts[y] = counts.get(y, 0) + 1
    print("\nBy year:")
    for year in sorted(counts.keys()):
        print(f"  {year if year > 0 else 'unknown'}: {counts[year]}")

    comm_counts = {}
    for doc in all_pdfs:
        comm_counts[doc['committee']] = comm_counts.get(doc['committee'], 0) + 1
    print("\nBy committee:")
    for c in sorted(comm_counts.keys()):
        print(f"  {c}: {comm_counts[c]}")

    os.makedirs(city_output, exist_ok=True)
    json_path = os.path.join(city_output, 'תל_אביב_יפו_data.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'city': 'תל אביב-יפו',
            'platform': 'tel-aviv.gov.il (Playwright)',
            'total_documents': len(all_pdfs),
            'counts_by_year': {str(k): v for k, v in counts.items()},
            'counts_by_committee': comm_counts,
            'documents': all_pdfs,
            'scraped_at': datetime.now().isoformat(),
        }, f, ensure_ascii=False, indent=2)
    print(f"\nData saved to {json_path}")

    if args.count_only or args.no_download:
        return

    print(f"\nDownloading {len(all_pdfs)} files to {city_output}...")
    success, errors = download_files(all_pdfs, city_output)
    print(f"\nDownload complete: {success} success, {errors} errors")


if __name__ == '__main__':
    main()
