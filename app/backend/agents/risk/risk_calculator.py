"""
TERA Risk Calculation Agent
Computes geospatial risk scores using PostGIS
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import asyncpg
from loguru import logger


class RiskZone(BaseModel):
    """Risk zone with geometry"""
    id: int
    name: str
    risk_score: float = Field(ge=0.0, le=100.0)
    event_type: str
    geometry_wkt: str  # WKT format
    affected_population: Optional[int] = None
    neighboring_risk: float = 0.0  # Spill-over effect
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RiskCalculator:
    """Calculate and diffuse risk scores using PostGIS"""
    
    SPILLOVER_FACTOR = 0.2  # 20% risk transfer to neighbors
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Initialize connection pool"""
        self.pool = await asyncpg.create_pool(
            self.database_url.replace("+asyncpg", ""),
            min_size=2,
            max_size=10
        )
        logger.info("Connected to PostGIS database")
    
    async def close(self):
        if self.pool:
            await self.pool.close()
    
    async def point_to_admin_region(
        self, 
        lat: float, 
        lon: float
    ) -> Optional[Dict[str, Any]]:
        """Find administrative region containing a point"""
        query = """
        SELECT 
            id, name, admin_level,
            ST_AsText(geom) as geometry_wkt,
            population
        FROM admin_boundaries
        WHERE ST_Contains(geom, ST_SetSRID(ST_MakePoint($1, $2), 4326))
        ORDER BY admin_level DESC
        LIMIT 1
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, lon, lat)
            if row:
                return dict(row)
        return None
    
    async def calculate_risk_score(
        self,
        base_severity: int,
        event_type: str,
        population: Optional[int] = None
    ) -> float:
        """Calculate composite risk score"""
        # Base score from severity (1-10 -> 10-100)
        base_score = base_severity * 10
        
        # Event type multipliers
        multipliers = {
            "conflict": 1.5,
            "drought": 1.2,
            "flood": 1.3,
            "earthquake": 1.4,
            "wildfire": 1.1,
            "famine": 1.6,
            "other": 1.0
        }
        multiplier = multipliers.get(event_type, 1.0)
        
        # Population exposure factor
        pop_factor = 1.0
        if population:
            if population > 1_000_000:
                pop_factor = 1.3
            elif population > 100_000:
                pop_factor = 1.2
            elif population > 10_000:
                pop_factor = 1.1
        
        final_score = min(100.0, base_score * multiplier * pop_factor)
        return round(final_score, 2)
    
    async def diffuse_risk_to_neighbors(
        self, 
        region_id: int, 
        risk_score: float
    ) -> List[Dict[str, Any]]:
        """Apply spillover effect to neighboring regions"""
        query = """
        UPDATE admin_boundaries ab
        SET 
            neighboring_risk = GREATEST(
                neighboring_risk, 
                $1 * $2
            ),
            updated_at = NOW()
        FROM admin_boundaries source
        WHERE source.id = $3
          AND ST_Touches(ab.geom, source.geom)
          AND ab.id != source.id
        RETURNING ab.id, ab.name, ab.neighboring_risk
        """
        spillover = risk_score * self.SPILLOVER_FACTOR
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, spillover, 1.0, region_id)
            return [dict(row) for row in rows]
    
    async def get_risk_geojson(
        self, 
        min_risk: float = 0.0
    ) -> Dict[str, Any]:
        """Get all risk zones as GeoJSON"""
        query = """
        SELECT 
            id,
            name,
            risk_score,
            event_type,
            ST_AsGeoJSON(geom)::json as geometry,
            population,
            neighboring_risk,
            updated_at
        FROM risk_zones
        WHERE risk_score >= $1 OR neighboring_risk >= $1
        ORDER BY risk_score DESC
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, min_risk)
            
            features = []
            for row in rows:
                feature = {
                    "type": "Feature",
                    "properties": {
                        "id": row["id"],
                        "name": row["name"],
                        "risk_score": row["risk_score"],
                        "event_type": row["event_type"],
                        "population": row["population"],
                        "neighboring_risk": row["neighboring_risk"],
                        "total_risk": row["risk_score"] + row["neighboring_risk"]
                    },
                    "geometry": row["geometry"]
                }
                features.append(feature)
            
            return {
                "type": "FeatureCollection",
                "features": features
            }
