"""
Geocode addresses to lat/lng using Nominatim (OpenStreetMap).
Includes caching to avoid repeated API calls.
"""
import json
import os
import httpx
import asyncio

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
CACHE_FILE = os.path.join(DATA_DIR, 'geocode_cache.json')

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def _load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {}


def _save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


async def geocode_address(address: str) -> dict | None:
    """Geocode a single address. Returns {lat, lng} or None."""
    if not address or address == "(ללא כתובת)":
        return None

    # Check cache first
    cache = _load_cache()
    if address in cache:
        return cache[address]

    # Clean address for search - add Israel
    query = address + " ישראל"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(NOMINATIM_URL, params={
                "q": query,
                "format": "json",
                "limit": 1,
                "countrycodes": "il",
            }, headers={
                "User-Agent": "NewaveLandDesign/1.0",
            })

        if resp.status_code == 200:
            results = resp.json()
            if results:
                result = {
                    "lat": float(results[0]["lat"]),
                    "lng": float(results[0]["lon"]),
                }
                # Save to cache
                cache[address] = result
                _save_cache(cache)
                return result

    except Exception:
        pass

    # Cache miss (not found)
    cache[address] = None
    _save_cache(cache)
    return None


async def geocode_batch(addresses: list[str]) -> dict:
    """
    Geocode a list of addresses. Returns {address: {lat, lng}}.
    Respects Nominatim rate limit (1 req/sec).
    """
    cache = _load_cache()
    results = {}
    to_fetch = []

    # Check cache
    for addr in addresses:
        if addr in cache:
            results[addr] = cache[addr]
        else:
            to_fetch.append(addr)

    # Fetch missing
    for addr in to_fetch:
        result = await geocode_address(addr)
        results[addr] = result
        # Nominatim rate limit: 1 request per second
        await asyncio.sleep(1.1)

    return results
