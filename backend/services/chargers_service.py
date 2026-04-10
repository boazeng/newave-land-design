"""
Chargers service - sync from Priority, grouped by site (DCODE).
Only shows devices that have a site code.
"""
import json
import os
import httpx
from datetime import datetime
from dotenv import load_dotenv
from services.geocode_service import geocode_batch

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
CHARGERS_FILE = os.path.join(DATA_DIR, 'chargers.json')

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


def get_charger_sites():
    return _read_json(CHARGERS_FILE)


async def sync_chargers():
    """Sync chargers from Priority, grouped by site (DCODE)."""
    priority_url = os.getenv('PRIORITY_URL_REAL', '')
    username = os.getenv('PRIORITY_USERNAME', '')
    password = os.getenv('PRIORITY_PASSWORD', '')

    if not priority_url or not username:
        return {"error": "חסרים פרטי התחברות לפריוריטי ב-.env"}

    fields = "PARTNAME,SERNUM,PARTDES,FAMILYDES,DCODE,DCODEDES,LOCATION,GPSY,GPSX,STATUSNAME,CDES"
    url = f"{priority_url}SERNUMBERS?$select={fields}&$filter=FAMILYDES eq 'מטעני AC'"

    try:
        async with httpx.AsyncClient(verify=False, timeout=60) as client:
            resp = await client.get(url, auth=(username, password))

            if resp.status_code == 401:
                return {"error": "שגיאת אימות"}
            if resp.status_code != 200:
                return {"error": f"שגיאה מפריוריטי: {resp.status_code}"}

            data = resp.json()
            records = data.get('value', [])

        # Resolve address: DCODEDES > LOCATION > CDES > PARTDES
        def resolve_address(r):
            for field in ['DCODEDES', 'LOCATION', 'CDES']:
                val = r.get(field)
                if val and str(val).strip() not in ('', 'None'):
                    return str(val).strip()
            name = (r.get("PARTDES") or "").strip()
            if " - " in name:
                parts = name.split(" - ")
                if len(parts) >= 3:
                    return " - ".join(parts[2:])
            return ""

        # Group by site code (DCODE) - only sites with DCODE
        grouped = {}
        for r in records:
            raw_dcode = r.get("DCODE")
            dcode = str(raw_dcode).strip() if raw_dcode and str(raw_dcode).strip() != "None" else ""
            if not dcode:
                continue

            address = resolve_address(r)
            family_des = r.get("FAMILYDES", "") or ""
            part_des = r.get("PARTDES", "") or ""

            if dcode not in grouped:
                grouped[dcode] = {
                    "site_code": dcode,
                    "site_name": address,
                    "families": [],
                    "products": [],
                    "count": 0,
                    "lat": r.get("GPSY"),
                    "lng": r.get("GPSX"),
                    "synced_at": datetime.now().isoformat(),
                }

            grouped[dcode]["count"] += 1
            if family_des and family_des not in grouped[dcode]["families"]:
                grouped[dcode]["families"].append(family_des)
            if part_des and part_des not in grouped[dcode]["products"]:
                grouped[dcode]["products"].append(part_des)

        sites = []
        for g in grouped.values():
            sites.append({
                "site_code": g["site_code"],
                "site_name": g["site_name"],
                "family": " | ".join(g["families"]),
                "product": " | ".join(g["products"]),
                "count": g["count"],
                "lat": g["lat"],
                "lng": g["lng"],
                "synced_at": g["synced_at"],
            })

        # Geocode sites without coordinates
        to_geocode = [s["site_name"] for s in sites if not s.get("lat") or not s.get("lng")]
        if to_geocode:
            geo = await geocode_batch(to_geocode)
            for s in sites:
                if not s.get("lat") or not s.get("lng"):
                    coords = geo.get(s["site_name"])
                    if coords:
                        s["lat"] = coords["lat"]
                        s["lng"] = coords["lng"]

        _write_json(CHARGERS_FILE, sites)
        return {"synced": len(sites)}

    except httpx.ConnectError:
        return {"error": "לא ניתן להתחבר לפריוריטי"}
    except Exception as e:
        return {"error": f"שגיאה: {str(e)}"}
