"""
Router for planning committee plans (תוכניות תכנון).
Provides endpoints for searching, filtering, and viewing plans.
"""
from fastapi import APIRouter, Query
from typing import Optional
from services.plans_service import (
    list_databases, search_plans, get_plan, get_plans_by_gush,
    get_statistics, invalidate_cache
)

router = APIRouter()


@router.get("/databases")
def get_databases():
    """List all available plan databases."""
    return list_databases()


@router.get("/search")
def search(
    db: str = Query('plans_tanai_saf', description='Database name'),
    q: Optional[str] = Query(None, description='Search query (plan number, name, location)'),
    authority: Optional[str] = Query(None, description='Filter by authority (מקומית/מחוזית/ארצית)'),
    has_pdf: Optional[bool] = Query(None, description='Filter by PDF availability'),
    min_area: Optional[float] = Query(None, description='Minimum area in dunam'),
    max_area: Optional[float] = Query(None, description='Maximum area in dunam'),
    gush: Optional[int] = Query(None, description='Filter by gush number'),
    settlement: Optional[str] = Query(None, description='Filter by settlement name'),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Search plans with various filters."""
    return search_plans(
        db_name=db, query=q, authority=authority, has_pdf=has_pdf,
        min_area=min_area, max_area=max_area, gush=gush,
        settlement=settlement, limit=limit, offset=offset,
    )


@router.get("/stats")
def stats(db: str = Query('plans_tanai_saf')):
    """Get statistics about the plans database."""
    return get_statistics(db)


@router.get("/by-gush/{gush_num}")
def plans_by_gush(gush_num: int, db: str = Query('plans_tanai_saf')):
    """Get all plans for a specific gush number."""
    return get_plans_by_gush(db, gush_num)


@router.get("/{plan_number}")
def plan_detail(plan_number: str, db: str = Query('plans_tanai_saf')):
    """Get details for a specific plan."""
    plan = get_plan(db, plan_number)
    if not plan:
        return {"error": "Plan not found"}
    return plan


@router.post("/refresh")
def refresh_cache():
    """Invalidate cache and reload data from disk."""
    invalidate_cache()
    return {"status": "ok", "message": "Cache cleared"}
