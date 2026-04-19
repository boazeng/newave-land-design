"""API for parking device search results."""
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import FileResponse
import json
import os
import glob

router = APIRouter()

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
PROTOCOLS_DIR = os.path.join(DATA_DIR, 'protocols')

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
}


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
            for b in buildings:
                key = (b.get('address', ''), b.get('gush', ''), b.get('helka', ''))
                if key not in seen:
                    seen.add(key)
                    b['city'] = config['name']
                    b['city_key'] = city_key
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

        sp_folders = [
            'החלטות ועדות תכנון/תל אביב-יפו/ועדת_משנה',
            'החלטות ועדות תכנון/תל אביב-יפו/ועדת_משנה_לפי_שנה',
            'החלטות ועדות תכנון/תל אביב-יפו/אחר',
            'החלטות ועדות תכנון/תל אביב-יפו',
            'החלטות ועדות תכנון/רמת גן/ועדת_משנה',
            'החלטות ועדות תכנון/רמת גן',
            'החלטות ועדות תכנון/חולון/ועדת_משנה',
            'החלטות ועדות תכנון/חולון',
            'החלטות ועדות תכנון/הרצליה/ועדת_משנה',
            'החלטות ועדות תכנון/הרצליה',
            'החלטות ועדות תכנון/יקנעם עילית',
        ]
        url = get_pdf_url(filename, sp_folders)
        if url:
            return RedirectResponse(url=url)
    except Exception as e:
        print(f"SharePoint PDF error for {filename}: {e}")
        return JSONResponse(status_code=502, content={"error": f"שגיאת SharePoint: {str(e)}"})

    return JSONResponse(status_code=404, content={"error": f"קובץ לא נמצא: {filename}"})
