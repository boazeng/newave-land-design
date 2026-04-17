"""
Service for managing planning committee plans (תוכניות תכנון).
Loads plans from JSON database, supports filtering by various criteria.
"""
import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')


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
