"""
TERA V2: Global-Local Causal Framework
========================================

Dieses Framework abstrahiert die Verbindung zwischen:
- Globalen Treibern (Tektonik, Ozean, Atmosphäre)
- Klima-Modi (ENSO, AMO, PDO, NAO, IOD, MJO)
- Regionaler Telekonnektion (wie wirken globale Modi lokal?)
- Lokaler Vulnerabilität (Topographie, Infrastruktur)
- Konkreten Ereignissen (Flut, Dürre, Sturm)

Das Ziel: Für JEDEN Punkt auf der Erde die relevanten globalen
Zusammenhänge identifizieren und quantifizieren.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
import numpy as np
from abc import ABC, abstractmethod


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 0: PRIMÄRE TREIBER
# ═══════════════════════════════════════════════════════════════════════════════

class PrimaryDriver(Enum):
    """Fundamentale geophysikalische Treiber."""
    # Tektonisch
    EARTHQUAKE = "earthquake"
    VOLCANIC_ERUPTION = "volcanic_eruption"
    TSUNAMI = "tsunami"
    
    # Solar/Kosmisch
    SOLAR_IRRADIANCE = "solar_irradiance"
    SOLAR_FLARE = "solar_flare"
    MILANKOVITCH_CYCLE = "milankovitch_cycle"
    
    # Ozeanisch
    THERMOHALINE_CIRCULATION = "thermohaline_circulation"
    UPWELLING = "upwelling"
    OCEAN_HEAT_CONTENT = "ocean_heat_content"
    
    # Atmosphärisch
    JET_STREAM_POSITION = "jet_stream_position"
    POLAR_VORTEX = "polar_vortex"
    MONSOON_SYSTEM = "monsoon_system"
    HADLEY_CELL = "hadley_cell"


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 1: KLIMA-MODI (Oszillationen)
# ═══════════════════════════════════════════════════════════════════════════════

class ClimateMode(Enum):
    """Große Klima-Oszillationen mit globaler Auswirkung."""
    ENSO = "enso"           # El Niño Southern Oscillation
    AMO = "amo"             # Atlantic Multidecadal Oscillation
    PDO = "pdo"             # Pacific Decadal Oscillation
    NAO = "nao"             # North Atlantic Oscillation
    IOD = "iod"             # Indian Ocean Dipole
    MJO = "mjo"             # Madden-Julian Oscillation
    AO = "ao"               # Arctic Oscillation
    AAO = "aao"             # Antarctic Oscillation
    QBO = "qbo"             # Quasi-Biennial Oscillation


@dataclass
class ClimateModeState:
    """Aktueller Zustand eines Klima-Modus."""
    mode: ClimateMode
    index_value: float      # Standardisierter Index (-3 bis +3 typisch)
    phase: str              # "positive", "negative", "neutral"
    strength: str           # "weak", "moderate", "strong", "extreme"
    trend: str              # "strengthening", "weakening", "stable"
    forecast_months: Dict[int, float] = field(default_factory=dict)  # Monat → Wert
    confidence: float = 0.5
    
    @classmethod
    def from_index(cls, mode: ClimateMode, value: float, trend: float = 0):
        """Erstelle Zustand aus Index-Wert."""
        if value > 0.5:
            phase = "positive"
        elif value < -0.5:
            phase = "negative"
        else:
            phase = "neutral"
        
        abs_val = abs(value)
        if abs_val > 2.0:
            strength = "extreme"
        elif abs_val > 1.5:
            strength = "strong"
        elif abs_val > 0.5:
            strength = "moderate"
        else:
            strength = "weak"
        
        if trend > 0.1:
            trend_str = "strengthening"
        elif trend < -0.1:
            trend_str = "weakening"
        else:
            trend_str = "stable"
        
        return cls(mode=mode, index_value=value, phase=phase, 
                   strength=strength, trend=trend_str)


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 2: TELEKONNEKTION (Global → Regional)
# ═══════════════════════════════════════════════════════════════════════════════

class Region(Enum):
    """Globale Regionen für Telekonnektion."""
    NORTH_AMERICA_EAST = "na_east"
    NORTH_AMERICA_WEST = "na_west"
    CENTRAL_AMERICA = "central_america"
    SOUTH_AMERICA_NORTH = "sa_north"
    SOUTH_AMERICA_SOUTH = "sa_south"
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
    PACIFIC_ISLANDS = "pacific_islands"


class HazardType(Enum):
    """Typen von Extremereignissen."""
    FLOOD = "flood"
    DROUGHT = "drought"
    TROPICAL_CYCLONE = "tropical_cyclone"
    WILDFIRE = "wildfire"
    HEAT_WAVE = "heat_wave"
    COLD_WAVE = "cold_wave"
    SEVERE_STORM = "severe_storm"
    COASTAL_FLOOD = "coastal_flood"
    LANDSLIDE = "landslide"


@dataclass
class TeleconnectionEffect:
    """Wirkung eines Klima-Modus auf eine Region."""
    climate_mode: ClimateMode
    phase: str  # "positive" oder "negative"
    region: Region
    hazard: HazardType
    effect_direction: str  # "increase", "decrease", "shift"
    magnitude: float  # 0-1 Stärke des Effekts
    delay_months: float  # Verzögerung
    confidence: float  # Wissenschaftliche Sicherheit
    mechanism: str  # Physikalische Erklärung


class TeleconnectionMatrix:
    """
    Die Telekonnektion-Matrix verbindet globale Klima-Modi
    mit regionalen Auswirkungen.
    
    Basiert auf wissenschaftlicher Literatur (IPCC, NOAA, etc.)
    """
    
    def __init__(self):
        self.effects: List[TeleconnectionEffect] = []
        self._build_matrix()
    
    def _build_matrix(self):
        """Fülle die Matrix mit wissenschaftlich fundierten Verbindungen."""
        
        # ════════════════════════════════════════════════════════════════
        # ENSO (El Niño / La Niña) - Der wichtigste globale Klima-Modus
        # ════════════════════════════════════════════════════════════════
        
        # El Niño (positive Phase)
        enso_positive = [
            # Nordamerika
            TeleconnectionEffect(
                climate_mode=ClimateMode.ENSO, phase="positive",
                region=Region.NORTH_AMERICA_WEST, hazard=HazardType.FLOOD,
                effect_direction="increase", magnitude=0.6, delay_months=3,
                confidence=0.85,
                mechanism="Verstärkter subtropischer Jetstream bringt mehr Stürme nach Kalifornien"
            ),
            TeleconnectionEffect(
                climate_mode=ClimateMode.ENSO, phase="positive",
                region=Region.NORTH_AMERICA_EAST, hazard=HazardType.COLD_WAVE,
                effect_direction="decrease", magnitude=0.4, delay_months=4,
                confidence=0.70,
                mechanism="Wärmerer Winter im Nordosten durch veränderte Jetstream-Position"
            ),
            # Südamerika
            TeleconnectionEffect(
                climate_mode=ClimateMode.ENSO, phase="positive",
                region=Region.SOUTH_AMERICA_NORTH, hazard=HazardType.FLOOD,
                effect_direction="increase", magnitude=0.8, delay_months=4,
                confidence=0.90,
                mechanism="Warmes Wasser vor Peru erhöht Verdunstung, extreme Niederschläge"
            ),
            TeleconnectionEffect(
                climate_mode=ClimateMode.ENSO, phase="positive",
                region=Region.SOUTH_AMERICA_SOUTH, hazard=HazardType.FLOOD,
                effect_direction="increase", magnitude=0.5, delay_months=5,
                confidence=0.75,
                mechanism="Verstärkte Niederschläge in Argentinien/Südbrasilien"
            ),
            # Australien/Asien
            TeleconnectionEffect(
                climate_mode=ClimateMode.ENSO, phase="positive",
                region=Region.AUSTRALIA, hazard=HazardType.DROUGHT,
                effect_direction="increase", magnitude=0.75, delay_months=3,
                confidence=0.88,
                mechanism="Walker-Zirkulation schwächt sich ab, weniger Monsun-Regen"
            ),
            TeleconnectionEffect(
                climate_mode=ClimateMode.ENSO, phase="positive",
                region=Region.AUSTRALIA, hazard=HazardType.WILDFIRE,
                effect_direction="increase", magnitude=0.7, delay_months=5,
                confidence=0.82,
                mechanism="Dürre führt zu erhöhter Waldbrandgefahr"
            ),
            TeleconnectionEffect(
                climate_mode=ClimateMode.ENSO, phase="positive",
                region=Region.SOUTHEAST_ASIA, hazard=HazardType.DROUGHT,
                effect_direction="increase", magnitude=0.65, delay_months=2,
                confidence=0.80,
                mechanism="Schwächerer Monsun in Indonesien/Philippinen"
            ),
            TeleconnectionEffect(
                climate_mode=ClimateMode.ENSO, phase="positive",
                region=Region.SOUTH_ASIA, hazard=HazardType.DROUGHT,
                effect_direction="increase", magnitude=0.4, delay_months=4,
                confidence=0.65,
                mechanism="Schwächerer indischer Monsun"
            ),
            # Afrika
            TeleconnectionEffect(
                climate_mode=ClimateMode.ENSO, phase="positive",
                region=Region.AFRICA_EAST, hazard=HazardType.DROUGHT,
                effect_direction="increase", magnitude=0.55, delay_months=4,
                confidence=0.70,
                mechanism="Reduzierte Niederschläge in Ostafrika"
            ),
            TeleconnectionEffect(
                climate_mode=ClimateMode.ENSO, phase="positive",
                region=Region.AFRICA_SOUTH, hazard=HazardType.DROUGHT,
                effect_direction="increase", magnitude=0.6, delay_months=5,
                confidence=0.75,
                mechanism="Dürre im südlichen Afrika"
            ),
            # Pazifik
            TeleconnectionEffect(
                climate_mode=ClimateMode.ENSO, phase="positive",
                region=Region.PACIFIC_ISLANDS, hazard=HazardType.TROPICAL_CYCLONE,
                effect_direction="increase", magnitude=0.5, delay_months=2,
                confidence=0.72,
                mechanism="Mehr Taifune im zentralen Pazifik"
            ),
        ]
        
        # La Niña (negative Phase) - oft inverse Effekte
        enso_negative = [
            TeleconnectionEffect(
                climate_mode=ClimateMode.ENSO, phase="negative",
                region=Region.AUSTRALIA, hazard=HazardType.FLOOD,
                effect_direction="increase", magnitude=0.7, delay_months=3,
                confidence=0.85,
                mechanism="Verstärkte Walker-Zirkulation bringt mehr Regen"
            ),
            TeleconnectionEffect(
                climate_mode=ClimateMode.ENSO, phase="negative",
                region=Region.NORTH_AMERICA_WEST, hazard=HazardType.DROUGHT,
                effect_direction="increase", magnitude=0.5, delay_months=4,
                confidence=0.70,
                mechanism="Trockenere Bedingungen im Südwesten USA"
            ),
            TeleconnectionEffect(
                climate_mode=ClimateMode.ENSO, phase="negative",
                region=Region.SOUTH_AMERICA_NORTH, hazard=HazardType.DROUGHT,
                effect_direction="increase", magnitude=0.4, delay_months=3,
                confidence=0.65,
                mechanism="Kühleres Wasser vor Peru reduziert Niederschläge"
            ),
        ]
        
        # ════════════════════════════════════════════════════════════════
        # AMO (Atlantic Multidecadal Oscillation)
        # ════════════════════════════════════════════════════════════════
        
        amo_effects = [
            TeleconnectionEffect(
                climate_mode=ClimateMode.AMO, phase="positive",
                region=Region.NORTH_AMERICA_EAST, hazard=HazardType.TROPICAL_CYCLONE,
                effect_direction="increase", magnitude=0.7, delay_months=0,
                confidence=0.85,
                mechanism="Wärmerer Atlantik liefert mehr Energie für Hurrikane"
            ),
            TeleconnectionEffect(
                climate_mode=ClimateMode.AMO, phase="positive",
                region=Region.CENTRAL_AMERICA, hazard=HazardType.TROPICAL_CYCLONE,
                effect_direction="increase", magnitude=0.65, delay_months=0,
                confidence=0.80,
                mechanism="Mehr und stärkere Hurrikane in der Karibik"
            ),
            TeleconnectionEffect(
                climate_mode=ClimateMode.AMO, phase="positive",
                region=Region.AFRICA_NORTH, hazard=HazardType.DROUGHT,
                effect_direction="decrease", magnitude=0.5, delay_months=2,
                confidence=0.70,
                mechanism="Mehr Niederschlag in der Sahel-Zone"
            ),
            TeleconnectionEffect(
                climate_mode=ClimateMode.AMO, phase="positive",
                region=Region.EUROPE_NORTH, hazard=HazardType.HEAT_WAVE,
                effect_direction="increase", magnitude=0.4, delay_months=1,
                confidence=0.65,
                mechanism="Wärmere Sommer in Nordeuropa"
            ),
        ]
        
        # ════════════════════════════════════════════════════════════════
        # NAO (North Atlantic Oscillation)
        # ════════════════════════════════════════════════════════════════
        
        nao_effects = [
            TeleconnectionEffect(
                climate_mode=ClimateMode.NAO, phase="positive",
                region=Region.EUROPE_NORTH, hazard=HazardType.FLOOD,
                effect_direction="increase", magnitude=0.5, delay_months=0,
                confidence=0.80,
                mechanism="Stärkere Westwinde bringen mehr Regen nach Nordeuropa"
            ),
            TeleconnectionEffect(
                climate_mode=ClimateMode.NAO, phase="positive",
                region=Region.EUROPE_SOUTH, hazard=HazardType.DROUGHT,
                effect_direction="increase", magnitude=0.45, delay_months=1,
                confidence=0.75,
                mechanism="Trockenere Bedingungen im Mittelmeerraum"
            ),
            TeleconnectionEffect(
                climate_mode=ClimateMode.NAO, phase="negative",
                region=Region.EUROPE_NORTH, hazard=HazardType.COLD_WAVE,
                effect_direction="increase", magnitude=0.6, delay_months=0,
                confidence=0.78,
                mechanism="Arktische Luft kann leichter nach Süden vordringen"
            ),
        ]
        
        # ════════════════════════════════════════════════════════════════
        # IOD (Indian Ocean Dipole)
        # ════════════════════════════════════════════════════════════════
        
        iod_effects = [
            TeleconnectionEffect(
                climate_mode=ClimateMode.IOD, phase="positive",
                region=Region.AUSTRALIA, hazard=HazardType.DROUGHT,
                effect_direction="increase", magnitude=0.65, delay_months=2,
                confidence=0.80,
                mechanism="Kühleres Wasser westlich von Australien reduziert Verdunstung"
            ),
            TeleconnectionEffect(
                climate_mode=ClimateMode.IOD, phase="positive",
                region=Region.AUSTRALIA, hazard=HazardType.WILDFIRE,
                effect_direction="increase", magnitude=0.6, delay_months=4,
                confidence=0.75,
                mechanism="Dürre erhöht Waldbrandgefahr"
            ),
            TeleconnectionEffect(
                climate_mode=ClimateMode.IOD, phase="positive",
                region=Region.AFRICA_EAST, hazard=HazardType.FLOOD,
                effect_direction="increase", magnitude=0.55, delay_months=1,
                confidence=0.72,
                mechanism="Wärmeres Wasser im westlichen Indik verstärkt Niederschläge"
            ),
            TeleconnectionEffect(
                climate_mode=ClimateMode.IOD, phase="positive",
                region=Region.SOUTH_ASIA, hazard=HazardType.FLOOD,
                effect_direction="increase", magnitude=0.4, delay_months=2,
                confidence=0.65,
                mechanism="Verstärkter Monsun in Indien"
            ),
        ]
        
        # Alle Effekte zusammenführen
        self.effects = enso_positive + enso_negative + amo_effects + nao_effects + iod_effects
    
    def get_effects_for_region(self, region: Region, 
                               active_modes: Dict[ClimateMode, ClimateModeState]) -> List[Dict]:
        """
        Berechne alle aktuell aktiven Effekte für eine Region.
        
        Args:
            region: Die Zielregion
            active_modes: Aktuelle Zustände aller Klima-Modi
            
        Returns:
            Liste von aktiven Effekten mit berechneter Intensität
        """
        active_effects = []
        
        for effect in self.effects:
            if effect.region != region:
                continue
            
            mode_state = active_modes.get(effect.climate_mode)
            if not mode_state:
                continue
            
            # Prüfe ob der Modus in der richtigen Phase ist
            if mode_state.phase != effect.phase:
                continue
            
            # Berechne effektive Intensität
            # Stärker ausgeprägte Modi haben stärkere Effekte
            intensity_factor = min(abs(mode_state.index_value) / 2.0, 1.5)
            effective_magnitude = effect.magnitude * intensity_factor
            
            active_effects.append({
                "climate_mode": effect.climate_mode.value,
                "phase": effect.phase,
                "mode_strength": mode_state.strength,
                "hazard": effect.hazard.value,
                "effect": effect.effect_direction,
                "magnitude": round(effective_magnitude, 2),
                "delay_months": effect.delay_months,
                "confidence": effect.confidence,
                "mechanism": effect.mechanism
            })
        
        return sorted(active_effects, key=lambda x: x["magnitude"], reverse=True)


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 3: LOKALE VULNERABILITÄT
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class LocalVulnerability:
    """Lokale Faktoren, die Hazard-Exposition verstärken oder abschwächen."""
    
    # Geographische Lage
    latitude: float
    longitude: float
    region: Region
    
    # Topographie
    elevation_m: float
    coastal_distance_km: float
    river_distance_km: float
    slope_degrees: float
    
    # Landnutzung
    urban_density: float  # 0-1
    forest_coverage: float  # 0-1
    agricultural_land: float  # 0-1
    
    # Infrastruktur-Schutz
    flood_protection_level: float  # 0-1 (Dämme, Deiche)
    fire_suppression_capacity: float  # 0-1
    early_warning_coverage: float  # 0-1
    
    def get_hazard_multipliers(self) -> Dict[HazardType, float]:
        """
        Berechne Multiplikatoren für jede Hazard-Art basierend auf lokalen Faktoren.
        
        Ein Multiplikator > 1 bedeutet erhöhte Vulnerabilität.
        Ein Multiplikator < 1 bedeutet reduzierte Vulnerabilität.
        """
        multipliers = {}
        
        # FLOOD - Überschwemmung
        flood_mult = 1.0
        if self.elevation_m < 10:
            flood_mult *= 1.5
        if self.coastal_distance_km < 5:
            flood_mult *= 1.4
        if self.river_distance_km < 2:
            flood_mult *= 1.3
        if self.urban_density > 0.5:  # Versiegelung
            flood_mult *= 1.2
        flood_mult *= (1 - self.flood_protection_level * 0.5)  # Schutz reduziert
        multipliers[HazardType.FLOOD] = flood_mult
        
        # COASTAL_FLOOD - Küstenflut
        coastal_mult = 1.0
        if self.coastal_distance_km < 1:
            coastal_mult *= 2.0
        elif self.coastal_distance_km < 5:
            coastal_mult *= 1.5
        elif self.coastal_distance_km < 20:
            coastal_mult *= 1.1
        else:
            coastal_mult *= 0.1  # Weit vom Meer = fast kein Risiko
        if self.elevation_m < 5:
            coastal_mult *= 1.5
        multipliers[HazardType.COASTAL_FLOOD] = coastal_mult
        
        # DROUGHT - Dürre
        drought_mult = 1.0
        if self.agricultural_land > 0.3:
            drought_mult *= 1.3  # Landwirtschaft anfälliger
        if 20 < abs(self.latitude) < 40:
            drought_mult *= 1.2  # Subtropische Zonen
        multipliers[HazardType.DROUGHT] = drought_mult
        
        # WILDFIRE - Waldbrand
        fire_mult = 1.0
        if self.forest_coverage > 0.3:
            fire_mult *= 1.5
        if 30 < abs(self.latitude) < 50:
            fire_mult *= 1.2  # Mediterrane Klimazonen
        fire_mult *= (1 - self.fire_suppression_capacity * 0.4)
        multipliers[HazardType.WILDFIRE] = fire_mult
        
        # TROPICAL_CYCLONE - Tropische Wirbelstürme
        cyclone_mult = 1.0
        if abs(self.latitude) < 30 and self.coastal_distance_km < 100:
            cyclone_mult *= 1.5
        if abs(self.latitude) > 35:
            cyclone_mult *= 0.1  # Außerhalb der Tropen
        multipliers[HazardType.TROPICAL_CYCLONE] = cyclone_mult
        
        # HEAT_WAVE - Hitzewelle
        heat_mult = 1.0
        if self.urban_density > 0.5:
            heat_mult *= 1.4  # Urban Heat Island
        if abs(self.latitude) < 35:
            heat_mult *= 1.2
        multipliers[HazardType.HEAT_WAVE] = heat_mult
        
        # COLD_WAVE - Kältewelle
        cold_mult = 1.0
        if abs(self.latitude) > 45:
            cold_mult *= 1.3
        if self.elevation_m > 1000:
            cold_mult *= 1.2
        multipliers[HazardType.COLD_WAVE] = cold_mult
        
        # LANDSLIDE - Erdrutsch
        slide_mult = 1.0
        if self.slope_degrees > 15:
            slide_mult *= 2.0
        elif self.slope_degrees > 5:
            slide_mult *= 1.3
        else:
            slide_mult *= 0.3
        multipliers[HazardType.LANDSLIDE] = slide_mult
        
        return multipliers


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION: Global → Lokal Pipeline
# ═══════════════════════════════════════════════════════════════════════════════

class GlobalLocalRiskEngine:
    """
    Die Haupt-Engine, die alles zusammenführt:
    
    1. Aktuelle globale Klima-Modi abfragen
    2. Telekonnektion auf Region anwenden
    3. Mit lokaler Vulnerabilität multiplizieren
    4. Finale Risiko-Scores berechnen
    """
    
    def __init__(self):
        self.teleconnection = TeleconnectionMatrix()
        self.climate_modes: Dict[ClimateMode, ClimateModeState] = {}
    
    def update_climate_mode(self, mode: ClimateMode, index_value: float, trend: float = 0):
        """Aktualisiere einen Klima-Modus mit neuen Daten."""
        self.climate_modes[mode] = ClimateModeState.from_index(mode, index_value, trend)
    
    def get_region_for_location(self, lat: float, lon: float) -> Region:
        """Bestimme die Region für einen Koordinatenpunkt."""
        # Vereinfachte Zuordnung - in Produktion würde man Shapefiles nutzen
        if lat > 24 and lat < 50 and lon > -125 and lon < -65:
            if lon < -100:
                return Region.NORTH_AMERICA_WEST
            else:
                return Region.NORTH_AMERICA_EAST
        elif lat > 5 and lat < 24 and lon > -120 and lon < -60:
            return Region.CENTRAL_AMERICA
        elif lat > -60 and lat < 5 and lon > -80 and lon < -30:
            if lat > -20:
                return Region.SOUTH_AMERICA_NORTH
            else:
                return Region.SOUTH_AMERICA_SOUTH
        elif lat > 45 and lon > -25 and lon < 40:
            return Region.EUROPE_NORTH
        elif lat > 35 and lat < 45 and lon > -10 and lon < 40:
            return Region.EUROPE_SOUTH
        elif lat > 15 and lat < 35 and lon > -20 and lon < 60:
            if lon < 30:
                return Region.AFRICA_NORTH
            else:
                return Region.MIDDLE_EAST
        elif lat > -35 and lat < 15 and lon > 10 and lon < 55:
            if lon > 30:
                return Region.AFRICA_EAST
            else:
                return Region.AFRICA_SOUTH
        elif lat > 5 and lat < 35 and lon > 60 and lon < 100:
            return Region.SOUTH_ASIA
        elif lat > 20 and lat < 55 and lon > 100 and lon < 150:
            return Region.EAST_ASIA
        elif lat > -10 and lat < 20 and lon > 95 and lon < 140:
            return Region.SOUTHEAST_ASIA
        elif lat > -45 and lat < -10 and lon > 110 and lon < 180:
            return Region.AUSTRALIA
        else:
            return Region.PACIFIC_ISLANDS
    
    def calculate_risk(self, lat: float, lon: float, 
                       vulnerability: LocalVulnerability) -> Dict:
        """
        Berechne das vollständige Risikoprofil für einen Punkt.
        
        Kombiniert:
        - Globale Klima-Modi → Telekonnektion
        - Regionale Effekte
        - Lokale Vulnerabilität
        """
        region = self.get_region_for_location(lat, lon)
        
        # Hole alle aktiven Telekonnektion-Effekte
        teleconnection_effects = self.teleconnection.get_effects_for_region(
            region, self.climate_modes
        )
        
        # Hole lokale Multiplikatoren
        local_multipliers = vulnerability.get_hazard_multipliers()
        
        # Berechne finale Risiken pro Hazard-Typ
        risk_scores = {}
        for hazard in HazardType:
            base_risk = 0.1  # Basis-Risiko
            
            # Addiere Telekonnektion-Effekte
            for effect in teleconnection_effects:
                if effect["hazard"] == hazard.value:
                    if effect["effect"] == "increase":
                        base_risk += effect["magnitude"] * effect["confidence"]
                    else:
                        base_risk -= effect["magnitude"] * effect["confidence"] * 0.5
            
            # Multipliziere mit lokaler Vulnerabilität
            local_mult = local_multipliers.get(hazard, 1.0)
            final_risk = min(base_risk * local_mult, 1.0)
            
            risk_scores[hazard.value] = round(final_risk, 3)
        
        # Gesamt-Risiko
        total_risk = sum(risk_scores.values()) / len(risk_scores)
        
        return {
            "location": {"lat": lat, "lon": lon},
            "region": region.value,
            "active_climate_modes": [
                {
                    "mode": m.mode.value,
                    "index": m.index_value,
                    "phase": m.phase,
                    "strength": m.strength
                }
                for m in self.climate_modes.values()
                if m.phase != "neutral"
            ],
            "teleconnection_effects": teleconnection_effects,
            "local_multipliers": {k.value: v for k, v in local_multipliers.items()},
            "hazard_risks": risk_scores,
            "total_risk": round(total_risk, 3),
            "top_hazards": sorted(
                [(k, v) for k, v in risk_scores.items()],
                key=lambda x: x[1], reverse=True
            )[:3]
        }


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 80)
    print("TERA Global-Local Framework Demo")
    print("=" * 80)
    
    # Initialisiere Engine
    engine = GlobalLocalRiskEngine()
    
    # Setze aktuelle Klima-Modi (Beispiel: El Niño Situation)
    print("\n📡 Aktuelle Klima-Modi:")
    engine.update_climate_mode(ClimateMode.ENSO, +1.8, trend=0.2)  # Starker El Niño
    engine.update_climate_mode(ClimateMode.AMO, +0.4, trend=0)     # Positiv
    engine.update_climate_mode(ClimateMode.NAO, -0.3, trend=-0.1)  # Leicht negativ
    engine.update_climate_mode(ClimateMode.IOD, +0.8, trend=0.1)   # Positiv
    
    for mode in [ClimateMode.ENSO, ClimateMode.AMO, ClimateMode.NAO, ClimateMode.IOD]:
        state = engine.climate_modes[mode]
        print(f"  {mode.value:6s}: {state.index_value:+.1f} ({state.phase}, {state.strength})")
    
    # Beispiel 1: Miami
    print("\n" + "─" * 80)
    print("📍 MIAMI, Florida")
    print("─" * 80)
    
    miami_vuln = LocalVulnerability(
        latitude=25.76,
        longitude=-80.19,
        region=Region.NORTH_AMERICA_EAST,
        elevation_m=2,
        coastal_distance_km=0.5,
        river_distance_km=5,
        slope_degrees=0.5,
        urban_density=0.85,
        forest_coverage=0.05,
        agricultural_land=0.02,
        flood_protection_level=0.4,
        fire_suppression_capacity=0.9,
        early_warning_coverage=0.95
    )
    
    miami_risk = engine.calculate_risk(25.76, -80.19, miami_vuln)
    
    print(f"\n🌍 Region: {miami_risk['region']}")
    print(f"\n📊 Aktive Telekonnektion-Effekte:")
    for effect in miami_risk["teleconnection_effects"][:3]:
        print(f"  • {effect['climate_mode']} ({effect['phase']}) → {effect['hazard']}: "
              f"{effect['effect']} {effect['magnitude']:.0%}")
        print(f"    Mechanismus: {effect['mechanism'][:60]}...")
    
    print(f"\n🎯 Top 3 Hazards:")
    for hazard, risk in miami_risk["top_hazards"]:
        print(f"  • {hazard:20s}: {risk:.1%}")
    
    print(f"\n⚠️ GESAMT-RISIKO: {miami_risk['total_risk']:.1%}")
    
    # Beispiel 2: Sydney
    print("\n" + "─" * 80)
    print("📍 SYDNEY, Australien")
    print("─" * 80)
    
    sydney_vuln = LocalVulnerability(
        latitude=-33.87,
        longitude=151.21,
        region=Region.AUSTRALIA,
        elevation_m=58,
        coastal_distance_km=2,
        river_distance_km=8,
        slope_degrees=3,
        urban_density=0.75,
        forest_coverage=0.15,
        agricultural_land=0.05,
        flood_protection_level=0.5,
        fire_suppression_capacity=0.8,
        early_warning_coverage=0.90
    )
    
    sydney_risk = engine.calculate_risk(-33.87, 151.21, sydney_vuln)
    
    print(f"\n🌍 Region: {sydney_risk['region']}")
    print(f"\n📊 Aktive Telekonnektion-Effekte:")
    for effect in sydney_risk["teleconnection_effects"][:3]:
        print(f"  • {effect['climate_mode']} ({effect['phase']}) → {effect['hazard']}: "
              f"{effect['effect']} {effect['magnitude']:.0%}")
    
    print(f"\n🎯 Top 3 Hazards:")
    for hazard, risk in sydney_risk["top_hazards"]:
        print(f"  • {hazard:20s}: {risk:.1%}")
    
    print(f"\n⚠️ GESAMT-RISIKO: {sydney_risk['total_risk']:.1%}")
    
    # Beispiel 3: Lima (El Niño Hotspot)
    print("\n" + "─" * 80)
    print("📍 LIMA, Peru (El Niño Hotspot)")
    print("─" * 80)
    
    lima_vuln = LocalVulnerability(
        latitude=-12.05,
        longitude=-77.04,
        region=Region.SOUTH_AMERICA_NORTH,
        elevation_m=154,
        coastal_distance_km=10,
        river_distance_km=5,
        slope_degrees=5,
        urban_density=0.80,
        forest_coverage=0.02,
        agricultural_land=0.10,
        flood_protection_level=0.25,
        fire_suppression_capacity=0.5,
        early_warning_coverage=0.60
    )
    
    lima_risk = engine.calculate_risk(-12.05, -77.04, lima_vuln)
    
    print(f"\n🌍 Region: {lima_risk['region']}")
    print(f"\n📊 Aktive Telekonnektion-Effekte:")
    for effect in lima_risk["teleconnection_effects"]:
        print(f"  • {effect['climate_mode']} ({effect['phase']}) → {effect['hazard']}: "
              f"{effect['effect']} {effect['magnitude']:.0%}")
        print(f"    Mechanismus: {effect['mechanism']}")
    
    print(f"\n🎯 Top 3 Hazards:")
    for hazard, risk in lima_risk["top_hazards"]:
        print(f"  • {hazard:20s}: {risk:.1%}")
    
    print(f"\n⚠️ GESAMT-RISIKO: {lima_risk['total_risk']:.1%}")
    
    print("\n" + "=" * 80)
    print("Framework bereit für Integration in TERA Backend!")
    print("=" * 80)












