"""
TERA Firecrawl Agent Integration
Nutzt den Firecrawl /agent Endpoint für autonome Web-Recherche
Docs: https://docs.firecrawl.dev/features/agent
"""

import os
import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

# Firecrawl API - User muss Key setzen
FIRECRAWL_API_KEY = os.environ.get('FIRECRAWL_API_KEY', 'fc-a0b3b8aa31244c10b0f15b4f2d570ac7')
FIRECRAWL_AGENT_URL = "https://api.firecrawl.dev/v1/agent"

@dataclass
class FirecrawlResult:
    """Ergebnis einer Firecrawl Agent Anfrage"""
    success: bool
    data: Dict[str, Any]
    sources: List[str]
    credits_used: int
    query: str
    timestamp: datetime


class FirecrawlAgent:
    """
    Firecrawl Agent für autonome Web-Recherche
    
    Der Agent kann:
    - Ohne URLs arbeiten (nur Prompt)
    - Tief in Websites suchen
    - Strukturierte Daten extrahieren
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or FIRECRAWL_API_KEY
        self.client = httpx.AsyncClient(timeout=120.0)  # Agent kann länger dauern
        
    async def research_location_risks(self, location: str, risk_type: str = "climate") -> FirecrawlResult:
        """
        Recherchiert Risiken für einen Standort
        
        Args:
            location: Stadt oder Land
            risk_type: 'climate', 'conflict', 'economic', 'health'
        """
        
        if not self.api_key:
            logger.warning("Firecrawl API Key nicht gesetzt")
            return FirecrawlResult(
                success=False,
                data={},
                sources=[],
                credits_used=0,
                query="",
                timestamp=datetime.utcnow()
            )
        
        # Prompt für den Firecrawl Agent
        prompts = {
            'climate': f"""
                Find the latest climate risk data for {location}:
                - Current flooding risks and recent events
                - Heat wave projections for 2025-2030
                - Sea level rise impact (if coastal)
                - Recent extreme weather events
                Return structured data with sources.
            """,
            'conflict': f"""
                Find current conflict and security data for {location}:
                - Recent security incidents
                - Political stability indicators
                - Refugee/migration impacts
                - Armed conflict status
                Return structured data with dates and sources.
            """,
            'economic': f"""
                Find economic risk indicators for {location}:
                - GDP trends and forecasts
                - Unemployment rates
                - Infrastructure investment
                - Climate adaptation spending
            """,
            'health': f"""
                Find health risk data for {location}:
                - Disease outbreaks
                - Healthcare capacity
                - Air quality index
                - Water quality issues
            """
        }
        
        prompt = prompts.get(risk_type, prompts['climate'])
        
        # Schema für strukturierte Ausgabe
        schema = {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "risk_level": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                "risks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "severity": {"type": "number"},
                            "description": {"type": "string"},
                            "source": {"type": "string"},
                            "date": {"type": "string"}
                        }
                    }
                },
                "summary": {"type": "string"},
                "data_sources": {"type": "array", "items": {"type": "string"}}
            }
        }
        
        try:
            logger.info(f"🔥 Firecrawl Agent: Recherchiere {risk_type} für {location}...")
            
            response = await self.client.post(
                FIRECRAWL_AGENT_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": prompt.strip(),
                    "schema": schema
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Firecrawl Agent erfolgreich: {result.get('creditsUsed', 0)} Credits")
                
                return FirecrawlResult(
                    success=True,
                    data=result.get('data', {}),
                    sources=result.get('data', {}).get('data_sources', []),
                    credits_used=result.get('creditsUsed', 0),
                    query=prompt.strip()[:100],
                    timestamp=datetime.utcnow()
                )
            else:
                logger.warning(f"Firecrawl Agent Fehler: {response.status_code}")
                return FirecrawlResult(
                    success=False,
                    data={'error': response.text},
                    sources=[],
                    credits_used=0,
                    query=prompt.strip()[:100],
                    timestamp=datetime.utcnow()
                )
                
        except Exception as e:
            logger.error(f"Firecrawl Agent Exception: {e}")
            return FirecrawlResult(
                success=False,
                data={'error': str(e)},
                sources=[],
                credits_used=0,
                query="",
                timestamp=datetime.utcnow()
            )
    
    async def extract_from_urls(self, urls: List[str], prompt: str) -> FirecrawlResult:
        """
        Extrahiert Daten von spezifischen URLs
        """
        if not self.api_key:
            return FirecrawlResult(
                success=False, data={}, sources=urls,
                credits_used=0, query=prompt, timestamp=datetime.utcnow()
            )
        
        try:
            response = await self.client.post(
                FIRECRAWL_AGENT_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "urls": urls,
                    "prompt": prompt
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return FirecrawlResult(
                    success=True,
                    data=result.get('data', {}),
                    sources=urls,
                    credits_used=result.get('creditsUsed', 0),
                    query=prompt,
                    timestamp=datetime.utcnow()
                )
        except Exception as e:
            logger.error(f"Firecrawl extract error: {e}")
        
        return FirecrawlResult(
            success=False, data={}, sources=urls,
            credits_used=0, query=prompt, timestamp=datetime.utcnow()
        )
    
    async def close(self):
        await self.client.aclose()


# Singleton
firecrawl_agent = FirecrawlAgent()
