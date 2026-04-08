"""API for public EV charging stations from data.gov.il."""
from fastapi import APIRouter
import json
import os

router = APIRouter()

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')


@router.get("")
def get_charging_stations():
    """Get all public EV charging stations with coordinates."""
    path = os.path.join(DATA_DIR, 'charging_stations_map.json')
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        return json.load(f)


@router.get("/stats")
def get_stats():
    """Get statistics about charging stations."""
    path = os.path.join(DATA_DIR, 'charging_stations_map.json')
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as f:
        data = json.load(f)

    by_operator = {}
    total_fast = 0
    total_slow = 0
    with_coords = 0
    for s in data:
        op = s.get('operator', '')
        by_operator[op] = by_operator.get(op, 0) + 1
        total_fast += s.get('fast_chargers', 0) or 0
        total_slow += s.get('slow_chargers', 0) or 0
        if s.get('lat'):
            with_coords += 1

    return {
        'total_stations': len(data),
        'with_coordinates': with_coords,
        'total_fast_chargers': total_fast,
        'total_slow_chargers': total_slow,
        'by_operator': dict(sorted(by_operator.items(), key=lambda x: -x[1])),
    }
