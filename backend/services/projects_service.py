"""
Service for managing projects (פרוייקטים).
A project tracks ongoing activity on a single plan from the plans databases.
Stored as a flat JSON file, same pattern as plans_status / plans_parties.
"""
import json
import os
from datetime import date
from urllib.parse import unquote

from services.plans_service import get_plan, list_databases

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
_PROJECTS_FILE = os.path.join(DATA_DIR, 'projects.json')

# Marker separating the drive root from the folder path inside a SharePoint URL
_SP_ROOT_MARKER = 'Shared Documents/'


def _load():
    if not os.path.exists(_PROJECTS_FILE):
        return {'projects': []}
    with open(_PROJECTS_FILE, encoding='utf-8') as f:
        return json.load(f)


def _save(data):
    with open(_PROJECTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def sharepoint_folder(plan):
    """Folder path relative to the SharePoint drive root, from a plan's sharepoint_url."""
    url = unquote(plan.get('sharepoint_url') or '')
    if _SP_ROOT_MARKER not in url:
        return None
    return url.split(_SP_ROOT_MARKER, 1)[1].strip('/')


def find_plan(plan_number, db_name=None):
    """Look up a plan, searching every database when db_name is not given."""
    if db_name:
        return get_plan(db_name, plan_number), db_name
    for db in list_databases():
        name = db['name']
        if not db.get('total_plans'):
            continue
        plan = get_plan(name, plan_number)
        if plan:
            return plan, name
    return None, None


def _documents(plan):
    """Build the document list shown on a project page."""
    docs = []
    for filename in plan.get('downloaded_files') or []:
        kind = 'הוראות' if 'הוראות' in filename else 'תשריט' if 'תשריט' in filename else 'מסמך'
        docs.append({
            'filename': filename,
            'kind': kind,
            'url': f"/api/plans/pdf/{plan['plan_number']}/{filename}",
        })
    return docs


def _enrich(project):
    """Attach live plan data to a stored project record."""
    plan, db_name = find_plan(project['plan_number'], project.get('db'))
    if not plan:
        return {**project, 'plan': None, 'documents': [], 'plan_missing': True}
    return {
        **project,
        'db': db_name,
        'plan': plan,
        'documents': _documents(plan),
    }


def list_projects():
    return [_enrich(p) for p in _load()['projects']]


def get_project(project_id):
    for p in _load()['projects']:
        if p['id'] == project_id:
            return _enrich(p)
    return None


def create_project(plan_number, name=None, db=None, status='פעיל', notes=''):
    data = _load()
    if any(p['plan_number'] == plan_number for p in data['projects']):
        return {'error': f'כבר קיים פרוייקט לתוכנית {plan_number}'}

    plan, db_name = find_plan(plan_number, db)
    if not plan:
        return {'error': f'תוכנית {plan_number} לא נמצאה'}

    project = {
        'id': plan_number,
        'plan_number': plan_number,
        'name': name or plan.get('plan_name') or plan_number,
        'db': db_name,
        'status': status,
        'notes': notes,
        'created_at': date.today().isoformat(),
    }
    data['projects'].append(project)
    _save(data)
    return _enrich(project)


def update_project(project_id, **updates):
    data = _load()
    for p in data['projects']:
        if p['id'] == project_id:
            for key in ('name', 'status', 'notes'):
                if updates.get(key) is not None:
                    p[key] = updates[key]
            _save(data)
            return _enrich(p)
    return {'error': 'פרוייקט לא נמצא'}


def delete_project(project_id):
    data = _load()
    remaining = [p for p in data['projects'] if p['id'] != project_id]
    if len(remaining) == len(data['projects']):
        return {'error': 'פרוייקט לא נמצא'}
    data['projects'] = remaining
    _save(data)
    return {'status': 'ok'}
