"""
GeoNames Data Loader
Downloads and imports global city/country data into PostGIS
"""
import asyncio
import asyncpg
import httpx
import zipfile
import io
import csv
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger
from dataclasses import dataclass

DATA_DIR = Path("/data/tera/data/geo")

# GeoNames URLs
GEONAMES_CITIES = "https://download.geonames.org/export/dump/cities15000.zip"
GEONAMES_COUNTRIES = "https://download.geonames.org/export/dump/countryInfo.txt"
NATURAL_EARTH_COUNTRIES = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"


@dataclass
class City:
    geoname_id: int
    name: str
    lat: float
    lon: float
    country_code: str
    population: int
    timezone: str


@dataclass  
class Country:
    iso_code: str
    name: str
    capital: str
    population: int
    continent: str


async def download_file(url: str, filename: str) -> Path:
    """Download a file from URL"""
    filepath = DATA_DIR / filename
    if filepath.exists():
        logger.info(f"File already exists: {filepath}")
        return filepath
    
    logger.info(f"Downloading {url}...")
    async with httpx.AsyncClient(timeout=300) as client:
        response = await client.get(url)
        response.raise_for_status()
        
        filepath.write_bytes(response.content)
        logger.info(f"Downloaded: {filepath}")
    return filepath


async def load_cities() -> List[City]:
    """Load cities from GeoNames"""
    zip_path = await download_file(GEONAMES_CITIES, "cities15000.zip")
    
    cities = []
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open("cities15000.txt") as f:
            reader = csv.reader(io.TextIOWrapper(f, encoding='utf-8'), delimiter='\t')
            for row in reader:
                try:
                    cities.append(City(
                        geoname_id=int(row[0]),
                        name=row[1],
                        lat=float(row[4]),
                        lon=float(row[5]),
                        country_code=row[8],
                        population=int(row[14]) if row[14] else 0,
                        timezone=row[17]
                    ))
                except (IndexError, ValueError) as e:
                    continue
    
    logger.info(f"Loaded {len(cities)} cities")
    return cities


async def load_countries() -> List[Country]:
    """Load countries from GeoNames"""
    txt_path = await download_file(GEONAMES_COUNTRIES, "countryInfo.txt")
    
    countries = []
    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#'):
                continue
            parts = line.strip().split('\t')
            if len(parts) >= 17:
                try:
                    countries.append(Country(
                        iso_code=parts[0],
                        name=parts[4],
                        capital=parts[5],
                        population=int(parts[7]) if parts[7] else 0,
                        continent=parts[8]
                    ))
                except (IndexError, ValueError):
                    continue
    
    logger.info(f"Loaded {len(countries)} countries")
    return countries


async def load_country_boundaries() -> Dict[str, Any]:
    """Load Natural Earth country boundaries as GeoJSON"""
    geojson_path = await download_file(NATURAL_EARTH_COUNTRIES, "countries.geojson")
    
    import json
    with open(geojson_path, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Loaded {len(data['features'])} country boundaries")
    return data


async def init_database(pool: asyncpg.Pool):
    """Initialize PostGIS tables for geo data"""
    async with pool.acquire() as conn:
        await conn.execute("""
            -- Enable PostGIS
            CREATE EXTENSION IF NOT EXISTS postgis;
            CREATE EXTENSION IF NOT EXISTS h3;
            
            -- Cities table
            CREATE TABLE IF NOT EXISTS cities (
                id SERIAL PRIMARY KEY,
                geoname_id INTEGER UNIQUE,
                name VARCHAR(255) NOT NULL,
                country_code VARCHAR(3),
                population INTEGER DEFAULT 0,
                timezone VARCHAR(100),
                geom GEOMETRY(Point, 4326),
                h3_index VARCHAR(20),
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            -- Countries table
            CREATE TABLE IF NOT EXISTS countries (
                id SERIAL PRIMARY KEY,
                iso_code VARCHAR(3) UNIQUE,
                name VARCHAR(255) NOT NULL,
                capital VARCHAR(255),
                population BIGINT DEFAULT 0,
                continent VARCHAR(50),
                geom GEOMETRY(MultiPolygon, 4326),
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            -- H3 Hexagons table (for risk data per cell)
            CREATE TABLE IF NOT EXISTS h3_cells (
                id SERIAL PRIMARY KEY,
                h3_index VARCHAR(20) UNIQUE NOT NULL,
                resolution INTEGER DEFAULT 7,
                center_lat DOUBLE PRECISION,
                center_lon DOUBLE PRECISION,
                country_code VARCHAR(3),
                city_name VARCHAR(255),
                risk_score FLOAT DEFAULT 0,
                climate_risk FLOAT DEFAULT 0,
                conflict_risk FLOAT DEFAULT 0,
                context_embedding_id VARCHAR(100),
                last_updated TIMESTAMP DEFAULT NOW(),
                geom GEOMETRY(Polygon, 4326)
            );
            
            -- Context data per H3 cell
            CREATE TABLE IF NOT EXISTS cell_contexts (
                id SERIAL PRIMARY KEY,
                h3_index VARCHAR(20) REFERENCES h3_cells(h3_index),
                source_type VARCHAR(50),  -- nasa, ipcc, news
                source_url TEXT,
                title TEXT,
                content TEXT,
                extracted_data JSONB,
                embedding_id VARCHAR(100),
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            -- Spatial indexes
            CREATE INDEX IF NOT EXISTS idx_cities_geom ON cities USING GIST (geom);
            CREATE INDEX IF NOT EXISTS idx_countries_geom ON countries USING GIST (geom);
            CREATE INDEX IF NOT EXISTS idx_h3_cells_geom ON h3_cells USING GIST (geom);
            CREATE INDEX IF NOT EXISTS idx_h3_cells_index ON h3_cells (h3_index);
            CREATE INDEX IF NOT EXISTS idx_cell_contexts_h3 ON cell_contexts (h3_index);
        """)
        logger.info("Database schema initialized")


async def import_cities(pool: asyncpg.Pool, cities: List[City]):
    """Import cities into PostGIS"""
    async with pool.acquire() as conn:
        # Batch insert
        for i in range(0, len(cities), 1000):
            batch = cities[i:i+1000]
            values = [
                (c.geoname_id, c.name, c.lat, c.lon, c.country_code, c.population, c.timezone)
                for c in batch
            ]
            await conn.executemany("""
                INSERT INTO cities (geoname_id, name, geom, country_code, population, timezone)
                VALUES ($1, $2, ST_SetSRID(ST_MakePoint($4, $3), 4326), $5, $6, $7)
                ON CONFLICT (geoname_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    population = EXCLUDED.population
            """, values)
            logger.info(f"Imported cities {i}-{i+len(batch)}")
    
    logger.info(f"Total cities imported: {len(cities)}")


async def import_countries(pool: asyncpg.Pool, countries: List[Country], boundaries: Dict):
    """Import countries with boundaries into PostGIS"""
    import json
    
    # Create lookup for boundaries
    boundary_lookup = {}
    for feature in boundaries['features']:
        iso = feature['properties'].get('ISO_A2') or feature['properties'].get('ISO_A3', '')[:2]
        if iso:
            boundary_lookup[iso] = json.dumps(feature['geometry'])
    
    async with pool.acquire() as conn:
        for country in countries:
            geom = boundary_lookup.get(country.iso_code)
            if geom:
                await conn.execute("""
                    INSERT INTO countries (iso_code, name, capital, population, continent, geom)
                    VALUES ($1, $2, $3, $4, $5, ST_SetSRID(ST_GeomFromGeoJSON($6), 4326))
                    ON CONFLICT (iso_code) DO UPDATE SET
                        name = EXCLUDED.name,
                        population = EXCLUDED.population,
                        geom = EXCLUDED.geom
                """, country.iso_code, country.name, country.capital, 
                    country.population, country.continent, geom)
    
    logger.info(f"Countries imported with boundaries")


async def main():
    """Main import function"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Connect to database
    pool = await asyncpg.create_pool(
        "postgresql://tera:tera_secure_2025@localhost:5432/tera",
        min_size=2, max_size=10
    )
    
    try:
        # Initialize schema
        await init_database(pool)
        
        # Load and import data
        cities = await load_cities()
        countries = await load_countries()
        boundaries = await load_country_boundaries()
        
        await import_cities(pool, cities)
        await import_countries(pool, countries, boundaries)
        
        logger.info("GeoNames import complete!")
        
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
