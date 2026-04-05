"""API for parking devices found in committee protocols."""
from fastapi import APIRouter
import json
import os

router = APIRouter()

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')


@router.get("/telaviv")
def telaviv_parking_sites():
    """Get Tel Aviv parking sites from committee protocols (with coordinates)."""
    path = os.path.join(DATA_DIR, 'parking_protocols_telaviv.json')
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        return json.load(f)
