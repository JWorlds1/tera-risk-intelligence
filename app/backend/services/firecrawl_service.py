"""
FireCrawl Service for Dynamic Web Crawling
Real-time news and report ingestion with geographic extraction
"""
import asyncio
import httpx
import h3
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from loguru import logger

FIRECRAWL_API = "https://api.firecrawl.dev/v1"

@dataclass
class CrawlResult:
    url: str
    title: str
    content: str
    markdown: str
    locations: List[Dict[str, Any]]
    topics: List[str]
    published_at: Optional[datetime] = None


class FireCrawlService:
    """
    Intelligent web crawling with:
    - Geographic entity extraction
    - Topic classification
    - H3 cell mapping
    """
    
    # Priority crawl sources
    PRIORITY_SOURCES = {
        "reliefweb": {
            "base_url": "https://reliefweb.int/updates",
            "type": "humanitarian",
            "priority": 10
        },
        "acled": {
            "base_url": "https://acleddata.com/data-export-tool/",
            "type": "conflict",
            "priority": 9
        },
        "crisis_group": {
            "base_url": "https://www.crisisgroup.org/",
            "type": "analysis",
            "priority": 8
        },
        "carbon_brief": {
            "base_url": "https://www.carbonbrief.org/",
            "type": "climate",
            "priority": 7
        }
    }
    
    # Topic keywords for classification
    TOPIC_KEYWORDS = {
        "climate": ["climate", "warming", "temperature", "carbon", "emissions", "greenhouse", "ipcc"],
        "conflict": ["war", "conflict", "attack", "military", "violence", "armed", "battle"],
        "disaster": ["flood", "earthquake", "hurricane", "drought", "wildfire", "tsunami", "cyclone"],
        "health": ["disease", "pandemic", "outbreak", "health", "mortality", "epidemic", "covid"],
        "migration": ["refugee", "migrant", "displacement", "asylum", "idp", "exodus"],
        "food_security": ["famine", "hunger", "food", "crop", "agriculture", "malnutrition"],
        "water": ["water", "groundwater", "irrigation", "aquifer", "scarcity"],
        "governance": ["election", "corruption", "democracy", "protest", "coup", "government"],
    }
    
    # Known locations for quick extraction
    KNOWN_LOCATIONS = {
        "gaza": {"lat": 31.5, "lon": 34.47},
        "ukraine": {"lat": 48.38, "lon": 31.17},
        "kyiv": {"lat": 50.45, "lon": 30.52},
        "sudan": {"lat": 12.86, "lon": 30.22},
        "darfur": {"lat": 13.5, "lon": 25.0},
        "yemen": {"lat": 15.55, "lon": 48.52},
        "syria": {"lat": 34.80, "lon": 39.0},
        "ethiopia": {"lat": 9.15, "lon": 40.49},
        "somalia": {"lat": 5.15, "lon": 46.2},
        "myanmar": {"lat": 21.91, "lon": 95.96},
        "haiti": {"lat": 18.97, "lon": -72.29},
        "afghanistan": {"lat": 33.94, "lon": 67.71},
        "iraq": {"lat": 33.22, "lon": 43.68},
        "libya": {"lat": 26.34, "lon": 17.23},
        "mali": {"lat": 17.57, "lon": -4.0},
        "niger": {"lat": 17.61, "lon": 8.08},
        "burkina faso": {"lat": 12.24, "lon": -1.56},
        "bangladesh": {"lat": 23.69, "lon": 90.36},
        "pakistan": {"lat": 30.38, "lon": 69.35},
        "indonesia": {"lat": -0.79, "lon": 113.92},
        "philippines": {"lat": 12.88, "lon": 121.77},
    }
    
    def __init__(self, api_key: str = None, geocoder=None):
        self.api_key = api_key
        self.geocoder = geocoder
        self.headers = {}
        if api_key:
            self.headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
    
    async def crawl_url(self, url: str) -> CrawlResult:
        """Crawl a single URL and extract content"""
        if not self.api_key:
            # Fallback to simple HTTP fetch
            return await self._simple_crawl(url)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{FIRECRAWL_API}/scrape",
                headers=self.headers,
                json={
                    "url": url,
                    "formats": ["markdown", "html"],
                    "onlyMainContent": True
                }
            )
            data = response.json()
        
        content = data.get("data", {})
        markdown = content.get("markdown", "")
        title = content.get("metadata", {}).get("title", "")
        
        locations = self._extract_locations(markdown)
        topics = self._classify_topics(markdown)
        
        return CrawlResult(
            url=url,
            title=title,
            content=content.get("html", ""),
            markdown=markdown,
            locations=locations,
            topics=topics,
            published_at=self._extract_date(content)
        )
    
    async def _simple_crawl(self, url: str) -> CrawlResult:
        """Simple crawl without FireCrawl API"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, follow_redirects=True)
            html = response.text
        
        # Basic extraction
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        
        title = soup.title.string if soup.title else ""
        
        # Remove scripts and styles
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        
        text = soup.get_text(separator=" ", strip=True)
        
        locations = self._extract_locations(text)
        topics = self._classify_topics(text)
        
        return CrawlResult(
            url=url,
            title=title,
            content=html,
            markdown=text[:10000],
            locations=locations,
            topics=topics
        )
    
    def _extract_locations(self, text: str) -> List[Dict[str, Any]]:
        """Extract geographic locations from text"""
        locations = []
        text_lower = text.lower()
        
        for name, coords in self.KNOWN_LOCATIONS.items():
            if name in text_lower:
                h3_index = h3.geo_to_h3(coords["lat"], coords["lon"], 7)
                locations.append({
                    "name": name.title(),
                    "lat": coords["lat"],
                    "lon": coords["lon"],
                    "h3_index": h3_index
                })
        
        return locations
    
    def _classify_topics(self, text: str) -> List[str]:
        """Classify text into topics"""
        topics = []
        text_lower = text.lower()
        
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in text_lower)
            if count >= 2:  # At least 2 keyword matches
                topics.append(topic)
        
        return topics
    
    def _extract_date(self, content: dict) -> Optional[datetime]:
        """Extract publication date"""
        metadata = content.get("metadata", {})
        date_str = metadata.get("publishedTime") or metadata.get("date")
        if date_str:
            try:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                pass
        return None
    
    async def crawl_priority_sources(self) -> List[CrawlResult]:
        """Crawl all priority sources"""
        results = []
        for name, config in self.PRIORITY_SOURCES.items():
            try:
                logger.info(f"Crawling {name}: {config['base_url']}")
                result = await self.crawl_url(config['base_url'])
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to crawl {name}: {e}")
        return results


# Convenience function
async def quick_crawl(url: str) -> dict:
    """Quick crawl a URL without API key"""
    service = FireCrawlService()
    result = await service.crawl_url(url)
    return asdict(result)
