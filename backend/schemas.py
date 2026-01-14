# schemas.py - Strukturierte Datenmodelle für Extraktion
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class PageRecord(BaseModel):
    """Basis-Schema für gescrapte Seite"""
    url: str
    source_domain: str
    source_name: str  # NASA, UN, WFP, WorldBank
    fetched_at: datetime
    title: Optional[str] = None
    summary: Optional[str] = None
    publish_date: Optional[str] = Field(None, description="ISO-Date oder leeres Feld")
    region: Optional[str] = Field(None, description="Geografische Region wenn erkennbar")
    topics: List[str] = Field(default_factory=list, description="Themen/Tags")
    content_type: Optional[str] = None  # article, report, press-release
    language: str = "en"
    
    # Metadaten
    links: List[str] = Field(default_factory=list)
    image_urls: List[str] = Field(default_factory=list)
    
    # Optional: Extrakte für Analyse
    full_text: Optional[str] = Field(None, description="Volltext wenn verfügbar")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://earthobservatory.nasa.gov/article/123",
                "source_domain": "earthobservatory.nasa.gov",
                "source_name": "NASA",
                "fetched_at": "2025-10-25T10:00:00Z",
                "title": "Drought in East Africa",
                "summary": "Severe drought conditions...",
                "publish_date": "2025-10-20",
                "region": "East Africa",
                "topics": ["drought", "climate", "agriculture"],
                "content_type": "article"
            }
        }


class NASARecord(PageRecord):
    """Spezialisiertes Schema für NASA Earth Observatory"""
    environmental_indicators: List[str] = Field(default_factory=list)  # NDVI, temperature, etc.
    satellite_source: Optional[str] = None


class UNPressRecord(PageRecord):
    """Spezialisiertes Schema für UN Press"""
    meeting_coverage: Optional[bool] = False
    security_council: Optional[bool] = False
    speakers: List[str] = Field(default_factory=list)


class WFPRecord(PageRecord):
    """Spezialisiertes Schema für World Food Programme"""
    crisis_type: Optional[str] = None  # drought, conflict, displacement
    affected_population: Optional[str] = None


class WorldBankRecord(PageRecord):
    """Spezialisiertes Schema für World Bank"""
    country: Optional[str] = None
    sector: Optional[str] = None  # climate, agriculture, poverty, etc.
    project_id: Optional[str] = None


# Mapping von Domains zu spezialisierten Schemas
SCHEMA_MAP = {
    "earthobservatory.nasa.gov": NASARecord,
    "press.un.org": UNPressRecord,
    "wfp.org": WFPRecord,
    "worldbank.org": WorldBankRecord,
}

