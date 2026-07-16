"""API for parking device search results."""
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import json
import os
import glob
from functools import lru_cache

router = APIRouter()

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
PROTOCOLS_DIR = os.path.join(DATA_DIR, 'protocols')

# SharePoint layout: 'החלטות ועדות תכנון/<city>/<committee>'. Protocols live in one of
# these committee subfolders; a city root is searched too, for cities filed flat.
SP_ROOT = 'החלטות ועדות תכנון'
SP_SUBFOLDERS = [
    'ועדת_משנה', 'ועדת_משנה_לפי_שנה', 'רשות_רישוי_מקומית',
    'מליאת_הועדה', 'ועדת_שימור', 'אחר',
]
# On SharePoint but not a parking-devices city, so absent from CITY_CONFIG
SP_EXTRA_CITIES = ['יקנעם עילית']

# City config: maps city key to display name and result files
CITY_CONFIG = {
    'tel_aviv': {
        'name': 'תל אביב-יפו',
        'result_files': ['parking_protocols_telaviv.json'],
        'protocol_dirs': ['תל_אביב_יפו/ועדת_משנה', 'תל_אביב_יפו_ועדת_משנה', 'תל_אביב_יפו_ועדת_משנה_רישוי'],
    },
    'ramat_gan': {
        'name': 'רמת גן',
        'result_files': ['parking_protocols_ramatgan.json'],
        'protocol_dirs': ['protocols_search/רמת_גן'],
    },
    'holon': {
        'name': 'חולון',
        'result_files': ['parking_results_holon.json'],
        'protocol_dirs': ['protocols_search/חולון'],
    },
    'herzliya': {
        'name': 'הרצליה',
        'result_files': ['parking_results_herzliya.json'],
        'protocol_dirs': ['protocols_search/הרצליה'],
    },
    'givatayim': {
        'name': 'גבעתיים',
        'result_files': ['parking_protocols_givatayim.json'],
        'protocol_dirs': ['protocols_search/גבעתיים'],
    },
    'bat_yam': {
        'name': 'בת ים',
        'result_files': ['parking_protocols_batya.json'],
        'protocol_dirs': ['protocols_search/בת_ים'],
    },
    'rishon': {
        'name': 'ראשון לציון',
        'result_files': ['parking_protocols_rishon.json'],
        'protocol_dirs': ['protocols_search/ראשון_לציון'],
    },
    'netanya': {
        'name': 'נתניה',
        'result_files': ['parking_protocols_netanya.json'],
        'protocol_dirs': ['protocols_search/נתניה'],
    },
    'haifa': {
        'name': 'חיפה',
        'result_files': ['parking_protocols_haifa.json'],
        'protocol_dirs': ['protocols_search/חיפה'],
    },
    'jerusalem': {
        'name': 'ירושלים',
        'result_files': ['parking_protocols_jerusalem.json'],
        'protocol_dirs': ['protocols_search/ירושלים'],
    },
}


@lru_cache(maxsize=1)
def _protocol_city_index():
    """Map each referenced protocol filename to the city it came from."""
    index = {}
    for city_key, config in CITY_CONFIG.items():
        for filename in config['result_files']:
            path = os.path.join(DATA_DIR, filename)
            if not os.path.exists(path):
                continue
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            buildings = data if isinstance(data, list) else data.get('buildings', [])
            for b in buildings:
                for src in (b.get('source_files') or []):
                    index[src] = city_key
    return index


def protocol_city(filename):
    """City key owning a protocol file, or None if nothing references it."""
    return _protocol_city_index().get(filename)


def sharepoint_folders(city_key=None):
    """SharePoint folders that may hold a protocol PDF.

    Derived from CITY_CONFIG so adding a city needs no second edit here. Narrowed to
    the owning city when known - searching every city costs a request per folder.
    """
    keys = [city_key] if city_key in CITY_CONFIG else list(CITY_CONFIG)
    folders = []
    for key in keys:
        city = f"{SP_ROOT}/{CITY_CONFIG[key]['name']}"
        folders.extend(f'{city}/{sub}' for sub in SP_SUBFOLDERS)
        folders.append(city)
    if city_key not in CITY_CONFIG:
        folders.extend(f'{SP_ROOT}/{c}' for c in SP_EXTRA_CITIES)
    return folders


def _load_results(city=None):
    """Load parking device results, optionally filtered by city."""
    all_buildings = []
    seen = set()

    configs = {city: CITY_CONFIG[city]} if (city and city in CITY_CONFIG) else CITY_CONFIG

    for city_key, config in configs.items():
        for filename in config['result_files']:
            path = os.path.join(DATA_DIR, filename)
            if not os.path.exists(path):
                continue
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            # Support both list format and dict with 'buildings' key
            buildings = data if isinstance(data, list) else data.get('buildings', [])
            for idx, b in enumerate(buildings):
                key = (b.get('address', ''), b.get('gush', ''), b.get('helka', ''))
                if key not in seen:
                    seen.add(key)
                    b['city'] = config['name']
                    b['city_key'] = city_key
                    b['_file'] = filename   # source file (for editing)
                    b['_row'] = idx         # index within source file (stable id)
                    all_buildings.append(b)

    return all_buildings


@router.get("/cities")
def get_cities():
    """Return available cities with building counts."""
    cities = []
    for key, config in CITY_CONFIG.items():
        count = len(_load_results(key))
        cities.append({
            'key': key,
            'name': config['name'],
            'count': count,
        })
    return cities


@router.get("/results")
def get_parking_devices(city: str = None):
    """Get all buildings with parking devices, optionally filtered by city."""
    return _load_results(city)


class BuildingUpdate(BaseModel):
    city_key: str
    file: str
    row: int
    # Optional[...] rather than `str | None`: the server runs Python 3.9
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


@router.post("/update")
async def update_building(payload: BuildingUpdate):
    """Edit a building's address (and re-geocode), or set coords manually.

    Identified by source file + row index so it works for every file format.
    Used to fix buildings that failed geocoding so they appear on the map.
    """
    from services.geocode_service import geocode_address

    config = CITY_CONFIG.get(payload.city_key)
    if not config or payload.file not in config['result_files']:
        return JSONResponse(status_code=400, content={"error": "עיר או קובץ לא תקין"})

    path = os.path.join(DATA_DIR, payload.file)
    if not os.path.exists(path):
        return JSONResponse(status_code=404, content={"error": "קובץ לא נמצא"})

    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    buildings = data if isinstance(data, list) else data.get('buildings', [])

    if payload.row < 0 or payload.row >= len(buildings):
        return JSONResponse(status_code=400, content={"error": "שורה לא תקינה"})

    b = buildings[payload.row]
    if payload.address is not None:
        b['address'] = payload.address.strip()

    geocoded = False
    if payload.lat is not None and payload.lng is not None:
        # manual coordinates
        b['lat'] = payload.lat
        b['lng'] = payload.lng
        geocoded = True
    elif b.get('address'):
        coords = await geocode_address(b['address'])
        if coords:
            b['lat'] = coords['lat']
            b['lng'] = coords['lng']
            geocoded = True
        # if geocoding fails, keep any existing coords (don't lose the pin)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {"status": "ok", "geocoded": geocoded, "building": b}


@router.post("/geocode")
async def geocode_parking_devices(background_tasks: BackgroundTasks):
    """Trigger background geocoding of all parking device addresses."""
    from services.geocode_service import geocode_batch

    async def _run():
        buildings = _load_results()
        missing_addresses = list({
            b['address'] for b in buildings
            if b.get('address') and not b.get('lat')
        })
        if not missing_addresses:
            return
        geo = await geocode_batch(missing_addresses)

        # Write coords back into each result file
        for city_key, config in CITY_CONFIG.items():
            for filename in config['result_files']:
                path = os.path.join(DATA_DIR, filename)
                if not os.path.exists(path):
                    continue
                with open(path, encoding='utf-8') as f:
                    data = json.load(f)
                changed = False
                for b in data.get('buildings', []):
                    if b.get('address') and not b.get('lat'):
                        coords = geo.get(b['address'])
                        if coords:
                            b['lat'] = coords['lat']
                            b['lng'] = coords['lng']
                            changed = True
                if changed:
                    with open(path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

    background_tasks.add_task(_run)
    return {"status": "geocoding started in background"}


@router.get("/stats")
def get_parking_stats(city: str = None):
    """Get statistics about parking device search."""
    buildings = _load_results(city)

    by_type = {}
    for b in buildings:
        dt = b.get('device_types') or b.get('device_type') or 'לא ידוע'
        by_type[dt] = by_type.get(dt, 0) + 1

    by_year = {}
    for b in buildings:
        date = b.get('dates') or b.get('date') or ''
        if '/' in date:
            parts = date.split('/')
            year = parts[-1] if len(parts) >= 3 else ''
            if len(year) == 4:
                by_year[year] = by_year.get(year, 0) + 1

    return {
        'total_buildings': len(buildings),
        'by_device_type': by_type,
        'by_year': dict(sorted(by_year.items())),
    }


@router.get("/pdf/{filename:path}")
async def serve_protocol_pdf(filename: str):
    """Serve a protocol PDF inline for viewing (not downloading)."""
    import httpx
    from fastapi.responses import Response, JSONResponse

    # First try local files
    for config in CITY_CONFIG.values():
        for proto_dir in config['protocol_dirs']:
            search_dir = os.path.join(PROTOCOLS_DIR, proto_dir)
            if not os.path.exists(search_dir):
                continue
            for root, dirs, files in os.walk(search_dir):
                if filename in files:
                    return FileResponse(
                        os.path.join(root, filename),
                        media_type='application/pdf',
                        headers={'Content-Disposition': f'inline; filename="{filename}"'},
                    )

    # Fallback: redirect to SharePoint URL
    try:
        from services.sharepoint_pdf_service import get_pdf_url
        from fastapi.responses import RedirectResponse

        url = get_pdf_url(filename, sharepoint_folders(protocol_city(filename)))
        if url:
            return RedirectResponse(url=url)
    except Exception as e:
        print(f"SharePoint PDF error for {filename}: {e}")
        return JSONResponse(status_code=502, content={"error": f"שגיאת SharePoint: {str(e)}"})

    return JSONResponse(status_code=404, content={"error": f"קובץ לא נמצא: {filename}"})
