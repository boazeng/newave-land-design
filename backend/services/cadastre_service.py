"""
Service for reading cadastre data from GeoPackage with bbox filtering.
Uses geopandas with spatial index for fast queries.
"""
import geopandas as gpd
import os
import json

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
GPKG_PATH = os.path.join(DATA_DIR, 'cadastre.gpkg')

# Max features to return per request
MAX_BLOCKS = 5000
MAX_PARCELS = 3000


def get_features(layer: str, bbox: list[float], limit: int | None = None) -> dict:
    """
    Get features from GeoPackage filtered by bounding box.
    bbox: [min_lng, min_lat, max_lng, max_lat] in WGS84
    Returns GeoJSON FeatureCollection.
    """
    if not os.path.exists(GPKG_PATH):
        return {"type": "FeatureCollection", "features": []}

    max_features = MAX_BLOCKS if layer == 'blocks' else MAX_PARCELS
    if limit:
        max_features = min(limit, max_features)

    # Read with bbox filter (uses spatial index in GeoPackage)
    gdf = gpd.read_file(
        GPKG_PATH,
        layer=layer,
        bbox=tuple(bbox),
        rows=max_features,
    )

    if gdf.empty:
        return {"type": "FeatureCollection", "features": []}

    # Simplify geometry for faster transfer
    # At zoom levels where we show many features, we don't need full precision
    if len(gdf) > 500:
        gdf['geometry'] = gdf['geometry'].simplify(0.0001, preserve_topology=True)

    # Convert to GeoJSON
    geojson = json.loads(gdf.to_json())
    geojson['totalFeatures'] = len(gdf)
    geojson['truncated'] = len(gdf) >= max_features

    return geojson
