from fastapi import APIRouter, Query
from services.search_service import search_by_parcel, search_by_address

router = APIRouter()


@router.get("/parcel")
def parcel_search(
    gush: int = Query(..., description="מספר גוש"),
    parcel: int = Query(None, description="מספר חלקה"),
):
    """Search by block number and optional parcel number."""
    return search_by_parcel(gush, parcel)


@router.get("/address")
async def address_search(
    city: str = Query(..., description="עיר"),
    street: str = Query(..., description="רחוב"),
    house: str = Query(None, description="מספר בית"),
):
    """Search by street address."""
    return await search_by_address(city, street, house)
