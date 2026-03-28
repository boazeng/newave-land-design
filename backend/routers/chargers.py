from fastapi import APIRouter, HTTPException
from services.chargers_service import get_charger_sites, sync_chargers

router = APIRouter()


@router.get("/sites")
def charger_sites():
    """Get charger sites (grouped by DCODE)."""
    return get_charger_sites()


@router.post("/sync")
async def sync():
    """Sync chargers from Priority."""
    result = await sync_chargers()
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])
    return result
