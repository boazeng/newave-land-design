"""API for parking devices found in committee protocols."""
from fastapi import APIRouter
import json
import os

router = APIRouter()

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')


def _load_sites(filename, no_location=False):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    if no_location:
        return [d for d in data if not d.get('lat') or not d.get('lng')]
    return data


@router.get("/telaviv")
def telaviv_parking_sites(no_location: bool = False):
    """Get Tel Aviv parking sites."""
    return _load_sites('parking_protocols_telaviv.json', no_location)


@router.get("/ramatgan")
def ramatgan_parking_sites(no_location: bool = False):
    """Get Ramat Gan parking sites."""
    return _load_sites('parking_protocols_ramatgan.json', no_location)
