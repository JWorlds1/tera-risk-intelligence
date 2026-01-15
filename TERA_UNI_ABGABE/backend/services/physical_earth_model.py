"""
TERA Physical Earth Model v2.0
=====================================

Physik-basiertes Modell für:
- Energie-Budget (Strahlungsbilanz)
- Wasser-Zyklus (Penman-Monteith ET)
- Carbon-Zyklus (Light Use Efficiency GPP)

Compatible with h3 v3.7.x
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timezone
import math
import h3


# =====================================================
# PHYSICAL CONSTANTS
# =====================================================

STEFAN_BOLTZMANN = 5.67e-8  # W/m²/K⁴
SOLAR_CONSTANT = 1361       # W/m²
LATENT_HEAT_VAPORIZATION = 2.45e6  # J/kg
SPECIFIC_HEAT_AIR = 1013    # J/kg/K
AIR_DENSITY = 1.225         # kg/m³
PSYCHROMETRIC_CONST = 0.066 # kPa/°C


# =====================================================
# DATA CLASSES
# =====================================================

@dataclass
class EnergyBudget:
    """Energy balance at Earth's surface"""
    sw_incoming: float = 0.0    # Shortwave radiation incoming (W/m²)
    sw_absorbed: float = 0.0    # After albedo (W/m²)
    lw_outgoing: float = 0.0    # Longwave radiation outgoing (W/m²)
    lw_incoming: float = 0.0    # Atmospheric back-radiation (W/m²)
    net_radiation: float = 0.0  # Rn = SW_net + LW_net (W/m²)
    sensible_heat: float = 0.0  # H - convection (W/m²)
    latent_heat: float = 0.0    # LE - evaporation (W/m²)
    ground_heat: float = 0.0    # G - soil heat flux (W/m²)
    bowen_ratio: float = 0.0    # H/LE ratio


@dataclass
class WaterCycle:
    """Water balance components"""
    precipitation: float = 0.0      # P (mm/day)
    evapotranspiration: float = 0.0 # ET (mm/day)
    runoff: float = 0.0             # R (mm/day)
    infiltration: float = 0.0       # I (mm/day)
    soil_moisture: float = 50.0     # θ (%)
    water_balance: float = 0.0      # ΔS = P - ET - R (mm/day)


@dataclass
class CarbonCycle:
    """Carbon exchange components"""
    gpp: float = 0.0      # Gross Primary Production (gC/m²/day)
    npp: float = 0.0      # Net Primary Production (gC/m²/day)
    ra: float = 0.0       # Autotrophic respiration (gC/m²/day)
    rh: float = 0.0       # Heterotrophic respiration (gC/m²/day)
    nee: float = 0.0      # Net Ecosystem Exchange (gC/m²/day)
    ndvi: float = 0.5     # Normalized Difference Vegetation Index
    lai: float = 2.0      # Leaf Area Index (m²/m²)
    fpar: float = 0.5     # Fraction of Absorbed PAR


@dataclass
class CellState:
    """Complete Earth state for an H3 cell"""
    h3_index: str
    lat: float
    lon: float
    timestamp: datetime
    
    # Atmospheric
    temperature_c: float = 15.0
    humidity_pct: float = 60.0
    wind_speed: float = 3.0
    cloud_cover_pct: float = 50.0
    
    # Cycles
    energy: EnergyBudget = field(default_factory=EnergyBudget)
    water: WaterCycle = field(default_factory=WaterCycle)
    carbon: CarbonCycle = field(default_factory=CarbonCycle)
    
    # Risk
    risk_score: float = 0.0
    risk_drivers: List[str] = field(default_factory=list)


# =====================================================
# PHYSICAL MODEL
# =====================================================

class PhysicalEarthModel:
    """
    Physics-based Earth System Model
    
    Calculates energy, water, and carbon cycles for any location
    using fundamental physical equations.
    """
    
    def __init__(self):
        self.now = datetime.now(timezone.utc)
    
    def calculate_cell_state(
        self,
        h3_index: str,
        precipitation_mm: float = 0.0,
        ndvi: float = 0.5,
        cloud_cover: float = 50.0,
        soil_moisture_pct: float = 50.0,
    ) -> CellState:
        """Calculate complete Earth state for H3 cell"""
        
        # Get center coordinates (h3 v3.x API)
        lat, lon = h3.h3_to_geo(h3_index)
        
        # Calculate solar geometry
        day_of_year = self.now.timetuple().tm_yday
        hour = self.now.hour + self.now.minute / 60.0
        
        # Temperature estimate (climatology + latitude + time)
        temp_c = self._estimate_temperature(lat, day_of_year)
        
        # Humidity based on temperature and location
        humidity = self._estimate_humidity(lat, temp_c, precipitation_mm)
        
        # Energy budget
        energy = self._calculate_energy_budget(
            lat, lon, day_of_year, hour,
            temp_c, cloud_cover, ndvi
        )
        
        # Water cycle
        water = self._calculate_water_cycle(
            temp_c, humidity, energy.net_radiation,
            precipitation_mm, ndvi, soil_moisture_pct
        )
        
        # Carbon cycle
        carbon = self._calculate_carbon_cycle(
            energy.sw_absorbed, temp_c, water.soil_moisture,
            ndvi
        )
        
        # Risk assessment
        risk_score, risk_drivers = self._assess_risk(
            temp_c, precipitation_mm, water.soil_moisture,
            carbon.nee, lat
        )
        
        return CellState(
            h3_index=h3_index,
            lat=lat,
            lon=lon,
            timestamp=self.now,
            temperature_c=temp_c,
            humidity_pct=humidity,
            cloud_cover_pct=cloud_cover,
            energy=energy,
            water=water,
            carbon=carbon,
            risk_score=risk_score,
            risk_drivers=risk_drivers,
        )
    
    def _estimate_temperature(self, lat: float, doy: int) -> float:
        """Estimate temperature from latitude and day of year"""
        # Base temperature from latitude
        base = 30 - abs(lat) * 0.7
        
        # Seasonal variation (reversed for southern hemisphere)
        amplitude = 15 * (1 - abs(lat) / 90) + 5
        phase = 172 if lat >= 0 else 355  # Summer solstice
        seasonal = amplitude * math.cos(2 * math.pi * (doy - phase) / 365)
        
        return round(base + seasonal, 1)
    
    def _estimate_humidity(
        self, lat: float, temp_c: float, precip: float
    ) -> float:
        """Estimate relative humidity"""
        # Base from climate zone
        if abs(lat) < 15:
            base = 75  # Tropical
        elif abs(lat) < 35:
            base = 50  # Subtropical
        elif abs(lat) < 55:
            base = 65  # Temperate
        else:
            base = 70  # Polar
        
        # Adjust for precipitation
        precip_effect = min(20, precip * 2)
        
        return min(100, max(10, base + precip_effect))
    
    def _calculate_energy_budget(
        self,
        lat: float, lon: float,
        doy: int, hour: float,
        temp_c: float,
        cloud_cover: float,
        ndvi: float
    ) -> EnergyBudget:
        """Calculate radiation and heat fluxes"""
        
        # Solar declination
        decl = 23.45 * math.sin(2 * math.pi * (doy - 81) / 365)
        decl_rad = math.radians(decl)
        lat_rad = math.radians(lat)
        
        # Hour angle
        hour_angle = math.radians((hour - 12) * 15)
        
        # Solar zenith angle
        cos_z = (math.sin(lat_rad) * math.sin(decl_rad) +
                 math.cos(lat_rad) * math.cos(decl_rad) * math.cos(hour_angle))
        cos_z = max(0, cos_z)
        
        # Top-of-atmosphere radiation
        toa_radiation = SOLAR_CONSTANT * cos_z
        
        # Atmospheric transmittance (clear sky ~0.75, cloudy ~0.3)
        tau = 0.75 - cloud_cover / 100 * 0.45
        sw_incoming = toa_radiation * tau
        
        # Albedo from NDVI (vegetation is darker)
        albedo = 0.3 - ndvi * 0.15
        albedo = max(0.05, min(0.9, albedo))
        
        sw_absorbed = sw_incoming * (1 - albedo)
        
        # Longwave radiation (Stefan-Boltzmann)
        temp_k = temp_c + 273.15
        emissivity = 0.95
        lw_outgoing = emissivity * STEFAN_BOLTZMANN * (temp_k ** 4)
        
        # Atmospheric back-radiation
        atm_emissivity = 0.7 + cloud_cover / 100 * 0.25
        atm_temp_k = temp_k - 15  # Effective atmosphere temperature
        lw_incoming = atm_emissivity * STEFAN_BOLTZMANN * (atm_temp_k ** 4)
        
        # Net radiation
        net_radiation = sw_absorbed + lw_incoming - lw_outgoing
        
        # Partition into heat fluxes (simplified)
        ground_heat = net_radiation * 0.1
        available = net_radiation - ground_heat
        
        # Bowen ratio depends on moisture/vegetation
        bowen = 1.0 / (0.5 + ndvi)  # More vegetation = more LE
        
        latent_heat = available / (1 + bowen) if (1 + bowen) > 0 else 0
        sensible_heat = available - latent_heat
        
        return EnergyBudget(
            sw_incoming=round(sw_incoming, 1),
            sw_absorbed=round(sw_absorbed, 1),
            lw_incoming=round(lw_incoming, 1),
            lw_outgoing=round(lw_outgoing, 1),
            net_radiation=round(net_radiation, 1),
            sensible_heat=round(sensible_heat, 1),
            latent_heat=round(latent_heat, 1),
            ground_heat=round(ground_heat, 1),
            bowen_ratio=round(bowen, 2),
        )
    
    def _calculate_water_cycle(
        self,
        temp_c: float,
        humidity: float,
        net_radiation: float,
        precipitation: float,
        ndvi: float,
        soil_moisture: float
    ) -> WaterCycle:
        """Calculate water balance using Penman-Monteith"""
        
        # Saturation vapor pressure (Tetens formula)
        es = 0.6108 * math.exp(17.27 * temp_c / (temp_c + 237.3))
        
        # Actual vapor pressure
        ea = es * humidity / 100
        
        # Vapor pressure deficit
        vpd = es - ea
        
        # Slope of saturation curve
        delta = 4098 * es / ((temp_c + 237.3) ** 2)
        
        # Reference ET (FAO Penman-Monteith simplified)
        # ET0 = [0.408 * Δ * Rn + γ * 900/(T+273) * u2 * VPD] / [Δ + γ * (1 + 0.34*u2)]
        u2 = 2.0  # Wind speed at 2m
        numerator = (0.408 * delta * net_radiation + 
                    PSYCHROMETRIC_CONST * 900 / (temp_c + 273) * u2 * vpd)
        denominator = delta + PSYCHROMETRIC_CONST * (1 + 0.34 * u2)
        
        et0 = max(0, numerator / denominator) if denominator != 0 else 0
        
        # Crop coefficient from NDVI
        kc = 0.2 + ndvi * 1.0
        
        # Soil moisture stress
        ks = min(1.0, soil_moisture / 50)
        
        # Actual ET
        et_actual = et0 * kc * ks
        
        # Runoff (simple curve number approach)
        if precipitation > 0:
            cn = 70 - ndvi * 20  # More vegetation = less runoff
            s = 254 * (100 / cn - 1)
            ia = 0.2 * s
            if precipitation > ia:
                runoff = (precipitation - ia) ** 2 / (precipitation - ia + s)
            else:
                runoff = 0
        else:
            runoff = 0
        
        # Infiltration
        infiltration = max(0, precipitation - runoff)
        
        # Water balance
        water_balance = precipitation - et_actual - runoff
        
        # Update soil moisture
        new_soil_moisture = soil_moisture + water_balance
        new_soil_moisture = max(0, min(100, new_soil_moisture))
        
        return WaterCycle(
            precipitation=round(precipitation, 2),
            evapotranspiration=round(et_actual, 2),
            runoff=round(runoff, 2),
            infiltration=round(infiltration, 2),
            soil_moisture=round(new_soil_moisture, 1),
            water_balance=round(water_balance, 2),
        )
    
    def _calculate_carbon_cycle(
        self,
        par: float,
        temp_c: float,
        soil_moisture: float,
        ndvi: float
    ) -> CarbonCycle:
        """Calculate carbon exchange using Light Use Efficiency"""
        
        # fPAR from NDVI (linear relationship)
        fpar = 1.1 * ndvi - 0.1
        fpar = max(0, min(1, fpar))
        
        # LAI from NDVI
        lai = max(0, (ndvi - 0.1) / 0.1)
        lai = min(8, lai)
        
        # APAR (Absorbed PAR) - assume PAR is 45% of SW
        par_fraction = 0.45
        apar = par * par_fraction * fpar
        
        # Light Use Efficiency (gC/MJ) - varies with stress
        lue_max = 2.5  # Maximum LUE
        
        # Temperature stress
        t_opt = 25
        t_stress = max(0, 1 - ((temp_c - t_opt) / 20) ** 2)
        
        # Water stress
        w_stress = min(1, soil_moisture / 40)
        
        # Actual LUE
        lue = lue_max * t_stress * w_stress
        
        # GPP (convert W/m² to MJ/m²/day: * 0.0864)
        gpp = apar * 0.0864 * lue
        gpp = max(0, gpp)
        
        # Autotrophic respiration (~50% of GPP)
        ra = gpp * 0.5
        
        # NPP
        npp = gpp - ra
        
        # Heterotrophic respiration (soil respiration)
        # Increases with temperature (Q10 relationship)
        q10 = 2.0
        rh_base = 1.5  # gC/m²/day at 10°C
        rh = rh_base * (q10 ** ((temp_c - 10) / 10))
        rh = rh * (soil_moisture / 50)  # Moisture effect
        
        # NEE = Ra + Rh - GPP (positive = source, negative = sink)
        nee = ra + rh - gpp
        
        return CarbonCycle(
            gpp=round(gpp, 2),
            npp=round(npp, 2),
            ra=round(ra, 2),
            rh=round(rh, 2),
            nee=round(nee, 2),
            ndvi=round(ndvi, 2),
            lai=round(lai, 1),
            fpar=round(fpar, 3),
        )
    
    def _assess_risk(
        self,
        temp_c: float,
        precip: float,
        soil_moisture: float,
        nee: float,
        lat: float
    ) -> Tuple[float, List[str]]:
        """Calculate integrated risk score and identify drivers"""
        
        risk_drivers = []
        scores = []
        
        # Heat stress
        if temp_c > 35:
            heat_risk = min(1, (temp_c - 35) / 10)
            scores.append(heat_risk)
            if heat_risk > 0.3:
                risk_drivers.append('extreme_heat')
        
        # Drought stress
        if soil_moisture < 30:
            drought_risk = 1 - soil_moisture / 30
            scores.append(drought_risk)
            if drought_risk > 0.3:
                risk_drivers.append('drought_stress')
        
        # Flood risk
        if precip > 50:
            flood_risk = min(1, (precip - 50) / 100)
            scores.append(flood_risk)
            if flood_risk > 0.3:
                risk_drivers.append('flood_risk')
        
        # Carbon stress (ecosystem losing carbon)
        if nee > 2:
            carbon_risk = min(1, (nee - 2) / 5)
            scores.append(carbon_risk)
            if carbon_risk > 0.3:
                risk_drivers.append('carbon_loss')
        
        # Overall risk
        if scores:
            risk_score = sum(scores) / len(scores) * max(scores)
        else:
            risk_score = 0.0
        
        return round(min(1, risk_score), 2), risk_drivers


# =====================================================
# ADAPTIVE TESSELLATION
# =====================================================

class AdaptiveTessellation:
    """Adaptive H3 tessellation based on zoom and risk"""
    
    @staticmethod
    def get_resolution_for_zoom(zoom: int) -> int:
        """Map zoom level to H3 resolution"""
        # Zoom 0-20 → Resolution 0-10
        resolution_map = {
            0: 0, 1: 0, 2: 1, 3: 1, 4: 2,
            5: 2, 6: 3, 7: 3, 8: 4, 9: 4,
            10: 5, 11: 5, 12: 6, 13: 6, 14: 7,
            15: 7, 16: 8, 17: 8, 18: 9, 19: 9, 20: 10
        }
        return resolution_map.get(zoom, 5)
    
    @staticmethod
    def get_cells_for_bbox(
        min_lat: float, min_lon: float,
        max_lat: float, max_lon: float,
        zoom: int
    ) -> List[str]:
        """Get H3 cells covering a bounding box"""
        resolution = AdaptiveTessellation.get_resolution_for_zoom(zoom)
        
        # Create polygon for bbox
        polygon = [
            (min_lat, min_lon),
            (min_lat, max_lon),
            (max_lat, max_lon),
            (max_lat, min_lon),
            (min_lat, min_lon),  # Close polygon
        ]
        
        # Use h3 v3.x polyfill (expects GeoJSON format)
        geojson = {
            "type": "Polygon",
            "coordinates": [[
                [min_lon, min_lat],
                [max_lon, min_lat],
                [max_lon, max_lat],
                [min_lon, max_lat],
                [min_lon, min_lat],
            ]]
        }
        
        try:
            cells = list(h3.polyfill_geojson(geojson, resolution))
        except Exception:
            # Fallback: generate grid
            cells = []
            lat_step = (max_lat - min_lat) / 20
            lon_step = (max_lon - min_lon) / 20
            for i in range(20):
                for j in range(20):
                    lat = min_lat + i * lat_step
                    lon = min_lon + j * lon_step
                    cell = h3.geo_to_h3(lat, lon, resolution)
                    if cell not in cells:
                        cells.append(cell)
        
        return cells


# =====================================================
# FRONTEND FORMATTER
# =====================================================

class FrontendFormatter:
    """Format data for MapLibre visualization"""
    
    @staticmethod
    def cell_to_feature(state: CellState) -> dict:
        """Convert CellState to GeoJSON Feature"""
        
        # Get boundary (h3 v3.x API)
        boundary = h3.h3_to_geo_boundary(state.h3_index, geo_json=True)
        
        # Risk-based color
        risk = state.risk_score
        if risk > 0.7:
            fill_color = '#ff0000'
        elif risk > 0.4:
            fill_color = '#ff8800'
        elif risk > 0.2:
            fill_color = '#ffff00'
        else:
            fill_color = '#00ff88'
        
        # Height from risk
        height = 50 + risk * 450
        
        return {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [boundary]
            },
            "properties": {
                "h3_index": state.h3_index,
                "lat": state.lat,
                "lon": state.lon,
                "fill_color": fill_color,
                "height": height,
                "risk_score": state.risk_score,
                "temperature": state.temperature_c,
                "ndvi": state.carbon.ndvi,
                "soil_moisture": state.water.soil_moisture,
                "net_radiation": state.energy.net_radiation,
                "gpp": state.carbon.gpp,
                "et": state.water.evapotranspiration,
            }
        }
    
    @staticmethod
    def cells_to_feature_collection(states: List[CellState]) -> dict:
        """Convert list of CellStates to GeoJSON FeatureCollection"""
        features = [FrontendFormatter.cell_to_feature(s) for s in states]
        return {
            "type": "FeatureCollection",
            "features": features
        }
