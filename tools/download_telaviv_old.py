"""Download old Tel Aviv protocols by constructing URLs directly."""
import sys, os, json, re, time, requests
from urllib.parse import quote, unquote
sys.stdout.reconfigure(encoding='utf-8')

BASE_DOCLIB = 'https://www.tel-aviv.gov.il/Transparency/DocLib3'

# Protocol naming patterns seen in existing files:
# פרוטוקול דיון ועדת משנה לתכנון ובניה 2-22-0004 מיום 16.2.22.pdf
# פרוטוקול דיון מאושר ועדת משנה לתכנון ובניה 2-25-0024.pdf
# פרוטוקול החלטות ועדת משנה לתכנון ובניה 2-22-0004.pdf
# החלטות - ועדת משנה לתכנון ובניה 2-22-0004.pdf

PATTERNS = [
    'פרוטוקול החלטות ועדת משנה לתכנון ובניה 2-{yy}-{num:04d}.pdf',
    'החלטות - ועדת משנה לתכנון ובניה 2-{yy}-{num:04d}.pdf',
    'פרוטוקול דיון ועדת משנה לתכנון ובניה 2-{yy}-{num:04d}.pdf',
    'פרוטוקול דיון מאושר ועדת משנה לתכנון ובניה 2-{yy}-{num:04d}.pdf',
    'החלטות - ועדת משנה לתכנון ובנייה - 2-{yy}-{num:04d}.pdf',
    'החלטות- ועדת משנה לתכנון ובניה 2-{yy}-{num:04d}.pdf',
    'פרוטוקול דיון ועדת משנה 2-{yy}-{num:04d}.pdf',
]

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'})

year = int(sys.argv[1]) if len(sys.argv) > 1 else 21
output_dir = sys.argv[2] if len(sys.argv) > 2 else f'c:/Users/boaze/Ai-Projects/newave land design/newave-land-design/data/protocols/תל_אביב_יפו_ועדת_משנה/{year}'
yy = str(year) if year < 100 else str(year)[-2:]

os.makedirs(output_dir, exist_ok=True)

print(f"Searching for year 20{yy} protocols...")
print(f"Output: {output_dir}")

found = []
not_found_streak = 0
max_streak = 10  # Stop after 10 consecutive misses

for num in range(1, 50):  # Typically ~25 meetings per year
    found_any = False

    for pattern in PATTERNS:
        filename = pattern.format(yy=yy, num=num)
        url = f'{BASE_DOCLIB}/{quote(filename)}'

        try:
            resp = session.head(url, timeout=10, allow_redirects=True)
            if resp.status_code == 200:
                # Verify it's actually a PDF (not a redirect to homepage)
                content_type = resp.headers.get('Content-Type', '')
                content_length = int(resp.headers.get('Content-Length', 0))

                if content_length > 5000:  # Real PDF
                    print(f"  FOUND: {filename} ({content_length // 1024} KB)")

                    # Download
                    filepath = os.path.join(output_dir, filename)
                    if not os.path.exists(filepath):
                        dl = session.get(url, timeout=60)
                        with open(filepath, 'wb') as f:
                            f.write(dl.content)

                    found.append({'filename': filename, 'url': url, 'size': content_length})
                    found_any = True
                    time.sleep(0.3)
                    break  # Found one pattern for this number, move to next

        except Exception as e:
            pass

        time.sleep(0.2)

    if found_any:
        not_found_streak = 0
    else:
        not_found_streak += 1
        if not_found_streak >= max_streak:
            print(f"  {max_streak} consecutive misses, stopping.")
            break

print(f"\n{'='*60}")
print(f"Year 20{yy}: Found {len(found)} protocols")
for f in found:
    print(f"  {f['filename']} ({f['size']//1024} KB)")

# Save index
index_path = os.path.join(output_dir, f'index_20{yy}.json')
with open(index_path, 'w', encoding='utf-8') as f:
    json.dump({'year': f'20{yy}', 'found': len(found), 'files': found}, f, ensure_ascii=False, indent=2)
