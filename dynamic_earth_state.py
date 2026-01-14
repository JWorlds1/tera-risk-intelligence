"""
TERA Dynamic Earth State Service
Echtzeit-Erddaten mit minimalem Storage

Prinzip:
- Daten werden ON-DEMAND von APIs abgerufen
- Redis cached kurzfristig (1-6h TTL)
- PostgreSQL speichert nur Tages-Aggregate
- H3 als universeller Spatial Index

Quellen:
- KNMI: Niederlande Radar + Stationen (10min)
- ERA5: Globale Reanalyse (stündlich)
- Sentinel/STAC: Satellitendaten (On-Demand)
- FIRMS: Feuer (NRT)
"""
import asyncio
import httpx
import h3
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict, field
from abc import ABC, abstractmethod
from loguru import logger


# =====================================================
# CONFIGURATION
# =====================================================

@dataclass
class CacheConfig:
    """Cache-Konfiguration"""
    redis_url: str = "redis://localhost:6379/0"
    default_ttl_seconds: int = 3600  # 1 Stunde
    weather_ttl_seconds: int = 600   # 10 Minuten
    satellite_ttl_seconds: int = 21600  # 6 Stunden


@dataclass
class EarthState:
    """Aktueller Erdzustand für eine H3-Zelle"""
    h3_index: str
    timestamp: datetime
    
    # Atmosphäre
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    pressure_hpa: Optional[float] = None
    wind_speed_ms: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    precipitation_mm: Optional[float] = None
    cloud_cover_pct: Optional[float] = None
    
    # Boden
    soil_moisture_pct: Optional[float] = None
    soil_temperature_c: Optional[float] = None
    
    # Vegetation
    ndvi: Optional[float] = None
    lai: Optional[float] = None
    
    # Anomalien (vs. Klimatologie)
    temp_anomaly_c: Optional[float] = None
    precip_anomaly_pct: Optional[float] = None
    
    # Risiko
    fire_risk: Optional[float] = None
    flood_risk: Optional[float] = None
    drought_risk: Optional[float] = None
    
    # Metadaten
    data_sources: List[str] = field(default_factory=list)
    quality_score: float = 1.0


# =====================================================
# CACHE LAYER (Redis-ähnlich, in-memory für Demo)
# =====================================================

class InMemoryCache:
    """Einfacher In-Memory Cache mit TTL"""
    
    def __init__(self):
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self._default_ttl = 3600
    
    def _make_key(self, prefix: str, *args) -> str:
        """Generiert Cache-Key"""
        key_data = f"{prefix}:{':'.join(str(a) for a in args)}"
        return hashlib.md5(key_data.encode()).hexdigest()[:16]
    
    async def get(self, key: str) -> Optional[Any]:
        """Holt Wert aus Cache wenn nicht abgelaufen"""
        if key in self._cache:
            value, expires = self._cache[key]
            if datetime.utcnow() < expires:
                return value
            else:
                del self._cache[key]
        return None
    
    async def set(self, key: str, value: Any, ttl_seconds: int = None):
        """Setzt Wert mit TTL"""
        ttl = ttl_seconds or self._default_ttl
        expires = datetime.utcnow() + timedelta(seconds=ttl)
        self._cache[key] = (value, expires)
    
    async def delete(self, key: str):
        """Löscht Key"""
        if key in self._cache:
            del self._cache[key]
    
    def stats(self) -> Dict[str, int]:
        """Cache-Statistiken"""
        now = datetime.utcnow()
        valid = sum(1 for _, (_, exp) in self._cache.items() if exp > now)
        return {
            "total_keys": len(self._cache),
            "valid_keys": valid,
            "expired_keys": len(self._cache) - valid
        }


# =====================================================
# DATA PROVIDERS (Abstrakte Basis)
# =====================================================

class DataProvider(ABC):
    """Basis-Klasse für Datenquellen"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def cache_ttl(self) -> int:
        """TTL in Sekunden"""
        pass
    
    @abstractmethod
    async def fetch(self, h3_index: str, timestamp: datetime) -> Dict[str, Any]:
        """Holt Daten für H3-Zelle und Zeitpunkt"""
        pass


# =====================================================
# KNMI PROVIDER
# =====================================================

class KNMIProvider(DataProvider):
    """
    KNMI Open Data API
    - 10-Minuten Stationsdaten
    - Radar-Niederschlag
    - Nur für Niederlande (Lat: 50.5-53.5, Lon: 3-7.5)
    """
    
    BASE_URL = "https://api.dataplatform.knmi.nl/open-data/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"Authorization": api_key}
    
    @property
    def name(self) -> str:
        return "KNMI"
    
    @property
    def cache_ttl(self) -> int:
        return 600  # 10 Minuten
    
    def _is_in_netherlands(self, lat: float, lon: float) -> bool:
        """Prüft ob Koordinaten in NL liegen"""
        return 50.5 <= lat <= 53.5 and 3.0 <= lon <= 7.5
    
    async def fetch(self, h3_index: str, timestamp: datetime) -> Dict[str, Any]:
        """Holt KNMI-Daten für H3-Zelle"""
        lat, lon = h3.cell_to_latlng(h3_index)
        
        if not self._is_in_netherlands(lat, lon):
            return {}  # Außerhalb NL
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Hole neueste Radar-Daten
                response = await client.get(
                    f"{self.BASE_URL}/datasets/radar_reflectivity_composites/versions/2.0/files",
                    headers=self.headers,
                    params={"sorting": "desc", "maxKeys": 1}
                )
                
                if response.status_code == 200:
                    files = response.json().get("files", [])
                    if files:
                        return {
                            "source": "KNMI",
                            "radar_available": True,
                            "latest_file": files[0].get("filename"),
                            "coverage": "Netherlands"
                        }
        except Exception as e:
            logger.warning(f"KNMI fetch error: {e}")
        
        return {}


# =====================================================
# ERA5 PROVIDER (Copernicus CDS)
# =====================================================

class ERA5Provider(DataProvider):
    """
    Copernicus ERA5 Reanalyse
    - Globale Abdeckung
    - Stündliche Daten
    - ~30km Auflösung
    """
    
    def __init__(self):
        self.cds_available = False
        try:
            import cdsapi
            self.client = cdsapi.Client()
            self.cds_available = True
        except:
            logger.warning("CDS API not available")
    
    @property
    def name(self) -> str:
        return "ERA5"
    
    @property
    def cache_ttl(self) -> int:
        return 3600  # 1 Stunde (Daten ändern sich nicht)
    
    async def fetch(self, h3_index: str, timestamp: datetime) -> Dict[str, Any]:
        """
        Für Echtzeit: Verwende Klimatologie-Baseline
        ERA5 hat ~5 Tage Latenz, also für "jetzt" verwenden wir Schätzungen
        """
        lat, lon = h3.cell_to_latlng(h3_index)
        
        # Klimatologie-basierte Schätzung (vereinfacht)
        month = timestamp.month
        
        # Basis-Temperatur nach Breitengrad und Monat
        base_temp = 15 - abs(lat) * 0.5
        seasonal_offset = 15 * (1 if 4 <= month <= 9 else -1) * (1 if lat > 0 else -1)
        temp = base_temp + seasonal_offset * 0.3
        
        # Niederschlag (mm/Tag)
        if abs(lat) < 20:  # Tropen
            precip = 8 if month in [6,7,8,9] else 3
        elif abs(lat) < 40:
            precip = 2.5
        else:
            precip = 2.0
        
        return {
            "source": "ERA5_climatology",
            "temperature_c": round(temp, 1),
            "precipitation_mm": round(precip, 1),
            "humidity_pct": 60 + (20 if abs(lat) < 30 else 0),
            "note": "Climatological estimate (ERA5 has 5-day latency)"
        }


# =====================================================
# PLANETARY COMPUTER PROVIDER (Sentinel/STAC)
# =====================================================

class PlanetaryComputerProvider(DataProvider):
    """
    Microsoft Planetary Computer STAC
    - Sentinel-2 (NDVI, Land Cover)
    - MODIS (LST, Vegetation)
    - On-Demand Abfrage
    """
    
    STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
    
    @property
    def name(self) -> str:
        return "PlanetaryComputer"
    
    @property
    def cache_ttl(self) -> int:
        return 21600  # 6 Stunden
    
    async def fetch(self, h3_index: str, timestamp: datetime) -> Dict[str, Any]:
        """Sucht nach Sentinel-2 Szenen für die Zelle"""
        lat, lon = h3.cell_to_latlng(h3_index)
        
        # Bounding Box für H3-Zelle
        boundary = h3.cell_to_boundary(h3_index)
        lats = [p[0] for p in boundary]
        lons = [p[1] for p in boundary]
        bbox = [min(lons), min(lats), max(lons), max(lats)]
        
        # Zeitfenster: letzte 30 Tage
        end_date = timestamp.strftime("%Y-%m-%d")
        start_date = (timestamp - timedelta(days=30)).strftime("%Y-%m-%d")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.STAC_URL}/search",
                    json={
                        "collections": ["sentinel-2-l2a"],
                        "bbox": bbox,
                        "datetime": f"{start_date}/{end_date}",
                        "limit": 1,
                        "query": {"eo:cloud_cover": {"lt": 30}}
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    features = data.get("features", [])
                    
                    if features:
                        props = features[0].get("properties", {})
                        return {
                            "source": "Sentinel-2",
                            "scene_date": props.get("datetime", ""),
                            "cloud_cover": props.get("eo:cloud_cover"),
                            "scenes_available": len(features)
                        }
        except Exception as e:
            logger.warning(f"Planetary Computer error: {e}")
        
        return {}


# =====================================================
# NASA FIRMS PROVIDER (Fire)
# =====================================================

class FIRMSProvider(DataProvider):
    """
    NASA FIRMS - Active Fire Detection
    - VIIRS und MODIS
    - Near Real-Time (3h Latenz)
    """
    
    BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api"
    
    def __init__(self, api_key: str = "DEMO_KEY"):
        self.api_key = api_key
    
    @property
    def name(self) -> str:
        return "NASA_FIRMS"
    
    @property
    def cache_ttl(self) -> int:
        return 1800  # 30 Minuten
    
    async def fetch(self, h3_index: str, timestamp: datetime) -> Dict[str, Any]:
        """Prüft auf aktive Feuer in der Nähe"""
        lat, lon = h3.cell_to_latlng(h3_index)
        
        # Suche in 50km Radius
        bbox = f"{lon-0.5},{lat-0.5},{lon+0.5},{lat+0.5}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/area/csv/{self.api_key}/VIIRS_NOAA20_NRT/{bbox}/1"
                )
                
                if response.status_code == 200:
                    lines = response.text.strip().split('\n')
                    fire_count = max(0, len(lines) - 1)  # Minus Header
                    
                    return {
                        "source": "NASA_FIRMS",
                        "active_fires_nearby": fire_count,
                        "fire_risk": min(1.0, fire_count / 10)
                    }
        except Exception as e:
            logger.warning(f"FIRMS error: {e}")
        
        return {}


# =====================================================
# DYNAMIC EARTH STATE SERVICE
# =====================================================

class DynamicEarthStateService:
    """
    Hauptservice für dynamische Erddaten
    
    Workflow:
    1. Anfrage kommt rein (H3-Index + optionale Zeit)
    2. Cache prüfen
    3. Wenn nicht im Cache: Parallele API-Abfragen
    4. Ergebnisse mergen
    5. In Cache speichern
    6. Zurückgeben
    """
    
    def __init__(
        self,
        knmi_key: str = None,
        firms_key: str = None
    ):
        self.cache = InMemoryCache()
        
        # Provider initialisieren
        self.providers: List[DataProvider] = [
            ERA5Provider(),
            PlanetaryComputerProvider(),
        ]
        
        if knmi_key:
            self.providers.append(KNMIProvider(knmi_key))
        
        if firms_key:
            self.providers.append(FIRMSProvider(firms_key))
        else:
            self.providers.append(FIRMSProvider())  # Demo key
    
    def _cache_key(self, h3_index: str, timestamp: datetime) -> str:
        """Generiert Cache-Key (stündliche Granularität)"""
        hour_str = timestamp.strftime("%Y%m%d%H")
        return f"earth:{h3_index}:{hour_str}"
    
    async def get_state(
        self,
        h3_index: str,
        timestamp: datetime = None
    ) -> EarthState:
        """
        Holt aktuellen Erdzustand für H3-Zelle
        
        Args:
            h3_index: H3-Index der Zelle
            timestamp: Zeitpunkt (default: jetzt)
        
        Returns:
            EarthState mit allen verfügbaren Daten
        """
        timestamp = timestamp or datetime.utcnow()
        cache_key = self._cache_key(h3_index, timestamp)
        
        # 1. Cache prüfen
        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for {h3_index}")
            return EarthState(**cached)
        
        logger.info(f"Fetching fresh data for {h3_index}")
        
        # 2. Parallele API-Abfragen
        tasks = [
            provider.fetch(h3_index, timestamp)
            for provider in self.providers
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 3. Ergebnisse mergen
        merged_data = {
            "h3_index": h3_index,
            "timestamp": timestamp,
            "data_sources": []
        }
        
        for provider, result in zip(self.providers, results):
            if isinstance(result, Exception):
                logger.warning(f"{provider.name} failed: {result}")
                continue
            
            if result:
                merged_data["data_sources"].append(provider.name)
                
                # Daten übernehmen
                if "temperature_c" in result:
                    merged_data["temperature_c"] = result["temperature_c"]
                if "precipitation_mm" in result:
                    merged_data["precipitation_mm"] = result["precipitation_mm"]
                if "humidity_pct" in result:
                    merged_data["humidity_pct"] = result["humidity_pct"]
                if "fire_risk" in result:
                    merged_data["fire_risk"] = result["fire_risk"]
                if "active_fires_nearby" in result:
                    merged_data["fire_risk"] = min(1.0, result["active_fires_nearby"] / 5)
        
        # 4. EarthState erstellen
        lat, lon = h3.cell_to_latlng(h3_index)
        state = EarthState(
            h3_index=h3_index,
            timestamp=timestamp,
            temperature_c=merged_data.get("temperature_c"),
            humidity_pct=merged_data.get("humidity_pct"),
            precipitation_mm=merged_data.get("precipitation_mm"),
            fire_risk=merged_data.get("fire_risk"),
            data_sources=merged_data.get("data_sources", []),
            quality_score=len(merged_data.get("data_sources", [])) / len(self.providers)
        )
        
        # 5. In Cache speichern
        await self.cache.set(cache_key, asdict(state), ttl_seconds=3600)
        
        return state
    
    async def get_states_batch(
        self,
        h3_indices: List[str],
        timestamp: datetime = None
    ) -> Dict[str, EarthState]:
        """Holt Erdzustand für mehrere Zellen parallel"""
        tasks = [self.get_state(idx, timestamp) for idx in h3_indices]
        results = await asyncio.gather(*tasks)
        return {idx: state for idx, state in zip(h3_indices, results)}
    
    async def get_state_for_location(
        self,
        lat: float,
        lon: float,
        resolution: int = 7
    ) -> EarthState:
        """Holt Erdzustand für Koordinaten"""
        h3_index = h3.latlng_to_cell(lat, lon, resolution)
        return await self.get_state(h3_index)
    
    def cache_stats(self) -> Dict[str, Any]:
        """Cache-Statistiken"""
        return self.cache.stats()


# =====================================================
# API ENDPOINTS (für FastAPI Integration)
# =====================================================

async def create_api_router(service: DynamicEarthStateService):
    """Erstellt FastAPI Router für den Service"""
    from fastapi import APIRouter, Query
    
    router = APIRouter()
    
    @router.get("/state/{h3_index}")
    async def get_earth_state(h3_index: str):
        state = await service.get_state(h3_index)
        return asdict(state)
    
    @router.get("/state/location")
    async def get_state_by_location(
        lat: float = Query(...),
        lon: float = Query(...),
        resolution: int = Query(default=7, ge=4, le=10)
    ):
        state = await service.get_state_for_location(lat, lon, resolution)
        return asdict(state)
    
    @router.get("/cache/stats")
    async def get_cache_stats():
        return service.cache_stats()
    
    return router


# =====================================================
# DEMO
# =====================================================

async def demo():
    """Demo des Dynamic Earth State Service"""
    
    print("=" * 60)
    print("🌍 TERA Dynamic Earth State Service")
    print("=" * 60)
    
    # Service initialisieren
    knmi_key = "eyJvcmciOiI1ZTU1NGUxOTI3NGE5NjAwMDEyYTNlYjEiLCJpZCI6IjczNGRmNDBlZTgzMTQ0Njg4NDU1ZjMzODE1YjI1YTM4IiwiaCI6Im11cm11cjEyOCJ9"
    
    service = DynamicEarthStateService(knmi_key=knmi_key)
    
    # Test-Locations
    locations = [
        ("Berlin", 52.52, 13.41),
        ("Amsterdam", 52.37, 4.90),  # In NL für KNMI
        ("Jakarta", -6.21, 106.85),
        ("Miami", 25.76, -80.19),
    ]
    
    print("\n📊 Echtzeit-Erddaten abrufen...\n")
    
    for name, lat, lon in locations:
        print(f"{'='*40}")
        print(f"📍 {name} ({lat:.2f}, {lon:.2f})")
        
        state = await service.get_state_for_location(lat, lon)
        
        print(f"   H3: {state.h3_index}")
        print(f"   Quellen: {', '.join(state.data_sources)}")
        
        if state.temperature_c is not None:
            print(f"   🌡️  Temperatur: {state.temperature_c}°C")
        if state.precipitation_mm is not None:
            print(f"   🌧️  Niederschlag: {state.precipitation_mm} mm")
        if state.humidity_pct is not None:
            print(f"   💧 Luftfeuchte: {state.humidity_pct}%")
        if state.fire_risk is not None:
            print(f"   🔥 Feuerrisiko: {state.fire_risk:.2f}")
        
        print(f"   📊 Qualität: {state.quality_score:.0%}")
    
    # Cache-Stats
    print(f"\n{'='*40}")
    print("📦 Cache-Statistiken:")
    stats = service.cache_stats()
    print(f"   Keys im Cache: {stats['valid_keys']}")
    
    # Zweiter Abruf (aus Cache)
    print(f"\n{'='*40}")
    print("🔄 Zweiter Abruf (sollte aus Cache kommen)...")
    
    state2 = await service.get_state_for_location(52.52, 13.41)
    print(f"   Berlin: {state2.temperature_c}°C")
    
    print(f"\n{'='*60}")
    print("✅ Dynamic Earth State Demo abgeschlossen!")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(demo())






















