"""
TERA API Server - 2026 Forecast Edition
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('🚀 TERA API Server - 2026 Edition')
    logger.info('📊 Datenquellen: IPCC AR6, ERA5, Copernicus DEM')
    logger.info('✅ Endpunkte: /analyze, /risk-map, /risk-map/viewport')
    yield
    logger.info('👋 TERA API Server shutdown')


app = FastAPI(
    title='TERA API - 2026 Forecast',
    description='Environmental Peace & Conflict Prediction System',
    version='2.3.0',
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routes - analysis hat /risk-map und /risk-map/viewport
from api.routes import analysis
from api.routes.extended import router as extended_router
from api.routes.v2_router import router as v2_router

app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(extended_router)
app.include_router(v2_router)


@app.get("/")
async def root():
    return {
        "name": "TERA API - 2026 Forecast Edition",
        "version": "2.3.0",
        "endpoints": {
            "analyze": "/api/analysis/analyze (GET/POST)",
            "risk_map": "/api/analysis/risk-map?city=Miami",
            "risk_map_viewport": "/api/analysis/risk-map/viewport"
        }
    }
