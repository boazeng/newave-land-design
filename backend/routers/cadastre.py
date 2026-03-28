from fastapi import APIRouter, Query
from services.cadastre_service import get_features

router = APIRouter()


@router.get("/blocks")
def get_blocks(
    bbox: str = Query(..., description="min_lng,min_lat,max_lng,max_lat"),
):
    """Get block features within bounding box."""
    coords = [float(x) for x in bbox.split(",")]
    return get_features("blocks", coords)


@router.get("/parcels")
def get_parcels(
    bbox: str = Query(..., description="min_lng,min_lat,max_lng,max_lat"),
):
    """Get parcel features within bounding box."""
    coords = [float(x) for x in bbox.split(",")]
    return get_features("parcels", coords)
