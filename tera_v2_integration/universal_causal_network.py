"""
TERA V2: Universelles Kausales Netzwerk
=========================================

Verbindet ALLE primären Treiber miteinander.
Bei jedem neuen Ereignis werden automatisch ALLE Kausalketten aktiviert
und die Wahrscheinlichkeiten für nachfolgende Ereignisse berechnet.

Dies ist das Herzstück des "Digital Earth Twin".
"""

import asyncio
import networkx as nx
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
import json
import random

from primary_drivers_catalog import (
    PRIMARY_DRIVERS, 
    PrimaryDriver, 
    CausalEffect,
    get_all_effects,
    find_effect_chains
)


@dataclass
class ActiveEvent:
    """Ein aktives Ereignis im System."""
    id: str
    driver_id: str
    driver_name: str
    timestamp: datetime
    magnitude: float
    unit: str
    location: Dict
    severity: str
    
    # Propagierte Effekte
    triggered_effects: List[Dict] = field(default_factory=list)
    
    # Status
    is_processed: bool = False


@dataclass
class PredictedEffect:
    """Ein vorhergesagter Effekt."""
    id: str
    trigger_event_id: str
    effect_type: str
    effect_name: str
    probability: float
    confidence: float
    expected_timing: str
    expected_regions: List[str]
    mechanism: str
    
    # Zustand
    status: str = "predicted"  # predicted, materializing, materialized, expired
    
    # Wenn materialisiert
    actual_event_id: Optional[str] = None


class UniversalCausalNetwork:
    """
    Universelles Kausal-Netzwerk das ALLE Treiber verbindet.
    """
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.active_events: Dict[str, ActiveEvent] = {}
        self.predicted_effects: Dict[str, PredictedEffect] = {}
        self.event_history: List[ActiveEvent] = []
        
        # Baue das Netzwerk auf
        self._build_network()
    
    def _build_network(self):
        """Baue das kausale Netzwerk aus allen Treibern."""
        # Füge alle Treiber als Knoten hinzu
        for driver_id, driver in PRIMARY_DRIVERS.items():
            self.graph.add_node(
                driver_id,
                name=driver.name,
                category=driver.category.value,
                type="driver"
            )
        
        # Füge alle Effekte als Knoten hinzu
        for driver_id, driver in PRIMARY_DRIVERS.items():
            for effect in driver.causal_effects:
                effect_node_id = f"{driver_id}_{effect.effect_id}"
                self.graph.add_node(
                    effect_node_id,
                    name=effect.name,
                    type="effect",
                    source_driver=driver_id
                )
                
                # Kante: Treiber → Effekt
                self.graph.add_edge(
                    driver_id,
                    effect_node_id,
                    probability=effect.probability,
                    delay=effect.delay_range,
                    mechanism=effect.mechanism,
                    confidence=effect.confidence,
                    regions=effect.affected_regions
                )
                
                # Prüfe ob dieser Effekt ein anderer Treiber ist
                # (z.B. volcanic_eruption kann el_nino auslösen)
                for target_driver_id in PRIMARY_DRIVERS.keys():
                    if effect.effect_id in target_driver_id or \
                       target_driver_id in effect.effect_id or \
                       effect.effect_id.replace("_", " ") in PRIMARY_DRIVERS[target_driver_id].name.lower():
                        # Kante: Effekt → nächster Treiber
                        self.graph.add_edge(
                            effect_node_id,
                            target_driver_id,
                            type="chain",
                            probability=0.8,  # Annahme
                            delay="varies"
                        )
        
        # Zusätzliche bekannte Verbindungen
        self._add_known_chains()
    
    def _add_known_chains(self):
        """Füge bekannte Kausalketten hinzu."""
        known_chains = [
            # Vulkan → SST → ENSO
            ("volcanic_eruption", "sst_anomaly", 0.6, "3-12 Monate", 
             "Vulkanasche blockiert Sonne → Ozean kühlt ab"),
            
            # ENSO → Monsun
            ("enso", "monsoon", 0.7, "1-6 Monate",
             "El Niño verschiebt Walker-Zirkulation → Monsun schwächer"),
            
            # Arktis-Eis → Jetstream
            ("arctic_sea_ice", "jet_stream", 0.5, "Wochen-Monate",
             "Weniger Eis → schwächerer Temperaturgradient → welligerer Jet"),
            
            # Jetstream → Blocking
            ("jet_stream", "atmospheric_blocking", 0.6, "Tage",
             "Wellen im Jet können sich zu Blocks verstärken"),
            
            # Treibhausgase → SST
            ("greenhouse_gas", "sst_anomaly", 0.9, "Jahrzehnte",
             "Erwärmung überträgt sich auf Ozean"),
            
            # Entwaldung → Monsun
            ("deforestation", "monsoon", 0.4, "Jahre",
             "Weniger Evapotranspiration → veränderte Feuchtigkeitszufuhr"),
            
            # Permafrost → Treibhausgase
            ("permafrost_thaw", "greenhouse_gas", 0.6, "Jahre-Jahrzehnte",
             "Methan und CO2 aus tauendem Permafrost"),
            
            # Sonnenzyklus → Polarwirbel
            ("solar_irradiance", "polar_vortex", 0.4, "Monate",
             "UV-Änderungen → stratosphärische Ozonchemie → Wirbel"),
            
            # AMO → NAO (bidirektional)
            ("amo", "nao", 0.5, "Monate-Jahre",
             "Warmer Atlantik moduliert atmosphärische Muster"),
            
            # Erdbeben → Vulkan
            ("earthquake", "volcanic_eruption", 0.2, "Tage-Monate",
             "Starke Erdbeben können Magmakammern destabilisieren"),
        ]
        
        for source, target, prob, delay, mechanism in known_chains:
            if source in self.graph and target in self.graph:
                self.graph.add_edge(
                    source, target,
                    probability=prob,
                    delay=delay,
                    mechanism=mechanism,
                    type="known_chain"
                )
    
    def propagate_event(self, event: ActiveEvent) -> List[PredictedEffect]:
        """
        Propagiere ein Ereignis durch das Netzwerk.
        Berechnet alle nachfolgenden Effekte mit Wahrscheinlichkeiten.
        """
        predictions = []
        visited = set()
        
        def propagate_recursive(node_id: str, cumulative_prob: float, depth: int = 0):
            if depth > 5 or node_id in visited or cumulative_prob < 0.01:
                return
            
            visited.add(node_id)
            
            # Hole alle ausgehenden Kanten
            for _, target, edge_data in self.graph.out_edges(node_id, data=True):
                edge_prob = edge_data.get("probability", 0.5)
                combined_prob = cumulative_prob * edge_prob
                
                if combined_prob >= 0.05:  # Mindestwahrscheinlichkeit
                    # Erstelle Vorhersage
                    target_data = self.graph.nodes[target]
                    
                    prediction = PredictedEffect(
                        id=f"pred_{event.id}_{target}_{depth}",
                        trigger_event_id=event.id,
                        effect_type=target,
                        effect_name=target_data.get("name", target),
                        probability=combined_prob,
                        confidence=edge_data.get("confidence", 0.7),
                        expected_timing=edge_data.get("delay", "unbekannt"),
                        expected_regions=edge_data.get("regions", ["global"]),
                        mechanism=edge_data.get("mechanism", "Kausale Verbindung"),
                    )
                    predictions.append(prediction)
                    
                    # Rekursiv weiter propagieren
                    propagate_recursive(target, combined_prob, depth + 1)
        
        # Starte Propagation vom Treiber
        propagate_recursive(event.driver_id, 1.0)
        
        # Speichere Vorhersagen
        for pred in predictions:
            self.predicted_effects[pred.id] = pred
        
        # Markiere Event als verarbeitet
        event.triggered_effects = [{"id": p.id, "effect": p.effect_name, "prob": p.probability} 
                                   for p in predictions]
        event.is_processed = True
        
        return predictions
    
    def inject_event(self, driver_id: str, magnitude: float, unit: str, 
                     location: Dict, severity: str) -> Tuple[ActiveEvent, List[PredictedEffect]]:
        """
        Injiziere ein neues Ereignis ins System und propagiere es.
        """
        driver = PRIMARY_DRIVERS.get(driver_id)
        if not driver:
            raise ValueError(f"Unbekannter Treiber: {driver_id}")
        
        event = ActiveEvent(
            id=f"{driver_id}_{datetime.now().timestamp()}",
            driver_id=driver_id,
            driver_name=driver.name,
            timestamp=datetime.now(),
            magnitude=magnitude,
            unit=unit,
            location=location,
            severity=severity
        )
        
        self.active_events[event.id] = event
        self.event_history.append(event)
        
        # Propagiere durch Netzwerk
        predictions = self.propagate_event(event)
        
        return event, predictions
    
    def get_network_stats(self) -> Dict:
        """Hole Netzwerk-Statistiken."""
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "drivers": len([n for n, d in self.graph.nodes(data=True) if d.get("type") == "driver"]),
            "effects": len([n for n, d in self.graph.nodes(data=True) if d.get("type") == "effect"]),
            "active_events": len(self.active_events),
            "active_predictions": len([p for p in self.predicted_effects.values() if p.status == "predicted"]),
        }
    
    def visualize_chain(self, start_driver: str, max_depth: int = 3) -> str:
        """Visualisiere Kausalketten als Text-Diagramm."""
        output = []
        visited = set()
        
        def draw_tree(node_id: str, prefix: str = "", is_last: bool = True, depth: int = 0):
            if depth > max_depth or node_id in visited:
                return
            
            visited.add(node_id)
            
            connector = "└── " if is_last else "├── "
            node_data = self.graph.nodes.get(node_id, {})
            node_name = node_data.get("name", node_id)
            
            if depth == 0:
                output.append(f"🔴 {node_name}")
            else:
                output.append(f"{prefix}{connector}{node_name}")
            
            new_prefix = prefix + ("    " if is_last else "│   ")
            
            # Hole Kinder
            children = list(self.graph.successors(node_id))
            for i, child in enumerate(children[:5]):  # Max 5 Kinder
                edge_data = self.graph.get_edge_data(node_id, child) or {}
                prob = edge_data.get("probability", 0)
                
                is_last_child = (i == len(children[:5]) - 1)
                draw_tree(child, new_prefix, is_last_child, depth + 1)
        
        draw_tree(start_driver)
        return "\n".join(output)
    
    def get_all_paths_to(self, target_effect: str) -> List[List[str]]:
        """Finde alle Pfade die zu einem bestimmten Effekt führen."""
        paths = []
        
        # Finde alle Knoten die das Ziel enthalten
        target_nodes = [n for n in self.graph.nodes() if target_effect.lower() in n.lower()]
        
        for target in target_nodes:
            for driver_id in PRIMARY_DRIVERS.keys():
                try:
                    for path in nx.all_simple_paths(self.graph, driver_id, target, cutoff=5):
                        if path not in paths:
                            paths.append(path)
                except nx.NetworkXNoPath:
                    continue
        
        return paths


def demo():
    """Demo des Universellen Kausalen Netzwerks."""
    print("\n" + "="*70)
    print("🌍 TERA UNIVERSELLES KAUSALES NETZWERK")
    print("="*70)
    
    network = UniversalCausalNetwork()
    
    # Statistiken
    stats = network.get_network_stats()
    print(f"\n📊 NETZWERK-STATISTIKEN:")
    print(f"   Knoten: {stats['total_nodes']}")
    print(f"   Kanten: {stats['total_edges']}")
    print(f"   Treiber: {stats['drivers']}")
    print(f"   Effekte: {stats['effects']}")
    
    # Visualisiere Vulkan-Kette
    print(f"\n{'='*70}")
    print("🌋 KAUSALKETTE: Vulkanausbruch")
    print("="*70)
    print(network.visualize_chain("volcanic_eruption", max_depth=3))
    
    # Visualisiere ENSO-Kette
    print(f"\n{'='*70}")
    print("🌊 KAUSALKETTE: ENSO")
    print("="*70)
    print(network.visualize_chain("enso", max_depth=2))
    
    # Simuliere Ereignis: Starker Vulkanausbruch
    print(f"\n{'='*70}")
    print("⚡ SIMULATION: Vulkanausbruch VEI-5 in Indonesien")
    print("="*70)
    
    event, predictions = network.inject_event(
        driver_id="volcanic_eruption",
        magnitude=5,
        unit="VEI",
        location={"lat": -7.54, "lon": 110.44, "name": "Merapi, Indonesien"},
        severity="critical"
    )
    
    print(f"\n📌 Ereignis: {event.driver_name}")
    print(f"   Magnitude: {event.magnitude} {event.unit}")
    print(f"   Ort: {event.location['name']}")
    print(f"   Schweregrad: {event.severity}")
    
    print(f"\n📈 VORHERGESAGTE FOLGEEFFEKTE ({len(predictions)}):")
    print("-" * 60)
    
    # Sortiere nach Wahrscheinlichkeit
    predictions_sorted = sorted(predictions, key=lambda p: -p.probability)
    
    for pred in predictions_sorted[:10]:
        prob_bar = "█" * int(pred.probability * 20)
        print(f"   {pred.effect_name:30} {pred.probability:5.0%} {prob_bar}")
        print(f"      ⏱️ Timing: {pred.expected_timing}")
        print(f"      🌍 Regionen: {', '.join(pred.expected_regions[:3])}")
        print()
    
    # Pfade zu Dürre
    print(f"\n{'='*70}")
    print("🔍 ALLE PFADE ZU 'drought'")
    print("="*70)
    drought_paths = network.get_all_paths_to("drought")
    for path in drought_paths[:5]:
        path_str = " → ".join([network.graph.nodes[n].get("name", n)[:20] for n in path])
        print(f"   {path_str}")


if __name__ == "__main__":
    demo()












