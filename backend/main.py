import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from routers import cadastre, search, autocomplete, parking, chargers, committees, energy_companies, parking_devices, parking_protocols, charging_stations, plans, projects, auth
from services import auth_service

app = FastAPI(title="Newave Land Design API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://newave.co.il",
        "https://www.newave.co.il",
        "http://newave.co.il",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Every /api route needs a signed-in user, except sign-in itself and the health
# check the deploy workflow polls.
PUBLIC_API_PREFIXES = ("/api/auth/", "/api/health")


@app.middleware("http")
async def require_login(request: Request, call_next):
    path = request.url.path
    if (path.startswith("/api/") and request.method != "OPTIONS"
            and not path.startswith(PUBLIC_API_PREFIXES)):
        token = request.cookies.get(auth_service.COOKIE_NAME)
        if not auth_service.read_session(token):
            return JSONResponse({"detail": "לא מחובר"}, status_code=401)
    return await call_next(request)


app.include_router(auth.router, prefix="/api/auth")

app.include_router(cadastre.router, prefix="/api/cadastre")
app.include_router(search.router, prefix="/api/search")
app.include_router(autocomplete.router, prefix="/api/autocomplete")
app.include_router(parking.router, prefix="/api/parking")
app.include_router(chargers.router, prefix="/api/chargers")
app.include_router(committees.router, prefix="/api/committees")
app.include_router(energy_companies.router, prefix="/api/energy-companies")
app.include_router(parking_devices.router, prefix="/api/parking-devices")
app.include_router(parking_protocols.router, prefix="/api/parking-protocols")
app.include_router(charging_stations.router, prefix="/api/charging-stations")
app.include_router(plans.router, prefix="/api/plans")
app.include_router(projects.router, prefix="/api/projects")


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Serve frontend static files in production
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist')
if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve frontend SPA - all non-API routes return index.html."""
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
