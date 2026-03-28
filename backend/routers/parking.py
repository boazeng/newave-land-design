from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.parking_service import (
    get_our_devices, sync_from_priority,
    get_competitor_devices, add_competitor_device, delete_competitor_device,
)

router = APIRouter()


# --- Our devices (from Priority) ---

@router.get("/ours")
def our_parking():
    """Get our parking devices (synced from Priority)."""
    return get_our_devices()


@router.post("/sync")
async def sync_priority():
    """Sync parking devices from Priority."""
    result = await sync_from_priority()
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])
    return result


# --- Competitor devices (manual entry) ---

class CompetitorDevice(BaseModel):
    competitor_name: str
    device_type: str
    customer: str = ""
    address: str
    city: str
    notes: str = ""


@router.get("/competitors")
def competitor_parking():
    """Get competitor parking devices."""
    return get_competitor_devices()


@router.post("/competitors")
def add_competitor(device: CompetitorDevice):
    """Add a competitor parking device."""
    return add_competitor_device(device.model_dump())


@router.delete("/competitors/{device_id}")
def delete_competitor(device_id: int):
    """Delete a competitor parking device."""
    return delete_competitor_device(device_id)
