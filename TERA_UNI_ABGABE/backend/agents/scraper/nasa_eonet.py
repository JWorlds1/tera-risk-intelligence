"""
NASA EONET (Earth Observatory Natural Event Tracker) Scraper
Real-time natural disaster events from NASA
"""
import asyncio
import httpx
import h3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger
import asyncpg


EONET_API_BASE = "https://eonet.gsfc.nasa.gov/api/v3"

# Event categories mapping to risk types
EVENT_CATEGORIES = {
    "wildfires": {"climate_risk": 0.8, "conflict_risk": 0.2},
    "severeStorms": {"climate_risk": 0.9, "conflict_risk": 0.1},
    "volcanoes": {"climate_risk": 0.7, "conflict_risk": 0.1},
    "floods": {"climate_risk": 0.85, "conflict_risk": 0.3},
    "drought": {"climate_risk": 0.9, "conflict_risk": 0.6},
    "earthquakes": {"climate_risk": 0.6, "conflict_risk": 0.2},
    "landslides": {"climate_risk": 0.7, "conflict_risk": 0.1},
    "snow": {"climate_risk": 0.5, "conflict_risk": 0.1},
    "seaLakeIce": {"climate_risk": 0.6, "conflict_risk": 0.0},
    "dustHaze": {"climate_risk": 0.4, "conflict_risk": 0.3},
}


@dataclass
class NASAEvent:
    id: str
    title: str
    category: str
    lat: float
    lon: float
    date: datetime
    source_url: str
    magnitude: Optional[float] = None
    

class NASAEONETScraper:
    def __init__(self, db_pool: asyncpg.Pool = None):
        self.db_pool = db_pool
        self.client = None
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        return self
    
    async def __aexit__(self, *args):
        if self.client:
            await self.client.aclose()
    
    async def fetch_events(
        self, 
        days: int = 30,
        category: str = None,
        status: str = "open"
    ) -> List[NASAEvent]:
        """Fetch recent events from NASA EONET"""
        params = {
            "days": days,
            "status": status,
        }
        if category:
            params["category"] = category
        
        url = f"{EONET_API_BASE}/events"
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        events = []
        for event in data.get("events", []):
            # Get latest geometry
            geometry = event.get("geometry", [])
            if not geometry:
                continue
            
            latest_geo = geometry[-1]  # Most recent location
            coords = latest_geo.get("coordinates", [])
            if len(coords) < 2:
                continue
            
            # Get category
            categories = event.get("categories", [])
            cat_id = categories[0]["id"] if categories else "unknown"
            
            # Get source URL
            sources = event.get("sources", [])
            source_url = sources[0]["url"] if sources else ""
            
            events.append(NASAEvent(
                id=event["id"],
                title=event["title"],
                category=cat_id,
                lon=coords[0],
                lat=coords[1],
                date=datetime.fromisoformat(latest_geo["date"].replace("Z", "+00:00")),
                source_url=source_url,
                magnitude=latest_geo.get("magnitudeValue")
            ))
        
        logger.info(f"Fetched {len(events)} NASA EONET events")
        return events
    
    async def fetch_all_categories(self) -> Dict[str, List[NASAEvent]]:
        """Fetch events from all categories"""
        all_events = {}
        
        for category in EVENT_CATEGORIES.keys():
            try:
                events = await self.fetch_events(category=category, days=60)
                all_events[category] = events
                await asyncio.sleep(0.5)  # Rate limiting
            except Exception as e:
                logger.error(f"Error fetching {category}: {e}")
                all_events[category] = []
        
        return all_events
    
    async def store_events(self, events: List[NASAEvent]):
        """Store events in database and update H3 cell risks"""
        if not self.db_pool:
            logger.warning("No database pool configured")
            return
        
        async with self.db_pool.acquire() as conn:
            for event in events:
                # Store event
                await conn.execute("""
                    INSERT INTO nasa_events (
                        event_id, title, category, lat, lon, 
                        event_date, source_url, magnitude, geom
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8,
                        ST_SetSRID(ST_MakePoint($5, $4), 4326)
                    )
                    ON CONFLICT (event_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        event_date = EXCLUDED.event_date
                """, event.id, event.title, event.category, event.lat, event.lon,
                    event.date, event.source_url, event.magnitude)
                
                # Update nearby H3 cells
                h3_index = h3.geo_to_h3(event.lat, event.lon, 7)
                risk_factors = EVENT_CATEGORIES.get(event.category, {"climate_risk": 0.5, "conflict_risk": 0.2})
                
                # Update center cell and neighbors
                affected_cells = h3.k_ring(h3_index, 2)  # Center + 2 rings
                
                for i, cell in enumerate(affected_cells):
                    # Risk decreases with distance
                    distance_factor = 1.0 if i == 0 else 0.7 if i <= 6 else 0.4
                    
                    climate_delta = risk_factors["climate_risk"] * distance_factor * 20
                    conflict_delta = risk_factors["conflict_risk"] * distance_factor * 20
                    
                    await conn.execute("""
                        INSERT INTO h3_cells (h3_index, resolution, center_lat, center_lon, 
                                            climate_risk, conflict_risk, last_updated)
                        VALUES ($1, 7, $2, $3, $4, $5, NOW())
                        ON CONFLICT (h3_index) DO UPDATE SET
                            climate_risk = LEAST(100, h3_cells.climate_risk + $4),
                            conflict_risk = LEAST(100, h3_cells.conflict_risk + $5),
                            last_updated = NOW()
                    """, cell, *h3.h3_to_geo(cell), climate_delta, conflict_delta)
        
        logger.info(f"Stored {len(events)} events and updated H3 cells")
    
    async def get_events_near_location(self, lat: float, lon: float, radius_km: float = 100) -> List[Dict]:
        """Get stored events near a location"""
        if not self.db_pool:
            return []
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT event_id, title, category, lat, lon, event_date, source_url, magnitude,
                       ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography) / 1000 as distance_km
                FROM nasa_events
                WHERE ST_DWithin(
                    geom::geography,
                    ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography,
                    $3 * 1000
                )
                ORDER BY event_date DESC
                LIMIT 50
            """, lat, lon, radius_km)
            
            return [dict(row) for row in rows]
