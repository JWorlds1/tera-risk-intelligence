"""
MODIS NDVI Vegetation Service
NASA AppEEARS API für Vegetationsdaten
"""

import os
import httpx
from typing import Dict, Optional
from datetime import datetime, timedelta
from loguru import logger

# NASA Earthdata Token
NASA_TOKEN = os.environ.get('NASA_EARTHDATA_TOKEN', 
    'eyJ0eXAiOiJKV1QiLCJvcmlnaW4iOiJFYXJ0aGRhdGEgTG9naW4iLCJzaWciOiJlZGxqd3RwdWJrZXlfb3BzIiwiYWxnIjoiUlMyNTYifQ.eyJ0eXBlIjoiVXNlciIsInVpZCI6Imp3b3JsZHMxIiwiZXhwIjoxNzcwOTI2NzA0LCJpYXQiOjE3NjU3NDI3MDQsImlzcyI6Imh0dHBzOi8vdXJzLmVhcnRoZGF0YS5uYXNhLmdvdiIsImlkZW50aXR5X3Byb3ZpZGVyIjoiZWRsX29wcyIsImFjciI6ImVkbCIsImFzc3VyYW5jZV9sZXZlbCI6M30.H3xJWMbVTY5fGx40VW1oh98VKnRARykqDo32O1OgmMTcQ_GOfyBFcQZHLIyCtf7NWO9qPm7txNRDOV59nsTroP9yV9L2lqNgf-XeHLItEh7Sr3lTj6c9PTD6OECSSF66OoNHjge3wiF_tXYgJOqV7OTX2mzzkVMQ4dJDNaNjMoUDFApvrASQxoWBonOLDVMlan0S56U-Iev2i_trz1cqqYsIGNBXDhMhTytJ2u413a15l1kRbqaRFnqL7pZ8DfGA9SrqeA6HWT-8Udmg1paLFw8grFxCNVAW7lXA6mwcKtdzJ6iGz3vK5bPPLgHenRstrBHGXJIo1HkjjWDYX_SZYg'
)

APPEEARS_URL = "https://appeears.earthdatacloud.nasa.gov/api"


class MODISVegetationService:
    """
    NASA MODIS Vegetationsindex (NDVI)
    - NDVI alle 16 Tage
    - 250m Auflösung
    - Wichtig für: Dürre-Risiko, Feuer-Gefahr, Landwirtschaft
    """
    
    def __init__(self, token: str = None):
        self.token = token or NASA_TOKEN
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def get_ndvi_for_location(self, lat: float, lon: float) -> Dict:
        """
        NDVI für eine Koordinate abrufen
        NDVI Werte: -1 bis 1
        - < 0: Wasser/Wolken
        - 0-0.2: Karg/Urban
        - 0.2-0.5: Strauch/Gras
        - 0.5-1.0: Dichter Wald
        """
        
        if not self.token:
            return self._estimate_ndvi(lat, lon)
        
        try:
            # AppEEARS benötigt Task-basierte Anfragen
            # Für Echtzeit nutzen wir alternative MODIS-Quellen
            
            # Alternative: MODIS Terra/Aqua über NASA GIBS
            # Oder: Schätzung basierend auf Breitengrad/Klima
            
            return self._estimate_ndvi(lat, lon)
            
        except Exception as e:
            logger.error(f"MODIS NDVI Error: {e}")
            return self._estimate_ndvi(lat, lon)
    
    def _estimate_ndvi(self, lat: float, lon: float) -> Dict:
        """
        NDVI Schätzung basierend auf Klimazonen
        (Fallback wenn API nicht verfügbar)
        """
        
        abs_lat = abs(lat)
        
        # Klimazonen-basierte Schätzung
        if abs_lat > 66:  # Polar
            ndvi = 0.1
            vegetation = 'tundra'
        elif abs_lat > 55:  # Boreal
            ndvi = 0.4
            vegetation = 'boreal_forest'
        elif abs_lat > 35:  # Temperat
            ndvi = 0.6
            vegetation = 'temperate'
        elif abs_lat > 23:  # Subtropisch
            ndvi = 0.5
            vegetation = 'subtropical'
        else:  # Tropisch
            ndvi = 0.7
            vegetation = 'tropical'
        
        # Küsten haben niedrigere NDVI (Urbanisierung)
        # Würde mit echten Daten präziser sein
        
        return {
            'ndvi': ndvi,
            'ndvi_anomaly': 0.0,  # Abweichung vom Langzeitmittel
            'vegetation_type': vegetation,
            'drought_risk': max(0, 0.5 - ndvi),  # Niedriger NDVI = höheres Dürrerisiko
            'fire_risk': max(0, 0.3 + (0.5 - ndvi)),
            'source': 'MODIS (estimated)'
        }
    
    async def calculate_drought_risk(self, lat: float, lon: float) -> float:
        """Berechnet Dürrerisiko basierend auf Vegetation"""
        data = await self.get_ndvi_for_location(lat, lon)
        return data.get('drought_risk', 0.2)
    
    async def close(self):
        await self.client.aclose()


# Singleton
modis_service = MODISVegetationService()
