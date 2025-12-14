"""
TERA API Server - Main Entry Point
Environmental Peace & Conflict Prediction System
With Earth System Data and 2026-2027 Forecasts
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from api.routes import health, regions, analysis, scraping
from api.routes import earth_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting TERA API Server...")
    logger.info("🌍 Earth Data Services: NASA FIRMS, Planetary Computer, ERA5")
    logger.info("📊 Forecast Engine: 2026-2027 Outlook")
    yield
    logger.info("👋 TERA API Server shutdown")


app = FastAPI(
    title="TERA API",
    description="""
    ## Environmental Peace & Conflict Prediction System
    
    ### Features
    - 🌍 Real-time Earth System Data (Energy, Water, Carbon cycles)
    - 🛰️ Satellite Data Integration (Sentinel, MODIS, VIIRS)
    - 🔥 NASA FIRMS Fire Detection
    - 📊 2026-2027 Risk Forecasts
    - 🗺️ H3 Hexagonal Grid Analysis
    
    ### Data Sources
    - ERA5 Reanalysis (ECMWF)
    - Copernicus Sentinel (ESA)
    - NASA EONET / FIRMS
    - Microsoft Planetary Computer
    """,
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core routes
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(regions.router, prefix="/api/regions", tags=["Regions"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(scraping.router, prefix="/api/scraping", tags=["Scraping"])

# Earth Data routes
app.include_router(earth_data.router, prefix="/api/earth", tags=["Earth Data & Forecasts"])


@app.get("/")
async def root():
    return {
        "name": "TERA API",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "analysis": "/api/analysis/analyze?city=Berlin",
            "forecast": "/api/earth/forecast/city/berlin",
            "fires": "/api/earth/fires/current?country=DEU",
            "satellites": "/api/earth/satellite/search",
            "cycles": "/api/earth/cycles",
            "sources": "/api/earth/sources"
        }
    }
