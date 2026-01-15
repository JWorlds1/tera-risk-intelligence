"""
TERA Scraping API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from loguru import logger

router = APIRouter()


class ScrapingRequest(BaseModel):
    source: Optional[str] = None


class ScrapingResponse(BaseModel):
    status: str
    message: str
    task_id: Optional[str] = None


@router.post("/start", response_model=ScrapingResponse)
async def start_scraping(request: ScrapingRequest):
    """
    Start a scraping job
    """
    try:
        # For now, just return success - Celery integration later
        source = request.source or "all"
        logger.info(f"Starting scraping for: {source}")
        
        return ScrapingResponse(
            status="started",
            message=f"Scraping started for {source}",
            task_id="demo-task-id"
        )
    except Exception as e:
        logger.error(f"Scraping error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}")
async def get_scraping_status(task_id: str):
    """Get status of a scraping task"""
    return {"task_id": task_id, "status": "pending"}
