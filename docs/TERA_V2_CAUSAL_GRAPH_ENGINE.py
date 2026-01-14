"""
TERA V2: Causal Earth Graph Engine
===================================

Dieses Modul implementiert den kausalen Graphen für die Vorhersage 
kaskadierender geophysikalischer Ereignisse (z.B. El Niño).

Konzept:
- Knoten = Messbare Zustände (Vulkan, SST, Druck, etc.)
- Kanten = Kausale Abhängigkeiten mit Zeitverzögerung und Wahrscheinlichkeit
- Inferenz = Bayesian Network + Monte Carlo Simulation
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum
import json


class EventType(Enum):
    """Typen von geophysikalischen Ereignissen."""
    VOLCANIC_ERUPTION = "volcanic_eruption"
    SEISMIC_ACTIVITY = "seismic_activity"
    SEAFLOOR_ACTIVITY = "seafloor_activity"
    SST_ANOMALY = "sst_anomaly"
    PRESSURE_ANOMALY = "pressure_anomaly"
    SEA_LEVEL_CHANGE = "sea_level_change"
    EL_NINO = "el_nino"
    LA_NINA = "la_nina"
    DROUGHT = "drought"
    FLOOD = "flood"
    TYPHOON = "typhoon"
    WILDFIRE = "wildfire"
    COLD_WAVE = "cold_wave"
    HEAT_WAVE = "heat_wave"


@dataclass
class CausalEdge:
    """Eine kausale Verbindung zwischen zwei Ereignissen."""
    source: EventType
    target: EventType
    delay_months_min: float  # Minimale Verzögerung
    delay_months_max: float  # Maximale Verzögerung
    probability: float       # P(target | source)
    uncertainty: float       # σ der Schätzung
    mechanism: str           # Physikalische Erklärung
    historical_evidence: List[Dict] = field(default_factory=list)
    
    def sample_delay(self) -> float:
        """Stochastische Verzögerung aus Verteilung."""
        mean = (self.delay_months_min + self.delay_months_max) / 2
        std = (self.delay_months_max - self.delay_months_min) / 4
        return max(0, np.random.normal(mean, std))
    
    def sample_activation(self) -> bool:
        """Stochastisch: Wird der Effekt ausgelöst?"""
        noise = np.random.normal(0, self.uncertainty)
        return np.random.random() < (self.probability + noise)


@dataclass
class CausalNode:
    """Ein Knoten im kausalen Graphen."""
    event_type: EventType
    description: str
    current_value: Optional[float] = None
    baseline: float = 0.0
    anomaly_threshold: float = 1.0  # Wie viele σ für Anomalie?
    data_sources: List[str] = field(default_factory=list)
    last_update: Optional[datetime] = None
    confidence: float = 0.5  # Datenqualität 0-1
    affected_regions: List[str] = field(default_factory=list)
    
    def is_anomalous(self) -> bool:
        """Ist der aktuelle Wert anomal?"""
        if self.current_value is None:
            return False
        deviation = abs(self.current_value - self.baseline)
        return deviation > self.anomaly_threshold


class CausalEarthGraph:
    """
    Kausaler Graph für Erd-System-Vorhersagen.
    
    Implementiert das Netzwerk aus dem El Niño Beispiel:
    Vulkan → Seebeben → SST-Anomalie → El Niño → regionale Auswirkungen
    """
    
    def __init__(self):
        self.nodes: Dict[EventType, CausalNode] = {}
        self.edges: List[CausalEdge] = []
        self._build_default_graph()
    
    def _build_default_graph(self):
        """Baut den Standard-Kausal-Graphen basierend auf wissenschaftlicher Literatur."""
        
        # === KNOTEN DEFINIEREN ===
        
        self.nodes[EventType.VOLCANIC_ERUPTION] = CausalNode(
            event_type=EventType.VOLCANIC_ERUPTION,
            description="Vulkanausbruch mit signifikanter Asche-/Aerosol-Emission",
            baseline=0,  # 0 = kein Ausbruch
            anomaly_threshold=0.5,  # Jeder Ausbruch ist anomal
            data_sources=["Smithsonian GVP", "USGS Volcano Hazards"],
            affected_regions=["global"]
        )
        
        self.nodes[EventType.SEISMIC_ACTIVITY] = CausalNode(
            event_type=EventType.SEISMIC_ACTIVITY,
            description="Erhöhte seismische Aktivität (Erdbeben M≥5.0)",
            baseline=15,  # Durchschnittliche M5+ pro Monat global
            anomaly_threshold=10,  # +10 über Baseline = anomal
            data_sources=["USGS Earthquake", "GeoFon", "EMSC"],
            affected_regions=["Pacific Ring of Fire", "Mid-Atlantic Ridge"]
        )
        
        self.nodes[EventType.SEAFLOOR_ACTIVITY] = CausalNode(
            event_type=EventType.SEAFLOOR_ACTIVITY,
            description="Aktivität am Meeresboden (Lavaströme, hydrothermale Vents)",
            baseline=0,
            anomaly_threshold=0.5,
            data_sources=["NOAA Ocean Explorer", "Research Vessels"],
            affected_regions=["East Pacific Rise", "Mid-Atlantic Ridge"]
        )
        
        self.nodes[EventType.SST_ANOMALY] = CausalNode(
            event_type=EventType.SST_ANOMALY,
            description="Meeresoberflächentemperatur-Anomalie",
            baseline=0,  # 0 = Durchschnitt
            anomaly_threshold=0.5,  # ±0.5°C = signifikant
            data_sources=["NOAA OISST", "ERSST", "Argo Floats"],
            affected_regions=["Niño 3.4 region", "Global Ocean"]
        )
        
        self.nodes[EventType.PRESSURE_ANOMALY] = CausalNode(
            event_type=EventType.PRESSURE_ANOMALY,
            description="Atmosphärische Druckanomalie",
            baseline=1013.25,  # hPa Meereshöhe
            anomaly_threshold=15,  # ±15 hPa = signifikant
            data_sources=["NOAA GFS", "ECMWF"],
            affected_regions=["Tahiti", "Darwin", "Easter Island"]
        )
        
        self.nodes[EventType.SEA_LEVEL_CHANGE] = CausalNode(
            event_type=EventType.SEA_LEVEL_CHANGE,
            description="Lokale Meeresspiegeländerung",
            baseline=0,  # cm relativ zu normal
            anomaly_threshold=10,  # ±10cm = signifikant
            data_sources=["Copernicus Altimetry", "Tide Gauges"],
            affected_regions=["Pacific Islands", "Coastal regions"]
        )
        
        self.nodes[EventType.EL_NINO] = CausalNode(
            event_type=EventType.EL_NINO,
            description="El Niño Southern Oscillation - Warmphase",
            baseline=0,  # ONI Index
            anomaly_threshold=0.5,  # +0.5 für 5 Monate = El Niño
            data_sources=["NOAA CPC", "BoM Australia"],
            affected_regions=["Pacific", "Americas", "Australia", "Africa"]
        )
        
        self.nodes[EventType.LA_NINA] = CausalNode(
            event_type=EventType.LA_NINA,
            description="El Niño Southern Oscillation - Kaltphase",
            baseline=0,
            anomaly_threshold=-0.5,
            data_sources=["NOAA CPC", "BoM Australia"],
            affected_regions=["Pacific", "Americas", "Australia"]
        )
        
        self.nodes[EventType.DROUGHT] = CausalNode(
            event_type=EventType.DROUGHT,
            description="Regionale Dürre",
            baseline=0,
            anomaly_threshold=0.5,
            data_sources=["MODIS NDVI", "GRACE", "Soil Moisture"],
            affected_regions=["Australia", "Indonesia", "India", "Africa"]
        )
        
        self.nodes[EventType.FLOOD] = CausalNode(
            event_type=EventType.FLOOD,
            description="Regionale Überschwemmung",
            baseline=0,
            anomaly_threshold=0.5,
            data_sources=["Satellite Imagery", "River Gauges"],
            affected_regions=["Peru", "Ecuador", "California", "East Africa"]
        )
        
        self.nodes[EventType.TYPHOON] = CausalNode(
            event_type=EventType.TYPHOON,
            description="Erhöhte Taifun/Hurrikan-Aktivität",
            baseline=26,  # Durchschnittliche Named Storms pro Jahr
            anomaly_threshold=10,  # +10 = anomal
            data_sources=["NOAA NHC", "JTWC"],
            affected_regions=["Pacific", "Atlantic", "Indian Ocean"]
        )
        
        self.nodes[EventType.WILDFIRE] = CausalNode(
            event_type=EventType.WILDFIRE,
            description="Erhöhte Waldbrandaktivität",
            baseline=0,
            anomaly_threshold=0.5,
            data_sources=["NASA FIRMS", "MODIS", "VIIRS"],
            affected_regions=["Australia", "Indonesia", "California", "Amazon"]
        )
        
        # === KANTEN (KAUSALE VERBINDUNGEN) DEFINIEREN ===
        
        # Vulkan → Seismik
        self.edges.append(CausalEdge(
            source=EventType.VOLCANIC_ERUPTION,
            target=EventType.SEISMIC_ACTIVITY,
            delay_months_min=0,
            delay_months_max=1,
            probability=0.85,
            uncertainty=0.10,
            mechanism="Magmabewegung verursacht Erdbeben; Druckentlastung destabilisiert tektonische Platten",
            historical_evidence=[
                {"year": 1982, "event": "El Chichón → Seebeben Ostpazifik", "delay_months": 0.5},
                {"year": 1991, "event": "Pinatubo → erhöhte Seismik Philippinen", "delay_months": 0}
            ]
        ))
        
        # Vulkan → Aerosole → Abkühlung → SST
        self.edges.append(CausalEdge(
            source=EventType.VOLCANIC_ERUPTION,
            target=EventType.SST_ANOMALY,
            delay_months_min=1,
            delay_months_max=6,
            probability=0.70,
            uncertainty=0.15,
            mechanism="Aerosole in Stratosphäre reflektieren Sonnenlicht, kühlen Ozeanoberfläche",
            historical_evidence=[
                {"year": 1991, "event": "Pinatubo → globale SST -0.5°C", "delay_months": 3},
                {"year": 1982, "event": "El Chichón → Pazifik SST Anomalie", "delay_months": 2}
            ]
        ))
        
        # Seismik → Seafloor
        self.edges.append(CausalEdge(
            source=EventType.SEISMIC_ACTIVITY,
            target=EventType.SEAFLOOR_ACTIVITY,
            delay_months_min=0,
            delay_months_max=2,
            probability=0.60,
            uncertainty=0.20,
            mechanism="Seebeben aktivieren unterseeische Vulkane und hydrothermale Systeme",
            historical_evidence=[
                {"year": 1982, "event": "Seebeben → Lavaströme Ostpazifische Schwelle", "delay_months": 0.5}
            ]
        ))
        
        # Seafloor → SST
        self.edges.append(CausalEdge(
            source=EventType.SEAFLOOR_ACTIVITY,
            target=EventType.SST_ANOMALY,
            delay_months_min=1,
            delay_months_max=4,
            probability=0.50,
            uncertainty=0.25,
            mechanism="Wärme von Unterwasservulkanen beeinflusst Meeresströmungen und SST",
            historical_evidence=[
                {"year": 1982, "event": "Lavaströme → Pazifik-Erwärmung", "delay_months": 2}
            ]
        ))
        
        # Druck-Anomalie → SST/Sea Level
        self.edges.append(CausalEdge(
            source=EventType.PRESSURE_ANOMALY,
            target=EventType.SEA_LEVEL_CHANGE,
            delay_months_min=0,
            delay_months_max=1,
            probability=0.80,
            uncertainty=0.10,
            mechanism="Southern Oscillation - Druckgefälle treibt Wassermassen",
            historical_evidence=[
                {"year": 1982, "event": "Osterinsel Druckabfall → Meeresspiegel Zentralpazifik +20cm", "delay_months": 1}
            ]
        ))
        
        # SST → El Niño
        self.edges.append(CausalEdge(
            source=EventType.SST_ANOMALY,
            target=EventType.EL_NINO,
            delay_months_min=1,
            delay_months_max=3,
            probability=0.75,
            uncertainty=0.15,
            mechanism="Anhaltende positive SST-Anomalie im Niño 3.4 Gebiet definiert El Niño",
            historical_evidence=[
                {"year": 1982, "event": "SST +7°C Peru → El Niño 82/83", "delay_months": 1},
                {"year": 1997, "event": "SST Anomalie → El Niño 97/98", "delay_months": 2}
            ]
        ))
        
        # El Niño → Regionale Effekte
        self.edges.append(CausalEdge(
            source=EventType.EL_NINO,
            target=EventType.DROUGHT,
            delay_months_min=2,
            delay_months_max=6,
            probability=0.70,
            uncertainty=0.15,
            mechanism="El Niño schwächt Monsun, verlagert Niederschlagszonen",
            historical_evidence=[
                {"year": 1982, "event": "El Niño → Dürre Australien/Indonesien", "delay_months": 4},
                {"year": 2015, "event": "El Niño → Dürre Südafrika/Indien", "delay_months": 5}
            ]
        ))
        
        self.edges.append(CausalEdge(
            source=EventType.EL_NINO,
            target=EventType.FLOOD,
            delay_months_min=2,
            delay_months_max=8,
            probability=0.75,
            uncertainty=0.12,
            mechanism="Warmes Wasser erhöht Verdunstung, führt zu extremen Niederschlägen",
            historical_evidence=[
                {"year": 1982, "event": "El Niño → Flut Peru/Ecuador (300x Niederschlag)", "delay_months": 6},
                {"year": 1997, "event": "El Niño → Kalifornien Fluten", "delay_months": 4}
            ]
        ))
        
        self.edges.append(CausalEdge(
            source=EventType.EL_NINO,
            target=EventType.TYPHOON,
            delay_months_min=1,
            delay_months_max=4,
            probability=0.65,
            uncertainty=0.18,
            mechanism="Warmer Ozean liefert mehr Energie für tropische Stürme",
            historical_evidence=[
                {"year": 1982, "event": "El Niño → 5 Taifune Französisch-Polynesien (normal: 1/50 Jahre)", "delay_months": 3}
            ]
        ))
        
        self.edges.append(CausalEdge(
            source=EventType.EL_NINO,
            target=EventType.WILDFIRE,
            delay_months_min=3,
            delay_months_max=8,
            probability=0.68,
            uncertainty=0.15,
            mechanism="Dürrebedingungen durch El Niño erhöhen Brandgefahr drastisch",
            historical_evidence=[
                {"year": 1982, "event": "El Niño → Australien Waldbrände (72 Tote)", "delay_months": 6},
                {"year": 2015, "event": "El Niño → Indonesien Waldbrände", "delay_months": 5}
            ]
        ))
        
        # Dürre → Waldbrände (direkte Verbindung)
        self.edges.append(CausalEdge(
            source=EventType.DROUGHT,
            target=EventType.WILDFIRE,
            delay_months_min=1,
            delay_months_max=3,
            probability=0.80,
            uncertainty=0.10,
            mechanism="Trockene Vegetation ist hochentzündlich",
            historical_evidence=[
                {"year": 1982, "event": "Dürre Australien → Waldbrände", "delay_months": 2}
            ]
        ))
    
    def get_downstream_effects(self, trigger: EventType, depth: int = 5) -> List[Dict]:
        """
        Finde alle downstream-Effekte eines Trigger-Ereignisses.
        
        Args:
            trigger: Das auslösende Ereignis
            depth: Maximale Tiefe der Kausalkette
            
        Returns:
            Liste von möglichen Effekten mit Wahrscheinlichkeiten und Timing
        """
        effects = []
        visited = set()
        queue = [(trigger, 0, 1.0, 0)]  # (node, depth, cumulative_prob, cumulative_delay)
        
        while queue:
            current, d, cum_prob, cum_delay = queue.pop(0)
            
            if d >= depth or current in visited:
                continue
            visited.add(current)
            
            # Finde alle ausgehenden Kanten
            for edge in self.edges:
                if edge.source == current:
                    new_prob = cum_prob * edge.probability
                    new_delay = cum_delay + (edge.delay_months_min + edge.delay_months_max) / 2
                    
                    effects.append({
                        "event": edge.target.value,
                        "triggered_by": current.value,
                        "probability": round(new_prob, 3),
                        "delay_months": round(new_delay, 1),
                        "uncertainty": edge.uncertainty,
                        "mechanism": edge.mechanism,
                        "affected_regions": self.nodes[edge.target].affected_regions,
                        "chain_depth": d + 1
                    })
                    
                    queue.append((edge.target, d + 1, new_prob, new_delay))
        
        # Sortiere nach Wahrscheinlichkeit
        return sorted(effects, key=lambda x: x["probability"], reverse=True)
    
    def simulate_cascade(self, trigger: EventType, n_simulations: int = 10000) -> Dict:
        """
        Monte Carlo Simulation einer Kaskade.
        
        Args:
            trigger: Das auslösende Ereignis
            n_simulations: Anzahl der Simulationen
            
        Returns:
            Aggregierte Ergebnisse mit Wahrscheinlichkeitsverteilungen
        """
        results = {event_type: {"triggered": 0, "delays": []} for event_type in EventType}
        
        for _ in range(n_simulations):
            # Simuliere eine Trajektorie
            active_events = [(trigger, 0)]  # (event, time)
            triggered = set([trigger])
            
            while active_events:
                current_event, current_time = active_events.pop(0)
                
                # Prüfe alle ausgehenden Kanten
                for edge in self.edges:
                    if edge.source == current_event and edge.target not in triggered:
                        # Stochastische Aktivierung
                        if edge.sample_activation():
                            delay = edge.sample_delay()
                            triggered.add(edge.target)
                            active_events.append((edge.target, current_time + delay))
                            
                            results[edge.target]["triggered"] += 1
                            results[edge.target]["delays"].append(current_time + delay)
        
        # Aggregiere Ergebnisse
        output = {}
        for event_type, data in results.items():
            if event_type == trigger:
                continue
            
            prob = data["triggered"] / n_simulations
            if prob > 0.01:  # Nur relevante Ereignisse
                delays = data["delays"]
                output[event_type.value] = {
                    "probability": round(prob, 3),
                    "mean_delay_months": round(np.mean(delays), 1) if delays else None,
                    "std_delay_months": round(np.std(delays), 1) if delays else None,
                    "p10_delay": round(np.percentile(delays, 10), 1) if delays else None,
                    "p90_delay": round(np.percentile(delays, 90), 1) if delays else None,
                    "affected_regions": self.nodes[event_type].affected_regions
                }
        
        return {
            "trigger": trigger.value,
            "n_simulations": n_simulations,
            "downstream_effects": output
        }
    
    def update_node_observation(self, event_type: EventType, value: float, 
                                 confidence: float = 0.8, source: str = "observation"):
        """Aktualisiere einen Knoten mit neuer Beobachtung."""
        if event_type in self.nodes:
            self.nodes[event_type].current_value = value
            self.nodes[event_type].confidence = confidence
            self.nodes[event_type].last_update = datetime.now()
            self.nodes[event_type].data_sources.append(f"{source}@{datetime.now().isoformat()}")
    
    def detect_active_cascades(self) -> List[Dict]:
        """
        Erkenne aktive Kaskaden basierend auf aktuellen Beobachtungen.
        
        Prüft alle anomalen Knoten und berechnet wahrscheinliche downstream-Effekte.
        """
        active_cascades = []
        
        for event_type, node in self.nodes.items():
            if node.is_anomalous():
                cascade = self.simulate_cascade(event_type, n_simulations=5000)
                
                # Filtere auf hohe Wahrscheinlichkeiten
                significant_effects = {
                    k: v for k, v in cascade["downstream_effects"].items()
                    if v["probability"] > 0.3
                }
                
                if significant_effects:
                    active_cascades.append({
                        "trigger": event_type.value,
                        "trigger_value": node.current_value,
                        "trigger_baseline": node.baseline,
                        "anomaly_severity": abs(node.current_value - node.baseline) / node.anomaly_threshold,
                        "confidence": node.confidence,
                        "last_update": node.last_update.isoformat() if node.last_update else None,
                        "predicted_effects": significant_effects
                    })
        
        return active_cascades
    
    def to_json(self) -> str:
        """Exportiere Graph als JSON für Frontend-Visualisierung."""
        nodes = []
        for event_type, node in self.nodes.items():
            nodes.append({
                "id": event_type.value,
                "label": node.description,
                "current_value": node.current_value,
                "baseline": node.baseline,
                "is_anomalous": node.is_anomalous(),
                "confidence": node.confidence,
                "affected_regions": node.affected_regions
            })
        
        edges = []
        for edge in self.edges:
            edges.append({
                "source": edge.source.value,
                "target": edge.target.value,
                "probability": edge.probability,
                "delay_min": edge.delay_months_min,
                "delay_max": edge.delay_months_max,
                "mechanism": edge.mechanism
            })
        
        return json.dumps({"nodes": nodes, "edges": edges}, indent=2)


# ============================================================
# BEISPIEL-NUTZUNG
# ============================================================

if __name__ == "__main__":
    # Initialisiere Graph
    graph = CausalEarthGraph()
    
    print("=" * 80)
    print("TERA Causal Earth Graph - El Niño Vorhersage Beispiel")
    print("=" * 80)
    
    # Simuliere: Was passiert nach einem Vulkanausbruch?
    print("\n📌 SZENARIO: Vulkanausbruch (wie El Chichón 1982)")
    print("-" * 60)
    
    # Direkte downstream-Effekte
    effects = graph.get_downstream_effects(EventType.VOLCANIC_ERUPTION, depth=4)
    
    print("\n🔗 KAUSALE KETTE (deterministische Schätzung):")
    for effect in effects[:10]:
        print(f"  → {effect['event']:20s} | P={effect['probability']:.1%} | "
              f"Delay: {effect['delay_months']:.1f} Monate | "
              f"Tiefe: {effect['chain_depth']}")
    
    # Monte Carlo Simulation
    print("\n🎲 MONTE CARLO SIMULATION (10,000 Durchläufe):")
    cascade = graph.simulate_cascade(EventType.VOLCANIC_ERUPTION, n_simulations=10000)
    
    for event, stats in sorted(cascade["downstream_effects"].items(), 
                                key=lambda x: x[1]["probability"], reverse=True)[:8]:
        print(f"  → {event:20s} | P={stats['probability']:.1%} | "
              f"Delay: {stats['mean_delay_months']:.1f}±{stats['std_delay_months']:.1f} Monate")
        print(f"    Regionen: {', '.join(stats['affected_regions'][:3])}")
    
    # Beispiel: Aktuelle Beobachtung einfügen
    print("\n📡 ECHTZEIT-UPDATE: Vulkanausbruch beobachtet!")
    print("-" * 60)
    graph.update_node_observation(
        EventType.VOLCANIC_ERUPTION, 
        value=5.2,  # VEI 5.2
        confidence=0.95,
        source="Smithsonian GVP"
    )
    graph.update_node_observation(
        EventType.SST_ANOMALY,
        value=2.5,  # +2.5°C über Baseline
        confidence=0.90,
        source="NOAA OISST"
    )
    
    # Erkenne aktive Kaskaden
    active = graph.detect_active_cascades()
    print(f"\n⚠️ {len(active)} AKTIVE KASKADEN ERKANNT:")
    for cascade in active:
        print(f"\n  TRIGGER: {cascade['trigger']}")
        print(f"  Wert: {cascade['trigger_value']} (Baseline: {cascade['trigger_baseline']})")
        print(f"  Schweregrad: {cascade['anomaly_severity']:.1f}x Schwelle")
        print(f"  Vorhergesagte Effekte:")
        for effect, stats in list(cascade['predicted_effects'].items())[:5]:
            print(f"    → {effect}: P={stats['probability']:.1%}, "
                  f"in {stats['mean_delay_months']:.1f} Monaten")
    
    print("\n" + "=" * 80)
    print("Graph JSON (für Frontend-Visualisierung):")
    print("=" * 80)
    print(graph.to_json()[:1000] + "...")












