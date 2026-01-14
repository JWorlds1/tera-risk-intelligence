"""
Scraping Routes
"""
from fastapi import APIRouter, BackgroundTasks
from typing import List, Optional

from models.schemas import ScrapingStatus, Article
from tasks.scraping_tasks import scrape_source_task
from loguru import logger

router = APIRouter()

# Available sources
SOURCES = {
    "nasa": "https://earthobservatory.nasa.gov",
    "un": "https://press.un.org",
    "wfp": "https://www.wfp.org/news",
    "worldbank": "https://www.worldbank.org/en/news"
}


@router.get("/sources")
async def list_sources():
    """List available scraping sources"""
    return {"sources": SOURCES}


@router.post("/start/{source}")
async def start_scraping(source: str, background_tasks: BackgroundTasks, limit: int = 10):
    """Start scraping a specific source"""
    if source not in SOURCES:
        return {"error": f"Unknown source: {source}", "available": list(SOURCES.keys())}
    
    # Queue task
    task = scrape_source_task.delay(source, limit)
    
    logger.info(f"Started scraping task for {source}: {task.id}")
    
    return {
        "task_id": task.id,
        "source": source,
        "status": "queued",
        "message": f"Scraping {source} with limit {limit}"
    }


@router.get("/status/{task_id}")
async def get_scraping_status(task_id: str) -> ScrapingStatus:
    """Get status of a scraping task"""
    from tasks.celery_app import celery_app
    
    result = celery_app.AsyncResult(task_id)
    
    return ScrapingStatus(
        task_id=task_id,
        status=result.status,
        progress=result.info.get("progress", 0) if result.info else 0,
        articles_scraped=result.info.get("articles", 0) if result.info else 0,
        errors=result.info.get("errors", []) if result.info else []
    )


@router.post("/start-all")
async def start_all_scraping(background_tasks: BackgroundTasks, limit_per_source: int = 5):
    """Start scraping all sources"""
    tasks = []
    
    for source in SOURCES:
        task = scrape_source_task.delay(source, limit_per_source)
        tasks.append({"source": source, "task_id": task.id})
    
    return {
        "status": "started",
        "tasks": tasks,
        "total_sources": len(SOURCES)
    }

