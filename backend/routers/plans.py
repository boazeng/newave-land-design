"""Router for planning committee plans."""
from fastapi import APIRouter, Query
from typing import Optional
from pydantic import BaseModel
from services.plans_service import (
    list_databases, search_plans, get_plan, get_plans_by_gush,
    get_statistics, invalidate_cache, get_plans_geojson,
    get_plan_status, set_plan_status, get_all_statuses,
    get_plan_parties, set_plan_parties, add_owner, remove_owner,
)


class PlanStatusUpdate(BaseModel):
    reviewed: Optional[bool] = None
    continue_handling: Optional[bool] = None
    check_stage: Optional[str] = None
    priority: Optional[str] = None
    not_interesting: Optional[bool] = None


router = APIRouter()


@router.get("/databases")
def get_databases():
    return list_databases()


@router.get("/search")
def search(
    db: str = Query('plans_tanai_saf'),
    q: Optional[str] = Query(None),
    authority: Optional[str] = Query(None),
    has_pdf: Optional[bool] = Query(None),
    min_area: Optional[float] = Query(None),
    max_area: Optional[float] = Query(None),
    gush: Optional[int] = Query(None),
    settlement: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    return search_plans(
        db_name=db, query=q, authority=authority, has_pdf=has_pdf,
        min_area=min_area, max_area=max_area, gush=gush,
        settlement=settlement, limit=limit, offset=offset,
    )


@router.get("/stats")
def stats(db: str = Query('plans_tanai_saf')):
    return get_statistics(db)


@router.get("/geojson")
def plans_geojson(
    db: str = Query('plans_tanai_saf'),
    bbox: Optional[str] = Query(None),
):
    bbox_coords = [float(x) for x in bbox.split(',')] if bbox else None
    return get_plans_geojson(db, bbox_coords)


@router.get("/by-gush/{gush_num}")
def plans_by_gush(gush_num: int, db: str = Query('plans_tanai_saf')):
    return get_plans_by_gush(db, gush_num)


# Status endpoints - MUST come before /{plan_number} catch-all
@router.get("/statuses")
def all_statuses():
    return get_all_statuses()


@router.put("/status/{plan_number:path}")
def update_status(plan_number: str, body: PlanStatusUpdate):
    """Update status fields for a plan. Saves immediately."""
    updates = {}
    if body.reviewed is not None:
        updates['reviewed'] = body.reviewed
    if body.continue_handling is not None:
        updates['continue_handling'] = body.continue_handling
    if body.check_stage is not None:
        updates['check_stage'] = body.check_stage
    if body.priority is not None:
        updates['priority'] = body.priority
    if body.not_interesting is not None:
        updates['not_interesting'] = body.not_interesting
    return set_plan_status(plan_number, **updates)


@router.get("/status/{plan_number:path}")
def plan_status(plan_number: str):
    return get_plan_status(plan_number)


class OwnerItem(BaseModel):
    name: str
    id_type: Optional[str] = None
    id_number: Optional[str] = None
    address: Optional[str] = None
    gush: Optional[int] = None
    parcel: Optional[int] = None
    notes: Optional[str] = None


class PartiesUpdate(BaseModel):
    submitter: Optional[str] = None
    developer: Optional[str] = None
    stakeholders: Optional[list] = None
    owners: Optional[list] = None


@router.get("/parties/{plan_number:path}")
def plan_parties(plan_number: str):
    return get_plan_parties(plan_number)


@router.put("/parties/{plan_number:path}")
def update_parties(plan_number: str, body: PartiesUpdate):
    return set_plan_parties(
        plan_number,
        submitter=body.submitter,
        developer=body.developer,
        stakeholders=body.stakeholders,
        owners=body.owners,
    )


@router.post("/parties/{plan_number:path}/owners")
def add_plan_owner(plan_number: str, owner: OwnerItem):
    return add_owner(plan_number, owner.model_dump(exclude_none=True))


@router.delete("/parties/{plan_number:path}/owners/{index}")
def remove_plan_owner(plan_number: str, index: int):
    return remove_owner(plan_number, index)


@router.post("/refresh")
def refresh_cache():
    invalidate_cache()
    return {"status": "ok"}


# Catch-all for plan detail - MUST be last
@router.get("/{plan_number:path}")
def plan_detail(plan_number: str, db: str = Query('plans_tanai_saf')):
    plan = get_plan(db, plan_number)
    if not plan:
        return {"error": "Plan not found"}
    return plan
