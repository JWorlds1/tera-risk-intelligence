"""
TERA Database Connection with AsyncPG
"""
import asyncpg
from typing import Optional
from loguru import logger
from config.settings import settings

pool: Optional[asyncpg.Pool] = None


async def init_db():
    """Initialize database connection pool"""
    global pool
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    pool = await asyncpg.create_pool(
        db_url,
        min_size=5,
        max_size=20,
        command_timeout=60
    )
    
    # Initialize schema
    async with pool.acquire() as conn:
        await conn.execute("""
            -- Enable PostGIS
            CREATE EXTENSION IF NOT EXISTS postgis;
            CREATE EXTENSION IF NOT EXISTS postgis_topology;
            
            -- Risk Zones Table
            CREATE TABLE IF NOT EXISTS risk_zones (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                risk_score FLOAT DEFAULT 0.0,
                neighboring_risk FLOAT DEFAULT 0.0,
                event_type VARCHAR(50),
                summary TEXT,
                geom GEOMETRY(MultiPolygon, 4326),
                population INTEGER,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            
            -- Admin Boundaries Table
            CREATE TABLE IF NOT EXISTS admin_boundaries (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                admin_level INTEGER DEFAULT 0,
                country_code VARCHAR(3),
                geom GEOMETRY(MultiPolygon, 4326),
                population INTEGER,
                neighboring_risk FLOAT DEFAULT 0.0,
                updated_at TIMESTAMP DEFAULT NOW()
            );
            
            -- Scraped Articles Table
            CREATE TABLE IF NOT EXISTS articles (
                id SERIAL PRIMARY KEY,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                content TEXT,
                source VARCHAR(100),
                published_at TIMESTAMP,
                scraped_at TIMESTAMP DEFAULT NOW(),
                processed BOOLEAN DEFAULT FALSE
            );
            
            -- Extracted Entities Table
            CREATE TABLE IF NOT EXISTS entities (
                id SERIAL PRIMARY KEY,
                article_id INTEGER REFERENCES articles(id),
                location VARCHAR(255),
                coordinates GEOMETRY(Point, 4326),
                event_type VARCHAR(50),
                severity INTEGER CHECK (severity >= 1 AND severity <= 10),
                summary TEXT,
                confidence FLOAT,
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            -- Generated Images Table
            CREATE TABLE IF NOT EXISTS generated_images (
                id SERIAL PRIMARY KEY,
                risk_zone_id INTEGER REFERENCES risk_zones(id),
                prompt TEXT,
                image_path TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            -- Create spatial indexes
            CREATE INDEX IF NOT EXISTS idx_risk_zones_geom ON risk_zones USING GIST (geom);
            CREATE INDEX IF NOT EXISTS idx_admin_boundaries_geom ON admin_boundaries USING GIST (geom);
            CREATE INDEX IF NOT EXISTS idx_entities_coordinates ON entities USING GIST (coordinates);
        """)
        logger.info("✓ Database schema initialized")


async def close_db():
    """Close database connection pool"""
    global pool
    if pool:
        await pool.close()


async def get_pool() -> asyncpg.Pool:
    """Get database connection pool"""
    return pool
