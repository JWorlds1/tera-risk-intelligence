"""
TERA Earth Cycles API v2.0
Physikalisches Erdmodell + Adaptive Tessellation für Frontend
"""
from fastapi import APIRouter, Query
from typing import List, Optional
from datetime import datetime
import h3
import math

router = APIRouter()


def get_resolution_for_zoom(zoom: int) -> int:
    """Map zoom level to H3 resolution - HIGHER resolution for more cells"""
    # Zoom 0-20 → Resolution 2-9
    if zoom <= 4: return 2
    elif zoom <= 6: return 3
    elif zoom <= 8: return 4
    elif zoom <= 10: return 5
    elif zoom <= 12: return 6
    elif zoom <= 14: return 7
    elif zoom <= 16: return 8
    else: return 9


def generate_grid_cells(min_lat, min_lon, max_lat, max_lon, resolution):
    """Generate H3 cells using grid sampling"""
    cells = set()
    
    # Calculate step size based on resolution
    # H3 resolution → approximate cell diameter
    cell_sizes = {
        2: 1.5, 3: 0.6, 4: 0.2, 5: 0.08, 
        6: 0.03, 7: 0.012, 8: 0.005, 9: 0.002
    }
    step = cell_sizes.get(resolution, 0.05) * 0.7  # Overlap for coverage
    
    lat = min_lat
    while lat <= max_lat:
        lon = min_lon
        while lon <= max_lon:
            cell = h3.geo_to_h3(lat, lon, resolution)
            cells.add(cell)
            lon += step
        lat += step
    
    return list(cells)


@router.get("/cells")
async def get_earth_cycle_cells(
    min_lat: float = Query(...),
    min_lon: float = Query(...),
    max_lat: float = Query(...),
    max_lon: float = Query(...),
    zoom: int = Query(default=10, ge=0, le=20)
):
    """
    Gibt H3-Zellen mit Erdzyklen-Daten für Bounding Box zurück
    Adaptive Resolution basierend auf Zoom
    """
    from services.physical_earth_model import (
        PhysicalEarthModel, 
        FrontendFormatter
    )
    
    model = PhysicalEarthModel()
    resolution = get_resolution_for_zoom(zoom)
    
    # Generate cells for bbox
    cells = generate_grid_cells(min_lat, min_lon, max_lat, max_lon, resolution)
    
    # Limit für Performance
    max_cells = 1000
    if len(cells) > max_cells:
        cells = cells[:max_cells]
    
    # Für jede Zelle Erdzyklen berechnen
    states = []
    for cell in cells:
        try:
            # Vary parameters slightly for realism
            lat, lon = h3.h3_to_geo(cell)
            precip = max(0, 2 + math.sin(lat * 0.1) * 3)
            ndvi = 0.3 + abs(math.cos(lon * 0.1)) * 0.4
            soil = 40 + abs(math.sin(lat * 0.05 + lon * 0.03)) * 40
            
            state = model.calculate_cell_state(
                cell,
                precipitation_mm=precip,
                ndvi=ndvi,
                soil_moisture_pct=soil
            )
            states.append(state)
        except Exception as e:
            continue
    
    # Zu GeoJSON konvertieren
    geojson = FrontendFormatter.cells_to_feature_collection(states)
    
    return {
        "status": "ok",
        "zoom": zoom,
        "resolution": resolution,
        "cell_count": len(states),
        "geojson": geojson
    }


@router.get("/cell/{h3_index}")
async def get_cell_cycles(h3_index: str):
    """Gibt detaillierte Erdzyklen für eine einzelne Zelle zurück"""
    from services.physical_earth_model import PhysicalEarthModel
    
    model = PhysicalEarthModel()
    state = model.calculate_cell_state(h3_index)
    
    return {
        "status": "ok",
        "h3_index": h3_index,
        "lat": state.lat,
        "lon": state.lon,
        "timestamp": state.timestamp.isoformat(),
        "atmosphere": {
            "temperature_c": state.temperature_c,
            "humidity_pct": state.humidity_pct,
            "cloud_cover_pct": state.cloud_cover_pct
        },
        "energy_budget": {
            "sw_incoming": state.energy.sw_incoming,
            "sw_absorbed": state.energy.sw_absorbed,
            "lw_outgoing": state.energy.lw_outgoing,
            "net_radiation": state.energy.net_radiation,
            "sensible_heat": state.energy.sensible_heat,
            "latent_heat": state.energy.latent_heat,
            "ground_heat": state.energy.ground_heat,
            "bowen_ratio": state.energy.bowen_ratio
        },
        "water_cycle": {
            "precipitation": state.water.precipitation,
            "evapotranspiration": state.water.evapotranspiration,
            "runoff": state.water.runoff,
            "soil_moisture": state.water.soil_moisture,
            "water_balance": state.water.water_balance
        },
        "carbon_cycle": {
            "gpp": state.carbon.gpp,
            "npp": state.carbon.npp,
            "nee": state.carbon.nee,
            "ndvi": state.carbon.ndvi,
            "lai": state.carbon.lai,
            "fpar": state.carbon.fpar
        },
        "risk": {
            "score": state.risk_score,
            "drivers": state.risk_drivers
        }
    }


@router.get("/location")
async def get_cycles_for_location(
    lat: float = Query(...),
    lon: float = Query(...),
    resolution: int = Query(default=7, ge=4, le=10)
):
    """Gibt Erdzyklen für einen Punkt zurück"""
    h3_index = h3.geo_to_h3(lat, lon, resolution)
    return await get_cell_cycles(h3_index)


@router.get("/summary")
async def get_global_summary():
    """Gibt globale Zusammenfassung der Erdzyklen zurück"""
    return {
        "status": "ok",
        "cycles": {
            "energy": {
                "name": "Energie-Budget",
                "unit": "W/m²",
                "variables": [
                    "sw_incoming", "sw_absorbed", "lw_outgoing",
                    "net_radiation", "sensible_heat", "latent_heat"
                ],
                "description": "Strahlungsbilanz und Wärmeflüsse"
            },
            "water": {
                "name": "Wasser-Zyklus",
                "unit": "mm/Tag",
                "variables": [
                    "precipitation", "evapotranspiration", "runoff",
                    "soil_moisture", "water_balance"
                ],
                "description": "Wasserbilanz: P - ET - R = ΔS"
            },
            "carbon": {
                "name": "Carbon-Zyklus",
                "unit": "gC/m²/Tag",
                "variables": [
                    "gpp", "npp", "nee", "ndvi", "lai"
                ],
                "description": "Kohlenstoff-Austausch: GPP - Ra - Rh = NEE"
            }
        },
        "projections": ["EPSG:4326", "Web Mercator"],
        "h3_resolutions": {
            "min": 2,
            "max": 9,
            "recommended": "6-7 für Stadt-Level"
        }
    }
