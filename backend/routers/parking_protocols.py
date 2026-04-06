"""API for parking devices found in committee protocols."""
from fastapi import APIRouter
import json
import os

router = APIRouter()

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')


@router.get("/telaviv")
def telaviv_parking_sites(no_location: bool = False):
    """Get Tel Aviv parking sites. Use ?no_location=true for sites without coordinates."""
    path = os.path.join(DATA_DIR, 'parking_protocols_telaviv.json')
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    if no_location:
        return [d for d in data if not d.get('lat') or not d.get('lng')]
    return data
