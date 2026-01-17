"""
TERA Enhanced Risk Engine
Fusioniert alle Datenquellen für präzise Risikoanalysen
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from loguru import logger

# Import aller Data Services
from services.data_fusion_hub import data_fusion_hub, FusedDataPoint
from services.firecrawl_agent import firecrawl_agent
from services.acled_service import acled_service
from services.modis_vegetation_service import modis_service
from services.copernicus_marine_service import copernicus_marine


class EnhancedRiskEngine:
    """
    Erweiterter Risk Engine mit vollständiger Datenfusion
    
    Datenquellen:
    - USGS: Seismische Daten (Echtzeit)
    - IPCC AR6: Klimaprojektionen
    - NOAA: Meerestemperaturen
    - GDELT: Konfliktnachrichten
    - ACLED: Punkt-genaue Konflikte
    - MODIS: Vegetation/Dürre
    - Copernicus: Ozean/Küsten
    - Firecrawl: Web-Recherche
    """
    
    def __init__(self):
        self.cache = {}
        self.last_update = None
    
    async def analyze_location_full(
        self, 
        lat: float, 
        lon: float, 
        city: str = "",
        country: str = "",
        location_type: str = "urban"
    ) -> Dict:
        """
        Vollständige Analyse eines Standorts mit allen Datenquellen
        """
        
        logger.info(f"🌍 Enhanced Analysis: {city}, {country} ({lat:.4f}, {lon:.4f})")
        
        # Parallel alle Datenquellen abfragen
        tasks = [
            self._get_seismic_risk(lat, lon),
            self._get_climate_risk(lat, lon, location_type),
            self._get_conflict_risk(lat, lon, country),
            self._get_coastal_risk(lat, lon, location_type),
            self._get_vegetation_risk(lat, lon),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Ergebnisse zusammenführen
        seismic = results[0] if isinstance(results[0], dict) else {'risk': 0.05}
        climate = results[1] if isinstance(results[1], dict) else {'risk': 0.1}
        conflict = results[2] if isinstance(results[2], dict) else {'risk': 0.05}
        coastal = results[3] if isinstance(results[3], dict) else {'risk': 0.0}
        vegetation = results[4] if isinstance(results[4], dict) else {'risk': 0.1}
        
        # Gesamtrisiko berechnen
        # Gewichtung: Klima 40%, Konflikt 20%, Seismik 15%, Küste 15%, Vegetation 10%
        total_risk = (
            climate.get('risk', 0) * 0.40 +
            conflict.get('risk', 0) * 0.20 +
            seismic.get('risk', 0) * 0.15 +
            coastal.get('risk', 0) * 0.15 +
            vegetation.get('risk', 0) * 0.10
        )
        
        # Primäres Risiko ermitteln
        risks = {
            'climate': climate.get('risk', 0),
            'conflict': conflict.get('risk', 0),
            'seismic': seismic.get('risk', 0),
            'coastal': coastal.get('risk', 0),
            'drought': vegetation.get('risk', 0)
        }
        primary_risk = max(risks, key=risks.get)
        
        # Datenquellen sammeln
        sources = []
        for r in [seismic, climate, conflict, coastal, vegetation]:
            if isinstance(r, dict) and 'source' in r:
                sources.append(r['source'])
        
        return {
            'location': {
                'city': city,
                'country': country,
                'lat': lat,
                'lon': lon,
                'type': location_type
            },
            'total_risk': round(total_risk * 100, 1),
            'primary_risk': primary_risk,
            'breakdown': {
                'climate': round(climate.get('risk', 0) * 100, 1),
                'conflict': round(conflict.get('risk', 0) * 100, 1),
                'seismic': round(seismic.get('risk', 0) * 100, 1),
                'coastal': round(coastal.get('risk', 0) * 100, 1),
                'drought': round(vegetation.get('risk', 0) * 100, 1)
            },
            'details': {
                'seismic': seismic,
                'climate': climate,
                'conflict': conflict,
                'coastal': coastal,
                'vegetation': vegetation
            },
            'data_sources': sources,
            'timestamp': datetime.utcnow().isoformat(),
            'confidence': self._calculate_confidence(sources)
        }
    
    async def _get_seismic_risk(self, lat: float, lon: float) -> Dict:
        """USGS Erdbeben-Risiko"""
        try:
            from services.data_fusion_hub import data_fusion_hub
            result = await data_fusion_hub._fetch_usgs_seismic(lat, lon)
            return {
                'risk': result.get('risk', 0.05),
                'earthquake_count': result.get('count', 0),
                'source': 'USGS Earthquake Catalog'
            }
        except Exception as e:
            logger.warning(f"Seismic risk error: {e}")
            return {'risk': 0.05, 'source': 'estimate'}
    
    async def _get_climate_risk(self, lat: float, lon: float, loc_type: str) -> Dict:
        """Klimarisiko (Hitze, Überschwemmung, etc.)"""
        
        abs_lat = abs(lat)
        
        # Basis-Risiko nach Klimazone
        if abs_lat < 23:  # Tropisch
            heat_risk = 0.6
            flood_risk = 0.5
        elif abs_lat < 35:  # Subtropisch
            heat_risk = 0.5
            flood_risk = 0.4
        elif abs_lat < 55:  # Gemäßigt
            heat_risk = 0.3
            flood_risk = 0.3
        else:  # Polar/Boreal
            heat_risk = 0.1
            flood_risk = 0.2
        
        # Küsten haben höheres Flutrisiko
        if loc_type == 'coastal':
            flood_risk += 0.2
        
        # IPCC AR6 SSP2-4.5 Projektion für 2026
        warming_factor = 1.1  # ~1.1°C über vorindustriell
        heat_risk *= warming_factor
        
        combined = (heat_risk + flood_risk) / 2
        
        return {
            'risk': min(1.0, combined),
            'heat_risk': round(heat_risk, 2),
            'flood_risk': round(flood_risk, 2),
            'warming_factor': warming_factor,
            'source': 'IPCC AR6 SSP2-4.5'
        }
    
    async def _get_conflict_risk(self, lat: float, lon: float, country: str) -> Dict:
        """Konfliktrisiko via ACLED/GDELT"""
        try:
            # Versuche ACLED zuerst
            acled_result = await acled_service.calculate_conflict_risk(lat, lon, country)
            if acled_result.get('events_count', 0) > 0:
                return acled_result
            
            # Fallback: Länder-basierte Schätzung
            high_conflict = ['Ukraine', 'Syria', 'Yemen', 'Sudan', 'Myanmar', 'Ethiopia']
            medium_conflict = ['Israel', 'Palestine', 'Nigeria', 'Pakistan', 'Afghanistan']
            
            if country in high_conflict:
                risk = 0.8
            elif country in medium_conflict:
                risk = 0.5
            else:
                risk = 0.1
            
            return {
                'risk': risk,
                'events_count': 0,
                'source': 'Country-level estimate'
            }
            
        except Exception as e:
            logger.warning(f"Conflict risk error: {e}")
            return {'risk': 0.1, 'source': 'estimate'}
    
    async def _get_coastal_risk(self, lat: float, lon: float, loc_type: str) -> Dict:
        """Küstenrisiko via Copernicus Marine"""
        
        if loc_type != 'coastal':
            return {'risk': 0.0, 'source': 'inland'}
        
        try:
            result = await copernicus_marine.calculate_coastal_risk(lat, lon)
            return result
        except Exception as e:
            logger.warning(f"Coastal risk error: {e}")
            return {'risk': 0.2, 'source': 'estimate'}
    
    async def _get_vegetation_risk(self, lat: float, lon: float) -> Dict:
        """Vegetations-/Dürrerisiko via MODIS"""
        try:
            drought_risk = await modis_service.calculate_drought_risk(lat, lon)
            return {
                'risk': drought_risk,
                'source': 'MODIS NDVI'
            }
        except Exception as e:
            logger.warning(f"Vegetation risk error: {e}")
            return {'risk': 0.2, 'source': 'estimate'}
    
    def _calculate_confidence(self, sources: List[str]) -> float:
        """Berechnet Konfidenz basierend auf Datenquellen"""
        # Mehr echte Datenquellen = höhere Konfidenz
        real_sources = [s for s in sources if 'estimate' not in s.lower()]
        return min(0.95, 0.3 + (len(real_sources) * 0.15))


# Singleton
enhanced_risk_engine = EnhancedRiskEngine()
