from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
import os
from services.scraper_service import get_available_committees, start_scrape, get_task, get_all_tasks

router = APIRouter()

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')


def _load(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        return json.load(f)


@router.get("/local")
def local_committees():
    """Get all local planning committees."""
    return _load('committees_local.json')


@router.get("/district")
def district_committees():
    """Get all district planning committees."""
    return _load('committees_district.json')


@router.get("/districts-geojson")
def districts_geojson():
    """Get district boundaries as GeoJSON."""
    return _load('districts.geojson')


@router.get("/scrapers")
def available_scrapers():
    """Return list of committees that have protocol scrapers."""
    return get_available_committees()


class ScrapeRequest(BaseModel):
    committee_name: str
    years_back: int = 5


@router.post("/scrape")
def scrape_committee(req: ScrapeRequest):
    """Start a protocol scraper for a committee."""
    if req.years_back < 1 or req.years_back > 15:
        raise HTTPException(400, "מספר שנים חייב להיות בין 1 ל-15")

    task_id, error = start_scrape(req.committee_name, req.years_back)
    if error:
        raise HTTPException(400, error)

    return {"task_id": task_id, "status": "running"}


@router.get("/scrape/all")
def all_scrape_tasks():
    """Get all scraper tasks."""
    tasks = get_all_tasks()
    return [{
        "id": t["id"],
        "committee": t["committee"],
        "status": t["status"],
        "start_year": t["start_year"],
        "end_year": t["end_year"],
        "started_at": t["started_at"],
        "finished_at": t.get("finished_at"),
        "result": t.get("result"),
    } for t in tasks]


@router.get("/scrape/{task_id}")
def scrape_status(task_id: str):
    """Get status of a running scraper task."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(404, "משימה לא נמצאה")

    resp = {
        "id": task["id"],
        "committee": task["committee"],
        "status": task["status"],
        "start_year": task["start_year"],
        "end_year": task["end_year"],
        "started_at": task["started_at"],
        "finished_at": task.get("finished_at"),
        "result": task.get("result"),
    }
    if task["status"] == "error":
        resp["output"] = task.get("output", "")
    return resp
