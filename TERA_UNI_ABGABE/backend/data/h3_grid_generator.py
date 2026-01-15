"""
H3 Hexagonal Grid Generator
Creates H3 cells for any region on Earth
"""
import h3
import asyncpg
import json
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass
from loguru import logger


@dataclass
class H3Cell:
    h3_index: str
    resolution: int
    center_lat: float
    center_lon: float
    boundary: List[Tuple[float, float]]


def get_h3_cells_for_bbox(
    min_lat: float, min_lon: float,
    max_lat: float, max_lon: float,
    resolution: int = 7
) -> List[H3Cell]:
    """
    Generate H3 cells covering a bounding box
    Resolution 7 = ~5.16 km² per hexagon (good for city-level)
    Resolution 5 = ~252.9 km² (good for country-level)
    """
    cells = []
    
    # Get all H3 cells that intersect with the bbox
    # Use polyfill for the rectangle
    polygon = [
        (min_lat, min_lon),
        (min_lat, max_lon),
        (max_lat, max_lon),
        (max_lat, min_lon),
        (min_lat, min_lon)
    ]
    
    h3_indexes = h3.polyfill_geojson({
        "type": "Polygon",
        "coordinates": [[
            [min_lon, min_lat],
            [max_lon, min_lat],
            [max_lon, max_lat],
            [min_lon, max_lat],
            [min_lon, min_lat]
        ]]
    }, resolution)
    
    for idx in h3_indexes:
        lat, lon = h3.h3_to_geo(idx)
        boundary = h3.h3_to_geo_boundary(idx)
        cells.append(H3Cell(
            h3_index=idx,
            resolution=resolution,
            center_lat=lat,
            center_lon=lon,
            boundary=boundary
        ))
    
    return cells


def get_h3_cells_for_point(lat: float, lon: float, resolution: int = 7, rings: int = 2) -> List[H3Cell]:
    """Get H3 cells around a point (center + k-rings)"""
    center = h3.geo_to_h3(lat, lon, resolution)
    indexes = h3.k_ring(center, rings)
    
    cells = []
    for idx in indexes:
        lat, lon = h3.h3_to_geo(idx)
        boundary = h3.h3_to_geo_boundary(idx)
        cells.append(H3Cell(
            h3_index=idx,
            resolution=resolution,
            center_lat=lat,
            center_lon=lon,
            boundary=boundary
        ))
    
    return cells


def h3_boundary_to_geojson(boundary: List[Tuple[float, float]]) -> Dict:
    """Convert H3 boundary to GeoJSON Polygon"""
    coords = [[lon, lat] for lat, lon in boundary]
    coords.append(coords[0])  # Close the polygon
    return {
        "type": "Polygon",
        "coordinates": [coords]
    }


async def store_h3_cells(pool: asyncpg.Pool, cells: List[H3Cell], country_code: str = None):
    """Store H3 cells in PostGIS"""
    async with pool.acquire() as conn:
        for cell in cells:
            geojson = json.dumps(h3_boundary_to_geojson(cell.boundary))
            await conn.execute("""
                INSERT INTO h3_cells (h3_index, resolution, center_lat, center_lon, country_code, geom)
                VALUES ($1, $2, $3, $4, $5, ST_SetSRID(ST_GeomFromGeoJSON($6), 4326))
                ON CONFLICT (h3_index) DO UPDATE SET
                    country_code = COALESCE(EXCLUDED.country_code, h3_cells.country_code)
            """, cell.h3_index, cell.resolution, cell.center_lat, cell.center_lon, country_code, geojson)
    
    logger.info(f"Stored {len(cells)} H3 cells")


async def generate_global_h3_grid(pool: asyncpg.Pool, resolution: int = 5):
    """Generate H3 grid for entire world at specified resolution"""
    # For global coverage at res 5, we process in chunks
    logger.info(f"Generating global H3 grid at resolution {resolution}")
    
    total_cells = 0
    for lat_start in range(-90, 90, 30):
        for lon_start in range(-180, 180, 30):
            cells = get_h3_cells_for_bbox(
                lat_start, lon_start,
                lat_start + 30, lon_start + 30,
                resolution
            )
            await store_h3_cells(pool, cells)
            total_cells += len(cells)
            logger.info(f"Progress: {total_cells} cells stored")
    
    return total_cells
