"""
ACLED Conflict Data Service
Punkt-genaue Konfliktdaten weltweit
Docs: https://acleddata.com/api-documentation/
"""

import os
import httpx
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from loguru import logger

# ACLED Credentials - via Environment oder hier setzen
ACLED_EMAIL = os.environ.get('ACLED_EMAIL', '')
ACLED_PASSWORD = os.environ.get('ACLED_PASSWORD', '')
ACLED_TOKEN_URL = "https://acleddata.com/oauth/token"
ACLED_API_URL = "https://acleddata.com/api/acled/read"

@dataclass
class ConflictEvent:
    """Ein ACLED Konfliktereignis"""
    event_id: str
    event_date: str
    event_type: str
    sub_event_type: str
    actor1: str
    actor2: str
    country: str
    admin1: str  # Region
    location: str
    latitude: float
    longitude: float
    fatalities: int
    notes: str


class ACLEDService:
    """
    ACLED - Armed Conflict Location & Event Data
    Liefert punkt-genaue Konfliktdaten weltweit
    """
    
    def __init__(self, email: str = None, password: str = None):
        self.email = email or ACLED_EMAIL
        self.password = password or ACLED_PASSWORD
        self.access_token = None
        self.token_expires = None
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def _get_token(self) -> Optional[str]:
        """OAuth Token von ACLED holen"""
        if not self.email or not self.password:
            logger.warning("ACLED Credentials nicht gesetzt")
            return None
        
        # Check if token still valid
        if self.access_token and self.token_expires:
            if datetime.utcnow() < self.token_expires:
                return self.access_token
        
        try:
            response = await self.client.post(
                ACLED_TOKEN_URL,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                data={
                    'username': self.email,
                    'password': self.password,
                    'grant_type': 'password',
                    'client_id': 'acled'
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data['access_token']
                # Token expires in 1 hour, refresh after 50 min
                self.token_expires = datetime.utcnow() + timedelta(minutes=50)
                logger.info("✅ ACLED Token erhalten")
                return self.access_token
            else:
                logger.error(f"ACLED Token Fehler: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"ACLED Token Exception: {e}")
            return None
    
    async def get_conflicts_for_country(self, country: str, year: int = 2024) -> List[ConflictEvent]:
        """Alle Konflikte für ein Land abrufen"""
        
        token = await self._get_token()
        if not token:
            return []
        
        try:
            response = await self.client.get(
                f"{ACLED_API_URL}?_format=json",
                params={
                    'country': country,
                    'year': year,
                    'fields': 'event_id_cnty|event_date|event_type|sub_event_type|actor1|actor2|country|admin1|location|latitude|longitude|fatalities|notes'
                },
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 200:
                    events = []
                    for row in data.get('data', []):
                        events.append(ConflictEvent(
                            event_id=row.get('event_id_cnty', ''),
                            event_date=row.get('event_date', ''),
                            event_type=row.get('event_type', ''),
                            sub_event_type=row.get('sub_event_type', ''),
                            actor1=row.get('actor1', ''),
                            actor2=row.get('actor2', ''),
                            country=row.get('country', ''),
                            admin1=row.get('admin1', ''),
                            location=row.get('location', ''),
                            latitude=float(row.get('latitude', 0) or 0),
                            longitude=float(row.get('longitude', 0) or 0),
                            fatalities=int(row.get('fatalities', 0) or 0),
                            notes=row.get('notes', '')
                        ))
                    logger.info(f"✅ ACLED: {len(events)} Konflikte für {country}")
                    return events
            
            return []
            
        except Exception as e:
            logger.error(f"ACLED Fetch Exception: {e}")
            return []
    
    async def get_conflicts_near_location(
        self, 
        lat: float, 
        lon: float, 
        radius_km: float = 100,
        year: int = 2024
    ) -> List[ConflictEvent]:
        """Konflikte in der Nähe einer Koordinate"""
        
        # ACLED hat keine direkte Geo-Query, daher:
        # 1. Land aus Koordinaten ermitteln
        # 2. Alle Events für Land holen
        # 3. Nach Entfernung filtern
        
        # Vereinfacht: Bounding Box berechnen
        # 1° ≈ 111km am Äquator
        deg_offset = radius_km / 111
        
        # Hier würden wir normalerweise alle Events im Bereich filtern
        # Für jetzt geben wir leere Liste zurück wenn kein Token
        return []
    
    async def calculate_conflict_risk(self, lat: float, lon: float, country: str = "") -> Dict:
        """Berechnet Konfliktrisiko basierend auf ACLED Daten"""
        
        events = await self.get_conflicts_for_country(country) if country else []
        
        if not events:
            return {
                'risk': 0.05,  # Base risk
                'events_count': 0,
                'fatalities_total': 0,
                'source': 'ACLED (no data)'
            }
        
        # Berechne Risiko basierend auf:
        # - Anzahl Events
        # - Todesfälle
        # - Entfernung zu Ereignissen
        
        total_fatalities = sum(e.fatalities for e in events)
        event_count = len(events)
        
        # Risiko-Formel: normalisiert auf 0-1
        risk = min(1.0, (event_count / 1000) + (total_fatalities / 10000))
        
        return {
            'risk': risk,
            'events_count': event_count,
            'fatalities_total': total_fatalities,
            'source': 'ACLED 2024'
        }
    
    async def close(self):
        await self.client.aclose()


# Singleton
acled_service = ACLEDService()
