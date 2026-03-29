"""
Energy companies data service - stores and manages company data.
"""
import json
import os
import sys
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
COMPANIES_FILE = os.path.join(DATA_DIR, 'energy_companies.json')

# Add agents to path for importing search agent
AGENT_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'agents', 'search_agent', 'energy_companies')
sys.path.insert(0, AGENT_DIR)


def _read():
    if not os.path.exists(COMPANIES_FILE):
        return []
    with open(COMPANIES_FILE, encoding='utf-8') as f:
        return json.load(f)


def _write(data):
    os.makedirs(os.path.dirname(COMPANIES_FILE), exist_ok=True)
    with open(COMPANIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_companies():
    return _read()


def add_company(company):
    companies = _read()
    company['id'] = max([c.get('id', 0) for c in companies], default=0) + 1
    company['added_at'] = datetime.now().isoformat()
    companies.append(company)
    _write(companies)
    return company


def delete_company(company_id):
    companies = _read()
    companies = [c for c in companies if c.get('id') != company_id]
    _write(companies)
    return {'deleted': company_id}


def search_and_add(query):
    """Run search agent and add new companies to database."""
    from search_agent import run_search

    results = run_search(query)

    companies = _read()
    existing_domains = set()
    for c in companies:
        if c.get('website'):
            import re
            domain = re.sub(r'^https?://(www\.)?', '', c['website']).split('/')[0].lower()
            existing_domains.add(domain)

    added = 0
    for r in results:
        import re
        domain = re.sub(r'^https?://(www\.)?', '', r.get('website', '')).split('/')[0].lower()
        if domain in existing_domains:
            continue

        existing_domains.add(domain)
        company = {
            'id': max([c.get('id', 0) for c in companies], default=0) + 1,
            'name': r.get('name', ''),
            'website': r.get('website', ''),
            'description': r.get('description', ''),
            'category': categorize(r),
            'phone': r.get('phone', ''),
            'email': r.get('email', ''),
            'source': r.get('source', ''),
            'added_at': datetime.now().isoformat(),
        }
        companies.append(company)
        added += 1

    _write(companies)
    return {'found': added, 'results': len(results)}


def categorize(company):
    """Try to categorize a company based on its description."""
    desc = (company.get('description', '') + ' ' + company.get('name', '')).lower()

    if any(w in desc for w in ['טעינה', 'charging', 'ev', 'רכב חשמלי', 'עמדת טעינה']):
        if any(w in desc for w in ['בניין', 'מגורים', 'ניהול', 'management']):
            return 'ניהול טעינה בבניינים'
        return 'טעינת רכבים חשמליים'
    if any(w in desc for w in ['סולארי', 'solar', 'אנרגיה מתחדשת']):
        return 'אנרגיה סולארית'
    if any(w in desc for w in ['חשמל', 'אנרגיה', 'energy']):
        return 'אנרגיה'

    return 'כללי'
