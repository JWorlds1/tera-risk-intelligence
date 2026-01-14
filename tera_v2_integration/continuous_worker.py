"""
TERA V2: Continuous Monitoring Worker
======================================

Läuft als Daemon-Prozess und überwacht kontinuierlich alle Datenquellen.
Bei erkannten Anomalien werden automatisch Alerts generiert und gepusht.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Set
from dataclasses import dataclass, asdict
import signal
import sys

from realtime_global_monitor import GlobalMonitor, DetectedEvent


@dataclass
class WorldState:
    """Aktueller Zustand der Erde."""
    timestamp: str
    
    # Klimaindizes
    climate_modes: Dict[str, float]
    enso_status: str
    
    # Aktive Anomalien
    active_anomalies: List[Dict]
    
    # Aktive Vorhersagen
    active_predictions: List[Dict]
    
    # Alerts nach Region
    alerts_by_region: Dict[str, List[str]]
    
    # Statistiken
    total_events_24h: int
    critical_count: int
    warning_count: int


class ContinuousWorker:
    """
    Kontinuierlicher Monitoring-Worker.
    
    Führt regelmäßige Scans durch und hält den World State aktuell.
    """
    
    def __init__(self):
        self.monitor = GlobalMonitor()
        self.world_state: WorldState = None
        self.event_history: List[DetectedEvent] = []
        self.seen_event_ids: Set[str] = set()
        self.running = False
        
        # Scan-Intervalle (Sekunden)
        self.intervals = {
            "earthquake": 60,      # 1 Minute
            "volcano": 3600,       # 1 Stunde
            "sst": 21600,          # 6 Stunden
            "fire": 3600,          # 1 Stunde
            "news": 900,           # 15 Minuten
        }
        
        self.last_scan: Dict[str, datetime] = {}
    
    async def scan_earthquakes(self) -> List[DetectedEvent]:
        """Scanne USGS auf neue Erdbeben."""
        events = []
        
        for source in self.monitor.data_sources:
            if source.id in ["usgs_earthquakes", "usgs_significant"]:
                data = await self.monitor.fetch_source(source)
                if data:
                    parsed = self.monitor.parse_usgs_earthquakes(data)
                    
                    # Nur neue Events
                    for event in parsed:
                        if event.id not in self.seen_event_ids:
                            self.seen_event_ids.add(event.id)
                            events.append(event)
        
        return events
    
    async def scan_sst(self) -> List[DetectedEvent]:
        """Scanne SST/ENSO Status."""
        # Demo-Wert - in Produktion von NOAA API
        oni_value = 1.8
        return self.monitor.analyze_sst_anomaly(oni_value)
    
    def update_world_state(self, new_events: List[DetectedEvent]):
        """Aktualisiere den World State."""
        # Füge neue Events zur Historie hinzu
        self.event_history.extend(new_events)
        
        # Entferne alte Events (>24h)
        cutoff = datetime.now() - timedelta(hours=24)
        self.event_history = [e for e in self.event_history if e.timestamp > cutoff]
        
        # Berechne Statistiken
        critical = [e for e in self.event_history if e.severity == "critical"]
        warning = [e for e in self.event_history if e.severity == "warning"]
        
        # Sammle Regionen
        alerts_by_region: Dict[str, List[str]] = {}
        for event in self.event_history:
            for region in event.affected_regions:
                if region not in alerts_by_region:
                    alerts_by_region[region] = []
                alerts_by_region[region].append(event.event_type)
        
        # Aktive Vorhersagen sammeln
        predictions = []
        for event in self.event_history:
            for effect in event.downstream_effects:
                predictions.append({
                    "trigger": event.event_type,
                    "effect": effect.get("effect"),
                    "probability": effect.get("probability"),
                    "timing": effect.get("delay_days") or effect.get("delay_hours"),
                    "regions": effect.get("regions", event.affected_regions)
                })
        
        self.world_state = WorldState(
            timestamp=datetime.now().isoformat(),
            climate_modes={"ENSO": 1.8, "IOD": 0.8, "AMO": 0.4},
            enso_status="El Niño (stark)",
            active_anomalies=[{
                "type": e.event_type,
                "magnitude": f"{e.magnitude} {e.unit}",
                "location": e.description,
                "severity": e.severity
            } for e in self.event_history[-10:]],
            active_predictions=predictions[:20],
            alerts_by_region=alerts_by_region,
            total_events_24h=len(self.event_history),
            critical_count=len(critical),
            warning_count=len(warning)
        )
    
    def print_status(self):
        """Drucke aktuellen Status."""
        if not self.world_state:
            return
        
        ws = self.world_state
        
        print(f"\n{'═'*70}")
        print(f"🌍 TERA WORLD STATE - {ws.timestamp}")
        print(f"{'═'*70}")
        
        print(f"\n📊 ÜBERSICHT (letzte 24h):")
        print(f"   Events: {ws.total_events_24h}")
        print(f"   🔴 Kritisch: {ws.critical_count}")
        print(f"   🟡 Warnung: {ws.warning_count}")
        
        print(f"\n🌡️ KLIMAINDIZES:")
        for mode, value in ws.climate_modes.items():
            print(f"   {mode}: {value:+.1f}")
        print(f"   Status: {ws.enso_status}")
        
        if ws.active_anomalies:
            print(f"\n⚠️ AKTIVE ANOMALIEN:")
            for a in ws.active_anomalies[:5]:
                emoji = "🔴" if a["severity"] == "critical" else "🟡"
                print(f"   {emoji} {a['type']}: {a['magnitude']} - {a['location'][:40]}")
        
        if ws.alerts_by_region:
            print(f"\n🗺️ ALERTS NACH REGION:")
            for region, alerts in list(ws.alerts_by_region.items())[:5]:
                print(f"   {region}: {', '.join(set(alerts))}")
        
        if ws.active_predictions:
            print(f"\n📈 AKTIVE VORHERSAGEN:")
            for p in ws.active_predictions[:5]:
                print(f"   → {p['effect']}: {p['probability']:.0%} in {p.get('timing', '?')} "
                      f"(Trigger: {p['trigger']})")
    
    async def run_once(self):
        """Führe einen einzelnen Scan-Zyklus durch."""
        now = datetime.now()
        new_events = []
        
        # Prüfe welche Scans fällig sind
        for source_type, interval in self.intervals.items():
            last = self.last_scan.get(source_type)
            
            if last is None or (now - last).total_seconds() >= interval:
                self.last_scan[source_type] = now
                
                if source_type == "earthquake":
                    events = await self.scan_earthquakes()
                    if events:
                        print(f"🌍 {len(events)} neue Erdbeben erkannt")
                        new_events.extend(events)
                
                elif source_type == "sst":
                    events = await self.scan_sst()
                    if events:
                        print(f"🌊 SST Anomalie aktualisiert")
                        # SST nur hinzufügen wenn noch nicht vorhanden
                        for e in events:
                            if e.id not in self.seen_event_ids:
                                self.seen_event_ids.add(e.id)
                                new_events.append(e)
        
        # Update World State
        if new_events or not self.world_state:
            self.update_world_state(new_events)
            self.print_status()
    
    async def run_continuous(self, duration_minutes: int = None):
        """
        Starte kontinuierliche Überwachung.
        
        Args:
            duration_minutes: Laufzeit in Minuten (None = unbegrenzt)
        """
        self.running = True
        start_time = datetime.now()
        scan_interval = 30  # Sekunden zwischen Checks
        
        print(f"\n{'═'*70}")
        print(f"🚀 TERA CONTINUOUS MONITORING STARTED")
        print(f"{'═'*70}")
        print(f"Zeit: {start_time}")
        print(f"Scan-Intervall: {scan_interval}s")
        if duration_minutes:
            print(f"Geplante Laufzeit: {duration_minutes} Minuten")
        print(f"\nDrücke Ctrl+C zum Beenden.")
        
        try:
            while self.running:
                await self.run_once()
                
                # Prüfe Laufzeit
                if duration_minutes:
                    elapsed = (datetime.now() - start_time).total_seconds() / 60
                    if elapsed >= duration_minutes:
                        print(f"\n⏱️ Laufzeit erreicht ({duration_minutes} min)")
                        break
                
                await asyncio.sleep(scan_interval)
        
        except asyncio.CancelledError:
            print("\n🛑 Monitoring gestoppt.")
        
        finally:
            self.running = False
            print(f"\n{'═'*70}")
            print(f"📊 ABSCHLUSSBERICHT")
            print(f"{'═'*70}")
            print(f"Laufzeit: {datetime.now() - start_time}")
            print(f"Erkannte Events: {len(self.event_history)}")
            if self.world_state:
                print(f"Kritische Alerts: {self.world_state.critical_count}")
                print(f"Warnungen: {self.world_state.warning_count}")
    
    def get_world_state_json(self) -> str:
        """Hole World State als JSON für API."""
        if not self.world_state:
            return json.dumps({"status": "initializing"})
        return json.dumps(asdict(self.world_state), indent=2)


async def main():
    """Demo: Laufe 2 Minuten."""
    worker = ContinuousWorker()
    await worker.run_continuous(duration_minutes=1)


if __name__ == "__main__":
    # Signal-Handler für sauberes Beenden
    def signal_handler(sig, frame):
        print("\n\n🛑 Beende Monitoring...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    asyncio.run(main())












