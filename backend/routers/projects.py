"""Router for projects (פרוייקטים) - managed activity on a plan."""
from fastapi import APIRouter
from typing import Optional
from pydantic import BaseModel
from fastapi.responses import JSONResponse

from services.projects_service import (
    list_projects, get_project, create_project, update_project, delete_project,
    get_projects_geojson,
)

router = APIRouter()


class ProjectCreate(BaseModel):
    plan_number: str
    name: Optional[str] = None
    db: Optional[str] = None
    status: Optional[str] = 'פעיל'
    notes: Optional[str] = ''


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


@router.get("")
def all_projects():
    return list_projects()


@router.post("")
def add_project(body: ProjectCreate):
    result = create_project(
        plan_number=body.plan_number,
        name=body.name,
        db=body.db,
        status=body.status,
        notes=body.notes,
    )
    if 'error' in result:
        return JSONResponse(status_code=400, content=result)
    return result


# MUST come before the /{project_id} catch-all
@router.get("/geojson")
def projects_geojson():
    """Cadastre blocks for every project's gushim, for the map layer."""
    return get_projects_geojson()


@router.get("/{project_id}")
def project_detail(project_id: str):
    project = get_project(project_id)
    if not project:
        return JSONResponse(status_code=404, content={"error": "פרוייקט לא נמצא"})
    return project


@router.put("/{project_id}")
def edit_project(project_id: str, body: ProjectUpdate):
    result = update_project(
        project_id, name=body.name, status=body.status, notes=body.notes,
    )
    if 'error' in result:
        return JSONResponse(status_code=404, content=result)
    return result


@router.delete("/{project_id}")
def remove_project(project_id: str):
    result = delete_project(project_id)
    if 'error' in result:
        return JSONResponse(status_code=404, content=result)
    return result
