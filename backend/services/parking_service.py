"""
Parking devices service - local JSON storage + Priority sync.
"""
import json
import os
import httpx
from datetime import datetime
from dotenv import load_dotenv
from services.geocode_service import geocode_batch

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
OUR_DEVICES_FILE = os.path.join(DATA_DIR, 'parking_ours.json')
COMPETITOR_DEVICES_FILE = os.path.join(DATA_DIR, 'parking_competitors.json')

# Load global env for Priority credentials
ENV_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'env', '.env')
if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)


def _read_json(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def _write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# --- Our devices ---

def get_our_devices():
    return _read_json(OUR_DEVICES_FILE)


async def sync_from_priority():
    """Sync parking devices from Priority ERP (SERNUMBERS table)."""
    priority_url = os.getenv('PRIORITY_URL_REAL', '')
    username = os.getenv('PRIORITY_USERNAME', '')
    password = os.getenv('PRIORITY_PASSWORD', '')

    if not priority_url or not username:
        return {"error": "חסרים פרטי התחברות לפריוריטי ב-.env"}

    fields = "PARTNAME,SERNUM,PARTDES,FAMILYDES,CDES,DCODE,DCODEDES,LOCATION,GPSY,GPSX,STATUSNAME"
    url = f"{priority_url}SERNUMBERS?$select={fields}"

    try:
        async with httpx.AsyncClient(verify=False, timeout=60) as client:
            resp = await client.get(url, auth=(username, password))

            if resp.status_code == 401:
                return {"error": "שגיאת אימות - בדוק שם משתמש וסיסמה"}

            if resp.status_code != 200:
                return {"error": f"שגיאה מפריוריטי: {resp.status_code}"}

            data = resp.json()
            records = data.get('value', [])

        # Resolve address: DCODEDES > LOCATION > CDES > PARTDES
        def resolve_address(r):
            dcodedes = (r.get("DCODEDES") or "").strip()
            if dcodedes:
                return dcodedes
            loc = (r.get("LOCATION") or "").strip()
            if loc:
                return loc
            cdes = (r.get("CDES") or "").strip()
            if cdes:
                return cdes
            name = (r.get("PARTDES") or "").strip()
            if " - " in name:
                parts = name.split(" - ")
                if len(parts) >= 3:
                    return " - ".join(parts[2:])
            return ""

        # Group by address - one row per location
        grouped = {}
        no_address = []
        for r in records:
            address = resolve_address(r)
            raw_dcode = r.get("DCODE")
            dcode = str(raw_dcode).strip() if raw_dcode and str(raw_dcode).strip() != "None" else ""
            family_des = r.get("FAMILYDES", "") or ""
            part_des = r.get("PARTDES", "") or ""

            if not address:
                no_address.append(r)
                continue

            if address not in grouped:
                grouped[address] = {
                    "site_code": dcode,
                    "site_name": address,
                    "families": [],
                    "products": [],
                    "count": 0,
                    "lat": r.get("GPSY"),
                    "lng": r.get("GPSX"),
                    "synced_at": datetime.now().isoformat(),
                }

            # Use first non-empty site code
            if dcode and not grouped[address]["site_code"]:
                grouped[address]["site_code"] = dcode

            grouped[address]["count"] += 1
            if family_des and family_des not in grouped[address]["families"]:
                grouped[address]["families"].append(family_des)
            if part_des and part_des not in grouped[address]["products"]:
                grouped[address]["products"].append(part_des)

        # Only keep sites with a site_code, deduplicate by site_code
        seen_codes = set()
        sites = []
        for g in grouped.values():
            code = g["site_code"]
            if not code or code in seen_codes:
                continue
            seen_codes.add(code)

            sites.append({
                "site_code": code,
                "site_name": g["site_name"],
                "family": " | ".join(g["families"]),
                "product": " | ".join(g["products"]),
                "count": g["count"],
                "lat": g["lat"],
                "lng": g["lng"],
                "synced_at": g["synced_at"],
            })

        # Geocode sites that don't have coordinates
        addresses_to_geocode = [
            s["site_name"] for s in sites
            if not s.get("lat") or not s.get("lng")
        ]
        if addresses_to_geocode:
            geo_results = await geocode_batch(addresses_to_geocode)
            for s in sites:
                if not s.get("lat") or not s.get("lng"):
                    coords = geo_results.get(s["site_name"])
                    if coords:
                        s["lat"] = coords["lat"]
                        s["lng"] = coords["lng"]

        _write_json(OUR_DEVICES_FILE, sites)
        return {"synced": len(sites)}

    except httpx.ConnectError:
        return {"error": "לא ניתן להתחבר לפריוריטי - בדוק את הכתובת"}
    except Exception as e:
        return {"error": f"שגיאה: {str(e)}"}


# --- Competitor devices ---

def get_competitor_devices():
    return _read_json(COMPETITOR_DEVICES_FILE)


def add_competitor_device(device: dict):
    devices = _read_json(COMPETITOR_DEVICES_FILE)
    device["id"] = max([d.get("id", 0) for d in devices], default=0) + 1
    device["created_at"] = datetime.now().isoformat()
    devices.append(device)
    _write_json(COMPETITOR_DEVICES_FILE, devices)
    return device


def delete_competitor_device(device_id: int):
    devices = _read_json(COMPETITOR_DEVICES_FILE)
    devices = [d for d in devices if d.get("id") != device_id]
    _write_json(COMPETITOR_DEVICES_FILE, devices)
    return {"deleted": device_id}
