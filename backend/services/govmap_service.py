import httpx

GOVMAP_BASE = "https://www.govmap.gov.il"

# Headers to mimic browser requests to GovMap
GOVMAP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": GOVMAP_BASE + "/",
    "Origin": GOVMAP_BASE,
    "Accept": "*/*",
}


async def fetch_wms_tile(
    layers: str,
    bbox: str,
    width: int,
    height: int,
    srs: str = "EPSG:3857",
) -> bytes:
    """Fetch a WMS tile from GovMap GeoServer."""
    params = {
        "service": "WMS",
        "version": "1.3.0",
        "request": "GetMap",
        "layers": layers,
        "bbox": bbox,
        "width": width,
        "height": height,
        "crs": srs,
        "format": "image/png",
        "transparent": "true",
    }

    async with httpx.AsyncClient(verify=False, timeout=15) as client:
        # Try the geoserver OWS endpoint
        url = GOVMAP_BASE + "/geoserver/ows"
        resp = await client.get(url, params=params, headers=GOVMAP_HEADERS)

        if resp.status_code == 200 and "image" in resp.headers.get("content-type", ""):
            return resp.content

        # Try public endpoint
        url = GOVMAP_BASE + "/geoserver/ows/public/"
        resp = await client.get(url, params=params, headers=GOVMAP_HEADERS)

        if resp.status_code == 200 and "image" in resp.headers.get("content-type", ""):
            return resp.content

    return None


async def search_parcel(block: int, parcel: int) -> dict:
    """Search for a specific block and parcel using GovMap API."""
    search_term = f"{block}-{parcel}"

    async with httpx.AsyncClient(verify=False, timeout=15) as client:
        url = f"{GOVMAP_BASE}/api/apps/parcel-search/address/{search_term}"
        resp = await client.get(url, headers=GOVMAP_HEADERS)

        if resp.status_code == 200:
            return resp.json()

    return None
