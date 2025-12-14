"""
TERA FastAPI Main Application
Environmental Peace & Conflict Prediction System
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
import asyncio

from config.settings import settings
from api.routes import analysis, scraping, regions, health
from services.database import init_db, close_db
from services.ollama_client import OllamaClient
from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting TERA System...")
    
    # Initialize database
    await init_db()
    logger.info("✓ Database connected")
    
    # Check Ollama
    ollama = OllamaClient()
    if await ollama.health_check():
        logger.info(f"✓ Ollama connected (model: {settings.OLLAMA_MODEL})")
    else:
        logger.warning("⚠ Ollama not available - LLM features disabled")
    
    yield
    
    # Cleanup
    await close_db()
    logger.info("👋 TERA System shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="TERA API",
    description="Environmental Peace & Conflict Prediction System",
    version=settings.APP_VERSION,
    default_response_class=ORJSONResponse,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(scraping.router, prefix="/api/v1/scraping", tags=["Scraping"])
app.include_router(regions.router, prefix="/api/v1/regions", tags=["Regions"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "documentation": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.DEBUG
    )

