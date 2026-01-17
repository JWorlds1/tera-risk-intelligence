"""
Geocoding Service
Convert location names to coordinates
"""
import httpx
from typing import Optional, Dict, Any
from functools import lru_cache

from loguru import logger


class GeocodingService:
    """
    Geocoding using Nominatim (OpenStreetMap).
    Free, no API key required, respects rate limits.
    """
    
    BASE_URL = "https://nominatim.openstreetmap.org"
    USER_AGENT = "TERA-EnvironmentalResearch/1.0"
    
    # Cache common locations
    KNOWN_LOCATIONS = {
        "jakarta": {"lat": -6.2088, "lon": 106.8456, "name": "Jakarta, Indonesia"},
        "tokyo": {"lat": 35.6762, "lon": 139.6503, "name": "Tokyo, Japan"},
        "new york": {"lat": 40.7128, "lon": -74.0060, "name": "New York, USA"},
        "london": {"lat": 51.5074, "lon": -0.1278, "name": "London, UK"},
        "lagos": {"lat": 6.5244, "lon": 3.3792, "name": "Lagos, Nigeria"},
        "mumbai": {"lat": 19.0760, "lon": 72.8777, "name": "Mumbai, India"},
        "rotterdam": {"lat": 51.9244, "lon": 4.4777, "name": "Rotterdam, Netherlands"},
        "phoenix": {"lat": 33.4484, "lon": -112.0740, "name": "Phoenix, USA"},
        "miami": {"lat": 25.7617, "lon": -80.1918, "name": "Miami, USA"},
        "dhaka": {"lat": 23.8103, "lon": 90.4125, "name": "Dhaka, Bangladesh"},
        "cairo": {"lat": 30.0444, "lon": 31.2357, "name": "Cairo, Egypt"},
        "nairobi": {"lat": -1.2921, "lon": 36.8219, "name": "Nairobi, Kenya"},
        "darfur": {"lat": 13.5000, "lon": 25.0000, "name": "Darfur, Sudan"},
        "bangladesh": {"lat": 23.6850, "lon": 90.3563, "name": "Bangladesh"},
        "somalia": {"lat": 5.1521, "lon": 46.1996, "name": "Somalia"},
        "yemen": {"lat": 15.5527, "lon": 48.5164, "name": "Yemen"},
    }
    
    async def geocode(self, location: str) -> Optional[Dict[str, Any]]:
        """
        Convert location name to coordinates.
        Returns dict with lat, lon, name or None if not found.
        """
        # Check cache first
        location_lower = location.lower().strip()
        if location_lower in self.KNOWN_LOCATIONS:
            logger.debug(f"Cache hit for: {location}")
            return self.KNOWN_LOCATIONS[location_lower]
        
        # Query Nominatim
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.BASE_URL}/search",
                    params={
                        "q": location,
                        "format": "json",
                        "limit": 1
                    },
                    headers={"User-Agent": self.USER_AGENT}
                )
                
                if response.status_code != 200:
                    logger.warning(f"Geocoding failed for {location}: {response.status_code}")
                    return None
                
                data = response.json()
                
                if not data:
                    logger.warning(f"No results for: {location}")
                    return None
                
                result = data[0]
                geocoded = {
                    "lat": float(result["lat"]),
                    "lon": float(result["lon"]),
                    "name": result.get("display_name", location)
                }
                
                # Cache for future use
                self.KNOWN_LOCATIONS[location_lower] = geocoded
                logger.info(f"Geocoded: {location} -> {geocoded['lat']}, {geocoded['lon']}")
                
                return geocoded
                
        except Exception as e:
            logger.error(f"Geocoding error for {location}: {e}")
            return None
    
    async def reverse_geocode(self, lat: float, lon: float) -> Optional[str]:
        """Convert coordinates to location name"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.BASE_URL}/reverse",
                    params={
                        "lat": lat,
                        "lon": lon,
                        "format": "json"
                    },
                    headers={"User-Agent": self.USER_AGENT}
                )
                
                if response.status_code != 200:
                    return None
                
                data = response.json()
                return data.get("display_name")
                
        except Exception as e:
            logger.error(f"Reverse geocoding error: {e}")
            return None


# Convenience function for routes expecting geocode_city
_geo_service = GeocodingService()


async def geocode_city(location: str) -> Optional[Dict[str, Any]]:
    """Geocode a city/location name to coordinates."""
    return await _geo_service.geocode(location)
