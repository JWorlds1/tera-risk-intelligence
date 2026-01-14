-- TERA Database Initialization
-- PostGIS enabled PostgreSQL

-- Enable Extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- TABLES
-- =============================================================================

-- Raw scraped articles
CREATE TABLE IF NOT EXISTS articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source VARCHAR(100) NOT NULL,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    content TEXT,
    summary TEXT,
    publish_date TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'
);

-- Extracted entities from LLM
CREATE TABLE IF NOT EXISTS extracted_entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
    location_name VARCHAR(255),
    coordinates GEOMETRY(Point, 4326),
    event_type VARCHAR(100),
    severity INTEGER CHECK (severity >= 1 AND severity <= 10),
    confidence FLOAT,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_llm_response JSONB
);

-- Administrative regions (loaded from OSM/Natural Earth)
CREATE TABLE IF NOT EXISTS admin_regions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    admin_level INTEGER,  -- 0=country, 1=state, 2=city
    iso_code VARCHAR(10),
    geometry GEOMETRY(MultiPolygon, 4326),
    centroid GEOMETRY(Point, 4326),
    properties JSONB DEFAULT '{}'
);

-- Risk scores per region
CREATE TABLE IF NOT EXISTS risk_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    region_id UUID REFERENCES admin_regions(id),
    risk_type VARCHAR(50),  -- flood, drought, conflict, etc.
    score FLOAT CHECK (score >= 0 AND score <= 100),
    hazard_score FLOAT,
    exposure_score FLOAT,
    vulnerability_score FLOAT,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scenario VARCHAR(50),  -- SSP1-2.6, SSP2-4.5, etc.
    year INTEGER,
    contributing_events JSONB DEFAULT '[]'
);

-- H3 Hexagonal Grid cells
CREATE TABLE IF NOT EXISTS h3_cells (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    h3_index VARCHAR(20) UNIQUE NOT NULL,
    resolution INTEGER,
    geometry GEOMETRY(Polygon, 4326),
    centroid GEOMETRY(Point, 4326),
    risk_score FLOAT DEFAULT 0,
    context_tensor JSONB DEFAULT '{}',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Generated images (Stable Diffusion)
CREATE TABLE IF NOT EXISTS generated_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    region_id UUID REFERENCES admin_regions(id),
    prompt TEXT NOT NULL,
    image_path TEXT,
    scenario VARCHAR(50),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- INDEXES (Performance Critical!)
-- =============================================================================

-- Geometry indexes (GIST)
CREATE INDEX IF NOT EXISTS idx_entities_coords ON extracted_entities USING GIST (coordinates);
CREATE INDEX IF NOT EXISTS idx_regions_geometry ON admin_regions USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_regions_centroid ON admin_regions USING GIST (centroid);
CREATE INDEX IF NOT EXISTS idx_h3_geometry ON h3_cells USING GIST (geometry);

-- Text search indexes
CREATE INDEX IF NOT EXISTS idx_articles_content ON articles USING GIN (to_tsvector('english', content));
CREATE INDEX IF NOT EXISTS idx_articles_title ON articles USING GIN (to_tsvector('english', title));

-- Standard indexes
CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
CREATE INDEX IF NOT EXISTS idx_articles_processed ON articles(processed);
CREATE INDEX IF NOT EXISTS idx_entities_event_type ON extracted_entities(event_type);
CREATE INDEX IF NOT EXISTS idx_entities_severity ON extracted_entities(severity);
CREATE INDEX IF NOT EXISTS idx_risk_region ON risk_scores(region_id);
CREATE INDEX IF NOT EXISTS idx_risk_type ON risk_scores(risk_type);
CREATE INDEX IF NOT EXISTS idx_h3_index ON h3_cells(h3_index);
CREATE INDEX IF NOT EXISTS idx_h3_resolution ON h3_cells(resolution);

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Function to calculate risk spillover to neighboring regions
CREATE OR REPLACE FUNCTION calculate_risk_spillover(source_region_id UUID, spillover_factor FLOAT DEFAULT 0.2)
RETURNS TABLE(neighbor_id UUID, spillover_risk FLOAT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ar.id,
        rs.score * spillover_factor AS spillover_risk
    FROM admin_regions ar
    JOIN admin_regions source ON source.id = source_region_id
    JOIN risk_scores rs ON rs.region_id = source_region_id
    WHERE ST_Touches(ar.geometry, source.geometry)
    AND ar.id != source_region_id;
END;
$$ LANGUAGE plpgsql;

-- Function to find region containing a point
CREATE OR REPLACE FUNCTION find_region_for_point(lat FLOAT, lon FLOAT)
RETURNS UUID AS $$
DECLARE
    region_id UUID;
BEGIN
    SELECT id INTO region_id
    FROM admin_regions
    WHERE ST_Contains(geometry, ST_SetSRID(ST_MakePoint(lon, lat), 4326))
    ORDER BY admin_level DESC
    LIMIT 1;
    
    RETURN region_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- INITIAL DATA
-- =============================================================================

-- Insert default risk types
INSERT INTO risk_scores (region_id, risk_type, score, scenario, year)
SELECT NULL, risk_type, 0, 'baseline', 2025
FROM unnest(ARRAY['flood', 'drought', 'conflict', 'heatwave', 'storm', 'wildfire']) AS risk_type
ON CONFLICT DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO tera;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO tera;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'TERA Database initialized successfully!';
    RAISE NOTICE 'PostGIS Version: %', PostGIS_Version();
END $$;

