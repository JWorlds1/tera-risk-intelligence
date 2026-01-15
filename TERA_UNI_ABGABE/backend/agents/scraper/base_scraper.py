"""
TERA Scraper Agent - Base Class
Async web scraper with rate limiting and compliance
"""
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Dict, Any

import aiohttp
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential


class ScrapedArticle(BaseModel):
    """Structured article data from scraping"""
    url: str
    title: str
    content: str
    published_date: Optional[datetime] = None
    source: str
    raw_html: Optional[str] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseScraper(ABC):
    """Base scraper with async support and rate limiting"""
    
    def __init__(
        self,
        rate_limit: float = 1.0,
        max_concurrent: int = 3,
        timeout: int = 30
    ):
        self.rate_limit = rate_limit
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self._last_request = 0.0
        
    async def _rate_limit_wait(self):
        """Ensure rate limiting between requests"""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request
        if elapsed < self.rate_limit:
            await asyncio.sleep(self.rate_limit - elapsed)
        self._last_request = asyncio.get_event_loop().time()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def fetch_url(self, url: str) -> Optional[str]:
        """Fetch URL content with retries"""
        async with self.semaphore:
            await self._rate_limit_wait()
            
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "User-Agent": "TERA-Research-Bot/1.0 (Academic Research)"
                    }
                    async with session.get(
                        url, 
                        headers=headers, 
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        if response.status == 200:
                            return await response.text()
                        else:
                            logger.warning(f"HTTP {response.status} for {url}")
                            return None
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                raise
    
    @abstractmethod
    async def parse(self, html: str, url: str) -> Optional[ScrapedArticle]:
        """Parse HTML into structured article"""
        pass
    
    @abstractmethod
    def get_urls(self) -> List[str]:
        """Get list of URLs to scrape"""
        pass
    
    async def scrape_all(self) -> List[ScrapedArticle]:
        """Scrape all URLs and return articles"""
        urls = self.get_urls()
        logger.info(f"Scraping {len(urls)} URLs from {self.__class__.__name__}")
        
        articles = []
        for url in urls:
            try:
                html = await self.fetch_url(url)
                if html:
                    article = await self.parse(html, url)
                    if article:
                        articles.append(article)
                        logger.info(f"✓ Scraped: {article.title[:50]}...")
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")
        
        return articles
