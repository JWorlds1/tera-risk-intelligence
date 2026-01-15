"""
TERA Realtime Intelligence Service
Firecrawl + Ollama Integration für aktuelle Datenanalyse
"""
import httpx
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from loguru import logger


class RealtimeIntelligenceService:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.ollama_model = "llama3.1:8b"
    
    async def get_realtime_context(
        self,
        location: str,
        country: str,
        risk_type: str,
        lat: float,
        lon: float
    ) -> Dict[str, Any]:
        logger.info(f"🔍 Realtime Intelligence für {location}, {country} ({risk_type})")
        
        raw_data = await self._fetch_current_data(location, country, risk_type)
        
        if not raw_data:
            return self._fallback(location)
        
        # LLM-Interpretation
        try:
            interpretation = await self._interpret_with_llm(raw_data, location, risk_type)
            if interpretation:
                return interpretation
        except Exception as e:
            logger.error(f"LLM error: {e}")
        
        # Fallback ohne LLM
        return {
            'realtime_assessment': f'{len(raw_data)} aktuelle Berichte für {location} gefunden',
            'trend': 'unbekannt',
            'risk_adjustment': 0.0,
            'current_events': [d.get('title', '')[:100] for d in raw_data[:3]],
            'recommendation': 'Aktuelle Entwicklung beobachten',
            'sources': list(set(d.get('source', '') for d in raw_data)),
            'llm_model': 'none',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _fetch_current_data(self, location: str, country: str, risk_type: str) -> List[Dict]:
        results = []
        
        # Wikipedia aktuelle Ereignisse (immer verfügbar)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    'https://en.wikipedia.org/api/rest_v1/page/summary/' + location.replace(' ', '_')
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results.append({
                        'source': 'Wikipedia',
                        'title': data.get('title', location),
                        'content': data.get('extract', '')[:500]
                    })
        except Exception as e:
            logger.warning(f"Wikipedia error: {e}")
        
        # USGS für seismische Gebiete
        if risk_type == 'seismic':
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get('https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson')
                    if resp.status_code == 200:
                        for eq in resp.json().get('features', [])[:3]:
                            props = eq['properties']
                            results.append({
                                'source': 'USGS',
                                'title': props.get('title', 'Erdbeben'),
                                'content': f"Magnitude {props.get('mag')} - {props.get('place')}"
                            })
            except Exception as e:
                logger.warning(f"USGS error: {e}")
        
        # OpenWeatherMap für Wetter (kostenlos)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f'https://wttr.in/{location}?format=j1'
                )
                if resp.status_code == 200:
                    data = resp.json()
                    current = data.get('current_condition', [{}])[0]
                    results.append({
                        'source': 'Weather',
                        'title': f"Wetter in {location}",
                        'content': f"Temperatur: {current.get('temp_C', '?')}°C, {current.get('weatherDesc', [{}])[0].get('value', 'unbekannt')}"
                    })
        except Exception as e:
            logger.warning(f"Weather error: {e}")
        
        # Newsdata.io (kostenlose News API mit Limit)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    'https://newsdata.io/api/1/news',
                    params={
                        'apikey': 'pub_12345',  # Public demo key
                        'q': location,
                        'language': 'en,de',
                        'size': 3
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for article in data.get('results', [])[:2]:
                        results.append({
                            'source': 'News',
                            'title': article.get('title', ''),
                            'content': article.get('description', '')[:200]
                        })
        except Exception as e:
            logger.warning(f"News API error: {e}")
        
        logger.info(f"📊 {len(results)} Echtzeit-Quellen gefunden")
        return results
    
    async def _interpret_with_llm(self, data: List[Dict], location: str, risk_type: str) -> Optional[Dict]:
        data_text = "\n".join([f"- {d['source']}: {d['title']} - {d.get('content', '')[:150]}" for d in data[:5]])
        
        prompt = f"""Analysiere diese aktuellen Informationen über {location} (Risikotyp: {risk_type}):

{data_text}

Gib eine kurze Risikoeinschätzung (1-2 Sätze) und sage ob der Trend "steigend", "stabil" oder "fallend" ist."""
        
        try:
            async with httpx.AsyncClient(timeout=45) as client:
                resp = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={'model': self.ollama_model, 'prompt': prompt, 'stream': False, 'options': {'temperature': 0.3}}
                )
                
                if resp.status_code == 200:
                    response_text = resp.json().get('response', '')
                    
                    trend = 'stabil'
                    response_lower = response_text.lower()
                    if any(w in response_lower for w in ['steigend', 'erhöht', 'zunehmend', 'verschlechtert', 'kritisch']):
                        trend = 'steigend'
                    elif any(w in response_lower for w in ['fallend', 'sinkt', 'verbessert', 'beruhigt']):
                        trend = 'fallend'
                    
                    risk_adj = 0.05 if trend == 'steigend' else (-0.03 if trend == 'fallend' else 0.0)
                    
                    return {
                        'realtime_assessment': response_text[:600],
                        'trend': trend,
                        'risk_adjustment': risk_adj,
                        'current_events': [d.get('title', '')[:80] for d in data[:3]],
                        'recommendation': 'Erhöhte Wachsamkeit' if trend == 'steigend' else 'Situation beobachten',
                        'sources': list(set(d.get('source', '') for d in data)),
                        'llm_model': self.ollama_model,
                        'timestamp': datetime.utcnow().isoformat()
                    }
        except Exception as e:
            logger.error(f"Ollama error: {e}")
        
        return None
    
    def _fallback(self, location: str) -> Dict[str, Any]:
        return {
            'realtime_assessment': f'Keine aktuellen Daten für {location} verfügbar',
            'trend': 'unbekannt',
            'risk_adjustment': 0.0,
            'current_events': [],
            'recommendation': 'Manuelle Prüfung empfohlen',
            'sources': [],
            'llm_model': 'fallback',
            'timestamp': datetime.utcnow().isoformat()
        }


realtime_service = RealtimeIntelligenceService()
