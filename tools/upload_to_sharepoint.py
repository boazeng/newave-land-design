"""Upload Yokneam protocols to SharePoint organized by year and committee type."""
import sys, os, json, requests, time
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv('c:/Users/User/Aiprojects/env/.env')

tenant_id = os.getenv('SHAREPOINT_TENANT_ID')
client_id = os.getenv('SHAREPOINT_CLIENT_ID')
client_secret = os.getenv('SHAREPOINT_CLIENT_SECRET')

SITE_ID = 'yaelisrael.sharepoint.com,1e880094-7633-4f48-aee6-88f272bd30ee,e624f0cf-a6b3-4f1c-b2d8-911f75d1c14f'
DRIVE_ID = 'b!lACIHjN2SE-u5ojycr0w7s_wJOazphxPstiRH3XRwU8YVObFPrGeSY2HFvo2E83m'
GRAPH = "https://graph.microsoft.com/v1.0"
BASE = f"{GRAPH}/sites/{SITE_ID}/drives/{DRIVE_ID}"

DATA_DIR = Path('c:/Users/User/Aiprojects/newave land design/data/yokneam_protocols')

COMMITTEE_NAMES = {"1": "רשות רישוי מקומית", "2": "ועדת משנה", "3": "מליאת הועדה", "4": "ועדת שימור"}
LOCAL_DIRS = {"1": "01_רשות_רישוי_מקומית", "2": "02_ועדת_משנה", "3": "03_מליאת_הועדה", "4": "04_ועדת_שימור"}


def get_token():
    resp = requests.post(f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token", data={
        'grant_type': 'client_credentials', 'client_id': client_id,
        'client_secret': client_secret, 'scope': 'https://graph.microsoft.com/.default',
    })
    return resp.json()['access_token']


def create_folder(headers, parent_id, name):
    url = f"{BASE}/items/{parent_id}/children"
    resp = requests.post(url, headers={**headers, 'Content-Type': 'application/json'}, json={
        'name': name, 'folder': {}, '@microsoft.graph.conflictBehavior': 'replace'
    })
    if resp.status_code in (200, 201):
        return resp.json()['id']
    # Already exists?
    list_resp = requests.get(url, headers=headers)
    if list_resp.status_code == 200:
        for item in list_resp.json().get('value', []):
            if item['name'] == name and 'folder' in item:
                return item['id']
    print(f"  ERROR creating {name}: {resp.status_code}")
    return None


def upload_file(headers, parent_id, filepath):
    name = os.path.basename(filepath)
    size = os.path.getsize(filepath)

    if size < 4 * 1024 * 1024:
        url = f"{BASE}/items/{parent_id}:/{name}:/content"
        with open(filepath, 'rb') as f:
            resp = requests.put(url, headers={**headers, 'Content-Type': 'application/octet-stream'}, data=f)
        return resp.status_code in (200, 201)
    else:
        url = f"{BASE}/items/{parent_id}:/{name}:/createUploadSession"
        sess = requests.post(url, headers={**headers, 'Content-Type': 'application/json'}, json={
            'item': {'@microsoft.graph.conflictBehavior': 'replace'}
        })
        if sess.status_code not in (200, 201):
            return False
        upload_url = sess.json()['uploadUrl']
        chunk_size = 10 * 1024 * 1024
        with open(filepath, 'rb') as f:
            offset = 0
            while offset < size:
                chunk = f.read(chunk_size)
                end = offset + len(chunk) - 1
                resp = requests.put(upload_url, headers={
                    'Content-Length': str(len(chunk)),
                    'Content-Range': f'bytes {offset}-{end}/{size}'
                }, data=chunk)
                if resp.status_code not in (200, 201, 202):
                    return False
                offset += len(chunk)
        return True


def main():
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}

    # Find root folder
    print("Finding root folder...")
    root_resp = requests.get(f"{BASE}/root/children", headers=headers)
    root_id = None
    for item in root_resp.json().get('value', []):
        if 'החלטות ועדות תכנון' in item['name']:
            root_id = item['id']
            break
    if not root_id:
        root_id = create_folder(headers, 'root', 'החלטות ועדות תכנון')
    print(f"  Root folder ready")

    # Create יקנעם עילית
    yokneam_id = create_folder(headers, root_id, 'יקנעם עילית')
    print(f"  יקנעם עילית folder ready")

    # Scan local files by year and committee
    uploaded = 0
    failed = 0

    for comm_type, local_dir_name in sorted(LOCAL_DIRS.items()):
        comm_name = COMMITTEE_NAMES.get(comm_type, comm_type)
        comm_local = DATA_DIR / local_dir_name

        if not comm_local.exists():
            continue

        for year_dir in sorted(comm_local.iterdir()):
            if not year_dir.is_dir():
                continue
            year = year_dir.name

            pdfs = list(year_dir.glob('*.pdf'))
            if not pdfs:
                continue

            # Create year folder, then committee folder inside
            year_id = create_folder(headers, yokneam_id, year)
            comm_folder_id = create_folder(headers, year_id, comm_name)

            print(f"\n{year} / {comm_name}: {len(pdfs)} files")

            for pdf in sorted(pdfs):
                ok = upload_file(headers, comm_folder_id, str(pdf))
                if ok:
                    uploaded += 1
                    print(f"  OK: {pdf.name}")
                else:
                    failed += 1
                    print(f"  FAILED: {pdf.name}")
                time.sleep(0.2)

    print(f"\n{'='*70}")
    print(f"Done! {uploaded} uploaded, {failed} failed")


if __name__ == "__main__":
    main()
