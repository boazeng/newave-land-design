from fastapi import APIRouter, Query
from services.autocomplete_service import search_cities, search_streets

router = APIRouter()


@router.get("/cities")
def cities(q: str = Query(..., min_length=1, description="טקסט חיפוש")):
    """Autocomplete cities by name."""
    return search_cities(q)


@router.get("/streets")
def streets(
    city_code: str = Query(..., description="קוד עיר"),
    q: str = Query("", description="טקסט חיפוש"),
):
    """Autocomplete streets within a city."""
    return search_streets(city_code, q)
