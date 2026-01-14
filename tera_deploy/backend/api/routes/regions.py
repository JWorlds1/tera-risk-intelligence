"""
Regions & GeoJSON Routes
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from models.schemas import GeoJSONFeatureCollection, RegionRisk, BoundingBox
from services.database import get_db
from loguru import logger

router = APIRouter()


@router.get("/geojson")
async def get_regions_geojson(
    admin_level: int = Query(0, ge=0, le=2),
    bbox: Optional[str] = None
) -> GeoJSONFeatureCollection:
    """
    Get administrative regions as GeoJSON.
    Use for MapLibre visualization.
    """
    # Parse bounding box if provided
    bounds = None
    if bbox:
        try:
            coords = [float(x) for x in bbox.split(",")]
            bounds = BoundingBox(
                min_lon=coords[0], min_lat=coords[1],
                max_lon=coords[2], max_lat=coords[3]
            )
        except:
            raise HTTPException(400, "Invalid bbox format. Use: min_lon,min_lat,max_lon,max_lat")
    
    # Query database
    async for db in get_db():
        query = """
            SELECT 
                id, name, admin_level, iso_code,
                ST_AsGeoJSON(geometry)::json as geometry,
                properties
            FROM admin_regions
            WHERE admin_level = :level
        """
        
        if bounds:
            query += """
                AND ST_Intersects(
                    geometry,
                    ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326)
                )
            """
        
        query += " LIMIT 1000"
        
        params = {"level": admin_level}
        if bounds:
            params.update(bounds.model_dump())
        
        result = await db.fetch_all(query, params)
        
        features = []
        for row in result:
            features.append({
                "type": "Feature",
                "geometry": row["geometry"],
                "properties": {
                    "id": str(row["id"]),
                    "name": row["name"],
                    "admin_level": row["admin_level"],
                    "iso_code": row["iso_code"],
                    **(row["properties"] or {})
                }
            })
        
        return GeoJSONFeatureCollection(
            type="FeatureCollection",
            features=features
        )


@router.get("/risk-geojson")
async def get_risk_geojson(
    scenario: str = "SSP2-4.5",
    year: int = 2030,
    risk_type: Optional[str] = None
) -> GeoJSONFeatureCollection:
    """
    Get regions with risk scores as GeoJSON.
    Color-coded for visualization.
    """
    async for db in get_db():
        query = """
            SELECT 
                ar.id, ar.name, ar.admin_level,
                ST_AsGeoJSON(ar.geometry)::json as geometry,
                rs.score as risk_score,
                rs.hazard_score,
                rs.exposure_score,
                rs.vulnerability_score,
                rs.risk_type
            FROM admin_regions ar
            LEFT JOIN risk_scores rs ON ar.id = rs.region_id
            WHERE rs.scenario = :scenario 
            AND rs.year = :year
        """
        
        params = {"scenario": scenario, "year": year}
        
        if risk_type:
            query += " AND rs.risk_type = :risk_type"
            params["risk_type"] = risk_type
        
        result = await db.fetch_all(query, params)
        
        features = []
        for row in result:
            # Calculate color based on risk score
            risk = row["risk_score"] or 0
            color = f"rgba({int(risk * 2.55)}, {int((100 - risk) * 2.55)}, 0, 0.7)"
            
            features.append({
                "type": "Feature",
                "geometry": row["geometry"],
                "properties": {
                    "id": str(row["id"]),
                    "name": row["name"],
                    "risk_score": risk,
                    "hazard": row["hazard_score"],
                    "exposure": row["exposure_score"],
                    "vulnerability": row["vulnerability_score"],
                    "risk_type": row["risk_type"],
                    "fill_color": color
                }
            })
        
        return GeoJSONFeatureCollection(
            type="FeatureCollection",
            features=features
        )


@router.get("/search")
async def search_regions(q: str, limit: int = 10):
    """Search regions by name"""
    async for db in get_db():
        result = await db.fetch_all("""
            SELECT id, name, admin_level, 
                   ST_X(centroid) as lon, ST_Y(centroid) as lat
            FROM admin_regions
            WHERE name ILIKE :query
            ORDER BY admin_level
            LIMIT :limit
        """, {"query": f"%{q}%", "limit": limit})
        
        return {
            "results": [
                {
                    "id": str(r["id"]),
                    "name": r["name"],
                    "admin_level": r["admin_level"],
                    "coordinates": {"lat": r["lat"], "lon": r["lon"]}
                }
                for r in result
            ]
        }

