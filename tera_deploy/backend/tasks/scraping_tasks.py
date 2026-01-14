"""
Scraping Background Tasks
"""
from tasks.celery_app import celery_app
from loguru import logger
import asyncio
import aiohttp
from bs4 import BeautifulSoup


@celery_app.task(bind=True)
def scrape_source_task(self, source: str, limit: int = 10):
    """
    Scrape articles from a source.
    Updates task state with progress.
    """
    logger.info(f"Starting scrape task for {source}")
    
    # Run async scraper
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(_scrape_source(self, source, limit))
        return result
    finally:
        loop.close()


async def _scrape_source(task, source: str, limit: int):
    """Async scraping implementation"""
    from services.ollama_client import OllamaClient
    
    urls = get_source_urls(source)[:limit]
    articles = []
    errors = []
    
    async with aiohttp.ClientSession() as session:
        for i, url in enumerate(urls):
            try:
                # Update progress
                progress = (i / len(urls)) * 100
                task.update_state(
                    state="PROGRESS",
                    meta={
                        "progress": progress,
                        "articles": len(articles),
                        "current_url": url
                    }
                )
                
                # Fetch page
                async with session.get(url, timeout=30) as response:
                    if response.status != 200:
                        errors.append(f"HTTP {response.status}: {url}")
                        continue
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, "lxml")
                    
                    # Extract content (simplified)
                    title = soup.find("h1")
                    title = title.get_text().strip() if title else ""
                    
                    # Get main content
                    content = ""
                    for p in soup.find_all("p"):
                        content += p.get_text() + " "
                    content = content[:5000]  # Limit
                    
                    if title and content:
                        articles.append({
                            "source": source,
                            "url": url,
                            "title": title,
                            "content": content
                        })
                        
                # Rate limit
                await asyncio.sleep(1)
                
            except Exception as e:
                errors.append(f"Error: {url} - {str(e)}")
                logger.error(f"Scrape error: {e}")
    
    # Process with LLM (optional)
    ollama = OllamaClient()
    if await ollama.health_check():
        for article in articles:
            entities = await ollama.extract_entities(article["content"])
            article["entities"] = [e.model_dump() for e in entities]
    
    return {
        "source": source,
        "articles_scraped": len(articles),
        "errors": errors,
        "articles": articles
    }


def get_source_urls(source: str) -> list:
    """Get URLs for a source (simplified)"""
    base_urls = {
        "nasa": [
            "https://earthobservatory.nasa.gov/images",
            "https://earthobservatory.nasa.gov/world-of-change"
        ],
        "un": [
            "https://press.un.org/en",
            "https://news.un.org/en/news/region/africa"
        ],
        "wfp": [
            "https://www.wfp.org/news"
        ],
        "worldbank": [
            "https://www.worldbank.org/en/news/all"
        ]
    }
    return base_urls.get(source, [])

