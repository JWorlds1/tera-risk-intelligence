"""
TERA Health Check API
"""
from fastapi import APIRouter
import httpx
from config.settings import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """System health check"""
    status = {
        "api": "healthy",
        "database": "unknown",
        "ollama": "unknown",
        "redis": "unknown"
    }
    
    # Check Ollama
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{settings.ollama_url}/api/tags")
            status["ollama"] = "healthy" if r.status_code == 200 else "unhealthy"
    except:
        status["ollama"] = "unavailable"
    
    return status
