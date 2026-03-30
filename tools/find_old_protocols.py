"""Exhaustive search for Tel Aviv 2015-2018 protocols."""
import sys, os, json, requests, time
from urllib.parse import quote
sys.stdout.reconfigure(encoding='utf-8')
# Force unbuffered
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1, encoding='utf-8')

BASE_URLS = [
    'https://www.tel-aviv.gov.il/Transparency/DocLib3',
    'https://www.tel-aviv.gov.il/Residents/Development/DocLib',
]

PATTERNS = [
    'החלטות - ועדת משנה לתכנון ובנייה - 2-{yy}-{num:04d}.pdf',
    'החלטות ועדת משנה לתכנון ובנייה 2-{yy}-{num:04d}.pdf',
    'החלטות - ועדת משנה לתכנון ובניה - 2-{yy}-{num:04d}.pdf',
    'החלטות - ועדת משנה לתכנון ובניה 2-{yy}-{num:04d}.pdf',
    'החלטות ועדת משנה לתכנון ובניה 2-{yy}-{num:04d}.pdf',
    'פרוטוקול החלטות ועדת משנה לתכנון ובנייה 2-{yy}-{num:04d}.pdf',
    'פרוטוקול החלטות ועדת משנה לתכנון ובניה 2-{yy}-{num:04d}.pdf',
    'פרוטוקול דיון ועדת משנה לתכנון ובנייה 2-{yy}-{num:04d}.pdf',
    'פרוטוקול דיון ועדת משנה לתכנון ובניה 2-{yy}-{num:04d}.pdf',
    'פרוטוקול דיון ועדת משנה 2-{yy}-{num:04d}.pdf',
    'פרוטוקול דיון - ועדת משנה לתכנון ובניה 2-{yy}-{num:04d}.pdf',
    'פרוטוקול ועדת משנה 2-{yy}-{num:04d}.pdf',
    'ועדת משנה 2-{yy}-{num:04d}.pdf',
    # Without leading zeros
    'החלטות - ועדת משנה לתכנון ובנייה - 2-{yy}-{num}.pdf',
    'החלטות - ועדת משנה לתכנון ובניה 2-{yy}-{num}.pdf',
    # Full year
    'החלטות - ועדת משנה לתכנון ובנייה - 2-20{yy}-{num:04d}.pdf',
    'החלטות - ועדת משנה לתכנון ובניה 2-20{yy}-{num:04d}.pdf',
    'פרוטוקול החלטות ועדת משנה 2-20{yy}-{num:04d}.pdf',
    # Hebrew number prefix
    'פרוטוקול מספר 2-{yy}-{num:04d}.pdf',
    'החלטות מספר 2-{yy}-{num:04d}.pdf',
]

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'})

output_base = 'c:/Users/boaze/Ai-Projects/newave land design/newave-land-design/data/protocols/תל_אביב_יפו_ועדת_משנה'
all_found = []

for yy in ['15', '16', '17', '18']:
    print(f'\n=== Year 20{yy} ===')
    found = 0
    miss_streak = 0

    for num in range(1, 35):
        hit = False
        for base_url in BASE_URLS:
            for pattern in PATTERNS:
                try:
                    filename = pattern.format(yy=yy, num=num)
                except:
                    continue
                url = f'{base_url}/{quote(filename)}'
                try:
                    r = s.head(url, timeout=8, allow_redirects=True)
                    cl = int(r.headers.get('Content-Length', 0))
                    if r.status_code == 200 and cl > 5000:
                        lib = base_url.split('/')[-1]
                        print(f'  FOUND [{lib}] #{num}: {filename} ({cl//1024} KB)')

                        # Download
                        out_dir = os.path.join(output_base, yy)
                        os.makedirs(out_dir, exist_ok=True)
                        filepath = os.path.join(out_dir, filename)
                        if not os.path.exists(filepath):
                            dl = s.get(url, timeout=60)
                            with open(filepath, 'wb') as f:
                                f.write(dl.content)

                        all_found.append({'year': f'20{yy}', 'num': num, 'filename': filename, 'size': cl})
                        found += 1
                        hit = True
                        break
                except:
                    pass
                time.sleep(0.05)
            if hit:
                break

        if hit:
            miss_streak = 0
        else:
            miss_streak += 1

    print(f'  Year 20{yy}: {found} found')

print(f'\n{"="*60}')
print(f'Total found: {len(all_found)}')
for f in all_found:
    print(f'  {f["year"]}: {f["filename"]}')
