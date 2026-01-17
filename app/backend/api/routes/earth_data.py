"""
TERA Earth Data API Routes
Real-time Earth system data and 2026-2027 forecasts
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

router = APIRouter()


class ForecastRequest(BaseModel):
    city: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    h3_index: Optional[str] = None


class EarthDataResponse(BaseModel):
    status: str
    data: Dict[str, Any]
    generated_at: str


@router.get("/sources")
async def get_data_sources():
    """List available Earth data sources"""
    sources = {
        "satellite": [
            {"name": "Sentinel-2", "type": "optical", "resolution": "10m", "revisit": "5 days"},
            {"name": "MODIS", "type": "multispectral", "resolution": "250m-1km", "revisit": "daily"},
            {"name": "VIIRS", "type": "fire/thermal", "resolution": "375m", "revisit": "daily"},
            {"name": "GOES-18", "type": "geostationary", "resolution": "2km", "revisit": "15min"},
        ],
        "reanalysis": [
            {"name": "ERA5", "provider": "ECMWF", "resolution": "31km", "temporal": "hourly"},
            {"name": "ERA5-Land", "provider": "ECMWF", "resolution": "9km", "temporal": "hourly"},
        ],
        "forecasts": [
            {"name": "GFS", "provider": "NOAA", "resolution": "25km", "lead_time": "16 days"},
            {"name": "ECMWF-IFS", "provider": "ECMWF", "resolution": "9km", "lead_time": "15 days"},
        ],
        "real_time": [
            {"name": "NASA FIRMS", "type": "fire", "latency": "3 hours"},
            {"name": "USGS Earthquakes", "type": "seismic", "latency": "minutes"},
        ]
    }
    return {"status": "ok", "sources": sources}


@router.get("/cycles")
async def get_earth_cycles():
    """Get Earth system cycles information"""
    cycles = {
        "energy_budget": {
            "description": "Ein- und ausgehende Strahlung, Wärmeflüsse",
            "variables": [
                "shortwave_incoming", "shortwave_reflected", "longwave_outgoing",
                "sensible_heat_flux", "latent_heat_flux", "net_radiation"
            ],
            "unit": "W/m²"
        },
        "water_cycle": {
            "description": "Verdunstung, Niederschlag, Abfluss, Bodenfeuchte",
            "variables": [
                "precipitation", "evapotranspiration", "runoff",
                "soil_moisture", "snow_water_equivalent", "groundwater"
            ],
            "unit": "mm/day or mm"
        },
        "carbon_cycle": {
            "description": "CO2-Austausch, Photosynthese, Respiration",
            "variables": [
                "gpp", "npp", "nee", "respiration",
                "co2_concentration", "ndvi", "lai"
            ],
            "unit": "gC/m²/day or ppm"
        },
        "atmosphere": {
            "description": "Wind, Druck, Wolken, Aerosole",
            "variables": [
                "wind_speed", "wind_direction", "pressure",
                "cloud_cover", "aod", "boundary_layer_height"
            ],
            "unit": "varies"
        }
    }
    return {"status": "ok", "cycles": cycles}


@router.get("/forecast/city/{city}")
async def get_city_forecast(city: str):
    """Get 2026-2027 forecast for a city"""
    try:
        from services.forecast_engine import get_forecast_for_city
        forecast = await get_forecast_for_city(city)
        return {"status": "ok", "forecast": forecast}
    except Exception as e:
        logger.error(f"Forecast error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecast/h3/{h3_index}")
async def get_h3_forecast(h3_index: str):
    """Get 2026-2027 forecast for an H3 cell"""
    try:
        from services.forecast_engine import ForecastEngine
        engine = ForecastEngine()
        forecast = engine.generate_2026_2027_outlook(h3_index)
        return {"status": "ok", "forecast": forecast}
    except Exception as e:
        logger.error(f"Forecast error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fires/current")
async def get_current_fires(
    country: str = Query(default="DEU", description="ISO3 country code"),
    days: int = Query(default=1, ge=1, le=10)
):
    """Get current fire detections from NASA FIRMS"""
    try:
        from services.earth_data_service import NASAFIRMSService
        service = NASAFIRMSService()
        fires = await service.fetch_fires(country=country, days=days)
        return {
            "status": "ok",
            "count": len(fires),
            "fires": [
                {
                    "lat": f.lat,
                    "lon": f.lon,
                    "h3_index": f.h3_index,
                    "brightness": f.variables.get("brightness", 0),
                    "frp": f.variables.get("frp", 0),
                    "confidence": f.confidence,
                    "time": f.observation_time.isoformat()
                }
                for f in fires
            ]
        }
    except Exception as e:
        logger.error(f"FIRMS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/satellite/search")
async def search_satellite_scenes(
    collection: str = Query(default="sentinel-2-l2a"),
    min_lon: float = Query(...),
    min_lat: float = Query(...),
    max_lon: float = Query(...),
    max_lat: float = Query(...),
    days: int = Query(default=7, ge=1, le=30)
):
    """Search for satellite scenes in Planetary Computer"""
    try:
        from services.earth_data_service import search_satellite_scenes
        scenes = await search_satellite_scenes(
            collection=collection,
            bbox=(min_lon, min_lat, max_lon, max_lat),
            days_back=days
        )
        return {
            "status": "ok",
            "count": len(scenes),
            "scenes": [
                {
                    "id": s.get("id"),
                    "datetime": s.get("properties", {}).get("datetime"),
                    "cloud_cover": s.get("properties", {}).get("eo:cloud_cover"),
                }
                for s in scenes
            ]
        }
    except Exception as e:
        logger.error(f"Satellite search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_earth_data_status():
    """Get status of Earth data services"""
    from datetime import datetime
    return {
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "nasa_firms": "available",
            "planetary_computer": "available",
            "era5": "requires_api_key",
            "noaa_goes": "available"
        },
        "database": {
            "earth_cycles_tables": [
                "h3_energy_budget",
                "h3_water_cycle",
                "h3_carbon_cycle",
                "h3_atmosphere",
                "h3_ocean",
                "nrt_observations",
                "forecasts"
            ]
        }
    }
