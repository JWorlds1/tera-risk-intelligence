# ai_agents.py - LangChain AI Agents für intelligente Extraktion
import asyncio
from typing import Dict, List, Optional, Any, Type
from datetime import datetime
import structlog
from pydantic import BaseModel, Field
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseLanguageModel
# Lokale LLMs entfernt - verwende OpenAI API stattdessen
# from langchain_community.llms import Ollama
# from langchain_community.llms import LlamaCpp
from openai import OpenAI
import os
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.pydantic_v1 import BaseModel as LangChainBaseModel
import firecrawl
import json

from schemas import PageRecord, NASARecord, UNPressRecord, WFPRecord, WorldBankRecord
from config import Config

logger = structlog.get_logger(__name__)


class ClimateConflictAnalysis(LangChainBaseModel):
    """Strukturierte Analyse für Klima-Konflikt-Daten"""
    climate_indicators: List[str] = Field(description="Klima-Indikatoren wie Dürre, Überschwemmung, Temperatur")
    conflict_indicators: List[str] = Field(description="Konflikt-Indikatoren wie Gewalt, Vertreibung, Krise")
    risk_level: str = Field(description="Risikostufe: niedrig, mittel, hoch, kritisch")
    affected_regions: List[str] = Field(description="Betroffene Regionen/Länder")
    urgency_score: int = Field(description="Dringlichkeits-Score 1-10")
    key_entities: List[str] = Field(description="Wichtige Entitäten: Organisationen, Personen, Orte")
    summary: str = Field(description="Zusammenfassung der wichtigsten Punkte")
    recommendations: List[str] = Field(description="Handlungsempfehlungen")


class FirecrawlAgent:
    """Firecrawl Agent für erweiterte Web-Extraktion"""
    
    def __init__(self, api_key: str):
        self.client = firecrawl.FirecrawlApp(api_key=api_key)
        self.stats = {
            'crawls_completed': 0,
            'pages_processed': 0,
            'extraction_errors': 0
        }
    
    async def extract_page(self, url: str, extract_schema: Optional[Dict] = None) -> Dict[str, Any]:
        """Extrahiere Seite mit Firecrawl"""
        try:
            # Firecrawl Scrape mit strukturierter Extraktion
            scrape_result = self.client.scrape_url(
                url=url,
                params={
                    'formats': ['markdown', 'html'],
                    'extract': extract_schema or self._get_default_schema(),
                    'onlyMainContent': True,
                    'waitFor': 3000  # 3 Sekunden warten für dynamischen Content
                }
            )
            
            self.stats['crawls_completed'] += 1
            self.stats['pages_processed'] += 1
            
            return {
                'success': True,
                'content': scrape_result.get('markdown', ''),
                'html': scrape_result.get('html', ''),
                'metadata': scrape_result.get('metadata', {}),
                'extracted_data': scrape_result.get('extract', {}),
                'url': url
            }
            
        except Exception as e:
            logger.error(f"Firecrawl extraction failed for {url}: {e}")
            self.stats['extraction_errors'] += 1
            return {
                'success': False,
                'error': str(e),
                'url': url
            }
    
    def _get_default_schema(self) -> Dict[str, Any]:
        """Standard-Extraktionsschema für Klima-Konflikt-Daten"""
        return {
            "title": {
                "type": "string",
                "description": "Titel des Artikels"
            },
            "summary": {
                "type": "string", 
                "description": "Zusammenfassung des Inhalts"
            },
            "publish_date": {
                "type": "string",
                "description": "Veröffentlichungsdatum"
            },
            "region": {
                "type": "string",
                "description": "Geografische Region"
            },
            "climate_keywords": {
                "type": "array",
                "description": "Klima-bezogene Schlüsselwörter"
            },
            "conflict_keywords": {
                "type": "array", 
                "description": "Konflikt-bezogene Schlüsselwörter"
            },
            "organizations": {
                "type": "array",
                "description": "Erwähnte Organisationen"
            },
            "countries": {
                "type": "array",
                "description": "Erwähnte Länder"
            }
        }


class OpenAILLMManager:
    """Manager für OpenAI LLMs - Ersetzt lokale LLMs"""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = None
        self._initialize_openai()
    
    def _initialize_openai(self):
        """Initialisiere OpenAI Client"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OPENAI_API_KEY nicht gesetzt - OpenAI nicht verfügbar")
                return
            
            self.client = OpenAI(api_key=api_key)
            logger.info("OpenAI Client initialisiert")
            
        except Exception as e:
            logger.warning(f"OpenAI nicht verfügbar: {e}")
            self.client = None
    
    def get_model(self, model_name: str = "gpt-4o-mini"):
        """Hole OpenAI Modell (kompatibel mit LangChain)"""
        if not self.client:
            return None
        
        # Verwende ChatOpenAI für LangChain-Kompatibilität
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=model_name,
                temperature=0.1,
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
        except ImportError:
            # Fallback wenn langchain_openai nicht verfügbar
            logger.warning("langchain_openai nicht verfügbar - verwende direkten OpenAI Client")
            return self.client
    
    def get_available_models(self) -> List[str]:
        """Liste verfügbare OpenAI Modelle"""
        return ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]


class ClimateConflictAgent:
    """LangChain Agent für Klima-Konflikt-Analyse"""
    
    def __init__(self, config: Config, firecrawl_api_key: str):
        self.config = config
        self.llm_manager = OpenAILLMManager(config)  # Verwende OpenAI statt lokale LLMs
        self.firecrawl_agent = FirecrawlAgent(firecrawl_api_key)
        self.parser = PydanticOutputParser(pydantic_object=ClimateConflictAnalysis)
        
        # Tools für den Agent
        self.tools = self._create_tools()
        
        # Prompt Template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("human", "Analysiere diesen Text auf Klima-Konflikt-Zusammenhänge:\n\n{text}\n\n{format_instructions}")
        ])
    
    def _get_system_prompt(self) -> str:
        """System-Prompt für den AI-Agenten"""
        return """
Du bist ein Experte für Klima-Konflikt-Analyse. Deine Aufgabe ist es, Texte auf Zusammenhänge zwischen Klimawandel und Konflikten zu analysieren.

Analysiere den gegebenen Text und extrahiere:
1. Klima-Indikatoren (Dürre, Überschwemmung, Temperatur, etc.)
2. Konflikt-Indikatoren (Gewalt, Vertreibung, Krise, etc.)
3. Betroffene Regionen und Länder
4. Risikobewertung und Dringlichkeit
5. Wichtige Entitäten und Organisationen
6. Handlungsempfehlungen

Sei präzise und fokussiere auf messbare Indikatoren.
"""
    
    def _create_tools(self) -> List[Tool]:
        """Erstelle Tools für den LangChain Agent"""
        return [
            Tool(
                name="extract_entities",
                description="Extrahiere wichtige Entitäten aus Text",
                func=self._extract_entities
            ),
            Tool(
                name="assess_risk",
                description="Bewerte das Risiko basierend auf Indikatoren",
                func=self._assess_risk
            ),
            Tool(
                name="identify_regions",
                description="Identifiziere betroffene Regionen",
                func=self._identify_regions
            )
        ]
    
    def _extract_entities(self, text: str) -> str:
        """Extrahiere Entitäten aus Text"""
        # Einfache Entitäts-Extraktion
        import re
        
        # Organisationen
        orgs = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        # Länder/Regionen
        regions = re.findall(r'\b(?:Africa|Asia|Europe|America|Middle East|Horn of Africa)\b', text, re.IGNORECASE)
        
        return f"Organisationen: {orgs[:5]}, Regionen: {regions[:5]}"
    
    def _assess_risk(self, indicators: str) -> str:
        """Bewerte Risiko basierend auf Indikatoren"""
        high_risk_keywords = ['crisis', 'emergency', 'disaster', 'conflict', 'violence', 'displacement']
        medium_risk_keywords = ['concern', 'warning', 'alert', 'drought', 'flood']
        
        indicators_lower = indicators.lower()
        high_count = sum(1 for keyword in high_risk_keywords if keyword in indicators_lower)
        medium_count = sum(1 for keyword in medium_risk_keywords if keyword in indicators_lower)
        
        if high_count >= 3:
            return "KRITISCH - Hohe Anzahl kritischer Indikatoren"
        elif high_count >= 1 or medium_count >= 3:
            return "HOCH - Mehrere Warnsignale"
        elif medium_count >= 1:
            return "MITTEL - Einige Warnsignale"
        else:
            return "NIEDRIG - Wenige Warnsignale"
    
    def _identify_regions(self, text: str) -> str:
        """Identifiziere betroffene Regionen"""
        regions = []
        region_keywords = [
            'East Africa', 'West Africa', 'Central Africa', 'Southern Africa',
            'North Africa', 'Sub-Saharan Africa', 'Horn of Africa',
            'Middle East', 'South Asia', 'Southeast Asia', 'East Asia',
            'Central Asia', 'Latin America', 'Caribbean', 'Central America',
            'South America', 'North America', 'Europe', 'Oceania'
        ]
        
        text_lower = text.lower()
        for region in region_keywords:
            if region.lower() in text_lower:
                regions.append(region)
        
        return f"Identifizierte Regionen: {regions}"
    
    async def analyze_text(self, text: str, model_name: str = "gpt-4o-mini") -> Optional[ClimateConflictAnalysis]:
        """Analysiere Text mit AI-Agent (OpenAI)"""
        try:
            model = self.llm_manager.get_model(model_name)
            if not model:
                logger.warning(f"OpenAI Modell {model_name} nicht verfügbar - prüfe OPENAI_API_KEY")
                return None
            
            # Erstelle Agent
            agent = create_tool_calling_agent(model, self.tools, self.prompt)
            agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
            
            # Führe Analyse durch
            result = await agent_executor.ainvoke({
                "text": text,
                "format_instructions": self.parser.get_format_instructions()
            })
            
            # Parse Ergebnis
            analysis = self.parser.parse(result["output"])
            return analysis
            
        except Exception as e:
            logger.error(f"AI-Analyse fehlgeschlagen: {e}")
            return None
    
    async def extract_with_ai(self, url: str, model_name: str = "gpt-4o-mini") -> Optional[ClimateConflictAnalysis]:
        """Extrahiere und analysiere URL mit AI"""
        try:
            # Firecrawl Extraktion
            firecrawl_result = await self.firecrawl_agent.extract_page(url)
            
            if not firecrawl_result['success']:
                logger.error(f"Firecrawl Extraktion fehlgeschlagen: {firecrawl_result.get('error')}")
                return None
            
            # AI-Analyse
            content = firecrawl_result.get('content', '')
            if not content:
                logger.warning(f"Kein Inhalt extrahiert von {url}")
                return None
            
            analysis = await self.analyze_text(content, model_name)
            return analysis
            
        except Exception as e:
            logger.error(f"AI-Extraktion fehlgeschlagen für {url}: {e}")
            return None


class EnhancedExtractor:
    """Erweiterte Extraktion mit AI-Unterstützung"""
    
    def __init__(self, config: Config, firecrawl_api_key: str):
        self.config = config
        self.ai_agent = ClimateConflictAgent(config, firecrawl_api_key)
        self.stats = {
            'ai_extractions': 0,
            'ai_successes': 0,
            'ai_failures': 0
        }
    
    async def extract_with_ai_support(self, url: str, source_name: str) -> Optional[PageRecord]:
        """Extrahiere mit AI-Unterstützung"""
        try:
            # AI-Analyse
            analysis = await self.ai_agent.extract_with_ai(url)
            
            if not analysis:
                self.stats['ai_failures'] += 1
                return None
            
            self.stats['ai_extractions'] += 1
            self.stats['ai_successes'] += 1
            
            # Erstelle PageRecord basierend auf AI-Analyse
            record = self._create_record_from_analysis(url, source_name, analysis)
            return record
            
        except Exception as e:
            logger.error(f"AI-unterstützte Extraktion fehlgeschlagen: {e}")
            self.stats['ai_failures'] += 1
            return None
    
    def _create_record_from_analysis(self, url: str, source_name: str, analysis: ClimateConflictAnalysis) -> PageRecord:
        """Erstelle PageRecord aus AI-Analyse"""
        # Bestimme Schema basierend auf Quelle
        schema_map = {
            "NASA": NASARecord,
            "UN Press": UNPressRecord,
            "WFP": WFPRecord,
            "World Bank": WorldBankRecord
        }
        
        record_class = schema_map.get(source_name, PageRecord)
        
        # Erstelle Record
        record_data = {
            'url': url,
            'source_domain': url.split('/')[2],
            'source_name': source_name,
            'fetched_at': datetime.now(),
            'title': analysis.summary[:100] if analysis.summary else None,
            'summary': analysis.summary,
            'publish_date': None,  # Wird von AI nicht extrahiert
            'region': ', '.join(analysis.affected_regions) if analysis.affected_regions else None,
            'topics': analysis.climate_indicators + analysis.conflict_indicators,
            'content_type': 'ai-analyzed',
            'language': 'en'
        }
        
        # Füge AI-spezifische Felder hinzu
        if record_class == NASARecord:
            record_data['environmental_indicators'] = analysis.climate_indicators
        elif record_class == UNPressRecord:
            record_data['meeting_coverage'] = 'meeting' in analysis.summary.lower()
            record_data['security_council'] = 'security council' in analysis.summary.lower()
        elif record_class == WFPRecord:
            record_data['crisis_type'] = analysis.conflict_indicators[0] if analysis.conflict_indicators else None
        elif record_class == WorldBankRecord:
            record_data['country'] = analysis.affected_regions[0] if analysis.affected_regions else None
            record_data['sector'] = 'climate' if analysis.climate_indicators else 'conflict'
        
        return record_class(**record_data)
    
    def get_stats(self) -> Dict[str, Any]:
        """Hole Statistiken"""
        return {
            **self.stats,
            'ai_success_rate': self.stats['ai_successes'] / max(self.stats['ai_extractions'], 1),
            'available_models': self.ai_agent.llm_manager.get_available_models()
        }
