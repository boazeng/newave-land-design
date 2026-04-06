"""
Search services: parcel search from local data, address search via Nominatim.
"""
import geopandas as gpd
import httpx
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
GPKG_PATH = os.path.join(DATA_DIR, 'cadastre.gpkg')

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def search_by_parcel(gush: int, parcel=None) -> dict:
    """Search for a block/parcel in local GeoPackage data."""
    if not os.path.exists(GPKG_PATH):
        return {"error": "נתוני קדסטר לא נמצאו"}

    # Search in parcels if parcel number given, otherwise in blocks
    if parcel:
        gdf = gpd.read_file(GPKG_PATH, layer='parcels')
        matches = gdf[(gdf['GUSH_NUM'] == gush) & (gdf['PARCEL'] == parcel)]
    else:
        gdf = gpd.read_file(GPKG_PATH, layer='blocks')
        matches = gdf[gdf['GUSH_NUM'] == gush]

    if matches.empty:
        return {"error": "לא נמצא"}

    feature = matches.iloc[0]
    centroid = feature.geometry.centroid
    bounds = feature.geometry.bounds  # (minx, miny, maxx, maxy)

    result = {
        "lat": centroid.y,
        "lng": centroid.x,
        "bounds": [bounds[1], bounds[0], bounds[3], bounds[2]],  # [s, w, n, e]
        "gush": int(feature['GUSH_NUM']),
        "locality": feature.get('LOCALITY_N', ''),
        "area": feature.get('SHAPE_AREA', 0),
    }

    if parcel:
        result["parcel"] = int(feature['PARCEL'])
        result["legal_area"] = feature.get('LEGAL_AREA', 0)

    return result


async def search_by_address(city: str, street: str, house=None) -> dict:
    """Search address using Nominatim (OpenStreetMap geocoder)."""
    query_parts = []
    if house:
        query_parts.append(house)
    query_parts.append(street)
    query_parts.append(city)
    query_parts.append("ישראל")

    query = " ".join(query_parts)

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(NOMINATIM_URL, params={
            "q": query,
            "format": "json",
            "limit": 1,
            "countrycodes": "il",
            "accept-language": "he",
        }, headers={
            "User-Agent": "NewaveLandDesign/1.0",
        })

    if resp.status_code != 200:
        return {"error": "שגיאה בשירות החיפוש"}

    results = resp.json()
    if not results:
        return {"error": "הכתובת לא נמצאה"}

    hit = results[0]
    return {
        "lat": float(hit["lat"]),
        "lng": float(hit["lon"]),
        "display_name": hit.get("display_name", ""),
        "type": "address",
    }
