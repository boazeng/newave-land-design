"""Download protocol PDFs from SharePoint for parking device search."""
import sys, os, requests, time
sys.stdout.reconfigure(encoding='utf-8')
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1, encoding='utf-8')
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'env', '.env'))

tenant_id = os.getenv('SHAREPOINT_TENANT_ID')
client_id = os.getenv('SHAREPOINT_CLIENT_ID')
client_secret = os.getenv('SHAREPOINT_CLIENT_SECRET')

SITE_ID = 'yaelisrael.sharepoint.com,1e880094-7633-4f48-aee6-88f272bd30ee,e624f0cf-a6b3-4f1c-b2d8-911f75d1c14f'
DRIVE_ID = 'b!lACIHjN2SE-u5ojycr0w7s_wJOazphxPstiRH3XRwU8YVObFPrGeSY2HFvo2E83m'
BASE = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/drives/{DRIVE_ID}"


def get_token():
    resp = requests.post(f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token", data={
        'grant_type': 'client_credentials', 'client_id': client_id,
        'client_secret': client_secret, 'scope': 'https://graph.microsoft.com/.default',
    })
    return resp.json()['access_token']


def download_folder(headers, folder_id, local_dir, depth=0):
    """Recursively download all PDFs from a SharePoint folder."""
    os.makedirs(local_dir, exist_ok=True)
    url = f"{BASE}/items/{folder_id}/children"
    total = 0

    while url:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            break
        data = resp.json()

        for item in data.get('value', []):
            if 'folder' in item:
                sub_total = download_folder(headers, item['id'], os.path.join(local_dir, item['name']), depth + 1)
                total += sub_total
            elif 'file' in item and item['name'].lower().endswith('.pdf'):
                filepath = os.path.join(local_dir, item['name'])
                if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
                    total += 1
                    continue
                # Download
                dl_url = item.get('@microsoft.graph.downloadUrl') or f"{BASE}/items/{item['id']}/content"
                try:
                    dl = requests.get(dl_url, timeout=60)
                    with open(filepath, 'wb') as f:
                        f.write(dl.content)
                    total += 1
                except:
                    pass
                time.sleep(0.1)

        url = data.get('@odata.nextLink')

    if depth <= 1:
        print(f"  {'  ' * depth}{os.path.basename(local_dir)}: {total} PDFs")
    return total


def main():
    city = sys.argv[1] if len(sys.argv) > 1 else 'רמת גן'
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    if not output_dir:
        safe_name = city.replace(' ', '_')
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'protocols_search', safe_name)

    print(f"Downloading '{city}' from SharePoint to {output_dir}")

    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}

    # Find root → החלטות ועדות תכנון → city
    root_resp = requests.get(f"{BASE}/root/children", headers=headers)
    root_id = None
    for item in root_resp.json().get('value', []):
        if 'החלטות ועדות תכנון' in item['name']:
            root_id = item['id']
            break

    if not root_id:
        print("ERROR: Root folder not found")
        return

    city_resp = requests.get(f"{BASE}/items/{root_id}/children", headers=headers)
    city_id = None
    for item in city_resp.json().get('value', []):
        if city in item['name']:
            city_id = item['id']
            print(f"Found folder: {item['name']}")
            break

    if not city_id:
        print(f"ERROR: City '{city}' not found in SharePoint")
        print("Available:")
        for item in city_resp.json().get('value', []):
            print(f"  {item['name']}")
        return

    total = download_folder(headers, city_id, output_dir)
    print(f"\nDone: {total} PDFs downloaded to {output_dir}")


if __name__ == '__main__':
    main()
