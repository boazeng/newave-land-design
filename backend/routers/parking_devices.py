"""API for parking device search results."""
from fastapi import APIRouter
from fastapi.responses import FileResponse
import json
import os

router = APIRouter()

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
PROTOCOLS_DIR = os.path.join(DATA_DIR, 'protocols')


def _load_results():
    """Load all parking device search result files and merge."""
    all_buildings = []
    seen = set()

    result_files = [
        'parking_results_vaada_mishne.json',
        'parking_results_vaada_old.json',
        'parking_results_vaada_rishui.json',
    ]

    for filename in result_files:
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            continue
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        for b in data.get('buildings', []):
            # Deduplicate by address+gush+helka
            key = (b.get('address', ''), b.get('gush', ''), b.get('helka', ''))
            if key not in seen:
                seen.add(key)
                all_buildings.append(b)

    return all_buildings


@router.get("/results")
def get_parking_devices():
    """Get all buildings with parking devices."""
    return _load_results()


@router.get("/stats")
def get_parking_stats():
    """Get statistics about parking device search."""
    buildings = _load_results()

    by_type = {}
    for b in buildings:
        dt = b.get('device_type') or 'לא ידוע'
        by_type[dt] = by_type.get(dt, 0) + 1

    by_year = {}
    for b in buildings:
        date = b.get('date') or ''
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
def serve_protocol_pdf(filename: str):
    """Serve a protocol PDF file."""
    # Search in all protocol directories
    search_dirs = [
        os.path.join(PROTOCOLS_DIR, 'תל_אביב_יפו', 'ועדת_משנה'),
        os.path.join(PROTOCOLS_DIR, 'תל_אביב_יפו_ועדת_משנה'),
        os.path.join(PROTOCOLS_DIR, 'תל_אביב_יפו_ועדת_משנה_רישוי'),
    ]

    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue
        for root, dirs, files in os.walk(search_dir):
            if filename in files:
                return FileResponse(
                    os.path.join(root, filename),
                    media_type='application/pdf',
                    filename=filename,
                )

    return {"error": "קובץ לא נמצא"}
