"""
TERA V2: Enhanced Tessellation
===============================

Erweitert die H3-Tessellation um:
1. Globalen Klimakontext
2. Kausale Ketten für jede Zelle
3. Zeitliche Projektionen
"""

import h3
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math

# Import unserer Services
from global_risk_engine import GlobalRiskEngine, HazardType, Region


@dataclass
class EnhancedHexagon:
    """Eine erweiterte H3-Zelle mit vollständigem Risiko-Kontext."""
    h3_index: str
    lat: float
    lon: float
    
    # Basis-Eigenschaften
    elevation: float
    coastal_distance: float
    is_land: bool
    
    # Globaler Kontext
    region: str
    active_climate_modes: List[Dict]
    teleconnection_effects: List[Dict]
    
    # Risiken
    hazard_risks: Dict[str, float]
    dominant_hazard: str
    dominant_risk: float
    total_risk: float
    
    # Kausale Erklärung
    causal_chains: List[str]
    
    # Visualisierung
    color: str
    height: float
    
    def to_geojson_feature(self) -> Dict:
        """Konvertiere zu GeoJSON Feature."""
        # h3 v4 API
        try:
            boundary = h3.cell_to_boundary(self.h3_index)
            # Konvertiere zu GeoJSON Format (lon, lat) und schließe Polygon
            boundary = [(lon, lat) for lat, lon in boundary]
            boundary.append(boundary[0])  # Schließe Polygon
        except:
            boundary = []
        
        return {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [boundary]
            },
            "properties": {
                "h3_index": self.h3_index,
                "lat": self.lat,
                "lon": self.lon,
                "elevation": self.elevation,
                "coastal_distance": self.coastal_distance,
                "is_land": self.is_land,
                "region": self.region,
                "zone": self.dominant_hazard,
                "intensity": self.dominant_risk,
                "total_risk": self.total_risk,
                "color": self.color,
                "height": self.height,
                "hazard_risks": self.hazard_risks,
                "causal_chains": self.causal_chains,
                "active_climate_modes": self.active_climate_modes,
                "teleconnection_effects": self.teleconnection_effects[:3]  # Top 3
            }
        }


class EnhancedTessellationEngine:
    """
    Generiert erweiterte H3-Tessellation mit globalem Klimakontext.
    """
    
    # Farben für Hazard-Typen
    HAZARD_COLORS = {
        "flood": "#3498db",           # Blau
        "coastal_flood": "#2980b9",   # Dunkelblau
        "drought": "#e67e22",         # Orange
        "wildfire": "#e74c3c",        # Rot
        "tropical_cyclone": "#9b59b6", # Lila
        "heat_wave": "#f39c12",       # Gelb
        "cold_wave": "#1abc9c",       # Türkis
        "landslide": "#795548",       # Braun
        "low_risk": "#2ecc71",        # Grün
        "water": "#1a5276",           # Dunkelblau
    }
    
    def __init__(self):
        self.risk_engine = GlobalRiskEngine()
    
    def generate_hexagons(self, center_lat: float, center_lon: float,
                          radius_km: float = 30,
                          resolution: int = 8,
                          climate_indices: Optional[Dict] = None,
                          year: int = 2026,
                          scenario: str = "SSP2-4.5") -> Dict:
        """
        Generiere erweiterte H3-Hexagone für eine Region.
        
        Args:
            center_lat, center_lon: Zentrum der Region
            radius_km: Radius in km
            resolution: H3 Auflösung (7-9)
            climate_indices: Aktuelle Klimaindizes
            year: Projektionsjahr
            scenario: IPCC Szenario
            
        Returns:
            GeoJSON FeatureCollection mit erweiterten Hexagonen
        """
        # Default Klimaindizes falls nicht übergeben
        if climate_indices is None:
            climate_indices = self._get_default_climate_indices()
        
        # Bestimme Region einmal für das Zentrum
        center_region = self.risk_engine.get_region(center_lat, center_lon)
        
        # Berechne globalen Kontext für die Region
        global_context = self.risk_engine.calculate_global_context(
            center_lat, center_lon, climate_indices
        )
        
        # Generiere H3-Indizes im Radius (h3 v4 API)
        center_h3 = h3.latlng_to_cell(center_lat, center_lon, resolution)
        k_ring_radius = self._km_to_k_ring(radius_km, resolution)
        h3_indices = h3.grid_disk(center_h3, k_ring_radius)
        
        # Generiere Features für jedes Hexagon
        features = []
        stats = {
            "total": 0,
            "land": 0,
            "water": 0,
            "by_hazard": {}
        }
        
        for h3_idx in h3_indices:
            lat, lon = h3.cell_to_latlng(h3_idx)
            
            # Lokale Eigenschaften (simuliert - in Produktion aus DEM)
            local_props = self._estimate_local_properties(lat, lon, center_lat, center_lon)
            
            # Skip wenn Wasser (vereinfacht)
            if not local_props["is_land"]:
                stats["water"] += 1
                # Wasser-Feature hinzufügen
                water_hex = self._create_water_hexagon(h3_idx, lat, lon, local_props)
                features.append(water_hex.to_geojson_feature())
                continue
            
            stats["land"] += 1
            
            # Lokale Vulnerabilitätsmultiplikatoren
            local_multipliers = self._calculate_local_multipliers(local_props)
            
            # Berechne Hazard-Risiken mit lokalen Multiplikatoren
            hazard_risks = {}
            for hazard, risk in global_context["hazard_risks"].items():
                mult = local_multipliers.get(hazard, 1.0)
                hazard_risks[hazard] = min(1.0, risk * mult)
            
            # Jahr-basierte Projektion
            hazard_risks = self._apply_temporal_projection(
                hazard_risks, year, scenario
            )
            
            # Dominantes Hazard bestimmen
            dominant_hazard, dominant_risk = max(
                hazard_risks.items(), key=lambda x: x[1]
            )
            
            # Zonenzuordnung
            if dominant_risk < 0.2:
                zone = "low_risk"
                color = self.HAZARD_COLORS["low_risk"]
            else:
                zone = dominant_hazard
                color = self.HAZARD_COLORS.get(dominant_hazard, "#808080")
            
            # Kausale Ketten für dominantes Hazard
            causal_chains = self._get_causal_chains_for_hazard(
                dominant_hazard, global_context["teleconnection_effects"]
            )
            
            # Statistik
            if zone not in stats["by_hazard"]:
                stats["by_hazard"][zone] = 0
            stats["by_hazard"][zone] += 1
            
            # Enhanced Hexagon erstellen
            hexagon = EnhancedHexagon(
                h3_index=h3_idx,
                lat=lat,
                lon=lon,
                elevation=local_props["elevation"],
                coastal_distance=local_props["coastal_distance"],
                is_land=True,
                region=center_region.value,
                active_climate_modes=global_context["active_climate_modes"],
                teleconnection_effects=global_context["teleconnection_effects"],
                hazard_risks=hazard_risks,
                dominant_hazard=zone,
                dominant_risk=dominant_risk,
                total_risk=sum(hazard_risks.values()) / len(hazard_risks),
                causal_chains=causal_chains,
                color=color,
                height=dominant_risk * 200  # Höhe basierend auf Risiko
            )
            
            features.append(hexagon.to_geojson_feature())
        
        stats["total"] = len(features)
        
        return {
            "type": "FeatureCollection",
            "metadata": {
                "center": {"lat": center_lat, "lon": center_lon},
                "radius_km": radius_km,
                "resolution": resolution,
                "year": year,
                "scenario": scenario,
                "region": center_region.value
            },
            "global_context": {
                "climate_modes": global_context["active_climate_modes"],
                "teleconnection_effects": global_context["teleconnection_effects"][:5],
                "top_hazards": global_context["top_hazards"]
            },
            "statistics": stats,
            "features": features
        }
    
    def _get_default_climate_indices(self) -> Dict:
        """Default Klimaindizes für Demo."""
        return {
            "ONI": {"value": 1.8, "phase": "positive", "strength": "strong"},
            "AMO": {"value": 0.4, "phase": "neutral", "strength": "weak"},
            "IOD": {"value": 0.8, "phase": "positive", "strength": "moderate"},
            "NAO": {"value": -0.3, "phase": "neutral", "strength": "weak"},
            "PDO": {"value": -0.2, "phase": "neutral", "strength": "weak"},
        }
    
    def _km_to_k_ring(self, radius_km: float, resolution: int) -> int:
        """Konvertiere km zu k-ring Radius."""
        # Ungefähre Hexagon-Größe pro Resolution
        hex_sizes = {
            7: 5.16,   # km edge length
            8: 1.95,
            9: 0.74,
            10: 0.28
        }
        edge_km = hex_sizes.get(resolution, 1.0)
        return max(1, int(radius_km / (edge_km * 2)))
    
    def _estimate_local_properties(self, lat: float, lon: float,
                                    center_lat: float, center_lon: float) -> Dict:
        """
        Schätze lokale Eigenschaften (vereinfacht).
        In Produktion würde man DEM und echte Daten nutzen.
        """
        # Einfache Distanzberechnung zum Zentrum
        dist_km = self._haversine(lat, lon, center_lat, center_lon)
        
        # Simulierte Elevation (höher weiter vom Zentrum)
        elevation = 10 + dist_km * 3 + abs(lat - center_lat) * 100
        
        # Simulierte Küstendistanz (näher an Küste bei niedrigen Koordinaten)
        # Dies ist sehr vereinfacht - in Produktion aus echten Daten
        coastal_distance = 5 + dist_km * 0.5
        
        # Ist es Land? (sehr vereinfacht)
        is_land = True
        # Zufällig einige Zellen als Wasser markieren wenn nah am Meer
        if coastal_distance < 2 and hash(f"{lat:.4f}{lon:.4f}") % 10 < 3:
            is_land = False
        
        return {
            "elevation": elevation,
            "coastal_distance": coastal_distance,
            "is_land": is_land,
            "forest_coverage": 0.2 + (hash(f"{lat:.3f}") % 30) / 100,
            "urban_density": 0.5 - dist_km * 0.02
        }
    
    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Berechne Distanz in km zwischen zwei Punkten."""
        R = 6371  # Erdradius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _calculate_local_multipliers(self, local_props: Dict) -> Dict[str, float]:
        """Berechne lokale Multiplikatoren."""
        multipliers = {}
        
        elevation = local_props.get("elevation", 100)
        coastal = local_props.get("coastal_distance", 50)
        forest = local_props.get("forest_coverage", 0.2)
        urban = local_props.get("urban_density", 0.5)
        
        # Flood
        multipliers["flood"] = 1.0
        if elevation < 10:
            multipliers["flood"] *= 1.5
        if coastal < 5:
            multipliers["flood"] *= 1.3
        
        # Coastal Flood
        multipliers["coastal_flood"] = max(0.1, 2.0 - coastal * 0.1)
        
        # Wildfire
        multipliers["wildfire"] = 1.0 + forest * 0.5
        
        # Heat Wave
        multipliers["heat_wave"] = 1.0 + urban * 0.5
        
        # Defaults
        for hazard in ["drought", "tropical_cyclone", "cold_wave", "landslide"]:
            if hazard not in multipliers:
                multipliers[hazard] = 1.0
        
        return multipliers
    
    def _apply_temporal_projection(self, risks: Dict[str, float], 
                                   year: int, scenario: str) -> Dict[str, float]:
        """Wende zeitliche Projektion an (IPCC Szenarien)."""
        if year <= 2024:
            return risks
        
        years_ahead = year - 2024
        
        # Szenario-Faktoren
        scenario_factors = {
            "SSP1-1.9": 0.3,   # Nachhaltigkeit
            "SSP2-4.5": 1.0,   # Mittlerer Weg
            "SSP3-7.0": 1.5,   # Hohe Emissionen
            "SSP5-8.5": 2.0,   # Fossile Zukunft
        }
        factor = scenario_factors.get(scenario, 1.0)
        
        projected = {}
        for hazard, risk in risks.items():
            # Verschiedene Hazards entwickeln sich unterschiedlich
            if hazard in ["heat_wave", "wildfire", "drought"]:
                # Diese steigen mit Klimawandel
                increase = years_ahead * 0.01 * factor
            elif hazard in ["flood", "coastal_flood"]:
                # Auch steigend
                increase = years_ahead * 0.008 * factor
            elif hazard == "cold_wave":
                # Sinkt leicht
                increase = -years_ahead * 0.005 * factor
            else:
                increase = years_ahead * 0.005 * factor
            
            projected[hazard] = min(1.0, max(0.0, risk + increase))
        
        return projected
    
    def _get_causal_chains_for_hazard(self, hazard: str, 
                                       teleconnection_effects: List[Dict]) -> List[str]:
        """Erstelle kausale Ketten-Beschreibungen für ein Hazard."""
        chains = []
        
        for effect in teleconnection_effects:
            if effect["hazard"] == hazard:
                chain = f"{effect['climate_mode']} ({effect['phase']}) → {hazard} ({effect['magnitude']:.0%})"
                chains.append(chain)
        
        if not chains:
            chains.append(f"Basis-Risiko → {hazard}")
        
        return chains[:3]  # Max 3 Ketten
    
    def _create_water_hexagon(self, h3_idx: str, lat: float, lon: float,
                               local_props: Dict) -> EnhancedHexagon:
        """Erstelle Wasser-Hexagon."""
        return EnhancedHexagon(
            h3_index=h3_idx,
            lat=lat,
            lon=lon,
            elevation=0,
            coastal_distance=0,
            is_land=False,
            region="water",
            active_climate_modes=[],
            teleconnection_effects=[],
            hazard_risks={"water": 0},
            dominant_hazard="water",
            dominant_risk=0,
            total_risk=0,
            causal_chains=[],
            color=self.HAZARD_COLORS["water"],
            height=0
        )


# Singleton
enhanced_tessellation = EnhancedTessellationEngine()


def main():
    """Test-Funktion."""
    print("=" * 70)
    print("TERA V2: Enhanced Tessellation - Test")
    print("=" * 70)
    
    engine = EnhancedTessellationEngine()
    
    # Klimaindizes (El Niño)
    climate = {
        "ONI": {"value": 1.8, "phase": "positive", "strength": "strong"},
        "IOD": {"value": 0.8, "phase": "positive", "strength": "moderate"},
    }
    
    # Test für Sydney
    print("\n📍 Generiere Tessellation für Sydney...")
    result = engine.generate_hexagons(
        center_lat=-33.87,
        center_lon=151.21,
        radius_km=20,
        resolution=8,
        climate_indices=climate,
        year=2026,
        scenario="SSP2-4.5"
    )
    
    print(f"\n📊 Statistiken:")
    print(f"   Total Zellen: {result['statistics']['total']}")
    print(f"   Land: {result['statistics']['land']}")
    print(f"   Wasser: {result['statistics']['water']}")
    
    print(f"\n🌍 Globaler Kontext:")
    for mode in result['global_context']['climate_modes']:
        print(f"   • {mode['mode']}: {mode['value']:+.1f} ({mode['phase']})")
    
    print(f"\n📡 Telekonnektion-Effekte:")
    for effect in result['global_context']['teleconnection_effects'][:3]:
        print(f"   • {effect['climate_mode']} → {effect['hazard']}: {effect['magnitude']:.0%}")
    
    print(f"\n🎯 Zellen nach Hazard:")
    for hazard, count in result['statistics']['by_hazard'].items():
        print(f"   {hazard:20s}: {count} Zellen")
    
    # Ein Beispiel-Feature
    if result['features']:
        example = result['features'][0]['properties']
        print(f"\n📍 Beispiel-Zelle:")
        print(f"   H3: {example['h3_index']}")
        print(f"   Zone: {example['zone']}")
        print(f"   Intensität: {example['intensity']:.0%}")
        print(f"   Kausale Ketten: {example['causal_chains']}")


if __name__ == "__main__":
    main()

