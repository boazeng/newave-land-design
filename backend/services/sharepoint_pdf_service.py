"""Service to get PDF download URLs from SharePoint."""
import os
import requests
from functools import lru_cache
from dotenv import load_dotenv

ENV_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'env', '.env')
if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)

SITE_ID = 'yaelisrael.sharepoint.com,1e880094-7633-4f48-aee6-88f272bd30ee,e624f0cf-a6b3-4f1c-b2d8-911f75d1c14f'
DRIVE_ID = 'b!lACIHjN2SE-u5ojycr0w7s_wJOazphxPstiRH3XRwU8YVObFPrGeSY2HFvo2E83m'
BASE = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/drives/{DRIVE_ID}"


def _get_token():
    tenant_id = os.getenv('SHAREPOINT_TENANT_ID')
    client_id = os.getenv('SHAREPOINT_CLIENT_ID')
    client_secret = os.getenv('SHAREPOINT_CLIENT_SECRET')
    if not all([tenant_id, client_id, client_secret]):
        return None
    resp = requests.post(
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
        data={
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': 'https://graph.microsoft.com/.default',
        },
        timeout=10,
    )
    data = resp.json()
    return data.get('access_token')


def get_pdf_url(filename, search_folders):
    """Search for a PDF in SharePoint and return its download URL."""
    token = _get_token()
    if not token:
        return None

    headers = {'Authorization': f'Bearer {token}'}
    from urllib.parse import quote

    # Try direct access first (fastest)
    for folder_path in search_folders:
        url = f"{BASE}/root:/{quote(folder_path)}/{quote(filename)}"
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                return resp.json().get('@microsoft.graph.downloadUrl')
        except:
            continue

    # Fallback: search recursively
    for folder_path in search_folders:
        result = _search_recursive(headers, folder_path, filename)
        if result:
            return result

    return None


def _search_recursive(headers, folder_path, filename, depth=0):
    """Recursively search for a file in SharePoint."""
    if depth > 3:
        return None
    from urllib.parse import quote
    encoded = quote(folder_path)
    url = f"{BASE}/root:/{encoded}:/children"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return None
        for item in resp.json().get('value', []):
            if item.get('name') == filename and 'file' in item:
                return item.get('@microsoft.graph.downloadUrl')
            if 'folder' in item:
                result = _search_recursive(
                    headers,
                    f"{folder_path}/{item['name']}",
                    filename,
                    depth + 1,
                )
                if result:
                    return result
    except:
        pass
    return None
