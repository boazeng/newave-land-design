from fastapi import APIRouter
import json
import os

router = APIRouter()

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')


def _load(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        return json.load(f)


@router.get("/local")
def local_committees():
    """Get all local planning committees."""
    return _load('committees_local.json')


@router.get("/district")
def district_committees():
    """Get all district planning committees."""
    return _load('committees_district.json')


@router.get("/districts-geojson")
def districts_geojson():
    """Get district boundaries as GeoJSON."""
    return _load('districts.geojson')
