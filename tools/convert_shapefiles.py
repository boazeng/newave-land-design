"""
Convert cadastre shapefiles to GeoPackage with WGS84 projection.
Creates spatial index for fast bbox queries.
"""
import geopandas as gpd
import sys
import os
import time

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


def fix_encoding(gdf):
    """Fix Hebrew encoding from CP1255 to UTF-8."""
    str_cols = gdf.select_dtypes(include='object').columns
    for col in str_cols:
        gdf[col] = gdf[col].apply(
            lambda x: x.encode('latin1').decode('cp1255') if isinstance(x, str) else x
        )
    return gdf


def convert_shapefile(shp_path, gpkg_path, layer_name):
    """Convert a shapefile to GeoPackage with WGS84 projection."""
    print(f'Reading {shp_path}...')
    start = time.time()

    gdf = gpd.read_file(shp_path)
    print(f'  Records: {len(gdf)}')
    print(f'  Original CRS: {gdf.crs}')

    # Fix Hebrew encoding
    print('  Fixing Hebrew encoding...')
    gdf = fix_encoding(gdf)

    # Reproject to WGS84
    print('  Reprojecting to WGS84 (EPSG:4326)...')
    gdf = gdf.to_crs(epsg=4326)

    # Save to GeoPackage
    print(f'  Saving to {gpkg_path} (layer: {layer_name})...')
    gdf.to_file(gpkg_path, layer=layer_name, driver='GPKG')

    elapsed = time.time() - start
    print(f'  Done in {elapsed:.1f}s')
    return len(gdf)


def main():
    sys.stdout.reconfigure(encoding='utf-8')

    gpkg_path = os.path.join(DATA_DIR, 'cadastre.gpkg')

    # Remove old file
    if os.path.exists(gpkg_path):
        os.remove(gpkg_path)

    # Convert blocks
    blocks_shp = os.path.join(DATA_DIR, 'blocks', 'gushim.shp')
    if os.path.exists(blocks_shp):
        convert_shapefile(blocks_shp, gpkg_path, 'blocks')
    else:
        print(f'WARNING: {blocks_shp} not found')

    # Convert parcels
    parcels_shp = os.path.join(DATA_DIR, 'parcels', 'helkot.shp')
    if os.path.exists(parcels_shp):
        convert_shapefile(parcels_shp, gpkg_path, 'parcels')
    else:
        print(f'WARNING: {parcels_shp} not found')

    print(f'\nOutput: {gpkg_path}')
    print(f'Size: {os.path.getsize(gpkg_path) / 1024 / 1024:.1f} MB')


if __name__ == '__main__':
    main()
