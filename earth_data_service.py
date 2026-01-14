"""
TERA Earth Data Service
Real-time ingestion of Earth System data for 2026-2027 forecasts

Data Sources:
- ERA5 / ERA5-Land (Copernicus CDS)
- Sentinel-2/3 (Planetary Computer / Copernicus)
- NASA FIRMS (Fire data)
- NOAA GOES (Geostationary)
- GFS/ECMWF (Weather forecasts)
"""
import asyncio
import httpx
import h3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from loguru import logger

# =====================================================
# DATA CLASSES
# =====================================================

@dataclass
class EarthObservation:
    """Generic Earth observation"""
    h3_index: str
    observation_time: datetime
    source: str
    obs_type: str
    variables: Dict[str, float]
    lat: float
    lon: float
    confidence: float = 1.0
    raw_data: Optional[Dict] = None


@dataclass 
class ForecastData:
    """Forecast for a specific location and time"""
    h3_index: str
    forecast_date: datetime
    target_date: datetime
    lead_days: int
    model_name: str
    variables: Dict[str, float]
    probabilities: Dict[str, float]
    confidence_interval: tuple


# =====================================================
# NASA FIRMS SERVICE (Near Real-Time Fire Data)
# =====================================================

class NASAFIRMSService:
    """
    NASA Fire Information for Resource Management System
    NRT fire detections from MODIS and VIIRS
    """
    
    BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api"
    
    SOURCES = {
        "MODIS_NRT": "MODIS C6.1 Near Real-Time",
        "VIIRS_NOAA20_NRT": "VIIRS NOAA-20 Near Real-Time",
        "VIIRS_SNPP_NRT": "VIIRS Suomi-NPP Near Real-Time"
    }
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or "DEMO_KEY"
        
    async def fetch_fires(
        self, 
        bbox: tuple = None,
        country: str = None,
        days: int = 1,
        source: str = "VIIRS_NOAA20_NRT"
    ) -> List[EarthObservation]:
        """Fetch active fire detections"""
        
        if bbox:
            endpoint = f"{self.BASE_URL}/area/csv/{self.api_key}/{source}"
            params = {
                "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
                "days": days
            }
        elif country:
            endpoint = f"{self.BASE_URL}/country/csv/{self.api_key}/{source}/{country}/{days}"
            params = {}
        else:
            endpoint = f"{self.BASE_URL}/area/csv/{self.api_key}/{source}"
            params = {"bbox": "-180,-90,180,90", "days": days}
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                
            import csv
            from io import StringIO
            
            reader = csv.DictReader(StringIO(response.text))
            observations = []
            
            for row in reader:
                try:
                    lat = float(row.get("latitude", 0))
                    lon = float(row.get("longitude", 0))
                    h3_index = h3.geo_to_h3(lat, lon, 7)
                    
                    acq_date = row.get("acq_date", "")
                    acq_time = row.get("acq_time", "0000")
                    
                    obs_time = datetime.strptime(
                        f"{acq_date} {acq_time}", 
                        "%Y-%m-%d %H%M"
                    )
                    
                    obs = EarthObservation(
                        h3_index=h3_index,
                        observation_time=obs_time,
                        source=source,
                        obs_type="fire",
                        variables={
                            "brightness": float(row.get("brightness", 0)),
                            "frp": float(row.get("frp", 0)),
                            "confidence": float(row.get("confidence", 50)),
                        },
                        lat=lat,
                        lon=lon,
                        confidence=float(row.get("confidence", 50)) / 100,
                        raw_data=dict(row)
                    )
                    observations.append(obs)
                except Exception as e:
                    logger.warning(f"Error parsing fire row: {e}")
                    continue
            
            logger.info(f"Fetched {len(observations)} fire detections from FIRMS")
            return observations
            
        except Exception as e:
            logger.error(f"FIRMS API error: {e}")
            return []


# =====================================================
# PLANETARY COMPUTER STAC SERVICE
# =====================================================

class PlanetaryComputerService:
    """
    Microsoft Planetary Computer STAC API
    Access to Sentinel-2, MODIS, Landsat, and more
    """
    
    STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
    
    COLLECTIONS = {
        "sentinel-2-l2a": "Sentinel-2 L2A (Surface Reflectance)",
        "modis-13Q1-061": "MODIS Vegetation Indices (16-day)",
        "modis-11A2-061": "MODIS Land Surface Temperature",
        "landsat-c2-l2": "Landsat Collection 2 Level 2",
    }
    
    async def search_scenes(
        self,
        collection: str,
        bbox: tuple,
        start_date: str,
        end_date: str,
        cloud_cover: float = 20,
        limit: int = 10
    ) -> List[Dict]:
        """Search for satellite scenes"""
        
        payload = {
            "collections": [collection],
            "bbox": list(bbox),
            "datetime": f"{start_date}/{end_date}",
            "limit": limit,
        }
        
        if "sentinel" in collection.lower():
            payload["query"] = {
                "eo:cloud_cover": {"lt": cloud_cover}
            }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.STAC_URL}/search",
                json=payload
            )
            response.raise_for_status()
            
        data = response.json()
        items = data.get("features", [])
        
        logger.info(f"Found {len(items)} scenes in {collection}")
        return items
    
    async def get_ndvi_observations(
        self,
        bbox: tuple,
        start_date: str,
        end_date: str
    ) -> List[EarthObservation]:
        """Get NDVI observations from Sentinel-2"""
        
        items = await self.search_scenes(
            collection="sentinel-2-l2a",
            bbox=bbox,
            start_date=start_date,
            end_date=end_date,
            cloud_cover=20
        )
        
        observations = []
        for item in items:
            props = item.get("properties", {})
            geom = item.get("geometry", {})
            
            if geom.get("type") == "Polygon":
                coords = geom["coordinates"][0]
                lon = sum(c[0] for c in coords) / len(coords)
                lat = sum(c[1] for c in coords) / len(coords)
            else:
                continue
            
            h3_index = h3.geo_to_h3(lat, lon, 7)
            
            dt_str = props.get("datetime", "")
            if dt_str:
                obs_time = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            else:
                obs_time = datetime.utcnow()
            
            obs = EarthObservation(
                h3_index=h3_index,
                observation_time=obs_time,
                source="Sentinel-2",
                obs_type="vegetation",
                variables={
                    "cloud_cover": props.get("eo:cloud_cover", 0),
                },
                lat=lat,
                lon=lon,
                raw_data={
                    "id": item.get("id"),
                    "assets": list(item.get("assets", {}).keys())
                }
            )
            observations.append(obs)
        
        return observations


# =====================================================
# ERA5 CLIMATE DATA STORE SERVICE
# =====================================================

class ERA5Service:
    """
    Copernicus Climate Data Store - ERA5 Reanalysis
    Note: Requires cdsapi and .cdsapirc configuration
    """
    
    VARIABLES = {
        "energy": [
            "surface_net_solar_radiation",
            "surface_net_thermal_radiation",
            "surface_sensible_heat_flux",
            "surface_latent_heat_flux",
            "2m_temperature",
            "skin_temperature",
        ],
        "water": [
            "total_precipitation",
            "evaporation",
            "runoff",
            "total_column_water_vapour",
            "volumetric_soil_water_layer_1",
            "volumetric_soil_water_layer_2",
            "snow_depth_water_equivalent",
        ],
        "atmosphere": [
            "10m_u_component_of_wind",
            "10m_v_component_of_wind",
            "surface_pressure",
            "total_cloud_cover",
            "boundary_layer_height",
        ]
    }
    
    def __init__(self):
        self.cds_available = False
        try:
            import cdsapi
            self.client = cdsapi.Client()
            self.cds_available = True
            logger.info("ERA5 CDS client initialized")
        except Exception as e:
            logger.warning(f"CDS API not available: {e}")
    
    async def fetch_era5_data(
        self,
        variables: List[str],
        date: str,
        area: List[float],
        output_file: str = None
    ) -> Optional[str]:
        """Fetch ERA5 data for given parameters"""
        
        if not self.cds_available:
            logger.warning("CDS API not configured")
            return None
        
        output_file = output_file or f"/tmp/era5_{date}.nc"
        
        request = {
            "product_type": "reanalysis",
            "variable": variables,
            "year": date[:4],
            "month": date[5:7],
            "day": date[8:10],
            "time": [f"{h:02d}:00" for h in range(0, 24, 6)],
            "area": area,
            "format": "netcdf",
        }
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.client.retrieve(
                    "reanalysis-era5-single-levels",
                    request,
                    output_file
                )
            )
            logger.info(f"ERA5 data saved to {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"ERA5 fetch error: {e}")
            return None


# =====================================================
# NOAA GOES SERVICE
# =====================================================

class NOAAGOESService:
    """
    NOAA GOES-16/18 Geostationary Satellite Data
    Available on AWS Open Data
    """
    
    GOES_BUCKET = "noaa-goes18"
    PRODUCTS = {
        "ABI-L2-MCMIPF": "Cloud & Moisture Imagery",
        "ABI-L2-LSTF": "Land Surface Temperature",
        "ABI-L2-FDCF": "Fire Detection",
        "ABI-L2-AODF": "Aerosol Optical Depth",
    }
    
    async def list_latest_files(
        self,
        product: str,
        hours_back: int = 3
    ) -> List[str]:
        """List latest GOES files from AWS S3"""
        
        now = datetime.utcnow()
        
        files = []
        for h in range(hours_back):
            dt = now - timedelta(hours=h)
            prefix = f"{product}/{dt.year}/{dt.timetuple().tm_yday:03d}/{dt.hour:02d}/"
            files.append(f"s3://{self.GOES_BUCKET}/{prefix}")
        
        return files


# =====================================================
# MASTER EARTH DATA INGESTION SERVICE
# =====================================================

class EarthDataIngestionService:
    """
    Master service for ingesting all Earth data sources
    """
    
    def __init__(self, db_pool=None):
        self.db = db_pool
        self.firms = NASAFIRMSService()
        self.planetary = PlanetaryComputerService()
        self.era5 = ERA5Service()
        self.goes = NOAAGOESService()
    
    async def ingest_observations(
        self, 
        observations: List[EarthObservation]
    ) -> int:
        """Insert observations into database"""
        
        if not self.db:
            logger.warning("No database connection")
            return 0
        
        inserted = 0
        async with self.db.acquire() as conn:
            for obs in observations:
                try:
                    first_value = list(obs.variables.values())[0] if obs.variables else 0
                    raw_json = json.dumps(obs.raw_data) if obs.raw_data else None
                    
                    await conn.execute("""
                        INSERT INTO nrt_observations 
                        (h3_index, observation_time, satellite, product, 
                         lat, lon, obs_type, value, confidence, raw_data)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        ON CONFLICT DO NOTHING
                    """,
                        obs.h3_index,
                        obs.observation_time,
                        obs.source,
                        obs.obs_type,
                        obs.lat,
                        obs.lon,
                        obs.obs_type,
                        first_value,
                        obs.confidence,
                        raw_json
                    )
                    inserted += 1
                except Exception as e:
                    logger.error(f"Insert error: {e}")
        
        logger.info(f"Inserted {inserted} observations")
        return inserted
    
    async def run_full_ingestion(
        self,
        region: str = "global",
        bbox: tuple = None
    ) -> Dict[str, int]:
        """Run full data ingestion pipeline"""
        
        results = {}
        
        # 1. NASA FIRMS Fire Data
        logger.info("Ingesting NASA FIRMS fire data...")
        if bbox:
            fires = await self.firms.fetch_fires(bbox=bbox, days=1)
        else:
            fires = await self.firms.fetch_fires(country="DEU", days=1)
        
        if fires:
            results["fires"] = await self.ingest_observations(fires)
        
        # 2. Planetary Computer (if bbox provided)
        if bbox:
            logger.info("Ingesting Sentinel-2 data...")
            today = datetime.utcnow()
            start = (today - timedelta(days=10)).strftime("%Y-%m-%d")
            end = today.strftime("%Y-%m-%d")
            
            sentinel = await self.planetary.get_ndvi_observations(
                bbox=bbox,
                start_date=start,
                end_date=end
            )
            if sentinel:
                results["sentinel"] = await self.ingest_observations(sentinel)
        
        logger.info(f"Ingestion complete: {results}")
        return results


# =====================================================
# CONVENIENCE FUNCTIONS
# =====================================================

async def fetch_current_fires(country: str = "DEU") -> List[Dict]:
    """Quick fetch of current fires"""
    service = NASAFIRMSService()
    fires = await service.fetch_fires(country=country, days=1)
    return [asdict(f) for f in fires]


async def search_satellite_scenes(
    collection: str,
    bbox: tuple,
    days_back: int = 7
) -> List[Dict]:
    """Search for satellite scenes"""
    service = PlanetaryComputerService()
    today = datetime.utcnow()
    start = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")
    
    return await service.search_scenes(
        collection=collection,
        bbox=bbox,
        start_date=start,
        end_date=end
    )


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":
    async def test():
        # Test FIRMS
        print("Testing NASA FIRMS...")
        fires = await fetch_current_fires("DEU")
        print(f"Found {len(fires)} fires in Germany")
        
        # Test Planetary Computer
        print("\nTesting Planetary Computer...")
        bbox = (5.0, 47.0, 15.0, 55.0)  # Germany approx
        scenes = await search_satellite_scenes("sentinel-2-l2a", bbox, 7)
        print(f"Found {len(scenes)} Sentinel-2 scenes")
        
    asyncio.run(test())






















