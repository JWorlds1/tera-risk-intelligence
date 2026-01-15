"""
GDELT Conflict Service
Real-time conflict data from GDELT Project (Global Database of Events, Language, and Tone)
Free API, no registration required.
"""

import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from loguru import logger
import pandas as pd
from io import StringIO

@dataclass
class GDELTEvent:
    event_id: str
    date: str
    lat: float
    lon: float
    event_type: str
    goldstein_scale: float  # -10 (conflict) to +10 (cooperation)
    num_mentions: int
    avg_tone: float
    actor1: str
    actor2: str
    source_url: str

class GDELTService:
    """
    GDELT provides real-time conflict/event data updated every 15 minutes.
    """
    
    def __init__(self):
        self.base_url = "http://data.gdeltproject.org/gdeltv2"
        self.gkg_url = "http://data.gdeltproject.org/gdeltv2"
        self.api_url = "https://api.gdeltproject.org/api/v2/doc/doc"
        
    async def get_events_near_location(
        self, 
        lat: float, 
        lon: float, 
        radius_km: float = 100,
        days_back: int = 30
    ) -> List[GDELTEvent]:
        """
        Fetch GDELT events near a specific location.
        Uses the GDELT DOC 2.0 API for geo-filtered queries.
        """
        logger.info(f"🌍 GDELT: Fetching events near ({lat}, {lon}) within {radius_km}km")
        
        # Build query for GDELT DOC 2.0 API
        query = f"sourcelang:eng near:{lat},{lon},{radius_km}km"
        
        params = {
            "query": query,
            "mode": "artlist",
            "maxrecords": "100",
            "format": "json",
            "timespan": f"{days_back}d"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(self.api_url, params=params)
                
                if response.status_code != 200:
                    logger.warning(f"GDELT API returned {response.status_code}")
                    return []
                
                data = response.json()
                articles = data.get("articles", [])
                
                events = []
                for article in articles[:50]:  # Limit to 50
                    # Extract tone/sentiment
                    tone = article.get("tone", 0)
                    
                    events.append(GDELTEvent(
                        event_id=article.get("url", "")[:32],
                        date=article.get("seendate", ""),
                        lat=lat,  # Approximate
                        lon=lon,  # Approximate  
                        event_type=article.get("domain", "news"),
                        goldstein_scale=-abs(tone) if tone < 0 else 0,
                        num_mentions=1,
                        avg_tone=tone,
                        actor1=article.get("socialimage", ""),
                        actor2="",
                        source_url=article.get("url", "")
                    ))
                
                logger.info(f"📊 GDELT: Found {len(events)} events")
                return events
                
        except Exception as e:
            logger.error(f"GDELT API error: {e}")
            return []
    
    async def get_conflict_intensity(
        self, 
        lat: float, 
        lon: float, 
        country: str,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate conflict intensity score for a location.
        Returns normalized 0-1 score with metadata.
        """
        events = await self.get_events_near_location(lat, lon, radius_km=150, days_back=days_back)
        
        if not events:
            return {
                "score": 0.05,
                "event_count": 0,
                "avg_tone": 0,
                "source": "GDELT (no events)",
                "confidence": "low"
            }
        
        # Calculate metrics
        total_events = len(events)
        avg_tone = sum(e.avg_tone for e in events) / total_events if events else 0
        negative_events = sum(1 for e in events if e.avg_tone < -3)
        
        # Normalize to 0-1 score
        # More negative events + more negative tone = higher conflict
        base_score = min(1.0, total_events / 100)  # Max at 100 events
        tone_factor = max(0, min(1, (-avg_tone + 5) / 10))  # -5 to +5 tone -> 0 to 1
        
        conflict_score = (base_score * 0.6 + tone_factor * 0.4)
        
        return {
            "score": round(conflict_score, 3),
            "event_count": total_events,
            "negative_events": negative_events,
            "avg_tone": round(avg_tone, 2),
            "source": f"GDELT DOC 2.0 ({days_back}d)",
            "confidence": "high" if total_events > 20 else "medium" if total_events > 5 else "low"
        }
    
    async def get_trending_themes(self, country: str) -> List[str]:
        """
        Get trending themes/topics for a country.
        """
        query = f"sourcecountry:{country.lower()[:2]}"
        
        params = {
            "query": query,
            "mode": "timelinetone",
            "format": "json",
            "timespan": "7d"
        }
        
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(self.api_url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("timeline", [])[:10]
        except:
            pass
        
        return []

# Singleton instance
gdelt_service = GDELTService()
