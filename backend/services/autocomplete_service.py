"""
Autocomplete service for cities and streets from local CSV data.
Loads data once into memory for fast lookups.
"""
import csv
import os
from functools import lru_cache

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
CSV_PATH = os.path.join(DATA_DIR, 'streets.csv')


@lru_cache(maxsize=1)
def _load_data():
    """Load streets CSV into memory. Called once."""
    cities = {}  # {city_name: city_code}
    streets = {}  # {city_code: [{street_name, street_code}]}

    if not os.path.exists(CSV_PATH):
        return cities, streets

    with open(CSV_PATH, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            city_name = row['city_name'].strip()
            city_code = row['city_code']
            street_name = row['street_name'].strip()
            street_code = row['street_code']

            if city_name and city_name not in cities:
                cities[city_name] = city_code

            if street_name and city_code:
                if city_code not in streets:
                    streets[city_code] = []
                streets[city_code].append({
                    'name': street_name,
                    'code': street_code,
                })

    return cities, streets


def search_cities(query: str, limit: int = 10) -> list[dict]:
    """Search cities by prefix."""
    cities, _ = _load_data()
    query = query.strip()
    if not query:
        return []

    results = []
    for name, code in cities.items():
        if name.startswith(query) or query in name:
            results.append({'name': name, 'code': code})
            if len(results) >= limit:
                break

    # Sort: starts-with first, then contains
    results.sort(key=lambda x: (0 if x['name'].startswith(query) else 1, x['name']))
    return results[:limit]


def search_streets(city_code: str, query: str, limit: int = 10) -> list[dict]:
    """Search streets within a city by prefix."""
    _, streets = _load_data()
    query = query.strip()

    city_streets = streets.get(city_code, [])
    if not query:
        return city_streets[:limit]

    results = []
    for s in city_streets:
        if s['name'].startswith(query) or query in s['name']:
            results.append(s)
            if len(results) >= limit:
                break

    results.sort(key=lambda x: (0 if x['name'].startswith(query) else 1, x['name']))
    return results[:limit]
