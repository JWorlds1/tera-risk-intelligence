"""
NOAA Ocean Service
Sea Surface Temperature (SST) and Ocean Heat data from NOAA ERDDAP.
Free API, no registration required.
"""

import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

@dataclass
class OceanData:
    sst: float  # Sea Surface Temperature in °C
    sst_anomaly: float  # Difference from climatology
    lat: float
    lon: float
    timestamp: str
    source: str

class NOAAOceanService:
    """
    NOAA ERDDAP provides gridded ocean data including SST.
    MUR SST: 0.01° resolution (~1km)
    """
    
    def __init__(self):
        # MUR SST Analysis (Multi-scale Ultra-high Resolution)
        self.mur_sst_url = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/jplMURSST41.json"
        
        # OISST (Optimum Interpolation SST)
        self.oisst_url = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21Agg.json"
        
    async def get_sst(self, lat: float, lon: float) -> Optional[OceanData]:
        """
        Get current Sea Surface Temperature for a location.
        """
        logger.info(f"🌊 NOAA: Fetching SST for ({lat}, {lon})")
        
        # Get most recent date (usually yesterday due to processing time)
        yesterday = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        
        # Build ERDDAP query
        # Format: dataset[(time)][(lat)][(lon)]
        query = f"?analysed_sst[({yesterday}T09:00:00Z)][({lat}):1:({lat})][({lon}):1:({lon})]"
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(self.mur_sst_url + query)
                
                if response.status_code != 200:
                    logger.warning(f"NOAA MUR SST returned {response.status_code}")
                    return None
                
                data = response.json()
                
                # Parse ERDDAP response
                table = data.get("table", {})
                rows = table.get("rows", [])
                
                if rows:
                    # SST in Kelvin, convert to Celsius
                    sst_kelvin = rows[0][3] if len(rows[0]) > 3 else None
                    if sst_kelvin:
                        sst_celsius = sst_kelvin - 273.15
                        
                        # Calculate anomaly (rough estimate based on latitude)
                        # Real climatology would come from NOAA databases
                        expected_sst = 28 - abs(lat) * 0.5  # Rough tropical-temperate gradient
                        anomaly = sst_celsius - expected_sst
                        
                        return OceanData(
                            sst=round(sst_celsius, 2),
                            sst_anomaly=round(anomaly, 2),
                            lat=lat,
                            lon=lon,
                            timestamp=yesterday,
                            source="NOAA MUR SST (1km)"
                        )
                
                logger.warning("NOAA: No SST data in response")
                return None
                
        except Exception as e:
            logger.error(f"NOAA SST error: {e}")
            return None
    
    async def get_ocean_risk(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Calculate ocean-related risk score.
        High SST anomalies = higher hurricane intensity, coral bleaching risk.
        """
        sst_data = await self.get_sst(lat, lon)
        
        if not sst_data:
            # Fallback: estimate based on location
            is_tropical = abs(lat) < 30
            is_coastal = True  # Assume coastal for now
            
            return {
                "score": 0.3 if is_tropical else 0.1,
                "sst": None,
                "sst_anomaly": None,
                "hurricane_potential": "moderate" if is_tropical else "low",
                "coral_bleaching_risk": "unknown",
                "source": "Estimated (no data)",
                "confidence": "low"
            }
        
        # Risk calculation based on SST anomaly
        anomaly = sst_data.sst_anomaly
        
        # Hurricane intensification threshold: > 26°C, stronger > 28°C
        hurricane_risk = 0
        if sst_data.sst > 26:
            hurricane_risk = min(1.0, (sst_data.sst - 26) / 6)  # 26-32°C -> 0-1
        
        # Coral bleaching risk: anomaly > 1°C is concerning, > 2°C is severe
        coral_risk = 0
        if anomaly > 0:
            coral_risk = min(1.0, anomaly / 3)  # 0-3°C anomaly -> 0-1
        
        # Combined ocean heat risk
        ocean_risk = (hurricane_risk * 0.6 + coral_risk * 0.4)
        
        return {
            "score": round(ocean_risk, 3),
            "sst": sst_data.sst,
            "sst_anomaly": sst_data.sst_anomaly,
            "hurricane_potential": "high" if hurricane_risk > 0.6 else "moderate" if hurricane_risk > 0.3 else "low",
            "coral_bleaching_risk": "severe" if coral_risk > 0.6 else "elevated" if coral_risk > 0.3 else "low",
            "source": sst_data.source,
            "confidence": "high"
        }
    
    async def get_coastal_flood_factor(self, lat: float, lon: float, year: int = 2026) -> float:
        """
        Estimate additional coastal flood risk from ocean conditions.
        Combines thermal expansion and current SST anomalies.
        """
        sst_data = await self.get_sst(lat, lon)
        
        if not sst_data:
            return 1.0  # Neutral factor
        
        # Warmer oceans = more thermal expansion = higher sea levels
        # Each 1°C anomaly adds ~2cm to local sea level (simplified)
        thermal_factor = 1.0 + (sst_data.sst_anomaly * 0.02) if sst_data.sst_anomaly > 0 else 1.0
        
        # Future projection (simplified IPCC-based)
        years_from_now = year - 2024
        projection_factor = 1.0 + (years_from_now * 0.003)  # ~0.3% per year increase
        
        return round(thermal_factor * projection_factor, 3)

# Singleton
noaa_service = NOAAOceanService()
