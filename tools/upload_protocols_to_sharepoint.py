"""
Upload a city's protocol PDFs to SharePoint so the app can serve them from the cloud.

Only uploads files actually referenced by the city's parking results JSON (source_files),
keeping SharePoint free of protocols nothing links to. Filenames are preserved exactly -
the app looks them up by name, so any rename breaks the lookup.

Usage:  python tools/upload_protocols_to_sharepoint.py <city_key> [--dry-run]
Example: python tools/upload_protocols_to_sharepoint.py givatayim --dry-run
"""
import sys
import os
import json
import time
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO, 'data')
load_dotenv(os.path.join(os.path.dirname(REPO), 'env', '.env'))

SITE_ID = 'yaelisrael.sharepoint.com,1e880094-7633-4f48-aee6-88f272bd30ee,e624f0cf-a6b3-4f1c-b2d8-911f75d1c14f'
DRIVE_ID = 'b!lACIHjN2SE-u5ojycr0w7s_wJOazphxPstiRH3XRwU8YVObFPrGeSY2HFvo2E83m'
BASE = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/drives/{DRIVE_ID}"
SP_ROOT = 'החלטות ועדות תכנון'
CHUNK_THRESHOLD = 4 * 1024 * 1024

# city_key -> (SharePoint city folder, results json, local protocol root)
CITIES = {
    'givatayim': ('גבעתיים', 'parking_protocols_givatayim.json', 'protocols_search/גבעתיים'),
}


def get_token():
    resp = requests.post(
        f"https://login.microsoftonline.com/{os.getenv('SHAREPOINT_TENANT_ID')}/oauth2/v2.0/token",
        data={
            'grant_type': 'client_credentials',
            'client_id': os.getenv('SHAREPOINT_CLIENT_ID'),
            'client_secret': os.getenv('SHAREPOINT_CLIENT_SECRET'),
            'scope': 'https://graph.microsoft.com/.default',
        }, timeout=30,
    )
    resp.raise_for_status()
    return resp.json()['access_token']


def referenced_files(results_json):
    """Filenames the app will actually ask SharePoint for."""
    path = os.path.join(DATA_DIR, results_json)
    data = json.load(open(path, encoding='utf-8'))
    items = data if isinstance(data, list) else data.get('results', data.get('protocols', []))
    names = set()
    for item in items:
        for f in (item.get('source_files') or []):
            names.add(f)
    return names


def index_local(root):
    """Map filename -> full path for every PDF under the local protocol root."""
    index = {}
    for dirpath, _, files in os.walk(os.path.join(DATA_DIR, root)):
        for f in files:
            if f.lower().endswith('.pdf'):
                index[f] = os.path.join(dirpath, f)
    return index


def existing_names(headers, folder):
    from urllib.parse import quote
    r = requests.get(f"{BASE}/root:/{quote(folder)}:/children?$top=999", headers=headers, timeout=30)
    if r.status_code != 200:
        return set()
    return {i['name'] for i in r.json().get('value', [])}


def upload(headers, folder, name, path):
    from urllib.parse import quote
    size = os.path.getsize(path)
    target = f"{BASE}/root:/{quote(folder)}/{quote(name)}:"

    if size < CHUNK_THRESHOLD:
        with open(path, 'rb') as f:
            r = requests.put(f"{target}/content", headers={**headers, 'Content-Type': 'application/octet-stream'},
                             data=f, timeout=120)
        return r.status_code in (200, 201), r.status_code

    # Large file: resumable upload session
    r = requests.post(f"{target}/createUploadSession", headers={**headers, 'Content-Type': 'application/json'},
                      json={'item': {'@microsoft.graph.conflictBehavior': 'replace'}}, timeout=30)
    if r.status_code not in (200, 201):
        return False, r.status_code
    url = r.json()['uploadUrl']
    chunk = 5 * 1024 * 1024
    with open(path, 'rb') as f:
        start = 0
        while start < size:
            block = f.read(chunk)
            end = start + len(block) - 1
            cr = requests.put(url, headers={'Content-Length': str(len(block)),
                                            'Content-Range': f'bytes {start}-{end}/{size}'},
                              data=block, timeout=300)
            if cr.status_code not in (200, 201, 202):
                return False, cr.status_code
            start = end + 1
    return True, 200


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in CITIES:
        print(f"Usage: python tools/upload_protocols_to_sharepoint.py <{'|'.join(CITIES)}> [--dry-run]")
        return 1
    city_key = sys.argv[1]
    dry = '--dry-run' in sys.argv
    sp_city, results_json, local_root = CITIES[city_key]

    refs = referenced_files(results_json)
    index = index_local(local_root)
    found = {n: p for n, p in index.items() if n in refs}
    missing = sorted(refs - set(index))

    print(f"City            : {sp_city}")
    print(f"Referenced      : {len(refs)}")
    print(f"Found locally   : {len(found)}")
    if missing:
        print(f"MISSING locally : {len(missing)}  e.g. {missing[:2]}")
    total = sum(os.path.getsize(p) for p in found.values())
    print(f"Upload size     : {total / 1024 / 1024:.1f} MB")

    headers = {'Authorization': f'Bearer {get_token()}'}

    # Group by the subfolder the file sits in locally, mirroring that structure on SharePoint
    groups = {}
    for name, path in found.items():
        sub = os.path.basename(os.path.dirname(path))
        groups.setdefault(sub, {})[name] = path

    uploaded = skipped = failed = 0
    for sub, files in sorted(groups.items()):
        folder = f"{SP_ROOT}/{sp_city}/{sub}"
        already = existing_names(headers, folder)
        todo = {n: p for n, p in files.items() if n not in already}
        print(f"\n{folder}")
        print(f"  {len(files)} to place | {len(files) - len(todo)} already there | {len(todo)} to upload")
        skipped += len(files) - len(todo)
        if dry:
            continue
        for i, (name, path) in enumerate(sorted(todo.items()), 1):
            ok, status = upload(headers, folder, name, path)
            if ok:
                uploaded += 1
            else:
                failed += 1
                print(f"  FAIL {status}: {name}")
            if i % 10 == 0:
                print(f"  ...{i}/{len(todo)}")
            time.sleep(0.05)

    print(f"\n{'[dry-run] ' if dry else ''}uploaded={uploaded} skipped={skipped} failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
