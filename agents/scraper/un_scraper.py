"""
UN Press Scraper
"""
from typing import Optional, List
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper, ScrapedArticle


class UNScraper(BaseScraper):
    """Scraper for UN Press releases"""
    
    SOURCE = "UN Press"
    BASE_URL = "https://press.un.org"
    
    def get_urls(self) -> List[str]:
        return [
            f"{self.BASE_URL}/en/content/security-council",
            f"{self.BASE_URL}/en/content/secretary-general",
        ]
    
    async def parse(self, html: str, url: str) -> Optional[ScrapedArticle]:
        soup = BeautifulSoup(html, 'lxml')
        
        title_elem = soup.find('h1')
        title = title_elem.get_text(strip=True) if title_elem else "UN Press"
        
        content_elem = soup.find('div', class_='field-body') or soup.find('article')
        content = content_elem.get_text(strip=True) if content_elem else ""
        
        return ScrapedArticle(
            url=url,
            title=title,
            content=content[:5000],
            source=self.SOURCE,
            metadata={"category": "political"}
        )
