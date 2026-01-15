"""
Scraping Tasks for Celery
"""
from .celery_app import app

@app.task(name="tasks.scrape_source")
def scrape_source_task(source: str):
    """Scrape a specific source"""
    return {"status": "completed", "source": source}
