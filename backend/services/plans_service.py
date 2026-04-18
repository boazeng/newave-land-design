"""
Service for managing planning committee plans (תוכניות תכנון).
Loads plans from JSON database, supports filtering by various criteria.
"""
import json
import os

try:
    import geopandas as gpd
    HAS_GEO = True
except ImportError:
    HAS_GEO = False

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
GPKG_PATH = os.path.join(DATA_DIR, 'cadastre.gpkg')


def _load_db(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return {'metadata': {}, 'plans': []}
    with open(path, encoding='utf-8') as f:
        return json.load(f)


# Cache loaded databases
_cache = {}


def get_plans_db(db_name='plans_tanai_saf'):
    """Load a plans database by name."""
    filename = f'{db_name}.json'
    if filename not in _cache:
        _cache[filename] = _load_db(filename)
    return _cache[filename]


def invalidate_cache():
    """Clear the cache to reload data."""
    _cache.clear()


def list_databases():
    """List all available plan databases."""
    dbs = []
    for f in os.listdir(DATA_DIR):
        if f.startswith('plans_') and f.endswith('.json'):
            name = f.replace('.json', '')
            db = get_plans_db(name)
            dbs.append({
                'name': name,
                'title': db.get('metadata', {}).get('search_criteria', name),
                'total_plans': db.get('metadata', {}).get('total_plans', 0),
                'plans_with_pdf': db.get('metadata', {}).get('plans_with_pdf', 0),
                'created_at': db.get('metadata', {}).get('created_at', ''),
            })
    return dbs


def search_plans(db_name='plans_tanai_saf', query=None, authority=None,
                 has_pdf=None, min_area=None, max_area=None,
                 gush=None, settlement=None, limit=100, offset=0):
    """Search plans with filters."""
    db = get_plans_db(db_name)
    plans = db.get('plans', [])

    # Apply filters
    if query:
        q = query.lower()
        plans = [p for p in plans if q in p.get('plan_number', '').lower()
                 or q in p.get('plan_name', '').lower()
                 or q in p.get('location', '').lower()]

    if authority:
        plans = [p for p in plans if p.get('authority', '') == authority]

    if has_pdf is not None:
        plans = [p for p in plans if p.get('has_downloaded_files', False) == has_pdf]

    if min_area is not None:
        plans = [p for p in plans if p.get('area_dunam') and p['area_dunam'] >= min_area]

    if max_area is not None:
        plans = [p for p in plans if p.get('area_dunam') and p['area_dunam'] <= max_area]

    if gush is not None:
        plans = [p for p in plans if any(g.get('gush') == gush for g in p.get('gushim', []))]

    if settlement:
        s = settlement.lower()
        plans = [p for p in plans if any(s in sett.lower() for sett in p.get('settlements', []))]

    total = len(plans)
    plans = plans[offset:offset + limit]

    return {
        'total': total,
        'offset': offset,
        'limit': limit,
        'plans': plans,
    }


def get_plan(db_name, plan_number):
    """Get a single plan by number."""
    db = get_plans_db(db_name)
    for p in db.get('plans', []):
        if p.get('plan_number') == plan_number:
            return p
    return None


def get_plans_by_gush(db_name, gush_num):
    """Get all plans that include a specific gush."""
    db = get_plans_db(db_name)
    return [p for p in db.get('plans', [])
            if any(g.get('gush') == gush_num for g in p.get('gushim', []))]


def get_plans_geojson(db_name='plans_tanai_saf', bbox=None):
    """
    Get plans as GeoJSON with geometries from cadastre blocks.
    Matches plan gush numbers to block geometries.
    """
    if not HAS_GEO or not os.path.exists(GPKG_PATH):
        return {"type": "FeatureCollection", "features": []}

    db = get_plans_db(db_name)
    plans = db.get('plans', [])

    # Only plans with gush data
    plans_with_gush = [p for p in plans if p.get('gushim')]
    if not plans_with_gush:
        return {"type": "FeatureCollection", "features": []}

    # Collect all unique gush numbers
    all_gush_nums = set()
    for p in plans_with_gush:
        for g in p['gushim']:
            all_gush_nums.add(g['gush'])

    if not all_gush_nums:
        return {"type": "FeatureCollection", "features": []}

    # Read blocks from GeoPackage
    kwargs = {}
    if bbox:
        kwargs['bbox'] = tuple(bbox)

    blocks_gdf = gpd.read_file(GPKG_PATH, layer='blocks', **kwargs)

    if blocks_gdf.empty:
        return {"type": "FeatureCollection", "features": []}

    # Filter to only blocks that match our plans
    matched = blocks_gdf[blocks_gdf['GUSH_NUM'].isin(all_gush_nums)]

    if matched.empty:
        return {"type": "FeatureCollection", "features": []}

    # Load review statuses
    all_statuses = _load_statuses()

    # Build plan-to-gush lookup
    gush_to_plans = {}
    for p in plans_with_gush:
        pnum = p['plan_number']
        st = all_statuses.get(pnum, {})
        for g in p['gushim']:
            gn = g['gush']
            if gn not in gush_to_plans:
                gush_to_plans[gn] = []
            gush_to_plans[gn].append({
                'plan_number': pnum,
                'plan_name': p['plan_name'],
                'authority': p['authority'],
                'status': p['status'],
                'area_dunam': p.get('area_dunam'),
                'purpose': p.get('purpose', ''),
                'explanation': p.get('explanation', ''),
                'housing_units': p.get('housing_units'),
                'main_instructions': p.get('main_instructions', ''),
                'has_pdf': p.get('has_downloaded_files', False),
                'mavat_url': p.get('mavat_url', ''),
                'sharepoint_url': p.get('sharepoint_url', ''),
                'reviewed': st.get('reviewed', False),
                'continue_handling': st.get('continue_handling', False),
                'check_stage': st.get('check_stage', ''),
                'priority': st.get('priority', ''),
            })

    # Build GeoJSON features - one per block, with plan info
    features = []
    for _, row in matched.iterrows():
        gush_num = row['GUSH_NUM']
        plan_list = gush_to_plans.get(gush_num, [])
        if not plan_list:
            continue

        geom = row.geometry.__geo_interface__
        features.append({
            'type': 'Feature',
            'geometry': geom,
            'properties': {
                'gush_num': int(gush_num),
                'plans': plan_list,
                'plan_count': len(plan_list),
                'plan_numbers': ', '.join(p['plan_number'] for p in plan_list),
            }
        })

    return {
        'type': 'FeatureCollection',
        'features': features,
        'totalFeatures': len(features),
    }


_STATUS_FILE = os.path.join(DATA_DIR, 'plans_status.json')


def _load_statuses():
    if os.path.exists(_STATUS_FILE):
        with open(_STATUS_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {}


def _save_statuses(data):
    with open(_STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_plan_status(plan_number):
    statuses = _load_statuses()
    return statuses.get(plan_number, {})


def set_plan_status(plan_number, **kwargs):
    statuses = _load_statuses()
    if plan_number not in statuses:
        statuses[plan_number] = {}
    for key, val in kwargs.items():
        if val is not None:
            statuses[plan_number][key] = val
    _save_statuses(statuses)
    return statuses[plan_number]


def get_all_statuses():
    return _load_statuses()


def get_statistics(db_name='plans_tanai_saf'):
    """Get statistics about the plans database."""
    db = get_plans_db(db_name)
    plans = db.get('plans', [])

    authorities = {}
    for p in plans:
        auth = p.get('authority', 'לא ידוע')
        authorities[auth] = authorities.get(auth, 0) + 1

    settlements = {}
    for p in plans:
        for s in p.get('settlements', []):
            if s:
                settlements[s] = settlements.get(s, 0) + 1

    return {
        'total_plans': len(plans),
        'plans_with_pdf': sum(1 for p in plans if p.get('has_downloaded_files')),
        'plans_with_gush': sum(1 for p in plans if p.get('gushim')),
        'plans_with_area': sum(1 for p in plans if p.get('area_dunam')),
        'by_authority': dict(sorted(authorities.items(), key=lambda x: -x[1])),
        'top_settlements': dict(sorted(settlements.items(), key=lambda x: -x[1])[:30]),
        'metadata': db.get('metadata', {}),
    }
