"""
LLM-Enhanced Tessellation Engine
================================
Kombiniert echte Topographie-Daten mit LLM-Prognosen
für präzise Risikozellen-Berechnung
"""
import h3
import math
import httpx
import asyncio
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

from services.topography_service import TopographyService


# IPCC AR6 SSP2-4.5 Basis-Faktoren
IPCC_FACTORS = {
    'coastal': {'temp_mult': 0.9, 'flood_risk': 0.8, 'sea_level': 3.4},
    'tropical': {'temp_mult': 1.1, 'flood_risk': 0.7, 'sea_level': 2.8},
    'arid': {'temp_mult': 1.3, 'flood_risk': 0.2, 'sea_level': 0},
    'temperate': {'temp_mult': 1.0, 'flood_risk': 0.4, 'sea_level': 1.5},
    'cold': {'temp_mult': 1.5, 'flood_risk': 0.3, 'sea_level': 0.5},
    'seismic': {'temp_mult': 1.0, 'flood_risk': 0.3, 'sea_level': 1.0},
    'conflict': {'temp_mult': 1.0, 'flood_risk': 0.4, 'sea_level': 1.0},
}

# Farben nach Risikotyp
RISK_COLORS = {
    'coastal_flood': '#dc2626',    # Rot - Küstenflut
    'flood': '#ea580c',            # Orange - Überschwemmung
    'urban_flood': '#f59e0b',      # Amber - Urban Flood
    'drought': '#d97706',          # Dunkel-Amber - Dürre
    'heat': '#ef4444',             # Rot - Hitze
    'seismic': '#7c3aed',          # Violett - Seismisch
    'conflict': '#be123c',         # Dunkelrot - Konflikt
    'stable': '#22c55e',           # Grün - Stabil
    'water': '#0ea5e9',            # Blau - Wasser
}


@dataclass 
class LLMCellData:
    """Von LLM berechnete Zelldaten"""
    h3_index: str
    lat: float
    lon: float
    
    # Topographie (echt)
    is_water: bool
    elevation_m: float
    coast_distance_km: float
    
    # LLM-berechnete Risiken
    risk_type: str
    risk_score: float  # 0-1
    intensity: float   # 0-1 für 3D-Höhe
    
    # Begründung
    reasons: List[str]
    color: str


class LLMEnhancedTessellation:
    """
    Tessellierung mit LLM-basierter Risikoberechnung
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.topo = TopographyService()
        self.ollama_url = ollama_url
        self.ollama_model = "llama3.1:8b"
        self._ocean_cache = {}
    
    async def generate_risk_map(
        self,
        lat: float,
        lon: float,
        city_type: str,
        resolution: int = 8,
        radius_km: float = 15.0,
        llm_forecast: Dict = None
    ) -> List[Dict]:
        """
        Generiert Risikokarte mit LLM-Enhanced Berechnung
        
        Args:
            lat, lon: Stadtzentrum
            city_type: coastal, conflict, seismic, etc.
            resolution: H3-Auflösung (7-10)
            radius_km: Radius um Zentrum
            llm_forecast: Precision Forecast vom LLM
        """
        logger.info(f"🎯 LLM-Enhanced Tessellation für ({lat}, {lon}) - {city_type}")
        
        # 1. H3 Hexagone generieren
        hexagons = self._generate_hexagons(lat, lon, radius_km, resolution)
        logger.info(f"📐 {len(hexagons)} Hexagone generiert")
        
        # 2. LLM-Faktoren aus Forecast extrahieren
        llm_factors = self._extract_llm_factors(llm_forecast, city_type)
        
        # 3. Jede Zelle analysieren
        features = []
        water_count = 0
        land_count = 0
        
        for h3_idx in hexagons:
            cell = await self._analyze_cell(h3_idx, lat, lon, city_type, llm_factors)
            if cell is None:
                continue
            
            if cell.is_water:
                water_count += 1
            else:
                land_count += 1
            
            feature = self._cell_to_feature(cell)
            features.append(feature)
        
        logger.info(f"✅ {len(features)} Features (Land: {land_count}, Wasser: {water_count})")
        return features
    
    def _generate_hexagons(self, lat: float, lon: float, radius_km: float, resolution: int) -> List[str]:
        """Generiert H3 Hexagone in Bounding Box"""
        lat_delta = radius_km / 111.0
        lon_delta = radius_km / (111.0 * math.cos(math.radians(lat)))
        
        min_lat, max_lat = lat - lat_delta, lat + lat_delta
        min_lon, max_lon = lon - lon_delta, lon + lon_delta
        
        hexagons = set()
        step = 0.005 if resolution >= 9 else 0.01
        
        curr_lat = min_lat
        while curr_lat <= max_lat:
            curr_lon = min_lon
            while curr_lon <= max_lon:
                h3_idx = h3.geo_to_h3(curr_lat, curr_lon, resolution)
                hexagons.add(h3_idx)
                curr_lon += step
            curr_lat += step
        
        return list(hexagons)
    
    def _extract_llm_factors(self, llm_forecast: Dict, city_type: str) -> Dict:
        """Extrahiert Risikofaktoren aus LLM Forecast"""
        base = IPCC_FACTORS.get(city_type, IPCC_FACTORS['temperate'])
        
        if not llm_forecast:
            return base
        
        # LLM-Werte übernehmen
        temp_change = llm_forecast.get('temperature_change', {}).get('expected', 1.0)
        precip_change = llm_forecast.get('precipitation_change', {}).get('expected', 0)
        sea_level = llm_forecast.get('sea_level_rise', {})
        sea_level_mm = sea_level.get('expected', 0) if sea_level else 0
        
        combined_risk = llm_forecast.get('combined_risk', 0.3)
        climate_risk = llm_forecast.get('climate_risk', 0.3)
        conflict_risk = llm_forecast.get('conflict_risk', 0)
        
        return {
            'temp_mult': base['temp_mult'],
            'temp_change': temp_change,
            'precip_change': precip_change,
            'sea_level': sea_level_mm,
            'flood_risk': base['flood_risk'] * (1 + precip_change/100),
            'combined_risk': combined_risk,
            'climate_risk': climate_risk,
            'conflict_risk': conflict_risk,
            'trend': llm_forecast.get('trend_2024_2026', 'stabil')
        }
    
    async def _analyze_cell(
        self,
        h3_idx: str,
        center_lat: float,
        center_lon: float,
        city_type: str,
        llm_factors: Dict
    ) -> Optional[LLMCellData]:
        """Analysiert eine Zelle mit echten + LLM Daten"""
        
        cell_lat, cell_lon = h3.h3_to_geo(h3_idx)
        
        # Entfernung zum Zentrum
        dist_km = self._haversine(cell_lat, cell_lon, center_lat, center_lon)
        
        # === ECHTE TOPOGRAPHIE ===
        is_ocean = self._is_ocean_cached(cell_lat, cell_lon)
        coast_dist = self._calc_coast_distance(h3_idx, is_ocean)
        
        # Offshore begrenzen (max 5km ins Meer)
        if is_ocean and abs(coast_dist) > 5.0:
            return None
        
        # Höhenschätzung
        elevation = self._estimate_elevation(cell_lat, coast_dist, is_ocean)
        
        # === LLM-ENHANCED RISIKO ===
        risk_type, risk_score, reasons = self._calculate_risk(
            is_ocean=is_ocean,
            elevation=elevation,
            coast_dist=coast_dist,
            dist_from_center=dist_km,
            city_type=city_type,
            llm_factors=llm_factors
        )
        
        # Intensität für 3D-Höhe (0-1)
        intensity = risk_score if not is_ocean else 0.1
        
        return LLMCellData(
            h3_index=h3_idx,
            lat=cell_lat,
            lon=cell_lon,
            is_water=is_ocean,
            elevation_m=elevation,
            coast_distance_km=coast_dist,
            risk_type=risk_type,
            risk_score=risk_score,
            intensity=intensity,
            reasons=reasons,
            color=RISK_COLORS.get(risk_type, '#6495ed')
        )
    
    def _calculate_risk(
        self,
        is_ocean: bool,
        elevation: float,
        coast_dist: float,
        dist_from_center: float,
        city_type: str,
        llm_factors: Dict
    ) -> Tuple[str, float, List[str]]:
        """
        Berechnet Risiko basierend auf Topographie + LLM-Faktoren
        """
        reasons = []
        
        if is_ocean:
            return 'water', 0.0, ['Wasserfläche']
        
        base_risk = llm_factors.get('combined_risk', 0.3)
        flood_factor = llm_factors.get('flood_risk', 0.4)
        sea_level = llm_factors.get('sea_level', 0)
        conflict = llm_factors.get('conflict_risk', 0)
        trend = llm_factors.get('trend', 'stabil')
        
        # Trend-Anpassung
        if trend == 'steigend':
            base_risk *= 1.15
            reasons.append('📈 Steigender Trend')
        
        # === KÜSTENFLUT (kritisch) ===
        if coast_dist < 1.0 and elevation < 3:
            risk = min(0.95, base_risk + 0.5 + (sea_level / 10))
            reasons.append(f'🌊 Kritische Küstenlage ({elevation:.1f}m)')
            reasons.append(f'📊 Meeresspiegel +{sea_level:.1f}mm/Jahr')
            return 'coastal_flood', risk, reasons
        
        # === KONFLIKT ===
        if city_type == 'conflict' or conflict > 0.3:
            risk = min(0.9, base_risk + conflict * 0.5)
            reasons.append('⚔️ Konfliktzone')
            if conflict > 0.5:
                reasons.append('🚨 Aktive Kampfhandlungen')
            return 'conflict', risk, reasons
        
        # === SEISMISCH ===
        if city_type == 'seismic':
            risk = base_risk + 0.2
            reasons.append('🌋 Seismisch aktive Zone')
            return 'seismic', min(0.85, risk), reasons
        
        # === ÜBERSCHWEMMUNG ===
        if elevation < 5 and coast_dist < 5:
            risk = min(0.8, base_risk + flood_factor * 0.4)
            reasons.append(f'💧 Niedrige Lage ({elevation:.1f}m)')
            reasons.append(f'🌊 Küstennah ({coast_dist:.1f}km)')
            return 'flood', risk, reasons
        
        # === URBAN FLOOD ===
        if dist_from_center < 5 and elevation < 15:
            risk = min(0.6, base_risk + 0.15)
            reasons.append('🏙️ Urbanes Gebiet')
            reasons.append(f'💧 Flood-Risiko: {flood_factor*100:.0f}%')
            return 'urban_flood', risk, reasons
        
        # === DÜRRE (für aride Gebiete) ===
        if city_type == 'arid':
            risk = base_risk + 0.25
            reasons.append('☀️ Arides Klima')
            reasons.append(f'🌡️ Temp +{llm_factors.get("temp_change", 1.0):.1f}°C')
            return 'drought', min(0.75, risk), reasons
        
        # === HITZE ===
        if city_type == 'tropical' and dist_from_center < 8:
            risk = base_risk + 0.2
            reasons.append('🌡️ Tropische Hitze')
            return 'heat', min(0.7, risk), reasons
        
        # === STABIL ===
        risk = max(0.1, base_risk - 0.1)
        reasons.append('✓ Moderate Risiken')
        reasons.append(f'📏 Höhe: {elevation:.0f}m')
        return 'stable', risk, reasons
    
    def _is_ocean_cached(self, lat: float, lon: float) -> bool:
        key = (round(lat, 3), round(lon, 3))
        if key not in self._ocean_cache:
            self._ocean_cache[key] = self.topo.is_ocean(lat, lon)
        return self._ocean_cache[key]
    
    def _calc_coast_distance(self, h3_idx: str, is_ocean: bool) -> float:
        """Berechnet ungefähre Küstendistanz über H3-Ringe"""
        edge_km = 0.5  # Ungefähr für Resolution 8
        
        for k in range(1, 8):
            try:
                ring = h3.k_ring(h3_idx, k)
                for neighbor in ring:
                    nlat, nlon = h3.h3_to_geo(neighbor)
                    neighbor_ocean = self._is_ocean_cached(nlat, nlon)
                    if neighbor_ocean != is_ocean:
                        dist = k * edge_km
                        return -dist if is_ocean else dist
            except:
                continue
        
        return 10.0 if not is_ocean else -10.0
    
    def _estimate_elevation(self, lat: float, coast_dist: float, is_ocean: bool) -> float:
        """Schnelle Höhenschätzung ohne externe API"""
        if is_ocean:
            return 0.0
        if coast_dist < 1:
            return 2.0 + coast_dist
        elif coast_dist < 5:
            return 5.0 + coast_dist * 2
        elif coast_dist < 20:
            return 15.0 + coast_dist * 3
        else:
            return 50.0 + abs(lat) * 0.5
    
    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))
    
    def _cell_to_feature(self, cell: LLMCellData) -> Dict:
        """Konvertiert Zelle zu GeoJSON Feature"""
        boundary = h3.h3_to_geo_boundary(cell.h3_index, geo_json=True)
        
        return {
            'type': 'Feature',
            'geometry': {
                'type': 'Polygon',
                'coordinates': [boundary]
            },
            'properties': {
                'h3': cell.h3_index,
                'primary_risk': cell.risk_type,
                'risk_score': round(cell.risk_score, 3),
                'intensity': round(cell.intensity, 3),
                'height': round(cell.intensity * 500, 1),  # 3D Höhe in Metern
                'color': cell.color,
                'zone': cell.risk_type,
                'ist_wasser': cell.is_water,
                'hoehe_meter': round(cell.elevation_m, 1),
                'kuestenentfernung_km': round(cell.coast_distance_km, 1),
                'gruende': cell.reasons,
                'year': 2026
            }
        }


# Globale Instanz
llm_tessellation = LLMEnhancedTessellation()
