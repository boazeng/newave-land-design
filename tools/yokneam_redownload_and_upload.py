"""
Re-download all Yokneam protocols with unique filenames and upload to SharePoint.
Adds a numeric suffix to avoid filename collisions.
"""
import sys, os, json, requests, time
from pathlib import Path
from dotenv import load_dotenv
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv('c:/Users/User/Aiprojects/env/.env')

DATA_DIR = Path('c:/Users/User/Aiprojects/newave land design/data/yokneam_protocols')
JSON_PATH = DATA_DIR / 'yokneam_data_2020_2026.json'

COMMITTEE_NAMES = {"1": "רשות רישוי מקומית", "2": "ועדת משנה", "3": "מליאת הועדה", "4": "ועדת שימור"}

# SharePoint config
tenant_id = os.getenv('SHAREPOINT_TENANT_ID')
client_id = os.getenv('SHAREPOINT_CLIENT_ID')
client_secret = os.getenv('SHAREPOINT_CLIENT_SECRET')
SITE_ID = 'yaelisrael.sharepoint.com,1e880094-7633-4f48-aee6-88f272bd30ee,e624f0cf-a6b3-4f1c-b2d8-911f75d1c14f'
DRIVE_ID = 'b!lACIHjN2SE-u5ojycr0w7s_wJOazphxPstiRH3XRwU8YVObFPrGeSY2HFvo2E83m'
BASE = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/drives/{DRIVE_ID}"


def get_token():
    r = requests.post(f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token", data={
        'grant_type': 'client_credentials', 'client_id': client_id,
        'client_secret': client_secret, 'scope': 'https://graph.microsoft.com/.default',
    })
    return r.json()['access_token']


def create_folder(headers, parent_id, name):
    url = f"{BASE}/items/{parent_id}/children"
    r = requests.post(url, headers={**headers, 'Content-Type': 'application/json'}, json={
        'name': name, 'folder': {}, '@microsoft.graph.conflictBehavior': 'replace'
    })
    if r.status_code in (200, 201):
        return r.json()['id']
    lr = requests.get(url, headers=headers)
    if lr.status_code == 200:
        for item in lr.json().get('value', []):
            if item['name'] == name and 'folder' in item:
                return item['id']
    return None


def delete_folder_contents(headers, folder_id):
    """Delete all items in a folder recursively."""
    url = f"{BASE}/items/{folder_id}/children"
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return
    for item in r.json().get('value', []):
        requests.delete(f"{BASE}/items/{item['id']}", headers=headers)
        time.sleep(0.1)


def upload_file(headers, parent_id, filepath):
    name = os.path.basename(filepath)
    size = os.path.getsize(filepath)
    if size < 4 * 1024 * 1024:
        url = f"{BASE}/items/{parent_id}:/{name}:/content"
        with open(filepath, 'rb') as f:
            r = requests.put(url, headers={**headers, 'Content-Type': 'application/octet-stream'}, data=f)
        return r.status_code in (200, 201)
    else:
        url = f"{BASE}/items/{parent_id}:/{name}:/createUploadSession"
        s = requests.post(url, headers={**headers, 'Content-Type': 'application/json'}, json={
            'item': {'@microsoft.graph.conflictBehavior': 'replace'}
        })
        if s.status_code not in (200, 201):
            return False
        upload_url = s.json()['uploadUrl']
        with open(filepath, 'rb') as f:
            offset = 0
            while offset < size:
                chunk = f.read(10 * 1024 * 1024)
                end = offset + len(chunk) - 1
                r = requests.put(upload_url, headers={
                    'Content-Length': str(len(chunk)), 'Content-Range': f'bytes {offset}-{end}/{size}'
                }, data=chunk)
                if r.status_code not in (200, 201, 202):
                    return False
                offset += len(chunk)
        return True


def sanitize(name):
    for c in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        name = name.replace(c, '_')
    return name.strip()


def process_year(year, docs, headers, yokneam_id):
    """Download and upload all docs for a single year."""
    print(f"\n{'='*60}")
    print(f"  YEAR {year}: {len(docs)} documents")
    print(f"{'='*60}")

    # Create/clean year folder on SharePoint
    year_id = create_folder(headers, yokneam_id, str(year))
    delete_folder_contents(headers, year_id)
    time.sleep(1)

    # Group by committee type
    by_comm = defaultdict(list)
    for d in docs:
        by_comm[d['committeeType']].append(d)

    downloaded = 0
    uploaded = 0
    failed = 0

    for comm_type in sorted(by_comm.keys()):
        comm_docs = by_comm[comm_type]
        comm_name = COMMITTEE_NAMES.get(comm_type, f"סוג_{comm_type}")

        # Create local dir
        local_dir = DATA_DIR / f"v2_{year}" / sanitize(comm_name)
        local_dir.mkdir(parents=True, exist_ok=True)

        # Create SharePoint folder
        comm_sp_id = create_folder(headers, year_id, comm_name)

        print(f"\n  {comm_name}: {len(comm_docs)} docs")

        # Generate unique filenames with counter
        name_counter = defaultdict(int)

        for doc in comm_docs:
            date_str = doc['date'].replace('/', '-')
            meeting = doc['meetingNumber']
            base_name = f"{date_str}_{meeting}"

            name_counter[base_name] += 1
            idx = name_counter[base_name]
            filename = f"{base_name}_doc{idx}.pdf"

            local_path = local_dir / filename

            # Download if not cached
            if not local_path.exists() or local_path.stat().st_size < 500:
                try:
                    r = requests.get(doc['url'], timeout=30)
                    r.raise_for_status()
                    local_path.write_bytes(r.content)
                    downloaded += 1
                    time.sleep(0.2)
                except Exception as e:
                    print(f"    DL FAIL: {filename} - {e}")
                    failed += 1
                    continue

            # Upload to SharePoint
            ok = upload_file(headers, comm_sp_id, str(local_path))
            if ok:
                uploaded += 1
            else:
                print(f"    UP FAIL: {filename}")
                failed += 1
            time.sleep(0.15)

    print(f"\n  Year {year}: downloaded={downloaded}, uploaded={uploaded}, failed={failed}")
    return uploaded, failed


def main():
    with open(JSON_PATH, encoding='utf-8') as f:
        data = json.load(f)

    docs = data['documents']

    # Group by year
    by_year = defaultdict(list)
    for d in docs:
        by_year[d['year']].append(d)

    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}

    # Find yokneam folder
    root_r = requests.get(f'{BASE}/root/children', headers=headers)
    root_id = None
    for item in root_r.json().get('value', []):
        if 'החלטות' in item['name']:
            root_id = item['id']
            break
    yokneam_id = create_folder(headers, root_id, 'יקנעם עילית')

    total_uploaded = 0
    total_failed = 0

    for year in sorted(by_year.keys()):
        year_docs = by_year[year]
        expected = {2020: 48, 2021: 90, 2022: 66, 2023: 51, 2024: 56, 2025: 56, 2026: 8}
        exp = expected.get(year, '?')
        print(f"\nExpected for {year}: {exp}, Got: {len(year_docs)}")

        up, fail = process_year(year, year_docs, headers, yokneam_id)
        total_uploaded += up
        total_failed += fail

        # Refresh token every year (in case it expires)
        token = get_token()
        headers = {'Authorization': f'Bearer {token}'}

    print(f"\n{'='*60}")
    print(f"  ALL DONE!")
    print(f"  Total uploaded: {total_uploaded}")
    print(f"  Total failed: {total_failed}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
