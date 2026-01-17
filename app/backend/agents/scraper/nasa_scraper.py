"""
NASA Earth Observatory Scraper
"""
from typing import Optional, List
from datetime import datetime
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper, ScrapedArticle


class NASAScraper(BaseScraper):
    """Scraper for NASA Earth Observatory"""
    
    SOURCE = "NASA Earth Observatory"
    BASE_URL = "https://earthobservatory.nasa.gov"
    
    def get_urls(self) -> List[str]:
        """Get NASA article URLs"""
        return [
            f"{self.BASE_URL}/images",
            f"{self.BASE_URL}/global-maps",
            f"{self.BASE_URL}/features",
        ]
    
    async def parse(self, html: str, url: str) -> Optional[ScrapedArticle]:
        """Parse NASA page"""
        soup = BeautifulSoup(html, 'lxml')
        
        title_elem = soup.find('h1') or soup.find('title')
        title = title_elem.get_text(strip=True) if title_elem else "Unknown"
        
        # Find main content
        content_elem = soup.find('div', class_='caption') or soup.find('article')
        content = content_elem.get_text(strip=True) if content_elem else ""
        
        return ScrapedArticle(
            url=url,
            title=title,
            content=content[:5000],
            source=self.SOURCE,
            metadata={"category": "environmental"}
        )
