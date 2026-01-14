# geocoding.py - Geocoding-Service für geospatial Daten
import asyncio
import aiohttp
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
import structlog
from dataclasses import dataclass

logger = structlog.get_logger(__name__)


@dataclass
class GeoLocation:
    """Geografische Lokation"""
    name: str
    location_type: str  # 'country', 'region', 'city', 'point'
    country_code: Optional[str] = None  # ISO 3166-1 alpha-2
    country_code_3: Optional[str] = None  # ISO 3166-1 alpha-3
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geojson: Optional[Dict] = None
    bbox: Optional[Dict] = None
    confidence: float = 0.0


class GeocodingService:
    """Geocoding-Service mit Nominatim (OpenStreetMap) - kostenlos"""
    
    def __init__(self, cache_file: str = "./data/geocoding_cache.json"):
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.cache_file = Path(cache_file)
        self.cache = self._load_cache()
        self.rate_limit_delay = 1.0  # 1 Request pro Sekunde (Nominatim Limit)
        self.last_request_time = 0.0
        
        # Region-Mapping für Standardisierung
        self.region_mapping = {
            "East Africa": ["KE", "ET", "SO", "UG", "TZ", "RW", "BI", "DJ", "ER"],
            "West Africa": ["SN", "ML", "NE", "NG", "GH", "CI", "BF", "GN", "MR"],
            "Central Africa": ["CM", "CF", "TD", "CG", "CD", "GA", "GQ", "ST"],
            "Southern Africa": ["ZA", "ZW", "BW", "NA", "MZ", "MW", "ZM", "AO"],
            "North Africa": ["EG", "LY", "TN", "DZ", "MA", "SD"],
            "Horn of Africa": ["ET", "ER", "DJ", "SO"],
            "Middle East": ["SA", "AE", "IQ", "IR", "IL", "JO", "LB", "SY", "YE"],
            "South Asia": ["IN", "PK", "BD", "LK", "NP", "BT", "MV", "AF"],
            "Southeast Asia": ["TH", "VN", "ID", "MY", "PH", "SG", "MM", "KH", "LA"],
            "East Asia": ["CN", "JP", "KR", "TW", "MN", "KP"],
            "Central Asia": ["KZ", "UZ", "TM", "KG", "TJ"],
            "Latin America": ["BR", "MX", "AR", "CO", "CL", "PE", "VE", "EC"],
            "Caribbean": ["CU", "JM", "HT", "DO", "TT", "BB", "BS"],
            "Central America": ["GT", "HN", "SV", "NI", "CR", "PA", "BZ"],
            "South America": ["BR", "AR", "CL", "PE", "CO", "VE", "EC", "BO", "PY", "UY"],
            "North America": ["US", "CA", "MX"],
            "Europe": ["DE", "FR", "GB", "IT", "ES", "PL", "RO", "NL", "BE"],
            "Oceania": ["AU", "NZ", "PG", "FJ", "NC", "PF"],
            "Pacific Islands": ["FJ", "PG", "SB", "VU", "NC", "PF", "WS", "TO"],
            "Arctic": ["NO", "SE", "FI", "RU", "IS", "GL", "CA", "US"],
            "Antarctic": []
        }
    
    def _load_cache(self) -> Dict:
        """Lade Geocoding-Cache"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """Speichere Geocoding-Cache"""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    async def _rate_limit(self):
        """Rate Limiting für Nominatim API"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    async def geocode(self, location_text: str, location_type: str = "region") -> Optional[GeoLocation]:
        """Geocode einen Ort"""
        # Prüfe Cache
        cache_key = f"{location_text}_{location_type}"
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            return GeoLocation(**cached_data)
        
        # Rate Limiting
        await self._rate_limit()
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "q": location_text,
                    "format": "json",
                    "limit": 1,
                    "addressdetails": 1
                }
                
                headers = {
                    "User-Agent": "ClimateConflictResearch/1.0 (Research Project)"
                }
                
                async with session.get(self.base_url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data and len(data) > 0:
                            result = data[0]
                            
                            # Extrahiere Koordinaten
                            lat = float(result.get("lat", 0))
                            lon = float(result.get("lon", 0))
                            
                            # Extrahiere Länder-Code
                            address = result.get("address", {})
                            country_code = address.get("country_code", "").upper()
                            
                            # Erstelle GeoLocation
                            geo_location = GeoLocation(
                                name=location_text,
                                location_type=location_type,
                                country_code=country_code if len(country_code) == 2 else None,
                                latitude=lat,
                                longitude=lon,
                                confidence=0.8  # Nominatim ist relativ zuverlässig
                            )
                            
                            # Cache speichern
                            self.cache[cache_key] = {
                                "name": geo_location.name,
                                "location_type": geo_location.location_type,
                                "country_code": geo_location.country_code,
                                "latitude": geo_location.latitude,
                                "longitude": geo_location.longitude,
                                "confidence": geo_location.confidence
                            }
                            self._save_cache()
                            
                            return geo_location
        except Exception as e:
            logger.error(f"Geocoding error for {location_text}: {e}")
            return None
        
        return None
    
    def get_country_codes_for_region(self, region_name: str) -> List[str]:
        """Hole Länder-Codes für eine Region"""
        return self.region_mapping.get(region_name, [])
    
    async def geocode_region(self, region_name: str) -> Optional[GeoLocation]:
        """Geocode eine Region mit Fallback auf Länder-Codes"""
        # Versuche Region direkt zu geocoden
        geo_location = await self.geocode(region_name, "region")
        
        if geo_location and geo_location.latitude:
            return geo_location
        
        # Fallback: Nutze erste Länder-Code der Region
        country_codes = self.get_country_codes_for_region(region_name)
        if country_codes:
            # Geocode erstes Land der Region
            country_name = self._get_country_name(country_codes[0])
            if country_name:
                geo_location = await self.geocode(country_name, "country")
                if geo_location:
                    geo_location.name = region_name
                    geo_location.location_type = "region"
                    return geo_location
        
        return None
    
    def _get_country_name(self, country_code: str) -> Optional[str]:
        """Hole Länder-Name aus Code (vereinfacht)"""
        # ISO 3166-1 alpha-2 zu Name Mapping
        country_names = {
            "KE": "Kenya", "ET": "Ethiopia", "SO": "Somalia",
            "UG": "Uganda", "TZ": "Tanzania", "RW": "Rwanda",
            "BI": "Burundi", "DJ": "Djibouti", "ER": "Eritrea",
            "IN": "India", "BD": "Bangladesh", "PK": "Pakistan",
            "PH": "Philippines", "VN": "Vietnam", "TH": "Thailand",
            "MM": "Myanmar", "ID": "Indonesia", "SD": "Sudan",
            "SS": "South Sudan", "CF": "Central African Republic",
            "TD": "Chad", "ML": "Mali", "NE": "Niger",
            "BF": "Burkina Faso", "NG": "Nigeria", "CM": "Cameroon",
            "HT": "Haiti", "DM": "Dominica", "HN": "Honduras",
            "GT": "Guatemala", "NI": "Nicaragua", "SY": "Syria",
            "IQ": "Iraq", "YE": "Yemen", "AF": "Afghanistan",
            "CN": "China", "BR": "Brazil", "MX": "Mexico",
            "CO": "Colombia", "PE": "Peru", "VE": "Venezuela",
            "EG": "Egypt", "LY": "Libya", "DZ": "Algeria",
            "MA": "Morocco", "TN": "Tunisia", "GH": "Ghana",
            "CI": "Ivory Coast", "SN": "Senegal", "MR": "Mauritania",
            "ZW": "Zimbabwe", "ZM": "Zambia", "MW": "Malawi",
            "MZ": "Mozambique"
        }
        return country_names.get(country_code)
    
    async def batch_geocode(self, locations: List[str]) -> List[Optional[GeoLocation]]:
        """Geocode mehrere Orte"""
        results = []
        for location in locations:
            result = await self.geocode(location)
            results.append(result)
        return results
    
    def geocode_country(self, country_code: str) -> Optional[GeoLocation]:
        """Geocode ein Land synchron (für einfache Nutzung)"""
        # Hole Länder-Name aus Code
        country_name = self._get_country_name(country_code)
        if not country_name:
            # Fallback: Versuche direkt mit Code
            country_name = country_code
        
        # Prüfe Cache
        cache_key = f"{country_name}_country"
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            return GeoLocation(**cached_data)
        
        # Synchroner Geocode - nutze Thread für async execution
        import concurrent.futures
        import asyncio
        
        def run_async():
            """Führe async geocode in neuem Event Loop aus"""
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(self.geocode(country_name, "country"))
            finally:
                new_loop.close()
        
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_async)
                return future.result(timeout=10)
        except Exception as e:
            # Fallback: Return None bei Fehler
            return None


# Beispiel-Nutzung
if __name__ == "__main__":
    async def test():
        geocoder = GeocodingService()
        
        # Test Region
        result = await geocoder.geocode_region("East Africa")
        if result:
            print(f"Region: {result.name}")
            print(f"Coordinates: {result.latitude}, {result.longitude}")
            print(f"Country Code: {result.country_code}")
        
        # Test Country
        result = await geocoder.geocode("Kenya", "country")
        if result:
            print(f"\nCountry: {result.name}")
            print(f"Coordinates: {result.latitude}, {result.longitude}")
    
    asyncio.run(test())

