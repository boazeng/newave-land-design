from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import cadastre, search, autocomplete, parking, chargers, committees, energy_companies

app = FastAPI(title="Newave Land Design API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cadastre.router, prefix="/api/cadastre")
app.include_router(search.router, prefix="/api/search")
app.include_router(autocomplete.router, prefix="/api/autocomplete")
app.include_router(parking.router, prefix="/api/parking")
app.include_router(chargers.router, prefix="/api/chargers")
app.include_router(committees.router, prefix="/api/committees")
app.include_router(energy_companies.router, prefix="/api/energy-companies")


@app.get("/api/health")
def health():
    return {"status": "ok"}
