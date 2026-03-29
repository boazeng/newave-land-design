from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.energy_companies_service import (
    get_companies, delete_company, search_and_add,
)

router = APIRouter()


@router.get("")
def list_companies():
    """Get all energy companies."""
    return get_companies()


class SearchRequest(BaseModel):
    query: str


@router.post("/search")
def search(req: SearchRequest):
    """Search for energy companies online and add to database."""
    result = search_and_add(req.query)
    return result


@router.delete("/{company_id}")
def delete(company_id: int):
    """Delete a company."""
    return delete_company(company_id)
