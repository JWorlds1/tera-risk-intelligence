"""
Risk Calculator - Multi-factor risk assessment with PostGIS
"""
import asyncpg
import h3
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
from loguru import logger


@dataclass
class CellRisk:
    h3_index: str
    climate_risk: float
    conflict_risk: float
    total_risk: float
    neighboring_risk: float
    event_count: int
    last_event_type: Optional[str]
    last_updated: datetime


class RiskCalculator:
    """
    Calculate risk scores for H3 cells using multiple factors
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
    
    async def calculate_cell_risk(self, h3_index: str) -> CellRisk:
        """Calculate comprehensive risk for a single cell"""
        async with self.db_pool.acquire() as conn:
            # Get base cell data
            cell = await conn.fetchrow("""
                SELECT h3_index, climate_risk, conflict_risk, 
                       risk_score as total_risk, last_updated
                FROM h3_cells WHERE h3_index = $1
            """, h3_index)
            
            if not cell:
                return CellRisk(
                    h3_index=h3_index,
                    climate_risk=0,
                    conflict_risk=0,
                    total_risk=0,
                    neighboring_risk=0,
                    event_count=0,
                    last_event_type=None,
                    last_updated=datetime.utcnow()
                )
            
            # Get neighboring risk (spillover effect)
            neighbors = list(h3.k_ring(h3_index, 1))
            neighbors.remove(h3_index)
            
            neighbor_risk = await conn.fetchval("""
                SELECT COALESCE(AVG(risk_score), 0) 
                FROM h3_cells 
                WHERE h3_index = ANY($1)
            """, neighbors)
            
            # Get recent events
            lat, lon = h3.h3_to_geo(h3_index)
            events = await conn.fetch("""
                SELECT category, event_date
                FROM nasa_events
                WHERE ST_DWithin(
                    geom::geography,
                    ST_SetSRID(ST_MakePoint($2, $1), 4326)::geography,
                    50000  -- 50km radius
                )
                ORDER BY event_date DESC
                LIMIT 10
            """, lat, lon)
            
            return CellRisk(
                h3_index=h3_index,
                climate_risk=cell["climate_risk"] or 0,
                conflict_risk=cell["conflict_risk"] or 0,
                total_risk=cell["total_risk"] or 0,
                neighboring_risk=float(neighbor_risk) * 0.2,  # 20% spillover
                event_count=len(events),
                last_event_type=events[0]["category"] if events else None,
                last_updated=cell["last_updated"] or datetime.utcnow()
            )
    
    async def update_cell_risk(
        self, 
        h3_index: str, 
        climate_delta: float = 0, 
        conflict_delta: float = 0
    ):
        """Update risk for a cell"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE h3_cells SET
                    climate_risk = LEAST(100, GREATEST(0, climate_risk + $2)),
                    conflict_risk = LEAST(100, GREATEST(0, conflict_risk + $3)),
                    risk_score = LEAST(100, GREATEST(0, 
                        (climate_risk + $2) * 0.6 + (conflict_risk + $3) * 0.4
                    )),
                    last_updated = NOW()
                WHERE h3_index = $1
            """, h3_index, climate_delta, conflict_delta)
    
    async def propagate_risk(self, center_h3: str, risk_value: float, decay: float = 0.2):
        """Propagate risk to neighboring cells"""
        rings = h3.k_ring_distances(center_h3, 3)
        
        async with self.db_pool.acquire() as conn:
            for distance, cells in enumerate(rings):
                if distance == 0:
                    continue  # Skip center
                
                factor = decay ** distance
                delta = risk_value * factor
                
                for cell in cells:
                    await conn.execute("""
                        INSERT INTO h3_cells (h3_index, resolution, center_lat, center_lon, risk_score)
                        VALUES ($1, 7, $2, $3, $4)
                        ON CONFLICT (h3_index) DO UPDATE SET
                            risk_score = LEAST(100, h3_cells.risk_score + $4),
                            last_updated = NOW()
                    """, cell, *h3.h3_to_geo(cell), delta)
    
    async def get_high_risk_cells(self, min_risk: float = 50, limit: int = 100) -> List[Dict]:
        """Get cells with risk above threshold"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT h3_index, center_lat, center_lon, 
                       climate_risk, conflict_risk, risk_score,
                       country_code, city_name,
                       ST_AsGeoJSON(geom)::json as geometry
                FROM h3_cells
                WHERE risk_score >= $1
                ORDER BY risk_score DESC
                LIMIT $2
            """, min_risk, limit)
            
            return [dict(row) for row in rows]
    
    async def get_risk_geojson(self, bbox: Tuple[float, float, float, float] = None) -> Dict:
        """Get risk data as GeoJSON for map rendering"""
        async with self.db_pool.acquire() as conn:
            if bbox:
                min_lon, min_lat, max_lon, max_lat = bbox
                rows = await conn.fetch("""
                    SELECT h3_index, center_lat, center_lon,
                           climate_risk, conflict_risk, risk_score,
                           ST_AsGeoJSON(geom)::json as geometry
                    FROM h3_cells
                    WHERE geom && ST_MakeEnvelope($1, $2, $3, $4, 4326)
                    AND risk_score > 0
                """, min_lon, min_lat, max_lon, max_lat)
            else:
                rows = await conn.fetch("""
                    SELECT h3_index, center_lat, center_lon,
                           climate_risk, conflict_risk, risk_score,
                           ST_AsGeoJSON(geom)::json as geometry
                    FROM h3_cells
                    WHERE risk_score > 0
                    LIMIT 10000
                """)
            
            features = []
            for row in rows:
                if row["geometry"]:
                    features.append({
                        "type": "Feature",
                        "properties": {
                            "h3_index": row["h3_index"],
                            "climate_risk": row["climate_risk"],
                            "conflict_risk": row["conflict_risk"],
                            "risk_score": row["risk_score"],
                            "color": self._risk_to_color(row["risk_score"])
                        },
                        "geometry": row["geometry"]
                    })
            
            return {
                "type": "FeatureCollection",
                "features": features
            }
    
    def _risk_to_color(self, risk: float) -> str:
        """Convert risk score to hex color"""
        risk = min(100, max(0, risk))
        if risk < 30:
            # Green to Yellow
            ratio = risk / 30
            r = int(255 * ratio)
            g = 255
        elif risk < 70:
            # Yellow to Orange
            ratio = (risk - 30) / 40
            r = 255
            g = int(255 * (1 - ratio * 0.5))
        else:
            # Orange to Red
            ratio = (risk - 70) / 30
            r = 255
            g = int(128 * (1 - ratio))
        
        return f"#{r:02x}{g:02x}00"
