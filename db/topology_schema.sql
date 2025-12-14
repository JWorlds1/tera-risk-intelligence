-- =====================================================
-- TERA TOPOGRAPHY DATABASE SCHEMA
-- Solide Grundlage für jeden Punkt auf der Erde
-- =====================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

-- =====================================================
-- LAYER 1: H3 TOPOLOGY (Hexagonal Global Grid)
-- =====================================================
CREATE TABLE IF NOT EXISTS h3_topology (
    h3_index VARCHAR(20) PRIMARY KEY,
    resolution INT NOT NULL,
    center_lat DOUBLE PRECISION,
    center_lon DOUBLE PRECISION,
    geom GEOMETRY(Polygon, 4326),
    
    -- Elevation (SRTM/Copernicus DEM)
    elevation_m REAL,
    slope_deg REAL,
    aspect_deg REAL,
    
    -- Coastal Analysis
    is_coastal BOOLEAN DEFAULT FALSE,
    is_island BOOLEAN DEFAULT FALSE,
    distance_to_coast_km REAL,
    
    -- Administrative
    country_iso3 CHAR(3),
    country_name VARCHAR(100),
    admin1_name VARCHAR(255),
    admin2_name VARCHAR(255),
    
    -- Climate Zone (Köppen-Geiger)
    climate_zone CHAR(3),
    climate_description VARCHAR(100),
    
    -- Land Cover (ESA WorldCover)
    land_cover_class VARCHAR(50),
    urban_density REAL,
    forest_pct REAL,
    water_pct REAL,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_h3_topology_geom ON h3_topology USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_h3_topology_country ON h3_topology (country_iso3);
CREATE INDEX IF NOT EXISTS idx_h3_topology_climate ON h3_topology (climate_zone);

-- =====================================================
-- LAYER 2: DEMOGRAPHICS & ECONOMICS
-- =====================================================
CREATE TABLE IF NOT EXISTS h3_demographics (
    h3_index VARCHAR(20) PRIMARY KEY REFERENCES h3_topology(h3_index),
    
    -- Population (WorldPop)
    population INT,
    population_density REAL,
    urban_population_pct REAL,
    
    -- Age structure
    median_age REAL,
    youth_pct REAL,  -- 0-14 years
    elderly_pct REAL, -- 65+
    
    -- Economics
    gdp_per_capita_usd REAL,
    poverty_rate REAL,
    gini_coefficient REAL,
    
    -- Night lights (VIIRS)
    nightlight_intensity REAL,
    
    data_year INT,
    source VARCHAR(100),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- LAYER 3: CLIMATE BASELINE
-- =====================================================
CREATE TABLE IF NOT EXISTS h3_climate (
    h3_index VARCHAR(20) PRIMARY KEY REFERENCES h3_topology(h3_index),
    
    -- Temperature
    mean_temp_c REAL,
    temp_anomaly_c REAL,
    max_temp_c REAL,
    min_temp_c REAL,
    heatwave_days_per_year REAL,
    
    -- Precipitation
    annual_precip_mm REAL,
    precip_variability REAL,
    wet_days_per_year REAL,
    drought_months_per_decade REAL,
    
    -- Sea Level (coastal cells only)
    sea_level_rise_mm REAL,
    subsidence_mm_per_year REAL,
    flood_return_period_years REAL,
    storm_surge_risk REAL,
    
    -- IPCC SSP Projections (2050)
    ssp126_temp_anomaly REAL,
    ssp245_temp_anomaly REAL,
    ssp370_temp_anomaly REAL,
    ssp585_temp_anomaly REAL,
    
    ssp126_risk_score REAL,
    ssp245_risk_score REAL,
    ssp370_risk_score REAL,
    ssp585_risk_score REAL,
    
    data_year INT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- LAYER 4: CONFLICT BASELINE
-- =====================================================
CREATE TABLE IF NOT EXISTS h3_conflict (
    h3_index VARCHAR(20) PRIMARY KEY REFERENCES h3_topology(h3_index),
    
    -- ACLED Historical (5 years)
    total_events INT DEFAULT 0,
    total_fatalities INT DEFAULT 0,
    events_per_year REAL DEFAULT 0,
    
    -- Event type breakdown
    battles_count INT DEFAULT 0,
    violence_civilians_count INT DEFAULT 0,
    riots_protests_count INT DEFAULT 0,
    explosions_count INT DEFAULT 0,
    
    -- Stability indicators
    fragility_index REAL,  -- 0-10
    governance_score REAL, -- 0-100
    
    -- Status
    is_active_conflict BOOLEAN DEFAULT FALSE,
    conflict_intensity VARCHAR(20),  -- none, low, medium, high, war
    
    last_event_date DATE,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- LAYER 5: REAL-TIME EVENTS
-- =====================================================
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(100) UNIQUE,
    source VARCHAR(50) NOT NULL,
    
    -- Location
    h3_index VARCHAR(20),
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    geom GEOMETRY(Point, 4326),
    location_name VARCHAR(255),
    country_iso3 CHAR(3),
    
    -- Event Details
    event_type VARCHAR(50),
    event_subtype VARCHAR(100),
    title TEXT,
    description TEXT,
    severity INT CHECK (severity >= 1 AND severity <= 10),
    
    -- Timing
    event_date TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT NOW(),
    
    -- Source
    source_url TEXT,
    raw_data JSONB,
    
    -- Processing
    processed BOOLEAN DEFAULT FALSE,
    topics TEXT[],
    embedding VECTOR(1536)
);

CREATE INDEX IF NOT EXISTS idx_events_geom ON events USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_events_h3 ON events (h3_index);
CREATE INDEX IF NOT EXISTS idx_events_date ON events (event_date DESC);
CREATE INDEX IF NOT EXISTS idx_events_type ON events (event_type);
CREATE INDEX IF NOT EXISTS idx_events_source ON events (source);

-- =====================================================
-- LAYER 6: CRAWLED CONTENT
-- =====================================================
CREATE TABLE IF NOT EXISTS crawled_articles (
    id SERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    domain VARCHAR(255),
    
    -- Content
    title TEXT,
    content TEXT,
    markdown TEXT,
    published_at TIMESTAMP,
    
    -- Extracted Entities
    locations JSONB,
    topics TEXT[],
    entities JSONB,
    sentiment REAL,
    
    -- H3 Links
    h3_indices TEXT[],
    
    -- Processing
    scraped_at TIMESTAMP DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    embedding VECTOR(1536),
    
    -- Metadata
    source_type VARCHAR(50),
    language CHAR(2),
    word_count INT
);

CREATE INDEX IF NOT EXISTS idx_articles_domain ON crawled_articles (domain);
CREATE INDEX IF NOT EXISTS idx_articles_date ON crawled_articles (published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_topics ON crawled_articles USING GIN (topics);

-- =====================================================
-- LAYER 7: TOPIC MODELING
-- =====================================================
CREATE TABLE IF NOT EXISTS h3_topics (
    h3_index VARCHAR(20),
    topic_id INT,
    topic_name VARCHAR(100),
    score REAL,
    
    keywords TEXT[],
    document_count INT DEFAULT 0,
    last_event_date DATE,
    
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (h3_index, topic_id)
);

-- Predefined global topics
CREATE TABLE IF NOT EXISTS topics (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE,
    description TEXT,
    keywords TEXT[],
    category VARCHAR(50)
);

INSERT INTO topics (name, description, keywords, category) VALUES
('climate_change', 'Climate change and global warming', ARRAY['warming', 'emissions', 'temperature', 'carbon', 'greenhouse', 'ipcc'], 'environmental'),
('conflict', 'Armed conflict and violence', ARRAY['war', 'violence', 'military', 'attack', 'armed', 'battle'], 'security'),
('natural_disaster', 'Natural disasters and extreme events', ARRAY['flood', 'earthquake', 'hurricane', 'drought', 'wildfire', 'tsunami'], 'environmental'),
('health_crisis', 'Public health emergencies', ARRAY['disease', 'pandemic', 'outbreak', 'mortality', 'epidemic'], 'health'),
('displacement', 'Migration and displacement', ARRAY['refugees', 'displacement', 'asylum', 'migration', 'idp'], 'humanitarian'),
('food_security', 'Food security and agriculture', ARRAY['famine', 'hunger', 'crops', 'agriculture', 'malnutrition'], 'humanitarian'),
('water_crisis', 'Water scarcity and management', ARRAY['drought', 'flooding', 'groundwater', 'irrigation', 'scarcity'], 'environmental'),
('energy', 'Energy and resources', ARRAY['oil', 'gas', 'renewable', 'electricity', 'nuclear'], 'economic'),
('governance', 'Political governance and stability', ARRAY['election', 'corruption', 'democracy', 'protest', 'coup'], 'political'),
('economic_crisis', 'Economic instability', ARRAY['gdp', 'inflation', 'trade', 'unemployment', 'recession'], 'economic')
ON CONFLICT (name) DO NOTHING;

-- =====================================================
-- LAYER 8: CRAWL MANAGEMENT
-- =====================================================
CREATE TABLE IF NOT EXISTS crawl_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    base_url TEXT NOT NULL,
    source_type VARCHAR(50),
    
    -- Schedule
    frequency_minutes INT DEFAULT 60,
    priority INT DEFAULT 5,
    enabled BOOLEAN DEFAULT TRUE,
    
    -- Config
    crawl_depth INT DEFAULT 2,
    selectors JSONB,
    
    -- Stats
    last_crawl_at TIMESTAMP,
    articles_count INT DEFAULT 0,
    success_rate REAL DEFAULT 1.0,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert priority sources
INSERT INTO crawl_sources (name, base_url, source_type, frequency_minutes, priority) VALUES
('ReliefWeb', 'https://reliefweb.int/updates', 'humanitarian', 60, 10),
('ACLED', 'https://acleddata.com/data-export-tool/', 'conflict', 360, 9),
('Crisis Group', 'https://www.crisisgroup.org/', 'analysis', 720, 8),
('UN News', 'https://news.un.org/en/', 'news', 120, 8),
('NASA Earth', 'https://earthobservatory.nasa.gov/', 'environmental', 240, 7),
('Carbon Brief', 'https://www.carbonbrief.org/', 'climate', 360, 6),
('OCHA', 'https://www.unocha.org/', 'humanitarian', 240, 9),
('USGS Earthquakes', 'https://earthquake.usgs.gov/', 'disaster', 15, 10)
ON CONFLICT DO NOTHING;

-- Crawl queue
CREATE TABLE IF NOT EXISTS crawl_queue (
    id SERIAL PRIMARY KEY,
    source_id INT REFERENCES crawl_sources(id),
    url TEXT NOT NULL,
    priority INT DEFAULT 5,
    status VARCHAR(20) DEFAULT 'pending',
    
    scheduled_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    error_message TEXT,
    retry_count INT DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_crawl_queue_status ON crawl_queue (status, priority DESC);

-- =====================================================
-- VIEWS
-- =====================================================

-- Combined risk view per H3 cell
CREATE OR REPLACE VIEW h3_risk_overview AS
SELECT 
    t.h3_index,
    t.country_name,
    t.climate_zone,
    
    -- Climate risk
    COALESCE(c.ssp245_risk_score, 0) as climate_risk,
    c.temp_anomaly_c,
    c.sea_level_rise_mm,
    
    -- Conflict risk
    COALESCE(cf.fragility_index, 0) as conflict_risk,
    cf.is_active_conflict,
    cf.total_events as conflict_events_5y,
    
    -- Population exposure
    d.population,
    d.population_density,
    
    -- Combined risk score
    (COALESCE(c.ssp245_risk_score, 0) * 0.5 + COALESCE(cf.fragility_index, 0) * 0.1 * 0.5) as combined_risk
    
FROM h3_topology t
LEFT JOIN h3_climate c ON t.h3_index = c.h3_index
LEFT JOIN h3_conflict cf ON t.h3_index = cf.h3_index
LEFT JOIN h3_demographics d ON t.h3_index = d.h3_index;

-- Recent events summary
CREATE OR REPLACE VIEW recent_events_summary AS
SELECT 
    event_type,
    COUNT(*) as count,
    AVG(severity) as avg_severity,
    MAX(event_date) as latest,
    array_agg(DISTINCT country_iso3) as countries
FROM events
WHERE event_date > NOW() - INTERVAL '30 days'
GROUP BY event_type
ORDER BY count DESC;

