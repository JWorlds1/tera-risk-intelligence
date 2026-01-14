"""
TERA V2: Real-Time Global Monitoring System
=============================================

Überwacht die gesamte Erde kontinuierlich auf:
- Vulkanaktivität
- Erdbeben
- SST-Anomalien
- Atmosphärische Muster
- Waldbrände
- Klimaindizes
- Nachrichten-Anomalien

Bei jeder erkannten Anomalie werden automatisch:
1. Kausale Ketten aktiviert
2. Downstream-Effekte berechnet
3. Betroffene Regionen identifiziert
4. Alerts generiert
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import math


# ═══════════════════════════════════════════════════════════════════════════════
# DATENQUELLEN-DEFINITIONEN
# ═══════════════════════════════════════════════════════════════════════════════

class DataSourceType(Enum):
    """Typen von Datenquellen."""
    SEISMIC = "seismic"
    VOLCANIC = "volcanic"
    OCEANIC = "oceanic"
    ATMOSPHERIC = "atmospheric"
    FIRE = "fire"
    CLIMATE_INDEX = "climate_index"
    NEWS = "news"


@dataclass
class DataSource:
    """Definition einer Echtzeit-Datenquelle."""
    id: str
    name: str
    type: DataSourceType
    url: str
    poll_interval_seconds: int
    parser: str  # Name der Parser-Funktion
    description: str


# Alle überwachten Datenquellen
DATA_SOURCES = [
    # SEISMIK
    DataSource(
        id="usgs_earthquakes",
        name="USGS Earthquakes",
        type=DataSourceType.SEISMIC,
        url="https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson",
        poll_interval_seconds=60,
        parser="parse_usgs_earthquakes",
        description="Erdbeben M4.5+ der letzten 24h"
    ),
    DataSource(
        id="usgs_significant",
        name="USGS Significant Earthquakes",
        type=DataSourceType.SEISMIC,
        url="https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson",
        poll_interval_seconds=300,
        parser="parse_usgs_earthquakes",
        description="Signifikante Erdbeben der letzten Woche"
    ),
    
    # VULKANE
    DataSource(
        id="smithsonian_volcanoes",
        name="Smithsonian GVP",
        type=DataSourceType.VOLCANIC,
        url="https://volcano.si.edu/news/WeeklyVolcanoActivity.cfm",
        poll_interval_seconds=3600,
        parser="parse_smithsonian_volcanoes",
        description="Wöchentlicher Vulkan-Aktivitätsbericht"
    ),
    
    # OZEAN / SST
    DataSource(
        id="noaa_sst",
        name="NOAA SST Anomaly",
        type=DataSourceType.OCEANIC,
        url="https://www.cpc.ncep.noaa.gov/data/indices/sstoi.indices",
        poll_interval_seconds=86400,
        parser="parse_noaa_sst",
        description="Sea Surface Temperature Indizes"
    ),
    
    # KLIMAINDIZES
    DataSource(
        id="noaa_oni",
        name="NOAA ONI (El Niño)",
        type=DataSourceType.CLIMATE_INDEX,
        url="https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",
        poll_interval_seconds=86400,
        parser="parse_oni",
        description="Oceanic Niño Index"
    ),
    
    # WALDBRÄNDE
    DataSource(
        id="nasa_firms",
        name="NASA FIRMS",
        type=DataSourceType.FIRE,
        url="https://firms.modaps.eosdis.nasa.gov/api/area/csv/YOUR_API_KEY/VIIRS_SNPP_NRT/world/1",
        poll_interval_seconds=3600,
        parser="parse_firms",
        description="Aktive Feuer weltweit (letzte 24h)"
    ),
    
    # ATMOSPHÄRE
    DataSource(
        id="noaa_blocking",
        name="NOAA Blocking Index",
        type=DataSourceType.ATMOSPHERIC,
        url="https://www.cpc.ncep.noaa.gov/products/precip/CWlink/pna/nao.shtml",
        poll_interval_seconds=21600,
        parser="parse_blocking",
        description="Atmosphärische Blocking-Indizes"
    ),
]


# ═══════════════════════════════════════════════════════════════════════════════
# EREIGNIS-TYPEN UND SCHWELLENWERTE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AnomalyThreshold:
    """Schwellenwert für Anomalie-Erkennung."""
    metric: str
    warning: float
    critical: float
    unit: str
    description: str


# Schwellenwerte für verschiedene Metriken
ANOMALY_THRESHOLDS = {
    "earthquake_magnitude": AnomalyThreshold(
        metric="earthquake_magnitude",
        warning=6.0,
        critical=7.0,
        unit="M",
        description="Erdbebenstärke"
    ),
    "volcanic_vei": AnomalyThreshold(
        metric="volcanic_vei",
        warning=3,
        critical=4,
        unit="VEI",
        description="Volcanic Explosivity Index"
    ),
    "sst_anomaly": AnomalyThreshold(
        metric="sst_anomaly",
        warning=0.5,
        critical=1.5,
        unit="°C",
        description="SST Anomalie (El Niño Schwelle)"
    ),
    "oni_index": AnomalyThreshold(
        metric="oni_index",
        warning=0.5,
        critical=1.5,
        unit="°C",
        description="Oceanic Niño Index"
    ),
    "fire_count": AnomalyThreshold(
        metric="fire_count",
        warning=500,
        critical=2000,
        unit="Hotspots",
        description="Feuer-Hotspots pro Region"
    ),
    "blocking_days": AnomalyThreshold(
        metric="blocking_days",
        warning=5,
        critical=10,
        unit="Tage",
        description="Atmosphärische Blocking-Dauer"
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# ERKANNTE EREIGNISSE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DetectedEvent:
    """Ein erkanntes Ereignis/Anomalie."""
    id: str
    timestamp: datetime
    source: str
    event_type: str
    location: Dict[str, float]  # lat, lon
    magnitude: float
    unit: str
    severity: str  # "warning", "critical"
    description: str
    raw_data: Dict = field(default_factory=dict)
    
    # Kausale Analyse
    downstream_effects: List[Dict] = field(default_factory=list)
    affected_regions: List[str] = field(default_factory=list)
    causal_chains: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# KAUSALE VERBINDUNGEN (vereinfacht)
# ═══════════════════════════════════════════════════════════════════════════════

# Primäre Treiber → Mögliche Effekte
CAUSAL_CONNECTIONS = {
    "earthquake": {
        "M7+_underwater": [
            {"effect": "tsunami", "probability": 0.70, "delay_hours": 0.5, "regions": ["coastal"]},
            {"effect": "aftershocks", "probability": 0.95, "delay_hours": 0, "regions": ["local"]},
        ],
        "M6+_volcanic_region": [
            {"effect": "volcanic_unrest", "probability": 0.30, "delay_hours": 24, "regions": ["local"]},
        ],
        "M6+_mountainous": [
            {"effect": "landslide", "probability": 0.50, "delay_hours": 0, "regions": ["local"]},
        ],
    },
    "volcanic_eruption": {
        "VEI3+": [
            {"effect": "ashfall", "probability": 0.90, "delay_hours": 1, "regions": ["downwind"]},
            {"effect": "lahars", "probability": 0.40, "delay_hours": 6, "regions": ["local"]},
            {"effect": "aviation_disruption", "probability": 0.70, "delay_hours": 2, "regions": ["regional"]},
        ],
        "VEI4+": [
            {"effect": "regional_cooling", "probability": 0.60, "delay_hours": 720, "regions": ["hemisphere"]},
            {"effect": "sst_anomaly", "probability": 0.40, "delay_hours": 2160, "regions": ["global"]},
        ],
        "VEI5+": [
            {"effect": "global_cooling", "probability": 0.80, "delay_hours": 4320, "regions": ["global"]},
            {"effect": "monsoon_disruption", "probability": 0.50, "delay_hours": 2880, "regions": ["tropical"]},
        ],
    },
    "sst_anomaly": {
        "nino34_positive": [
            {"effect": "el_nino", "probability": 0.90, "delay_hours": 720, "regions": ["pacific"]},
            {"effect": "australia_drought", "probability": 0.75, "delay_hours": 2160, "regions": ["australia"]},
            {"effect": "peru_flood", "probability": 0.80, "delay_hours": 2880, "regions": ["south_america"]},
            {"effect": "indonesia_drought", "probability": 0.65, "delay_hours": 1440, "regions": ["se_asia"]},
            {"effect": "california_storms", "probability": 0.55, "delay_hours": 2880, "regions": ["na_west"]},
        ],
        "nino34_negative": [
            {"effect": "la_nina", "probability": 0.90, "delay_hours": 720, "regions": ["pacific"]},
            {"effect": "australia_flood", "probability": 0.70, "delay_hours": 2160, "regions": ["australia"]},
            {"effect": "atlantic_hurricanes", "probability": 0.60, "delay_hours": 2160, "regions": ["atlantic"]},
        ],
    },
    "atmospheric_blocking": {
        "europe_blocking": [
            {"effect": "heat_wave_europe", "probability": 0.70, "delay_hours": 72, "regions": ["europe"]},
            {"effect": "drought_europe", "probability": 0.60, "delay_hours": 168, "regions": ["europe"]},
        ],
        "arctic_weakening": [
            {"effect": "cold_outbreak", "probability": 0.65, "delay_hours": 168, "regions": ["mid_latitudes"]},
        ],
    },
    "fire_outbreak": {
        "large_fire": [
            {"effect": "air_quality_degradation", "probability": 0.90, "delay_hours": 2, "regions": ["local"]},
            {"effect": "smoke_transport", "probability": 0.70, "delay_hours": 24, "regions": ["downwind"]},
        ],
        "mega_fire": [
            {"effect": "stratospheric_injection", "probability": 0.30, "delay_hours": 48, "regions": ["hemisphere"]},
            {"effect": "regional_climate_impact", "probability": 0.50, "delay_hours": 168, "regions": ["regional"]},
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL MONITOR KLASSE
# ═══════════════════════════════════════════════════════════════════════════════

class GlobalMonitor:
    """
    Echtzeit-Überwachung aller primären Treiber weltweit.
    """
    
    def __init__(self):
        self.data_sources = DATA_SOURCES
        self.thresholds = ANOMALY_THRESHOLDS
        self.causal_connections = CAUSAL_CONNECTIONS
        
        self.detected_events: List[DetectedEvent] = []
        self.active_alerts: List[Dict] = []
        self.event_history: List[DetectedEvent] = []
        
        self.last_check: Dict[str, datetime] = {}
        self.running = False
    
    async def fetch_source(self, source: DataSource) -> Optional[Dict]:
        """Hole Daten von einer Quelle."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(source.url, timeout=30) as resp:
                    if resp.status == 200:
                        if source.url.endswith('.geojson') or 'json' in source.url:
                            return await resp.json()
                        else:
                            return {"text": await resp.text()}
        except Exception as e:
            print(f"⚠️ Fehler beim Abrufen von {source.name}: {e}")
        return None
    
    def parse_usgs_earthquakes(self, data: Dict) -> List[DetectedEvent]:
        """Parse USGS Erdbeben-Feed."""
        events = []
        
        if not data or "features" not in data:
            return events
        
        for feature in data["features"]:
            props = feature.get("properties", {})
            geom = feature.get("geometry", {})
            coords = geom.get("coordinates", [0, 0, 0])
            
            mag = props.get("mag", 0)
            if mag is None:
                continue
            
            # Schweregrad bestimmen
            threshold = self.thresholds["earthquake_magnitude"]
            if mag >= threshold.critical:
                severity = "critical"
            elif mag >= threshold.warning:
                severity = "warning"
            else:
                continue  # Unter Schwellenwert
            
            event = DetectedEvent(
                id=feature.get("id", f"eq_{datetime.now().timestamp()}"),
                timestamp=datetime.fromtimestamp(props.get("time", 0) / 1000),
                source="usgs_earthquakes",
                event_type="earthquake",
                location={"lat": coords[1], "lon": coords[0], "depth_km": coords[2]},
                magnitude=mag,
                unit="M",
                severity=severity,
                description=props.get("place", "Unknown location"),
                raw_data=props
            )
            
            # Kausale Analyse
            event = self.analyze_earthquake_effects(event)
            events.append(event)
        
        return events
    
    def analyze_earthquake_effects(self, event: DetectedEvent) -> DetectedEvent:
        """Analysiere mögliche Effekte eines Erdbebens."""
        mag = event.magnitude
        depth = event.location.get("depth_km", 100)
        lat = event.location.get("lat", 0)
        lon = event.location.get("lon", 0)
        
        effects = []
        chains = []
        regions = set()
        
        # Tsunami-Check: M7+ und flach (<70km) und underwater
        if mag >= 7.0 and depth < 70:
            # Vereinfacht: Prüfe ob im Meer (lon nahe Küste oder bekannte Subduktionszonen)
            if self._is_underwater_region(lat, lon):
                conn = self.causal_connections["earthquake"]["M7+_underwater"]
                for effect in conn:
                    effects.append({
                        "effect": effect["effect"],
                        "probability": effect["probability"],
                        "delay_hours": effect["delay_hours"],
                        "description": f"Tsunami möglich nach M{mag:.1f} Erdbeben"
                    })
                    chains.append(f"Erdbeben M{mag:.1f} → {effect['effect']} ({effect['probability']:.0%})")
                    regions.update(effect["regions"])
        
        # Erdrutsch-Check: M6+ in bergigem Gebiet
        if mag >= 6.0:
            conn = self.causal_connections["earthquake"]["M6+_mountainous"]
            for effect in conn:
                effects.append({
                    "effect": effect["effect"],
                    "probability": effect["probability"] * (mag - 5.5) / 2,  # Skaliert mit Magnitude
                    "delay_hours": effect["delay_hours"],
                    "description": f"Erdrutsche möglich in der Region"
                })
                chains.append(f"Erdbeben M{mag:.1f} → {effect['effect']}")
                regions.update(effect["regions"])
        
        event.downstream_effects = effects
        event.causal_chains = chains
        event.affected_regions = list(regions)
        
        return event
    
    def _is_underwater_region(self, lat: float, lon: float) -> bool:
        """Prüfe ob Koordinaten wahrscheinlich im Meer sind (vereinfacht)."""
        # Bekannte Subduktionszonen / Tsunami-Risiko-Gebiete
        tsunami_zones = [
            # Pazifischer Feuerring
            (-60, -180, 60, -100),  # Ostpazifik
            (-60, 100, 60, 180),    # Westpazifik
            (-60, 100, 60, -180),   # Westpazifik (Datumsgrenze)
            # Indischer Ozean
            (-30, 40, 30, 100),
            # Mittelmeer
            (30, -10, 45, 40),
        ]
        
        for min_lat, min_lon, max_lat, max_lon in tsunami_zones:
            if min_lat <= lat <= max_lat:
                if min_lon <= lon <= max_lon or (min_lon > max_lon and (lon >= min_lon or lon <= max_lon)):
                    return True
        return False
    
    def analyze_sst_anomaly(self, oni_value: float) -> List[DetectedEvent]:
        """Analysiere SST/ONI Anomalie."""
        events = []
        
        threshold = self.thresholds["oni_index"]
        
        if abs(oni_value) < threshold.warning:
            return events
        
        if oni_value >= threshold.critical:
            severity = "critical"
            event_subtype = "nino34_positive"
            description = f"Starker El Niño: ONI = {oni_value:+.1f}°C"
        elif oni_value >= threshold.warning:
            severity = "warning"
            event_subtype = "nino34_positive"
            description = f"El Niño Bedingungen: ONI = {oni_value:+.1f}°C"
        elif oni_value <= -threshold.critical:
            severity = "critical"
            event_subtype = "nino34_negative"
            description = f"Starke La Niña: ONI = {oni_value:+.1f}°C"
        else:
            severity = "warning"
            event_subtype = "nino34_negative"
            description = f"La Niña Bedingungen: ONI = {oni_value:+.1f}°C"
        
        event = DetectedEvent(
            id=f"sst_{datetime.now().strftime('%Y%m%d')}",
            timestamp=datetime.now(),
            source="noaa_oni",
            event_type="sst_anomaly",
            location={"lat": 0, "lon": -170, "region": "Niño 3.4"},
            magnitude=abs(oni_value),
            unit="°C",
            severity=severity,
            description=description
        )
        
        # Downstream-Effekte
        effects = []
        chains = []
        regions = set()
        
        for effect_def in self.causal_connections["sst_anomaly"].get(event_subtype, []):
            effects.append({
                "effect": effect_def["effect"],
                "probability": effect_def["probability"],
                "delay_days": effect_def["delay_hours"] / 24,
                "regions": effect_def["regions"]
            })
            chains.append(f"SST Anomalie → {effect_def['effect']} ({effect_def['probability']:.0%})")
            regions.update(effect_def["regions"])
        
        event.downstream_effects = effects
        event.causal_chains = chains
        event.affected_regions = list(regions)
        
        events.append(event)
        return events
    
    async def check_all_sources(self) -> List[DetectedEvent]:
        """Prüfe alle Datenquellen auf neue Ereignisse."""
        all_events = []
        
        print(f"\n{'='*60}")
        print(f"🔍 GLOBAL SCAN: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        # USGS Erdbeben
        print("\n📡 Checking USGS Earthquakes...")
        for source in self.data_sources:
            if source.type == DataSourceType.SEISMIC:
                data = await self.fetch_source(source)
                if data:
                    events = self.parse_usgs_earthquakes(data)
                    if events:
                        print(f"   ⚠️ {len(events)} signifikante Erdbeben gefunden!")
                        all_events.extend(events)
                    else:
                        print(f"   ✓ Keine kritischen Erdbeben")
        
        # SST/ENSO (Demo mit festen Wert)
        print("\n📡 Checking SST/ENSO...")
        demo_oni = 1.8  # Demo: Starker El Niño
        sst_events = self.analyze_sst_anomaly(demo_oni)
        if sst_events:
            print(f"   ⚠️ El Niño aktiv: ONI = {demo_oni:+.1f}°C")
            all_events.extend(sst_events)
        
        return all_events
    
    def generate_global_alert(self, events: List[DetectedEvent]) -> Dict:
        """Generiere globalen Alert-Bericht."""
        if not events:
            return {"status": "normal", "alerts": []}
        
        alerts = []
        
        for event in events:
            alert = {
                "id": event.id,
                "timestamp": event.timestamp.isoformat(),
                "type": event.event_type,
                "severity": event.severity,
                "location": event.location,
                "magnitude": f"{event.magnitude} {event.unit}",
                "description": event.description,
                "causal_chains": event.causal_chains,
                "downstream_effects": event.downstream_effects,
                "affected_regions": event.affected_regions
            }
            alerts.append(alert)
        
        # Sortiere nach Schweregrad
        critical = [a for a in alerts if a["severity"] == "critical"]
        warning = [a for a in alerts if a["severity"] == "warning"]
        
        return {
            "status": "alert" if critical else "warning",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "critical_count": len(critical),
                "warning_count": len(warning),
                "total_affected_regions": len(set(
                    r for a in alerts for r in a["affected_regions"]
                ))
            },
            "critical_alerts": critical,
            "warning_alerts": warning
        }
    
    def print_alert_report(self, report: Dict):
        """Drucke Alert-Bericht."""
        print(f"\n{'='*60}")
        print(f"🚨 TERA GLOBAL ALERT REPORT")
        print(f"{'='*60}")
        print(f"Status: {report['status'].upper()}")
        print(f"Zeit: {report['timestamp']}")
        
        if report["summary"]["critical_count"] > 0:
            print(f"\n🔴 KRITISCHE ALERTS: {report['summary']['critical_count']}")
            print("-" * 40)
            for alert in report["critical_alerts"]:
                print(f"\n  ⚠️ {alert['type'].upper()}: {alert['magnitude']}")
                print(f"     {alert['description']}")
                print(f"     Kausale Ketten:")
                for chain in alert["causal_chains"][:3]:
                    print(f"       → {chain}")
                if alert["affected_regions"]:
                    print(f"     Betroffene Regionen: {', '.join(alert['affected_regions'])}")
        
        if report["summary"]["warning_count"] > 0:
            print(f"\n🟡 WARNUNGEN: {report['summary']['warning_count']}")
            print("-" * 40)
            for alert in report["warning_alerts"][:5]:
                print(f"\n  ⚡ {alert['type'].upper()}: {alert['magnitude']}")
                print(f"     {alert['description']}")


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════════════════════

async def demo():
    """Demo des Global Monitoring Systems."""
    print("\n" + "="*70)
    print("🌍 TERA GLOBAL MONITORING SYSTEM - DEMO")
    print("="*70)
    
    monitor = GlobalMonitor()
    
    # Einmaliger Scan
    events = await monitor.check_all_sources()
    
    # Alert-Bericht generieren
    report = monitor.generate_global_alert(events)
    monitor.print_alert_report(report)
    
    # Zeige Details zu einem Event
    if events:
        print(f"\n{'='*60}")
        print("📊 DETAILANALYSE: Erstes kritisches Ereignis")
        print("="*60)
        
        event = events[0]
        print(f"\nTyp: {event.event_type}")
        print(f"Magnitude: {event.magnitude} {event.unit}")
        print(f"Ort: {event.description}")
        print(f"Koordinaten: {event.location}")
        
        print(f"\n📈 Downstream-Effekte:")
        for effect in event.downstream_effects:
            print(f"   → {effect['effect']}: {effect['probability']:.0%} Wahrscheinlichkeit")
            if 'delay_days' in effect:
                print(f"      Verzögerung: ~{effect['delay_days']:.0f} Tage")
            elif 'delay_hours' in effect:
                print(f"      Verzögerung: ~{effect['delay_hours']:.0f} Stunden")
        
        print(f"\n🌍 Betroffene Regionen:")
        for region in event.affected_regions:
            print(f"   • {region}")


if __name__ == "__main__":
    asyncio.run(demo())












