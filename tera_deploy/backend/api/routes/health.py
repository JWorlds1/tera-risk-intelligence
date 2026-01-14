"""
Health Check Routes
"""
from fastapi import APIRouter
from datetime import datetime
import httpx

from config.settings import settings
from models.schemas import HealthCheck

router = APIRouter()


@router.get("/", response_model=HealthCheck)
async def health_check():
    """System health check"""
    services = {
        "database": False,
        "redis": False,
        "ollama": False,
        "chromadb": False
    }
    
    # Check services
    async with httpx.AsyncClient(timeout=5) as client:
        # Ollama
        try:
            r = await client.get(f"{settings.OLLAMA_URL}/api/tags")
            services["ollama"] = r.status_code == 200
        except:
            pass
        
        # ChromaDB
        try:
            r = await client.get(f"{settings.CHROMA_URL}/api/v1/heartbeat")
            services["chromadb"] = r.status_code == 200
        except:
            pass
    
    # Redis
    try:
        import redis.asyncio as redis
        r = redis.from_url(settings.REDIS_URL)
        await r.ping()
        services["redis"] = True
        await r.close()
    except:
        pass
    
    # Database
    try:
        from services.database import get_db
        async for db in get_db():
            await db.execute("SELECT 1")
            services["database"] = True
    except:
        pass
    
    all_ok = all(services.values())
    
    return HealthCheck(
        status="healthy" if all_ok else "degraded",
        version=settings.APP_VERSION,
        services=services,
        timestamp=datetime.utcnow()
    )


@router.get("/ready")
async def readiness():
    """Kubernetes readiness probe"""
    return {"status": "ready"}


@router.get("/live")
async def liveness():
    """Kubernetes liveness probe"""
    return {"status": "alive"}

