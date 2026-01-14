"""
TERA V2: Global Risk Engine
============================

Kombiniert:
1. Aktuelle Klimaindizes (climate_index_service)
2. Kausale Verbindungen (causal_graph)
3. Telekonnektion (regional effects)
4. Lokale Vulnerabilität

Um für jeden Punkt einen vollständigen Risiko-Kontext zu berechnen.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math


# ═══════════════════════════════════════════════════════════════════════════════
# REGIONEN UND HAZARDS
# ═══════════════════════════════════════════════════════════════════════════════

class Region(Enum):
    """Globale Regionen für Telekonnektion."""
    NA_EAST = "na_east"
    NA_WEST = "na_west"
    CENTRAL_AMERICA = "central_america"
    SA_NORTH = "sa_north"
    SA_SOUTH = "sa_south"
    EUROPE_NORTH = "eu_north"
    EUROPE_SOUTH = "eu_south"
    AFRICA_NORTH = "af_north"
    AFRICA_EAST = "af_east"
    AFRICA_SOUTH = "af_south"
    MIDDLE_EAST = "middle_east"
    SOUTH_ASIA = "south_asia"
    EAST_ASIA = "east_asia"
    SOUTHEAST_ASIA = "se_asia"
    AUSTRALIA = "australia"
    PACIFIC_ISLANDS = "pacific"


class HazardType(Enum):
    """Typen von Extremereignissen."""
    FLOOD = "flood"
    DROUGHT = "drought"
    WILDFIRE = "wildfire"
    TROPICAL_CYCLONE = "tropical_cyclone"
    HEAT_WAVE = "heat_wave"
    COLD_WAVE = "cold_wave"
    COASTAL_FLOOD = "coastal_flood"
    LANDSLIDE = "landslide"


# ═══════════════════════════════════════════════════════════════════════════════
# TELEKONNEKTION MATRIX
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class TeleconnectionEffect:
    """Ein Telekonnektion-Effekt."""
    climate_mode: str
    phase: str
    region: Region
    hazard: HazardType
    magnitude: float
    delay_months: float
    mechanism: str


# Die Telekonnektion-Matrix: Wie globale Klima-Modi regionale Risiken beeinflussen
TELECONNECTION_MATRIX: List[TeleconnectionEffect] = [
    # ═══════════════════════════════════════════════════════════════════════
    # ENSO POSITIVE (El Niño)
    # ═══════════════════════════════════════════════════════════════════════
    
    # Südamerika
    TeleconnectionEffect("ONI", "positive", Region.SA_NORTH, HazardType.FLOOD, 0.80, 4, 
                        "Warmes Wasser vor Peru erhöht Verdunstung → extreme Niederschläge"),
    TeleconnectionEffect("ONI", "positive", Region.SA_SOUTH, HazardType.FLOOD, 0.50, 5,
                        "Verstärkte Niederschläge in Argentinien/Südbrasilien"),
    
    # Nordamerika
    TeleconnectionEffect("ONI", "positive", Region.NA_WEST, HazardType.FLOOD, 0.60, 3,
                        "Verstärkter subtropischer Jetstream → mehr Stürme in Kalifornien"),
    TeleconnectionEffect("ONI", "positive", Region.NA_EAST, HazardType.COLD_WAVE, -0.40, 4,
                        "Wärmerer Winter im Nordosten (negativer Effekt auf Kälte)"),
    
    # Australien/Asien - DIE HAUPTEFFEKTE
    TeleconnectionEffect("ONI", "positive", Region.AUSTRALIA, HazardType.DROUGHT, 0.75, 3,
                        "Walker-Zirkulation schwächt sich ab → weniger Monsun-Regen"),
    TeleconnectionEffect("ONI", "positive", Region.AUSTRALIA, HazardType.WILDFIRE, 0.70, 5,
                        "Dürre führt zu erhöhter Waldbrandgefahr"),
    TeleconnectionEffect("ONI", "positive", Region.SOUTHEAST_ASIA, HazardType.DROUGHT, 0.65, 2,
                        "Schwächerer Monsun in Indonesien/Philippinen"),
    TeleconnectionEffect("ONI", "positive", Region.SOUTH_ASIA, HazardType.DROUGHT, 0.40, 4,
                        "Schwächerer indischer Monsun"),
    
    # Afrika
    TeleconnectionEffect("ONI", "positive", Region.AFRICA_EAST, HazardType.DROUGHT, 0.55, 4,
                        "Reduzierte Niederschläge in Ostafrika"),
    TeleconnectionEffect("ONI", "positive", Region.AFRICA_SOUTH, HazardType.DROUGHT, 0.60, 5,
                        "Dürre im südlichen Afrika"),
    
    # Pazifik
    TeleconnectionEffect("ONI", "positive", Region.PACIFIC_ISLANDS, HazardType.TROPICAL_CYCLONE, 0.50, 2,
                        "Mehr Taifune im zentralen Pazifik"),
    
    # ═══════════════════════════════════════════════════════════════════════
    # ENSO NEGATIVE (La Niña)
    # ═══════════════════════════════════════════════════════════════════════
    
    TeleconnectionEffect("ONI", "negative", Region.AUSTRALIA, HazardType.FLOOD, 0.70, 3,
                        "Verstärkte Walker-Zirkulation → mehr Regen"),
    TeleconnectionEffect("ONI", "negative", Region.NA_WEST, HazardType.DROUGHT, 0.50, 4,
                        "Trockenere Bedingungen im Südwesten USA"),
    TeleconnectionEffect("ONI", "negative", Region.SA_NORTH, HazardType.DROUGHT, 0.40, 3,
                        "Kühleres Wasser vor Peru → weniger Niederschläge"),
    
    # ═══════════════════════════════════════════════════════════════════════
    # AMO (Atlantic Multidecadal Oscillation)
    # ═══════════════════════════════════════════════════════════════════════
    
    TeleconnectionEffect("AMO", "positive", Region.NA_EAST, HazardType.TROPICAL_CYCLONE, 0.70, 0,
                        "Wärmerer Atlantik → mehr Energie für Hurrikane"),
    TeleconnectionEffect("AMO", "positive", Region.CENTRAL_AMERICA, HazardType.TROPICAL_CYCLONE, 0.65, 0,
                        "Mehr und stärkere Hurrikane in der Karibik"),
    TeleconnectionEffect("AMO", "positive", Region.AFRICA_NORTH, HazardType.DROUGHT, -0.50, 2,
                        "Mehr Niederschlag in der Sahel-Zone (weniger Dürre)"),
    TeleconnectionEffect("AMO", "positive", Region.EUROPE_NORTH, HazardType.HEAT_WAVE, 0.40, 1,
                        "Wärmere Sommer in Nordeuropa"),
    
    # ═══════════════════════════════════════════════════════════════════════
    # NAO (North Atlantic Oscillation)
    # ═══════════════════════════════════════════════════════════════════════
    
    TeleconnectionEffect("NAO", "positive", Region.EUROPE_NORTH, HazardType.FLOOD, 0.50, 0,
                        "Stärkere Westwinde → mehr Regen in Nordeuropa"),
    TeleconnectionEffect("NAO", "positive", Region.EUROPE_SOUTH, HazardType.DROUGHT, 0.45, 1,
                        "Trockenere Bedingungen im Mittelmeerraum"),
    TeleconnectionEffect("NAO", "negative", Region.EUROPE_NORTH, HazardType.COLD_WAVE, 0.60, 0,
                        "Arktische Luft kann leichter nach Süden vordringen"),
    
    # ═══════════════════════════════════════════════════════════════════════
    # IOD (Indian Ocean Dipole)
    # ═══════════════════════════════════════════════════════════════════════
    
    TeleconnectionEffect("IOD", "positive", Region.AUSTRALIA, HazardType.DROUGHT, 0.65, 2,
                        "Kühleres Wasser westlich von Australien → weniger Verdunstung"),
    TeleconnectionEffect("IOD", "positive", Region.AUSTRALIA, HazardType.WILDFIRE, 0.60, 4,
                        "Dürre erhöht Waldbrandgefahr"),
    TeleconnectionEffect("IOD", "positive", Region.AFRICA_EAST, HazardType.FLOOD, 0.55, 1,
                        "Wärmeres Wasser im westlichen Indik → mehr Niederschläge"),
    TeleconnectionEffect("IOD", "positive", Region.SOUTH_ASIA, HazardType.FLOOD, 0.40, 2,
                        "Verstärkter Monsun in Indien"),
]


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL RISK ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class GlobalRiskEngine:
    """
    Berechnet globalen Risiko-Kontext für jeden Punkt.
    """
    
    def __init__(self):
        self.teleconnection_matrix = TELECONNECTION_MATRIX
    
    def get_region(self, lat: float, lon: float) -> Region:
        """Bestimme die Region für Koordinaten."""
        # Nordamerika
        if 24 < lat < 50 and -125 < lon < -65:
            return Region.NA_WEST if lon < -100 else Region.NA_EAST
        
        # Mittelamerika
        if 5 < lat < 24 and -120 < lon < -60:
            return Region.CENTRAL_AMERICA
        
        # Südamerika
        if -60 < lat < 15 and -85 < lon < -30:
            return Region.SA_NORTH if lat > -20 else Region.SA_SOUTH
        
        # Europa
        if 35 < lat < 72 and -25 < lon < 45:
            return Region.EUROPE_NORTH if lat > 50 else Region.EUROPE_SOUTH
        
        # Afrika
        if -35 < lat < 35 and -20 < lon < 55:
            if lat > 20:
                return Region.AFRICA_NORTH
            elif lon > 25:
                return Region.AFRICA_EAST
            else:
                return Region.AFRICA_SOUTH
        
        # Mittlerer Osten
        if 15 < lat < 45 and 25 < lon < 65:
            return Region.MIDDLE_EAST
        
        # Südasien
        if 5 < lat < 40 and 60 < lon < 100:
            return Region.SOUTH_ASIA
        
        # Ostasien
        if 20 < lat < 55 and 100 < lon < 150:
            return Region.EAST_ASIA
        
        # Südostasien
        if -10 < lat < 25 and 95 < lon < 145:
            return Region.SOUTHEAST_ASIA
        
        # Australien
        if -45 < lat < -10 and 110 < lon < 180:
            return Region.AUSTRALIA
        
        # Default: Pazifik
        return Region.PACIFIC_ISLANDS
    
    def get_active_effects(self, region: Region, 
                           climate_indices: Dict[str, dict]) -> List[Dict]:
        """
        Finde alle aktiven Telekonnektion-Effekte für eine Region.
        
        Args:
            region: Die Zielregion
            climate_indices: Dict von Klimaindizes mit "value" und "phase"
            
        Returns:
            Liste von aktiven Effekten
        """
        active_effects = []
        
        for effect in self.teleconnection_matrix:
            if effect.region != region:
                continue
            
            # Prüfe ob der Klimamodus aktiv ist
            index_data = climate_indices.get(effect.climate_mode)
            if not index_data:
                continue
            
            # Prüfe Phase
            if index_data.get("phase") != effect.phase:
                continue
            
            # Berechne effektive Stärke basierend auf Index-Wert
            index_value = abs(index_data.get("value", 0))
            intensity_factor = min(index_value / 1.5, 1.5)  # Max 1.5x
            effective_magnitude = effect.magnitude * intensity_factor
            
            active_effects.append({
                "climate_mode": effect.climate_mode,
                "climate_mode_value": index_data.get("value"),
                "phase": effect.phase,
                "hazard": effect.hazard.value,
                "magnitude": round(effective_magnitude, 2),
                "delay_months": effect.delay_months,
                "mechanism": effect.mechanism
            })
        
        return sorted(active_effects, key=lambda x: abs(x["magnitude"]), reverse=True)
    
    def calculate_hazard_risks(self, region: Region, 
                               climate_indices: Dict[str, dict],
                               local_multipliers: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """
        Berechne Risiken für alle Hazard-Typen.
        
        Args:
            region: Die Zielregion
            climate_indices: Aktuelle Klimaindizes
            local_multipliers: Optionale lokale Verstärker/Dämpfer
            
        Returns:
            Dict mit Hazard-Typ als Key und Risiko (0-1) als Value
        """
        if local_multipliers is None:
            local_multipliers = {}
        
        effects = self.get_active_effects(region, climate_indices)
        
        # Basis-Risiken
        risks = {h.value: 0.10 for h in HazardType}
        
        # Addiere Telekonnektion-Effekte
        for effect in effects:
            hazard = effect["hazard"]
            if effect["magnitude"] > 0:
                risks[hazard] = min(1.0, risks[hazard] + effect["magnitude"])
            else:
                # Negativer Effekt reduziert Risiko
                risks[hazard] = max(0.0, risks[hazard] + effect["magnitude"])
        
        # Multipliziere mit lokalen Faktoren
        for hazard, risk in risks.items():
            multiplier = local_multipliers.get(hazard, 1.0)
            risks[hazard] = min(1.0, risk * multiplier)
        
        return {k: round(v, 3) for k, v in risks.items()}
    
    def calculate_global_context(self, lat: float, lon: float,
                                  climate_indices: Dict[str, dict],
                                  local_vulnerability: Optional[Dict] = None) -> Dict:
        """
        Berechne den vollständigen globalen Kontext für einen Punkt.
        
        Args:
            lat, lon: Koordinaten
            climate_indices: Aktuelle Klimaindizes
            local_vulnerability: Optionale lokale Vulnerabilitätsdaten
            
        Returns:
            Vollständiger Risiko-Kontext
        """
        region = self.get_region(lat, lon)
        
        # Lokale Multiplikatoren berechnen
        local_multipliers = self._calculate_local_multipliers(
            lat, lon, local_vulnerability or {}
        )
        
        # Aktive Effekte
        effects = self.get_active_effects(region, climate_indices)
        
        # Hazard-Risiken
        risks = self.calculate_hazard_risks(region, climate_indices, local_multipliers)
        
        # Top Hazards
        top_hazards = sorted(
            [(k, v) for k, v in risks.items()],
            key=lambda x: x[1], reverse=True
        )[:3]
        
        # Kausale Ketten erstellen
        causal_chains = []
        for effect in effects[:5]:
            chain = f"{effect['climate_mode']} ({effect['phase']}) → {effect['hazard']} ({effect['magnitude']:.0%})"
            causal_chains.append(chain)
        
        return {
            "location": {"lat": lat, "lon": lon},
            "region": region.value,
            "active_climate_modes": [
                {
                    "mode": k,
                    "value": v.get("value"),
                    "phase": v.get("phase"),
                    "strength": v.get("strength", "unknown")
                }
                for k, v in climate_indices.items()
                if v.get("phase") != "neutral"
            ],
            "teleconnection_effects": effects,
            "local_multipliers": local_multipliers,
            "hazard_risks": risks,
            "top_hazards": top_hazards,
            "causal_chains": causal_chains,
            "total_risk": round(sum(risks.values()) / len(risks), 3)
        }
    
    def _calculate_local_multipliers(self, lat: float, lon: float, 
                                     vulnerability: Dict) -> Dict[str, float]:
        """Berechne lokale Multiplikatoren basierend auf Geographie."""
        multipliers = {}
        
        # Elevation
        elevation = vulnerability.get("elevation", 100)
        coastal_distance = vulnerability.get("coastal_distance", 50)
        forest_coverage = vulnerability.get("forest_coverage", 0.2)
        urban_density = vulnerability.get("urban_density", 0.5)
        
        # Flood
        flood_mult = 1.0
        if elevation < 10:
            flood_mult *= 1.5
        if coastal_distance < 5:
            flood_mult *= 1.4
        multipliers["flood"] = flood_mult
        
        # Coastal Flood
        coastal_mult = 1.0
        if coastal_distance < 1:
            coastal_mult = 2.0
        elif coastal_distance < 5:
            coastal_mult = 1.5
        elif coastal_distance > 20:
            coastal_mult = 0.2
        multipliers["coastal_flood"] = coastal_mult
        
        # Wildfire
        fire_mult = 1.0
        if forest_coverage > 0.3:
            fire_mult *= 1.3
        if 30 < abs(lat) < 45:  # Mediterran
            fire_mult *= 1.2
        multipliers["wildfire"] = fire_mult
        
        # Heat Wave
        heat_mult = 1.0
        if urban_density > 0.5:
            heat_mult *= 1.4
        multipliers["heat_wave"] = heat_mult
        
        # Tropical Cyclone
        cyclone_mult = 1.0
        if abs(lat) > 35:
            cyclone_mult = 0.1
        elif coastal_distance < 50:
            cyclone_mult = 1.3
        multipliers["tropical_cyclone"] = cyclone_mult
        
        # Default für andere
        for hazard in HazardType:
            if hazard.value not in multipliers:
                multipliers[hazard.value] = 1.0
        
        return multipliers


# Singleton
global_risk_engine = GlobalRiskEngine()


def main():
    """Test-Funktion."""
    print("=" * 70)
    print("TERA V2: Global Risk Engine - Test")
    print("=" * 70)
    
    # Simulierte Klimaindizes (El Niño Situation)
    climate_indices = {
        "ONI": {"value": 1.8, "phase": "positive", "strength": "strong"},
        "AMO": {"value": 0.4, "phase": "neutral", "strength": "weak"},
        "IOD": {"value": 0.8, "phase": "positive", "strength": "moderate"},
        "NAO": {"value": -0.3, "phase": "neutral", "strength": "weak"},
    }
    
    print("\n📡 Aktuelle Klimaindizes:")
    for name, data in climate_indices.items():
        print(f"   {name}: {data['value']:+.1f} ({data['phase']})")
    
    # Test-Standorte
    locations = [
        ("Sydney, Australien", -33.87, 151.21),
        ("Miami, USA", 25.76, -80.19),
        ("Lima, Peru", -12.05, -77.04),
        ("Mumbai, Indien", 19.08, 72.88),
    ]
    
    engine = GlobalRiskEngine()
    
    for name, lat, lon in locations:
        print(f"\n{'─'*70}")
        print(f"📍 {name}")
        print(f"{'─'*70}")
        
        context = engine.calculate_global_context(lat, lon, climate_indices)
        
        print(f"\n   Region: {context['region']}")
        
        print(f"\n   Aktive Telekonnektion:")
        for effect in context['teleconnection_effects'][:3]:
            print(f"   • {effect['climate_mode']} → {effect['hazard']}: {effect['magnitude']:.0%}")
            print(f"     {effect['mechanism'][:60]}...")
        
        print(f"\n   Top Risiken:")
        for hazard, risk in context['top_hazards']:
            emoji = "🔴" if risk > 0.5 else "🟡" if risk > 0.3 else "🟢"
            print(f"   {emoji} {hazard:20s}: {risk:.0%}")
        
        print(f"\n   GESAMT-RISIKO: {context['total_risk']:.0%}")


if __name__ == "__main__":
    main()












