"""
Service for running committee protocol scrapers.
Maps committee names to their scraper configurations and manages background execution.
"""
import os
import sys
import json
import subprocess
import threading
import uuid
from datetime import datetime

SCRAPERS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'agents', 'search_agent', 'vaadot_search'))
OUTPUT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'protocols'))

# Mapping of committee names to their scraper config
SCRAPER_CONFIG = {
    # Complot-based
    'רמת גן': {
        'platform': 'complot',
        'script': 'complot/complot_scraper.py',
        'args': ['--site-id', '3', '--city-name', 'רמת_גן', '--protocols-only'],
    },
    'חולון': {
        'platform': 'complot',
        'script': 'complot/complot_scraper.py',
        'args': ['--site-id', '34', '--city-name', 'חולון', '--protocols-only'],
    },
    'בת ים': {
        'platform': 'complot',
        'script': 'complot/complot_scraper.py',
        'args': ['--site-id', '81', '--city-name', 'בת_ים', '--protocols-only'],
    },
    'אור יהודה': {
        'platform': 'complot',
        'script': 'complot/complot_scraper.py',
        'args': ['--site-id', '73', '--city-name', 'אור_יהודה', '--protocols-only'],
    },
    'רמת השרון': {
        'platform': 'complot',
        'script': 'complot/complot_scraper.py',
        'args': ['--site-id', '118', '--city-name', 'רמת_השרון', '--protocols-only'],
    },
    'גבעתיים': {
        'platform': 'complot',
        'script': 'complot/complot_scraper.py',
        'args': ['--site-id', '98', '--city-name', 'גבעתיים'],
    },
    'הרצליה': {
        'platform': 'complot',
        'script': 'complot/complot_scraper.py',
        'args': ['--site-id', '121', '--city-name', 'הרצליה', '--protocols-only'],
    },
    'בני ברק': {
        'platform': 'complot',
        'script': 'complot/complot_scraper.py',
        'args': ['--site-id', '75', '--city-name', 'בני_ברק', '--protocols-only'],
    },
    # Bartech-based
    'קרית אונו': {
        'platform': 'bartech',
        'script': 'bartech/bartech_scraper.py',
        'args': ['--city-code', 'ono', '--city-name', 'קרית_אונו', '--protocols-only'],
    },
    'אזור': {
        'platform': 'bartech',
        'script': 'bartech/bartech_scraper.py',
        'args': ['--city-code', 'azr', '--city-name', 'אזור', '--protocols-only'],
    },
    # Tel Aviv - independent
    'תל אביב - יפו': {
        'platform': 'telaviv',
        'script': 'telaviv/telaviv_scraper.py',
        'args': [],
    },
    # Yokneam
    'יקנעם עילית': {
        'platform': 'yokneam',
        'script': 'yokneam/yokneam_scraper_auto.py',
        'args': ['--protocols-only'],
    },
}

# In-memory task store
_tasks = {}


def get_available_committees():
    """Return list of committee names that have scrapers available."""
    return list(SCRAPER_CONFIG.keys())


def get_task(task_id):
    """Get task status by ID."""
    return _tasks.get(task_id)


def get_all_tasks():
    """Return all tasks."""
    return list(_tasks.values())


def start_scrape(committee_name, years_back):
    """Start a scraper for the given committee. Returns task_id."""
    config = SCRAPER_CONFIG.get(committee_name)
    if not config:
        return None, f"אין סקריפט הורדה עבור '{committee_name}'"

    if config.get('needs_discovery'):
        return None, f"ועדת '{committee_name}' דורשת גילוי Site ID. הרץ find_complot_ids.py קודם."

    end_year = datetime.now().year
    start_year = end_year - years_back + 1

    task_id = str(uuid.uuid4())[:8]

    _tasks[task_id] = {
        'id': task_id,
        'committee': committee_name,
        'platform': config['platform'],
        'status': 'running',
        'start_year': start_year,
        'end_year': end_year,
        'started_at': datetime.now().isoformat(),
        'output': '',
        'result': None,
    }

    thread = threading.Thread(target=_run_scraper, args=(task_id, config, start_year, end_year))
    thread.daemon = True
    thread.start()

    return task_id, None


def _run_scraper(task_id, config, start_year, end_year):
    """Run a scraper in a background thread."""
    task = _tasks[task_id]

    script_path = os.path.join(SCRAPERS_DIR, config['script'])
    if not os.path.exists(script_path):
        task['status'] = 'error'
        task['result'] = {'error': f'סקריפט לא נמצא: {config["script"]}'}
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    cmd = [
        sys.executable, script_path,
        '--start-year', str(start_year),
        '--end-year', str(end_year),
        '--output-dir', OUTPUT_DIR,
        *config['args'],
    ]

    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800,
            encoding='utf-8',
            env=env,
            cwd=SCRAPERS_DIR,
        )

        task['output'] = result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout
        if result.stderr:
            task['output'] += '\n--- STDERR ---\n' + result.stderr[-500:]

        if result.returncode == 0:
            task['status'] = 'completed'
            task['result'] = _parse_scraper_output(task, config)
        else:
            task['status'] = 'error'
            task['result'] = {'error': f'הסקריפט נכשל (exit code {result.returncode})'}

    except subprocess.TimeoutExpired:
        task['status'] = 'error'
        task['result'] = {'error': 'הסקריפט חרג מזמן הריצה המותר (30 דקות)'}
    except Exception as e:
        task['status'] = 'error'
        task['result'] = {'error': str(e)}

    task['finished_at'] = datetime.now().isoformat()


def _parse_scraper_output(task, config):
    """Try to read the JSON output file produced by the scraper."""
    # Try to find the data JSON file
    city_names = [a for i, a in enumerate(config['args']) if i > 0 and config['args'][i-1] in ('--city-name', '--city')]
    if not city_names:
        # For telaviv scraper
        city_names = ['תל_אביב_יפו']

    for city_name in city_names:
        json_path = os.path.join(OUTPUT_DIR, city_name, f'{city_name}_data.json')
        if os.path.exists(json_path):
            try:
                with open(json_path, encoding='utf-8') as f:
                    data = json.load(f)
                return {
                    'total_documents': data.get('total_documents', 0),
                    'counts_by_year': data.get('counts_by_year', {}),
                    'total_meetings': data.get('total_meetings', 0),
                }
            except:
                pass

    # Fallback: parse stdout for counts
    return {'message': 'הסקריפט הסתיים בהצלחה'}
