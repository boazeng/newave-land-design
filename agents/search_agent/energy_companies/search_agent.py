"""
Energy Companies Search Agent
Searches Google and Israeli business directories for EV charging
and energy management companies.
"""
import re
import requests
import time
from urllib.parse import quote_plus


def search_google(query, num_results=20):
    """Search Google and extract URLs from results."""
    results = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    for start in range(0, num_results, 10):
        url = f"https://www.google.com/search?q={quote_plus(query)}&start={start}&num=10&hl=he"
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                continue

            links = re.findall(r'<a href="/url\?q=(https?://[^&"]+)', resp.text)
            titles = re.findall(r'<h3[^>]*>(.*?)</h3>', resp.text)

            for i, link in enumerate(links):
                if any(x in link for x in ['google.com', 'youtube.com', 'facebook.com', 'instagram.com', 'twitter.com', 'linkedin.com']):
                    continue

                title = titles[i] if i < len(titles) else ''
                title = re.sub(r'<[^>]+>', '', title)

                results.append({
                    'url': link,
                    'title': title,
                    'source': 'google',
                })

            time.sleep(1.5)
        except Exception:
            pass

    return results


def extract_company_info(url):
    """Try to extract company info from a website."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    info = {'website': url}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return info

        text = resp.text

        title_match = re.search(r'<title[^>]*>(.*?)</title>', text, re.IGNORECASE | re.DOTALL)
        if title_match:
            info['title'] = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()[:200]

        desc_match = re.search(
            r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']',
            text, re.IGNORECASE
        )
        if desc_match:
            info['description'] = desc_match.group(1).strip()[:500]

        phone_match = re.search(r'(0\d{1,2}[-\s]?\d{7,8})', text)
        if phone_match:
            info['phone'] = phone_match.group(1)

        email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', text)
        if email_match:
            email = email_match.group(0)
            if not any(x in email for x in ['example.com', 'sentry.io', 'wixpress']):
                info['email'] = email

    except Exception:
        pass

    return info


def run_search(query):
    """
    Run a full search across multiple sources.
    Returns list of company dicts.
    """
    all_results = []

    queries = [
        query,
        "EV charging company Israel",
        "electric vehicle charging management building Israel",
        "smart charging residential building Israel",
        "EVSE Israel company",
    ]

    for q in queries:
        results = search_google(q, num_results=10)
        all_results.extend(results)
        time.sleep(2)

    # Deduplicate by domain
    seen_domains = set()
    unique = []
    for r in all_results:
        url = r.get('url', '')
        if not url:
            continue
        domain = re.sub(r'^https?://(www\.)?', '', url).split('/')[0].lower()
        if domain not in seen_domains and domain and '.' in domain:
            seen_domains.add(domain)
            unique.append(r)

    # Enrich with website info
    companies = []
    for r in unique:
        url = r.get('url', '')
        info = extract_company_info(url)

        name = r.get('title') or info.get('title', '')
        name = name.split('|')[0].split(' - ')[0].strip() if name else ''

        if not name or len(name) < 2:
            continue

        companies.append({
            'name': name,
            'website': url,
            'description': info.get('description', ''),
            'phone': info.get('phone', ''),
            'email': info.get('email', ''),
            'source': r.get('source', 'google'),
        })

        time.sleep(0.5)

    return companies
