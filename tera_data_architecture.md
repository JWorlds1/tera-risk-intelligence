# TERA Data Architecture - Geospatial Knowledge Base

## 🎯 Ziel
Aufbau einer soliden topographischen Datenbank mit:
- **Statische Grundlage**: Jeder Punkt auf der Erde hat kontextuelle Basisdaten
- **Thematische Layer**: Topic Modeling für Klima, Konflikte, Wirtschaft
- **Dynamische Updates**: Echtzeit-Crawling mit FireCrawl

---

## 📊 Datenquellen-Übersicht

### Layer 1: Statische Topographie (einmalig laden)

| Datenquelle | URL | Format | Lizenz |
|-------------|-----|--------|--------|
| Natural Earth | https://www.naturalearthdata.com/ | GeoJSON/SHP | Public Domain |
| SRTM Elevation | https://dwtkns.com/srtm30m/ | GeoTIFF | Public Domain |
| Copernicus DEM | https://spacedata.copernicus.eu/explore-more/news-archive/-/asset_publisher/Ye8egYeRPg0b/content/cop-dem-glo-30-available | GeoTIFF | Open License |
| OpenStreetMap | https://planet.openstreetmap.org/ | PBF | ODbL |
| GADM Boundaries | https://gadm.org/download_world.html | GeoJSON | Free |
| Köppen Climate | http://www.gloh2o.org/koppen/ | GeoTIFF | CC BY |

### Layer 2: Thematische Daten (periodisch aktualisieren)

| Datenquelle | URL | Aktualisierung | API |
|-------------|-----|----------------|-----|
| WorldPop Population | https://www.worldpop.org/ | Jährlich | REST |
| ACLED Conflicts | https://acleddata.com/data-export-tool/ | Wöchentlich | REST |
| World Bank | https://data.worldbank.org/ | Jährlich | REST |
| NASA Night Lights | https://earthobservatory.nasa.gov/features/NightLights | Monatlich | Download |
| FAO Food Prices | https://fpma.apps.fao.org/giews/food-prices/ | Wöchentlich | REST |

### Layer 3: Echtzeit-Events (kontinuierlich crawlen)

| Datenquelle | URL | Frequenz | API Type |
|-------------|-----|----------|----------|
| NASA EONET | https://eonet.gsfc.nasa.gov/api/v3/events | Echtzeit | REST |
| GDELT | https://api.gdeltproject.org/api/v2/ | 15 min | REST |
| ReliefWeb | https://api.reliefweb.int/v1/ | Stündlich | REST |
| USGS Earthquakes | https://earthquake.usgs.gov/fdsnws/event/1/query | Echtzeit | REST |
| Global Flood Monitor | https://www.globalfloodmonitor.org/ | Täglich | REST |

---

## 🗄️ PostgreSQL Schema

```sql
-- =====================================================
-- LAYER 1: STATIC TOPOGRAPHY
-- =====================================================

-- H3 Hexagonal Grid (Resolution 5-9)
CREATE TABLE h3_topology (
    h3_index VARCHAR(20) PRIMARY KEY,
    resolution INT NOT NULL,
    center_lat DOUBLE PRECISION,
    center_lon DOUBLE PRECISION,
    geom GEOMETRY(Polygon, 4326),
    
    -- Elevation
    elevation_m REAL,
    slope_deg REAL,
    aspect_deg REAL,
    
    -- Geography
    is_coastal BOOLEAN DEFAULT FALSE,
    is_island BOOLEAN DEFAULT FALSE,
    distance_to_coast_km REAL,
    
    -- Administrative
    country_iso3 CHAR(3),
    admin1_name VARCHAR(255),
    admin2_name VARCHAR(255),
    
    -- Climate (Köppen-Geiger)
    climate_zone CHAR(3),  -- e.g., 'Af', 'Cfb', 'BWh'
    climate_description VARCHAR(100),
    
    -- Land Cover
    land_cover_class VARCHAR(50),
    urban_density REAL,  -- 0-1
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_h3_topology_geom ON h3_topology USING GIST (geom);
CREATE INDEX idx_h3_topology_country ON h3_topology (country_iso3);

-- =====================================================
-- LAYER 2: THEMATIC LAYERS
-- =====================================================

-- Population & Demographics
CREATE TABLE h3_demographics (
    h3_index VARCHAR(20) PRIMARY KEY REFERENCES h3_topology(h3_index),
    population INT,
    population_density REAL,  -- per km²
    urban_population_pct REAL,
    median_age REAL,
    data_year INT,
    source VARCHAR(100),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Economic Indicators
CREATE TABLE h3_economics (
    h3_index VARCHAR(20) PRIMARY KEY REFERENCES h3_topology(h3_index),
    gdp_per_capita_usd REAL,
    nightlight_intensity REAL,  -- 0-63 (VIIRS)
    poverty_rate REAL,
    gini_coefficient REAL,
    data_year INT,
    source VARCHAR(100),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Climate Risk Baseline
CREATE TABLE h3_climate_baseline (
    h3_index VARCHAR(20) PRIMARY KEY REFERENCES h3_topology(h3_index),
    
    -- Temperature
    mean_temp_c REAL,
    temp_anomaly_c REAL,  -- vs 1950-1980 baseline
    heatwave_days_per_year REAL,
    
    -- Precipitation
    annual_precip_mm REAL,
    precip_variability REAL,
    drought_frequency REAL,
    
    -- Sea Level
    sea_level_rise_mm REAL,
    subsidence_mm_per_year REAL,
    flood_return_period_years REAL,
    
    -- IPCC Scenario Projections (2050)
    ssp126_risk REAL,
    ssp245_risk REAL,
    ssp370_risk REAL,
    ssp585_risk REAL,
    
    data_year INT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Conflict Baseline
CREATE TABLE h3_conflict_baseline (
    h3_index VARCHAR(20) PRIMARY KEY REFERENCES h3_topology(h3_index),
    
    -- Historical (last 5 years)
    total_events INT,
    fatalities INT,
    events_per_year REAL,
    
    -- Type breakdown
    battles_pct REAL,
    violence_against_civilians_pct REAL,
    riots_protests_pct REAL,
    
    -- Stability
    fragility_index REAL,  -- 0-10
    governance_score REAL,  -- 0-100
    
    last_event_date DATE,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- LAYER 3: DYNAMIC EVENTS
-- =====================================================

-- Real-time Events
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(100) UNIQUE,
    source VARCHAR(50) NOT NULL,  -- 'nasa_eonet', 'acled', 'gdelt', 'reliefweb'
    
    -- Location
    h3_index VARCHAR(20) REFERENCES h3_topology(h3_index),
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    geom GEOMETRY(Point, 4326),
    
    -- Event Details
    event_type VARCHAR(50),
    title TEXT,
    description TEXT,
    severity INT,  -- 1-10
    
    -- Timing
    event_date TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT NOW(),
    
    -- Source Data
    source_url TEXT,
    raw_data JSONB,
    
    -- Processing
    processed BOOLEAN DEFAULT FALSE,
    embedding VECTOR(1536)  -- for semantic search
);

CREATE INDEX idx_events_geom ON events USING GIST (geom);
CREATE INDEX idx_events_h3 ON events (h3_index);
CREATE INDEX idx_events_date ON events (event_date DESC);
CREATE INDEX idx_events_source ON events (source, event_type);

-- Crawled Articles
CREATE TABLE crawled_articles (
    id SERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    domain VARCHAR(255),
    
    -- Content
    title TEXT,
    content TEXT,
    published_at TIMESTAMP,
    
    -- Extracted Entities
    locations JSONB,  -- [{name, lat, lon, h3_index}]
    topics JSONB,     -- [{topic, score}]
    entities JSONB,   -- [{type, name, salience}]
    sentiment REAL,   -- -1 to 1
    
    -- Processing
    scraped_at TIMESTAMP DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    embedding VECTOR(1536),
    
    -- Source
    source_type VARCHAR(50),  -- 'news', 'report', 'social', 'scientific'
    language CHAR(2)
);

CREATE INDEX idx_articles_domain ON crawled_articles (domain);
CREATE INDEX idx_articles_date ON crawled_articles (published_at DESC);

-- =====================================================
-- TOPIC MODELING
-- =====================================================

-- Geographic Topics (per H3 cell)
CREATE TABLE h3_topics (
    h3_index VARCHAR(20) REFERENCES h3_topology(h3_index),
    topic_id INT,
    topic_name VARCHAR(100),
    score REAL,  -- 0-1 relevance
    
    -- Topic details
    keywords TEXT[],
    document_count INT,
    
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (h3_index, topic_id)
);

-- Predefined Topics
INSERT INTO h3_topics (h3_index, topic_id, topic_name, keywords) VALUES
('global', 1, 'climate_change', ARRAY['warming', 'emissions', 'temperature', 'carbon']),
('global', 2, 'conflict', ARRAY['war', 'violence', 'military', 'attack']),
('global', 3, 'disaster', ARRAY['flood', 'earthquake', 'hurricane', 'drought']),
('global', 4, 'health', ARRAY['disease', 'pandemic', 'outbreak', 'mortality']),
('global', 5, 'migration', ARRAY['refugees', 'displacement', 'asylum', 'border']),
('global', 6, 'food_security', ARRAY['famine', 'crops', 'agriculture', 'hunger']),
('global', 7, 'water', ARRAY['drought', 'flooding', 'groundwater', 'irrigation']),
('global', 8, 'energy', ARRAY['oil', 'gas', 'renewable', 'electricity']),
('global', 9, 'governance', ARRAY['election', 'corruption', 'democracy', 'protest']),
('global', 10, 'economy', ARRAY['gdp', 'inflation', 'trade', 'unemployment']);

-- =====================================================
-- CRAWL MANAGEMENT
-- =====================================================

-- Crawl Sources (FireCrawl config)
CREATE TABLE crawl_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    base_url TEXT NOT NULL,
    source_type VARCHAR(50),  -- 'news', 'api', 'report', 'social'
    
    -- Crawl Config
    frequency_minutes INT DEFAULT 60,
    priority INT DEFAULT 5,  -- 1-10
    enabled BOOLEAN DEFAULT TRUE,
    
    -- FireCrawl Settings
    crawl_depth INT DEFAULT 2,
    wait_time_ms INT DEFAULT 1000,
    selectors JSONB,  -- CSS selectors for content
    
    -- Stats
    last_crawl_at TIMESTAMP,
    articles_count INT DEFAULT 0,
    error_count INT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert priority sources
INSERT INTO crawl_sources (name, base_url, source_type, frequency_minutes, priority) VALUES
('ReliefWeb', 'https://reliefweb.int/updates', 'report', 60, 10),
('ACLED Dashboard', 'https://acleddata.com/dashboard/', 'data', 360, 9),
('UN News', 'https://news.un.org/en/', 'news', 120, 8),
('NASA Earth', 'https://earthobservatory.nasa.gov/', 'news', 240, 7),
('Crisis Group', 'https://www.crisisgroup.org/', 'report', 720, 8),
('Carbon Brief', 'https://www.carbonbrief.org/', 'news', 360, 6),
('Climate Home', 'https://www.climatechangenews.com/', 'news', 360, 6),
('OCHA', 'https://www.unocha.org/', 'report', 240, 9);

-- Crawl Queue
CREATE TABLE crawl_queue (
    id SERIAL PRIMARY KEY,
    source_id INT REFERENCES crawl_sources(id),
    url TEXT NOT NULL,
    priority INT DEFAULT 5,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, processing, completed, failed
    
    scheduled_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    error_message TEXT,
    retry_count INT DEFAULT 0
);

CREATE INDEX idx_crawl_queue_status ON crawl_queue (status, priority DESC);
```

---

## 🔥 FireCrawl Service Implementation

```python
# backend/services/firecrawl_service.py
"""
FireCrawl Service for Dynamic Web Crawling
Real-time news and report ingestion with geographic extraction
"""
import asyncio
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import h3
from loguru import logger

# FireCrawl API
FIRECRAWL_API = "https://api.firecrawl.dev/v1"

@dataclass
class CrawlResult:
    url: str
    title: str
    content: str
    markdown: str
    locations: List[Dict[str, Any]]
    topics: List[str]
    published_at: Optional[datetime]


class FireCrawlService:
    """
    Intelligent web crawling with:
    - Geographic entity extraction
    - Topic classification
    - H3 cell mapping
    """
    
    def __init__(self, api_key: str, geocoder, topic_model):
        self.api_key = api_key
        self.geocoder = geocoder
        self.topic_model = topic_model
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def crawl_url(self, url: str) -> CrawlResult:
        """Crawl a single URL and extract content"""
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
        
        # Extract content
        content = data.get("data", {})
        markdown = content.get("markdown", "")
        title = content.get("metadata", {}).get("title", "")
        
        # Extract locations
        locations = await self._extract_locations(markdown)
        
        # Classify topics
        topics = await self._classify_topics(markdown)
        
        return CrawlResult(
            url=url,
            title=title,
            content=content.get("html", ""),
            markdown=markdown,
            locations=locations,
            topics=topics,
            published_at=self._extract_date(content)
        )
    
    async def crawl_site(self, base_url: str, max_pages: int = 50) -> List[CrawlResult]:
        """Crawl entire site with FireCrawl"""
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Start crawl job
            response = await client.post(
                f"{FIRECRAWL_API}/crawl",
                headers=self.headers,
                json={
                    "url": base_url,
                    "limit": max_pages,
                    "scrapeOptions": {
                        "formats": ["markdown"],
                        "onlyMainContent": True
                    }
                }
            )
            job = response.json()
            job_id = job.get("id")
            
            # Poll for completion
            while True:
                status_response = await client.get(
                    f"{FIRECRAWL_API}/crawl/{job_id}",
                    headers=self.headers
                )
                status = status_response.json()
                
                if status.get("status") == "completed":
                    break
                elif status.get("status") == "failed":
                    raise Exception(f"Crawl failed: {status.get('error')}")
                
                await asyncio.sleep(5)
            
            # Process results
            results = []
            for page in status.get("data", []):
                result = await self._process_page(page)
                results.append(result)
            
            return results
    
    async def _extract_locations(self, text: str) -> List[Dict[str, Any]]:
        """Extract geographic locations from text"""
        # Use NER or regex for location extraction
        # Then geocode and map to H3
        locations = []
        
        # Example: Use spaCy or similar
        # For now, use simple pattern matching
        import re
        
        # Common city patterns
        city_pattern = r'\b(New York|London|Tokyo|Jakarta|Miami|Cairo|Kyiv|Berlin|Mumbai|Lagos)\b'
        matches = re.findall(city_pattern, text, re.IGNORECASE)
        
        for city in set(matches):
            coords = await self.geocoder.geocode(city)
            if coords:
                h3_index = h3.geo_to_h3(coords['lat'], coords['lon'], 7)
                locations.append({
                    "name": city,
                    "lat": coords['lat'],
                    "lon": coords['lon'],
                    "h3_index": h3_index
                })
        
        return locations
    
    async def _classify_topics(self, text: str) -> List[str]:
        """Classify text into topics"""
        # Use topic model or keyword matching
        topics = []
        
        topic_keywords = {
            "climate": ["climate", "warming", "temperature", "carbon", "emissions"],
            "conflict": ["war", "conflict", "attack", "military", "violence"],
            "disaster": ["flood", "earthquake", "hurricane", "drought", "wildfire"],
            "health": ["disease", "pandemic", "outbreak", "health", "mortality"],
            "migration": ["refugee", "migrant", "displacement", "asylum"],
        }
        
        text_lower = text.lower()
        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords):
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
```

---

## 🚀 Setup Commands

```bash
# 1. Initialize H3 Global Grid (Resolution 5 = ~252k hexagons)
python -m data.init_h3_grid --resolution 5

# 2. Load Static Data
python -m data.load_natural_earth
python -m data.load_koppen_climate
python -m data.load_gadm_boundaries

# 3. Load Thematic Data
python -m data.load_worldpop
python -m data.load_acled --years 2020-2024
python -m data.load_worldbank

# 4. Start Crawlers
celery -A tasks.crawler worker --loglevel=info

# 5. Schedule Periodic Updates
celery -A tasks.crawler beat --loglevel=info
```

---

## 📈 API Endpoints

```
GET  /api/topology/{h3_index}     - Get all data for a cell
GET  /api/topics/{h3_index}       - Get topics for a cell
GET  /api/events?bbox=...         - Get events in bounding box
GET  /api/search?q=...            - Semantic search across content
POST /api/crawl                   - Add URL to crawl queue
GET  /api/crawl/status            - Get crawler status
```






















