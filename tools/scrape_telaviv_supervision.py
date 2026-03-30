"""Scrape all protocols from Tel Aviv Supervision page - clicking through all pages."""
import sys, os, json, re, time, requests
from urllib.parse import unquote
sys.stdout.reconfigure(encoding='utf-8')
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1, encoding='utf-8')
from playwright.sync_api import sync_playwright

URL = 'https://www.tel-aviv.gov.il/Transparency/Pages/Supervision.aspx'
OUTPUT_DIR = sys.argv[1] if len(sys.argv) > 1 else 'c:/Users/boaze/Ai-Projects/newave land design/newave-land-design/data/protocols/תל_אביב_יפו_ועדת_משנה_רישוי'

def sanitize(name):
    for c in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        name = name.replace(c, '_')
    return name.strip()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    print(f"Loading {URL}")
    page.goto(URL, timeout=60000)
    page.wait_for_timeout(5000)
    print(f"Title: {page.title()}")

    all_pdfs = []
    seen_urls = set()
    page_num = 1

    while True:
        print(f"\n  Page {page_num}...")
        page.wait_for_timeout(2000)

        # Get all PDF links
        links = page.eval_on_selector_all('a[href*=".pdf"]', '''els => els.map(e => ({
            href: e.href,
            text: e.textContent.trim()
        }))''')

        new_count = 0
        for link in links:
            if link['href'] not in seen_urls:
                seen_urls.add(link['href'])
                decoded = unquote(link['href'])
                filename = decoded.split('/')[-1]
                all_pdfs.append({
                    'url': link['href'],
                    'text': link['text'],
                    'filename': filename,
                })
                new_count += 1

        print(f"    {len(links)} links, {new_count} new ({len(all_pdfs)} total)")

        if new_count == 0 and page_num > 1:
            print("    No new PDFs, stopping.")
            break

        # Find next page button
        try:
            btns = page.evaluate('''() => Array.from(document.querySelectorAll('a[onclick*=".page("]')).map(e => {
                let m = e.getAttribute("onclick").match(/page\\((\\d+)\\)/);
                return m ? parseInt(m[1]) : 0;
            }).filter(x => x > 0)''')

            current_max = (page_num - 1) * 15 + 1
            higher = sorted([b for b in btns if b > current_max])

            if not higher:
                print("    No more pages.")
                break

            target = higher[0]
            btn = page.query_selector(f'a[onclick*="page({target})"]')
            if btn:
                btn.click()
                page.wait_for_timeout(2500)
                page_num += 1
            else:
                print("    No button found.")
                break
        except Exception as e:
            print(f"    Navigation error: {e}")
            break

        if page_num > 500:
            print("    Page limit reached.")
            break

    browser.close()

print(f"\nTotal unique PDFs: {len(all_pdfs)}")

# Filter only protocols (not agendas)
protocols = [p for p in all_pdfs if 'פרוטוקול' in p['text'] or 'החלטות' in p['text']]
agendas = [p for p in all_pdfs if 'סדר יום' in p['text']]
other = [p for p in all_pdfs if p not in protocols and p not in agendas]
print(f"Protocols: {len(protocols)}, Agendas: {len(agendas)}, Other: {len(other)}")

# Check year range
years = {}
for pdf in all_pdfs:
    for m in re.finditer(r'2-(\d{2})-', pdf['filename']):
        y = f'20{m.group(1)}'
        years[y] = years.get(y, 0) + 1
print(f"Years: {dict(sorted(years.items()))}")

# Download all
os.makedirs(OUTPUT_DIR, exist_ok=True)
session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'})

print(f"\nDownloading {len(all_pdfs)} files to {OUTPUT_DIR}...")
ok = 0
errors = 0
for i, pdf in enumerate(all_pdfs):
    filename = sanitize(pdf['filename'])
    if not filename.lower().endswith('.pdf'):
        filename += '.pdf'
    filepath = os.path.join(OUTPUT_DIR, filename)

    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        ok += 1
        continue

    try:
        resp = session.get(pdf['url'], timeout=60)
        resp.raise_for_status()
        with open(filepath, 'wb') as f:
            f.write(resp.content)
        ok += 1
    except Exception as e:
        errors += 1
        if errors <= 5:
            print(f"  ERROR: {filename}: {e}")

    if (i + 1) % 50 == 0 or i == len(all_pdfs) - 1:
        print(f"  [{i+1}/{len(all_pdfs)}] ({ok} ok, {errors} errors)")
    time.sleep(0.2)

# Save index
with open(os.path.join(OUTPUT_DIR, 'index.json'), 'w', encoding='utf-8') as f:
    json.dump({
        'total': len(all_pdfs),
        'protocols': len(protocols),
        'agendas': len(agendas),
        'years': years,
        'files': all_pdfs,
    }, f, ensure_ascii=False, indent=2)

print(f"\nDone: {ok} downloaded, {errors} errors")
