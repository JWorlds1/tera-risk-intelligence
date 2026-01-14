"""
TERA Physical Earth Cycle Model
Physikalisch basiertes Modell für Erdzyklen

Basiert auf:
- IPCC AR6 Parametrisierungen
- ERA5 Reanalyse-Formeln
- Land Surface Models (CLM, JULES)

Zyklen:
1. Energie-Budget: SW + LW → Net Radiation → Sensible + Latent Heat
2. Wasser-Zyklus: P - ET - R = ΔS (Bodenfeuchte-Änderung)
3. Carbon-Zyklus: GPP - Ra - Rh = NEE (Net Ecosystem Exchange)
"""
import math
import h3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum


# =====================================================
# PHYSIKALISCHE KONSTANTEN
# =====================================================

class PhysicalConstants:
    """Physikalische Konstanten für Erdmodellierung"""
    
    # Stefan-Boltzmann Konstante (W/m²/K⁴)
    STEFAN_BOLTZMANN = 5.67e-8
    
    # Solarkonstante (W/m²)
    SOLAR_CONSTANT = 1361
    
    # Latente Wärme der Verdunstung (J/kg)
    LATENT_HEAT_VAPORIZATION = 2.45e6
    
    # Spezifische Wärme Luft (J/kg/K)
    SPECIFIC_HEAT_AIR = 1005
    
    # Dichte Luft (kg/m³)
    AIR_DENSITY = 1.225
    
    # Wasserdichte (kg/m³)
    WATER_DENSITY = 1000
    
    # CO2 Hintergrund (ppm)
    CO2_PREINDUSTRIAL = 280
    CO2_CURRENT = 420


# =====================================================
# KLIMAZONEN (Köppen-Geiger)
# =====================================================

class ClimateZone(Enum):
    """Köppen-Geiger Klimazonen"""
    Af = "Tropical Rainforest"
    Am = "Tropical Monsoon"
    Aw = "Tropical Savanna"
    BWh = "Hot Desert"
    BWk = "Cold Desert"
    BSh = "Hot Steppe"
    BSk = "Cold Steppe"
    Csa = "Mediterranean Hot Summer"
    Csb = "Mediterranean Warm Summer"
    Cfa = "Humid Subtropical"
    Cfb = "Oceanic"
    Cfc = "Subpolar Oceanic"
    Dfa = "Hot Summer Continental"
    Dfb = "Warm Summer Continental"
    Dfc = "Subarctic"
    ET = "Tundra"
    EF = "Ice Cap"


# =====================================================
# DATENSTRUKTUREN
# =====================================================

@dataclass
class EnergyBudget:
    """Energie-Budget einer Zelle (W/m²)"""
    # Kurzwellige Strahlung
    sw_incoming: float = 0.0      # Einstrahlung (TOA)
    sw_reflected: float = 0.0     # Reflektiert (Albedo)
    sw_absorbed: float = 0.0      # Absorbiert
    
    # Langwellige Strahlung
    lw_incoming: float = 0.0      # Atmosphärische Gegenstrahlung
    lw_outgoing: float = 0.0      # Ausstrahlung
    
    # Netto-Strahlung
    net_radiation: float = 0.0    # Rn = SW_net + LW_net
    
    # Wärmeflüsse
    sensible_heat: float = 0.0    # H (fühlbar)
    latent_heat: float = 0.0      # LE (Verdunstung)
    ground_heat: float = 0.0      # G (Boden)
    
    # Bowen Ratio
    bowen_ratio: float = 0.0      # H / LE


@dataclass
class WaterCycle:
    """Wasser-Zyklus einer Zelle (mm/Tag)"""
    # Flüsse
    precipitation: float = 0.0     # P
    evaporation: float = 0.0       # E (Oberfläche)
    transpiration: float = 0.0     # T (Pflanzen)
    evapotranspiration: float = 0.0  # ET = E + T
    runoff: float = 0.0            # R (Abfluss)
    infiltration: float = 0.0      # Infiltration
    
    # Speicher (mm)
    soil_moisture: float = 0.0     # Bodenfeuchte
    snow_water: float = 0.0        # Schnee
    groundwater: float = 0.0       # Grundwasser
    
    # Indices
    spi: float = 0.0               # Standardized Precipitation Index
    water_balance: float = 0.0     # P - ET - R


@dataclass
class CarbonCycle:
    """Carbon-Zyklus einer Zelle (gC/m²/Tag)"""
    # Flüsse
    gpp: float = 0.0               # Gross Primary Production
    npp: float = 0.0               # Net Primary Production
    autotrophic_resp: float = 0.0  # Ra (Pflanzen-Respiration)
    heterotrophic_resp: float = 0.0  # Rh (Boden-Respiration)
    nee: float = 0.0               # Net Ecosystem Exchange
    
    # Vegetation
    ndvi: float = 0.0              # Vegetation Index
    lai: float = 0.0               # Leaf Area Index
    fpar: float = 0.0              # Fraction of PAR absorbed
    
    # Feuer
    fire_emissions: float = 0.0    # Feuer-Emissionen


@dataclass
class CellState:
    """Vollständiger Zustand einer H3-Zelle"""
    h3_index: str
    resolution: int
    lat: float
    lon: float
    timestamp: datetime
    
    # Geografie
    elevation_m: float = 0.0
    slope_deg: float = 0.0
    aspect_deg: float = 0.0
    is_coastal: bool = False
    is_land: bool = True
    climate_zone: Optional[ClimateZone] = None
    
    # Oberfläche
    albedo: float = 0.2
    emissivity: float = 0.95
    roughness_length: float = 0.1
    land_cover: str = "grassland"
    
    # Atmosphäre
    temperature_c: float = 15.0
    humidity_pct: float = 60.0
    pressure_hpa: float = 1013.0
    wind_speed_ms: float = 3.0
    cloud_cover_pct: float = 50.0
    
    # Zyklen
    energy: EnergyBudget = field(default_factory=EnergyBudget)
    water: WaterCycle = field(default_factory=WaterCycle)
    carbon: CarbonCycle = field(default_factory=CarbonCycle)
    
    # Anomalien
    temp_anomaly_c: float = 0.0
    precip_anomaly_pct: float = 0.0
    
    # Risiko
    risk_score: float = 0.0
    risk_drivers: List[str] = field(default_factory=list)


# =====================================================
# PHYSIKALISCHES MODELL
# =====================================================

class PhysicalEarthModel:
    """
    Physikalisch basiertes Erdmodell
    
    Berechnet Erdzyklen basierend auf:
    - Position (lat, lon)
    - Zeit (Jahreszeit, Tageszeit)
    - Oberflächeneigenschaften
    """
    
    def __init__(self):
        self.constants = PhysicalConstants()
    
    # =========================================
    # SOLAR GEOMETRY
    # =========================================
    
    def solar_declination(self, day_of_year: int) -> float:
        """Sonnendeklination in Radiant"""
        return 0.409 * math.sin(2 * math.pi * day_of_year / 365 - 1.39)
    
    def hour_angle(self, hour: float, lon: float) -> float:
        """Stundenwinkel in Radiant"""
        solar_noon = 12 - lon / 15
        return math.pi * (hour - solar_noon) / 12
    
    def solar_zenith_angle(
        self, 
        lat: float, 
        lon: float, 
        timestamp: datetime
    ) -> float:
        """Sonnenzenitwinkel in Radiant"""
        lat_rad = math.radians(lat)
        doy = timestamp.timetuple().tm_yday
        hour = timestamp.hour + timestamp.minute / 60
        
        decl = self.solar_declination(doy)
        ha = self.hour_angle(hour, lon)
        
        cos_zen = (math.sin(lat_rad) * math.sin(decl) + 
                   math.cos(lat_rad) * math.cos(decl) * math.cos(ha))
        
        return math.acos(max(-1, min(1, cos_zen)))
    
    def extraterrestrial_radiation(
        self, 
        lat: float, 
        day_of_year: int
    ) -> float:
        """Extraterrestrische Strahlung (W/m²/Tag)"""
        lat_rad = math.radians(lat)
        decl = self.solar_declination(day_of_year)
        
        # Erde-Sonne Distanz Korrektur
        dr = 1 + 0.033 * math.cos(2 * math.pi * day_of_year / 365)
        
        # Sunset hour angle
        ws = math.acos(-math.tan(lat_rad) * math.tan(decl))
        ws = max(0, min(math.pi, ws))
        
        # Ra (MJ/m²/Tag → W/m²)
        Ra = (24 * 60 / math.pi) * 0.0820 * dr * (
            ws * math.sin(lat_rad) * math.sin(decl) +
            math.cos(lat_rad) * math.cos(decl) * math.sin(ws)
        )
        
        return Ra * 11.57  # MJ/m²/Tag → W/m² (Tagesmittel)
    
    # =========================================
    # ENERGIE-BUDGET
    # =========================================
    
    def calculate_energy_budget(
        self,
        lat: float,
        lon: float,
        timestamp: datetime,
        albedo: float = 0.2,
        temperature_c: float = 15.0,
        cloud_cover_pct: float = 50.0,
        emissivity: float = 0.95
    ) -> EnergyBudget:
        """Berechnet vollständiges Energie-Budget"""
        
        doy = timestamp.timetuple().tm_yday
        
        # Kurzwellige Strahlung
        Ra = self.extraterrestrial_radiation(lat, doy)
        
        # Atmosphärische Transmission (vereinfacht)
        cloud_factor = 1 - 0.75 * (cloud_cover_pct / 100) ** 3.4
        atmospheric_transmission = 0.75 * cloud_factor
        
        sw_incoming = Ra * atmospheric_transmission
        sw_reflected = sw_incoming * albedo
        sw_absorbed = sw_incoming - sw_reflected
        
        # Langwellige Strahlung (Stefan-Boltzmann)
        T_surface_k = temperature_c + 273.15
        T_air_k = T_surface_k - 2  # Vereinfachung
        
        lw_outgoing = emissivity * self.constants.STEFAN_BOLTZMANN * T_surface_k**4
        
        # Atmosphärische Gegenstrahlung (Brutsaert-Formel vereinfacht)
        e_a = 0.7 + 0.17 * (cloud_cover_pct / 100)  # Effektive Emissivität
        lw_incoming = e_a * self.constants.STEFAN_BOLTZMANN * T_air_k**4
        
        # Netto-Strahlung
        net_radiation = sw_absorbed + lw_incoming - lw_outgoing
        
        # Wärmeflüsse (vereinfachte Partitionierung)
        if net_radiation > 0:
            # Tagsüber: Bowen Ratio basiert
            bowen_ratio = 0.5  # Typisch für gemäßigtes Klima
            latent_heat = net_radiation / (1 + bowen_ratio) * 0.8
            sensible_heat = latent_heat * bowen_ratio
            ground_heat = net_radiation * 0.1
        else:
            # Nachts: Hauptsächlich Ausstrahlung
            latent_heat = 0
            sensible_heat = net_radiation * 0.4
            ground_heat = net_radiation * 0.3
            bowen_ratio = 0
        
        return EnergyBudget(
            sw_incoming=round(sw_incoming, 1),
            sw_reflected=round(sw_reflected, 1),
            sw_absorbed=round(sw_absorbed, 1),
            lw_incoming=round(lw_incoming, 1),
            lw_outgoing=round(lw_outgoing, 1),
            net_radiation=round(net_radiation, 1),
            sensible_heat=round(sensible_heat, 1),
            latent_heat=round(latent_heat, 1),
            ground_heat=round(ground_heat, 1),
            bowen_ratio=round(bowen_ratio, 2)
        )
    
    # =========================================
    # WASSER-ZYKLUS
    # =========================================
    
    def calculate_potential_et(
        self,
        temperature_c: float,
        net_radiation: float,
        wind_speed_ms: float,
        humidity_pct: float
    ) -> float:
        """
        Potenzielle Evapotranspiration (mm/Tag)
        Penman-Monteith Referenz-ET (FAO-56)
        """
        T = temperature_c
        Rn = net_radiation  # W/m²
        u2 = wind_speed_ms
        RH = humidity_pct
        
        # Sättigungsdampfdruck (kPa)
        es = 0.6108 * math.exp(17.27 * T / (T + 237.3))
        
        # Aktueller Dampfdruck
        ea = es * RH / 100
        
        # Dampfdruckdefizit
        vpd = es - ea
        
        # Steigung der Sättigungsdampfdruckkurve
        delta = 4098 * es / (T + 237.3)**2
        
        # Psychrometerkonstante (kPa/°C)
        gamma = 0.067
        
        # Rn in MJ/m²/Tag umrechnen
        Rn_mj = Rn * 0.0864
        
        # Penman-Monteith (Gras-Referenz)
        numerator = 0.408 * delta * Rn_mj + gamma * (900 / (T + 273)) * u2 * vpd
        denominator = delta + gamma * (1 + 0.34 * u2)
        
        ET0 = numerator / denominator
        
        return max(0, ET0)
    
    def calculate_water_cycle(
        self,
        temperature_c: float,
        net_radiation: float,
        wind_speed_ms: float,
        humidity_pct: float,
        precipitation_mm: float,
        soil_moisture_pct: float,
        ndvi: float
    ) -> WaterCycle:
        """Berechnet Wasser-Zyklus"""
        
        # Potenzielle ET
        ET0 = self.calculate_potential_et(
            temperature_c, net_radiation, wind_speed_ms, humidity_pct
        )
        
        # Aktuelle ET (begrenzt durch Bodenfeuchte und Vegetation)
        soil_factor = min(1.0, soil_moisture_pct / 50)  # Austrocknung
        veg_factor = 0.3 + 0.7 * ndvi  # Vegetationsdecke
        
        ET = ET0 * soil_factor * veg_factor
        
        # Aufteilung E und T
        transpiration = ET * ndvi * 0.8
        evaporation = ET - transpiration
        
        # Wasserbilanz
        # P - ET - R = ΔS
        if precipitation_mm > ET:
            # Überschuss → Abfluss/Infiltration
            excess = precipitation_mm - ET
            runoff = excess * 0.3  # 30% Abfluss
            infiltration = excess * 0.7
        else:
            runoff = 0
            infiltration = 0
        
        water_balance = precipitation_mm - ET - runoff
        
        # Neue Bodenfeuchte (vereinfacht)
        new_soil_moisture = soil_moisture_pct + water_balance * 0.5
        new_soil_moisture = max(5, min(100, new_soil_moisture))
        
        return WaterCycle(
            precipitation=round(precipitation_mm, 2),
            evaporation=round(evaporation, 2),
            transpiration=round(transpiration, 2),
            evapotranspiration=round(ET, 2),
            runoff=round(runoff, 2),
            infiltration=round(infiltration, 2),
            soil_moisture=round(new_soil_moisture, 1),
            water_balance=round(water_balance, 2)
        )
    
    # =========================================
    # CARBON-ZYKLUS
    # =========================================
    
    def calculate_carbon_cycle(
        self,
        temperature_c: float,
        soil_moisture_pct: float,
        sw_absorbed: float,
        ndvi: float,
        lai: float = None
    ) -> CarbonCycle:
        """
        Berechnet Carbon-Zyklus
        Basiert auf Light Use Efficiency Modell
        """
        
        # LAI aus NDVI schätzen wenn nicht gegeben
        if lai is None:
            lai = max(0, (ndvi - 0.1) / 0.05)  # Vereinfachte Beziehung
            lai = min(8, lai)
        
        # FPAR (Fraction of PAR absorbed)
        fpar = 1 - math.exp(-0.5 * lai)
        
        # PAR (Photosynthetically Active Radiation) ≈ 50% der SW
        par = sw_absorbed * 0.5
        apar = par * fpar
        
        # Light Use Efficiency (gC/MJ)
        # Basiswert, reduziert durch Stress
        lue_max = 1.5  # gC/MJ für C3 Pflanzen
        
        # Temperatur-Stress
        T_opt = 25
        temp_stress = max(0, 1 - ((temperature_c - T_opt) / 20)**2)
        
        # Wasser-Stress
        water_stress = min(1, soil_moisture_pct / 40)
        
        lue = lue_max * temp_stress * water_stress
        
        # GPP (Gross Primary Production)
        # apar in MJ/m²/Tag, GPP in gC/m²/Tag
        apar_mj = apar * 0.0864  # W/m² → MJ/m²/Tag
        gpp = apar_mj * lue
        
        # Autotrophe Respiration (Ra) ≈ 50% GPP
        ra = gpp * 0.5
        
        # NPP = GPP - Ra
        npp = gpp - ra
        
        # Heterotrophe Respiration (Rh)
        # Boden-Respiration, temperaturabhängig (Q10)
        rh_base = 2.0  # gC/m²/Tag bei 20°C
        q10 = 2.0
        rh = rh_base * q10 ** ((temperature_c - 20) / 10)
        rh = rh * (soil_moisture_pct / 50)  # Feuchte-Modulation
        
        # NEE = Ra + Rh - GPP (negativ = Senke)
        nee = ra + rh - gpp
        
        return CarbonCycle(
            gpp=round(gpp, 2),
            npp=round(npp, 2),
            autotrophic_resp=round(ra, 2),
            heterotrophic_resp=round(rh, 2),
            nee=round(nee, 2),
            ndvi=round(ndvi, 3),
            lai=round(lai, 2),
            fpar=round(fpar, 3)
        )
    
    # =========================================
    # VOLLSTÄNDIGE ZELL-BERECHNUNG
    # =========================================
    
    def calculate_cell_state(
        self,
        h3_index: str,
        timestamp: datetime = None,
        temperature_c: float = None,
        humidity_pct: float = 60,
        precipitation_mm: float = 0,
        cloud_cover_pct: float = 50,
        wind_speed_ms: float = 3,
        soil_moisture_pct: float = 50,
        ndvi: float = 0.5,
        albedo: float = 0.2
    ) -> CellState:
        """
        Berechnet vollständigen Zustand einer H3-Zelle
        """
        timestamp = timestamp or datetime.utcnow()
        lat, lon = h3.cell_to_latlng(h3_index)
        resolution = h3.get_resolution(h3_index)
        
        # Temperatur schätzen wenn nicht gegeben
        if temperature_c is None:
            # Klimatologie-basiert
            month = timestamp.month
            base_temp = 15 - abs(lat) * 0.5
            seasonal = 10 * math.cos((month - 7) * math.pi / 6) * (1 if lat > 0 else -1)
            temperature_c = base_temp + seasonal * 0.6
        
        # 1. Energie-Budget
        energy = self.calculate_energy_budget(
            lat, lon, timestamp,
            albedo=albedo,
            temperature_c=temperature_c,
            cloud_cover_pct=cloud_cover_pct
        )
        
        # 2. Wasser-Zyklus
        water = self.calculate_water_cycle(
            temperature_c=temperature_c,
            net_radiation=energy.net_radiation,
            wind_speed_ms=wind_speed_ms,
            humidity_pct=humidity_pct,
            precipitation_mm=precipitation_mm,
            soil_moisture_pct=soil_moisture_pct,
            ndvi=ndvi
        )
        
        # 3. Carbon-Zyklus
        carbon = self.calculate_carbon_cycle(
            temperature_c=temperature_c,
            soil_moisture_pct=water.soil_moisture,
            sw_absorbed=energy.sw_absorbed,
            ndvi=ndvi
        )
        
        # Risiko-Berechnung
        risk_score, risk_drivers = self._calculate_risk(
            temperature_c, water, carbon, precipitation_mm
        )
        
        return CellState(
            h3_index=h3_index,
            resolution=resolution,
            lat=lat,
            lon=lon,
            timestamp=timestamp,
            temperature_c=round(temperature_c, 1),
            humidity_pct=humidity_pct,
            pressure_hpa=1013,
            wind_speed_ms=wind_speed_ms,
            cloud_cover_pct=cloud_cover_pct,
            albedo=albedo,
            energy=energy,
            water=water,
            carbon=carbon,
            risk_score=risk_score,
            risk_drivers=risk_drivers
        )
    
    def _calculate_risk(
        self,
        temperature_c: float,
        water: WaterCycle,
        carbon: CarbonCycle,
        precipitation_mm: float
    ) -> Tuple[float, List[str]]:
        """Berechnet Risiko-Score und Treiber"""
        
        risk = 0.0
        drivers = []
        
        # Dürre-Risiko
        if water.soil_moisture < 20:
            risk += 0.3
            drivers.append("low_soil_moisture")
        
        # Hitze-Risiko
        if temperature_c > 35:
            risk += 0.25
            drivers.append("extreme_heat")
        elif temperature_c > 30:
            risk += 0.1
        
        # Überschwemmungs-Risiko
        if precipitation_mm > 50:
            risk += 0.3
            drivers.append("heavy_precipitation")
        
        # Vegetations-Stress
        if carbon.ndvi < 0.2:
            risk += 0.15
            drivers.append("vegetation_stress")
        
        # Wasser-Defizit
        if water.water_balance < -5:
            risk += 0.2
            drivers.append("water_deficit")
        
        return min(1.0, risk), drivers


# =====================================================
# ADAPTIVE TESSELLATION
# =====================================================

class AdaptiveTessellation:
    """
    Adaptive H3 Tessellation
    
    Passt Auflösung basierend auf:
    - Zoom-Level
    - Risiko-Intensität
    - Datenverfügbarkeit
    """
    
    # Zoom → H3 Resolution Mapping
    ZOOM_TO_RESOLUTION = {
        0: 0, 1: 0, 2: 1, 3: 1, 4: 2, 5: 2,
        6: 3, 7: 3, 8: 4, 9: 4, 10: 5, 11: 5,
        12: 6, 13: 6, 14: 7, 15: 7, 16: 8,
        17: 8, 18: 9, 19: 9, 20: 10
    }
    
    @classmethod
    def get_resolution_for_zoom(cls, zoom: int) -> int:
        """Bestimmt H3-Auflösung für Zoom-Level"""
        return cls.ZOOM_TO_RESOLUTION.get(min(20, max(0, zoom)), 5)
    
    @classmethod
    def get_cells_for_bbox(
        cls,
        min_lat: float,
        min_lon: float,
        max_lat: float,
        max_lon: float,
        zoom: int
    ) -> List[str]:
        """Gibt H3-Zellen für Bounding Box zurück"""
        
        resolution = cls.get_resolution_for_zoom(zoom)
        
        # Polygon für H3
        polygon = [
            (min_lat, min_lon),
            (min_lat, max_lon),
            (max_lat, max_lon),
            (max_lat, min_lon),
            (min_lat, min_lon)
        ]
        
        # H3 Polygon to Cells
        try:
            cells = h3.polygon_to_cells(
                h3.LatLngPoly(polygon),
                resolution
            )
            return list(cells)
        except:
            # Fallback: Grid-Sampling
            cells = set()
            lat_step = (max_lat - min_lat) / 10
            lon_step = (max_lon - min_lon) / 10
            
            for lat in range(int((max_lat - min_lat) / lat_step) + 1):
                for lon in range(int((max_lon - min_lon) / lon_step) + 1):
                    cell = h3.latlng_to_cell(
                        min_lat + lat * lat_step,
                        min_lon + lon * lon_step,
                        resolution
                    )
                    cells.add(cell)
            
            return list(cells)
    
    @classmethod
    def adaptive_refinement(
        cls,
        cells: List[str],
        risk_scores: Dict[str, float],
        threshold: float = 0.5
    ) -> List[str]:
        """
        Verfeinert Zellen mit hohem Risiko
        
        Zellen mit risk > threshold werden auf höhere Resolution gebracht
        """
        refined = []
        
        for cell in cells:
            risk = risk_scores.get(cell, 0)
            
            if risk > threshold:
                # Verfeinern (eine Stufe höher)
                children = h3.cell_to_children(cell)
                refined.extend(children)
            else:
                refined.append(cell)
        
        return refined


# =====================================================
# FRONTEND DATA FORMATTER
# =====================================================

class FrontendFormatter:
    """Formatiert Daten für Frontend-Visualisierung"""
    
    @staticmethod
    def cell_to_geojson(state: CellState) -> Dict[str, Any]:
        """Konvertiert CellState zu GeoJSON Feature"""
        
        boundary = h3.cell_to_boundary(state.h3_index)
        coordinates = [[p[1], p[0]] for p in boundary]
        coordinates.append(coordinates[0])  # Schließen
        
        return {
            "type": "Feature",
            "id": state.h3_index,
            "geometry": {
                "type": "Polygon",
                "coordinates": [coordinates]
            },
            "properties": {
                "h3_index": state.h3_index,
                "resolution": state.resolution,
                "lat": state.lat,
                "lon": state.lon,
                
                # Atmosphäre
                "temperature_c": state.temperature_c,
                "humidity_pct": state.humidity_pct,
                "cloud_cover_pct": state.cloud_cover_pct,
                
                # Energie
                "net_radiation": state.energy.net_radiation,
                "latent_heat": state.energy.latent_heat,
                
                # Wasser
                "evapotranspiration": state.water.evapotranspiration,
                "soil_moisture": state.water.soil_moisture,
                "water_balance": state.water.water_balance,
                
                # Carbon
                "gpp": state.carbon.gpp,
                "nee": state.carbon.nee,
                "ndvi": state.carbon.ndvi,
                
                # Risiko
                "risk_score": state.risk_score,
                "risk_drivers": state.risk_drivers,
                
                # Für Visualisierung
                "fill_color": FrontendFormatter._risk_to_color(state.risk_score),
                "height": state.risk_score * 1000  # Höhe in Metern
            }
        }
    
    @staticmethod
    def _risk_to_color(risk: float) -> str:
        """Risiko zu Hex-Farbe"""
        if risk > 0.7:
            return "#FF0000"  # Rot
        elif risk > 0.5:
            return "#FF8800"  # Orange
        elif risk > 0.3:
            return "#FFFF00"  # Gelb
        elif risk > 0.1:
            return "#00FF00"  # Grün
        else:
            return "#00FFFF"  # Cyan
    
    @staticmethod
    def cells_to_feature_collection(
        states: List[CellState]
    ) -> Dict[str, Any]:
        """Konvertiert Liste von CellStates zu GeoJSON FeatureCollection"""
        
        features = [
            FrontendFormatter.cell_to_geojson(state)
            for state in states
        ]
        
        return {
            "type": "FeatureCollection",
            "features": features
        }


# =====================================================
# DEMO
# =====================================================

async def demo():
    """Demo des Physical Earth Model"""
    import asyncio
    
    print("=" * 60)
    print("🌍 TERA Physical Earth Cycle Model")
    print("=" * 60)
    
    model = PhysicalEarthModel()
    
    # Test-Locations
    locations = [
        ("Berlin", 52.52, 13.41),
        ("Jakarta", -6.21, 106.85),
        ("Sahara", 25.0, 10.0),
        ("Amazon", -3.0, -60.0),
    ]
    
    print("\n📊 Erdzyklen-Berechnung:\n")
    
    for name, lat, lon in locations:
        h3_index = h3.latlng_to_cell(lat, lon, 7)
        
        state = model.calculate_cell_state(
            h3_index,
            precipitation_mm=5,
            ndvi=0.5 if "Amazon" in name else 0.1 if "Sahara" in name else 0.4
        )
        
        print(f"{'='*50}")
        print(f"📍 {name}")
        print(f"   H3: {state.h3_index}")
        print(f"\n   ☀️ ENERGIE-BUDGET:")
        print(f"      SW absorbed: {state.energy.sw_absorbed} W/m²")
        print(f"      Net radiation: {state.energy.net_radiation} W/m²")
        print(f"      Latent heat: {state.energy.latent_heat} W/m²")
        
        print(f"\n   💧 WASSER-ZYKLUS:")
        print(f"      ET: {state.water.evapotranspiration} mm/Tag")
        print(f"      Soil moisture: {state.water.soil_moisture}%")
        print(f"      Water balance: {state.water.water_balance} mm")
        
        print(f"\n   🌿 CARBON-ZYKLUS:")
        print(f"      GPP: {state.carbon.gpp} gC/m²/Tag")
        print(f"      NEE: {state.carbon.nee} gC/m²/Tag")
        print(f"      NDVI: {state.carbon.ndvi}")
        
        print(f"\n   ⚠️ RISIKO: {state.risk_score:.2f}")
        if state.risk_drivers:
            print(f"      Treiber: {', '.join(state.risk_drivers)}")
    
    # Adaptive Tessellation Demo
    print(f"\n{'='*50}")
    print("🔷 ADAPTIVE TESSELLATION:")
    
    cells = AdaptiveTessellation.get_cells_for_bbox(
        min_lat=52.0, min_lon=13.0,
        max_lat=53.0, max_lon=14.0,
        zoom=10
    )
    print(f"   Zoom 10 → Resolution {AdaptiveTessellation.get_resolution_for_zoom(10)}")
    print(f"   Zellen für Berlin: {len(cells)}")
    
    print(f"\n{'='*60}")
    print("✅ Physical Earth Model Demo abgeschlossen!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo())






















