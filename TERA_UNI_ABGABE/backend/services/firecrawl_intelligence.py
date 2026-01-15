
"""
TERA Firecrawl Integration v2.0
Nutzt Scrape + Search für Web-Intelligence
"""

import os
import httpx
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger

FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "fc-a0b3b8aa31244c10b0f15b4f2d570ac7")
FIRECRAWL_BASE_URL = "https://api.firecrawl.dev/v1"


class FirecrawlIntelligence:
    """Firecrawl für Web-Intelligence"""
    
    def __init__(self):
        self.api_key = FIRECRAWL_API_KEY
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def research_city_risks(self, city: str, country: str) -> Dict:
        """Recherchiert Risiken für eine Stadt"""
        
        if not self.api_key:
            return {"error": "No API key"}
        
        results = {
            "city": city,
            "country": country,
            "timestamp": datetime.utcnow().isoformat(),
            "climate_data": {},
            "news_data": {},
            "sources": []
        }
        
        # Such-URLs für Klimarisiken
        search_urls = [
            f"https://en.wikipedia.org/wiki/{city.replace( , _)}",
        ]
        
        try:
            # Scrape Wikipedia für Basis-Info
            response = await self.client.post(
                f"{FIRECRAWL_BASE_URL}/scrape",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "url": search_urls[0],
                    "formats": ["markdown"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    markdown = data.get("data", {}).get("markdown", "")
                    # Extrahiere relevante Abschnitte
                    results["climate_data"]["wikipedia"] = markdown[:2000]
                    results["sources"].append(search_urls[0])
                    logger.info(f"✅ Firecrawl: Wikipedia scraped for {city}")
            
        except Exception as e:
            logger.warning(f"Firecrawl error: {e}")
            results["error"] = str(e)
        
        return results
    
    async def close(self):
        await self.client.aclose()


# Singleton
firecrawl_intel = FirecrawlIntelligence()
