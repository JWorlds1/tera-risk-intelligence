#!/usr/bin/env python3
"""
Mehrstufige Verarbeitungspipeline für Meta-Extraktion
- Stufe 1: Datensammlung (Crawling, Research, Berechnung)
- Stufe 2: Meta-Extraktion (Text, Zahlen, Bilder)
- Stufe 3: Vektorkontextraum-Erstellung
- Stufe 4: Sensorfusion
- Stufe 5: LLM-Inference & Predictions
- Stufe 6: Dynamische Updates & Frühwarnsystem
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import numpy as np
from dataclasses import dataclass, asdict
from enum import Enum

sys.path.append(str(Path(__file__).parent))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel

console = Console()

from optimized_crawler import OptimizedCrawler
from optimized_enrichment import OptimizedEnrichmentPipeline
from multimodal_vector_space import MultiModalVectorSpace, MultiModalChunk, SimilarityMetrics
from sensor_fusion import SensorFusionEngine, FusedDataPoint
from ipcc_context_engine import IPCCContextEngine
from data_extraction import NumberExtractor
from image_processing import ImageProcessor
from llm_predictions import LLMPredictor
from risk_scoring import RiskScorer


# Kritische europäische Städte - Fokus auf am stärksten betroffene
CRITICAL_EUROPEAN_CITIES = {
    "Barcelona": {
        "country_code": "ES",
        "coordinates": (41.3851, 2.1734),
        "risk_factors": {
            "heat_deaths": "high",
            "heat_waves": "extreme",
            "drought": "high",
            "sea_level_rise": "high"
        },
        "priority": 1
    },
    "Rome": {
        "country_code": "IT",
        "coordinates": (41.9028, 12.4964),
        "risk_factors": {
            "heat_deaths": "high",
            "floods": "high",
            "drought": "medium",
            "migration": "high"
        },
        "priority": 1
    },
    "Madrid": {
        "country_code": "ES",
        "coordinates": (40.4168, -3.7038),
        "risk_factors": {
            "heat_waves": "extreme",  # 41 Tage bis 2050
            "water_stress": "extreme",  # +65%
            "drought": "extreme"
        },
        "priority": 1
    },
    "Frankfurt": {
        "country_code": "DE",
        "coordinates": (50.1109, 8.6821),
        "risk_factors": {
            "heat_days": "high",  # +79% bis 2050
            "heavy_rain": "high",  # +38% bis 2050
            "floods": "medium"
        },
        "priority": 1
    },
    "Athens": {
        "country_code": "GR",
        "coordinates": (37.9838, 23.7275),
        "risk_factors": {
            "heat_waves": "extreme",
            "wildfires": "high",
            "migration": "high",
            "drought": "high"
        },
        "priority": 2
    },
    "Istanbul": {
        "country_code": "TR",
        "coordinates": (41.0082, 28.9784),
        "risk_factors": {
            "earthquakes": "high",
            "migration": "extreme",
            "climate_extremes": "high"
        },
        "priority": 2
    },
    "Paris": {
        "country_code": "FR",
        "coordinates": (48.8566, 2.3522),
        "risk_factors": {
            "heat_waves": "high",
            "floods": "high"
        },
        "priority": 2
    },
    "London": {
        "country_code": "GB",
        "coordinates": (51.5074, -0.1278),
        "risk_factors": {
            "floods": "high",
            "migration": "medium",
            "sea_level_rise": "medium"
        },
        "priority": 2
    }
}


class ProcessingStage(Enum):
    """Verarbeitungsstufen"""
    DATA_COLLECTION = "data_collection"
    META_EXTRACTION = "meta_extraction"
    VECTOR_CONTEXT = "vector_context"
    SENSOR_FUSION = "sensor_fusion"
    LLM_INFERENCE = "llm_inference"
    EARLY_WARNING = "early_warning"
    DYNAMIC_UPDATE = "dynamic_update"


@dataclass
class CityContext:
    """Kontext für eine kritische Stadt"""
    city_name: str
    country_code: str
    coordinates: Tuple[float, float]
    risk_factors: Dict[str, str]
    priority: int
    
    # Verarbeitete Daten
    text_chunks: List[str] = None
    numerical_data: Dict[str, float] = None
    image_urls: List[str] = None
    vector_chunks: List[MultiModalChunk] = None
    
    # Fusionierte Daten
    fused_data: Optional[FusedDataPoint] = None
    
    # Predictions
    llm_predictions: Dict[str, Any] = None
    
    # Frühwarn-Indikatoren
    early_warning_signals: List[Dict[str, Any]] = None
    
    # Update-Status
    last_update: datetime = None
    update_frequency_hours: int = 24
    
    def __post_init__(self):
        if self.text_chunks is None:
            self.text_chunks = []
        if self.numerical_data is None:
            self.numerical_data = {}
        if self.image_urls is None:
            self.image_urls = []
        if self.vector_chunks is None:
            self.vector_chunks = []
        if self.early_warning_signals is None:
            self.early_warning_signals = []
        if self.last_update is None:
            self.last_update = datetime.now()


class MultiStageProcessor:
    """Mehrstufige Verarbeitungspipeline"""
    
    def __init__(
        self,
        max_concurrent_crawl: int = 10,
        max_concurrent_enrich: int = 5
    ):
        self.crawler = None  # Wird async initialisiert
        self.enrichment_pipeline = OptimizedEnrichmentPipeline(max_concurrent_enrich)
        self.vector_space = MultiModalVectorSpace(embedding_dim=1536)
        self.sensor_fusion = SensorFusionEngine()
        self.ipcc_engine = IPCCContextEngine()
        self.number_extractor = NumberExtractor()
        self.image_processor = ImageProcessor()
        self.llm_predictor = LLMPredictor() if hasattr(LLMPredictor, '__init__') else None
        self.risk_scorer = RiskScorer()
        
        self.max_concurrent_crawl = max_concurrent_crawl
        self.city_contexts: Dict[str, CityContext] = {}
        
        # Initialisiere Stadt-Kontexte
        for city_name, city_data in CRITICAL_EUROPEAN_CITIES.items():
            self.city_contexts[city_name] = CityContext(
                city_name=city_name,
                country_code=city_data['country_code'],
                coordinates=city_data['coordinates'],
                risk_factors=city_data['risk_factors'],
                priority=city_data['priority']
            )
    
    async def stage_1_data_collection(
        self,
        city_name: str,
        city_context: CityContext
    ) -> Dict[str, Any]:
        """Stufe 1: Datensammlung (Crawling, Research, Berechnung)"""
        console.print(f"\n[bold cyan]📡 Stufe 1: Datensammlung für {city_name}[/bold cyan]")
        
        collection_results = {
            'crawled_urls': [],
            'research_data': [],
            'calculated_metrics': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # 1.1: Optimiertes Crawling
        if not self.crawler:
            self.crawler = OptimizedCrawler(max_concurrent=self.max_concurrent_crawl)
            await self.crawler.__aenter__()
        
        # URLs für diese Stadt
        urls = self._get_city_urls(city_name, city_context)
        
        try:
            # Crawle mit optimiertem Crawler
            crawl_result = await self.crawler.crawl_source_optimized(
                city_name,
                urls,
                max_articles=30
            )
            
            collection_results['crawled_urls'] = crawl_result.get('urls_discovered', [])
            collection_results['crawled_records'] = crawl_result.get('records_extracted', 0)
        
        except Exception as e:
            console.print(f"[yellow]⚠️  Crawling-Fehler: {e}[/yellow]")
        
        # 1.2: Research-Daten (Firecrawl Search) - Dynamische Suche
        try:
            # Nutze dynamische Suche wenn keine Daten gefunden
            from dynamic_data_search import DynamicDataSearcher
            
            dynamic_searcher = DynamicDataSearcher()
            await dynamic_searcher.__aenter__()
            
            search_result = await dynamic_searcher.search_until_found(
                location=city_name,
                country_code=city_context.country_code,
                location_type='city',
                max_iterations=15,
                min_data_threshold=3
            )
            
            # Verwende gefundene Daten
            if search_result['found']:
                collection_results['research_data'] = search_result['data'].get('records', [])
                collection_results['dynamic_search'] = {
                    'found': True,
                    'sources_searched': search_result['sources_searched'],
                    'total_searches': search_result['total_searches'],
                    'comprehensive_search': search_result['comprehensive_search']
                }
            else:
                # Keine Daten gefunden - markiere umfassende Suche
                collection_results['research_data'] = []
                collection_results['dynamic_search'] = {
                    'found': False,
                    'sources_searched': search_result['sources_searched'],
                    'total_searches': search_result['total_searches'],
                    'comprehensive_search': search_result['comprehensive_search'],
                    'note': 'Umfassende Suche durchgeführt - keine passenden Daten gefunden'
                }
                console.print(f"[yellow]⚠️  Keine Daten gefunden nach umfassender Suche[/yellow]")
            
            await dynamic_searcher.__aexit__(None, None, None)
        
        except Exception as e:
            console.print(f"[yellow]⚠️  Research-Fehler: {e}[/yellow]")
            # Fallback zu normaler Suche
            try:
                research_keywords = self._generate_research_keywords(city_name, city_context)
                search_results, _ = self.enrichment_pipeline.firecrawl_enricher.enrich_with_search(
                    keywords=research_keywords[:5],
                    region=city_name,
                    limit=10,
                    scrape_content=True,
                    categories=["research"]
                )
                collection_results['research_data'] = search_results
            except:
                collection_results['research_data'] = []
        
        # 1.3: Berechnete Metriken (basierend auf Risk Factors)
        calculated_metrics = self._calculate_city_metrics(city_context)
        collection_results['calculated_metrics'] = calculated_metrics
        
        return collection_results
    
    async def stage_2_meta_extraction(
        self,
        city_name: str,
        city_context: CityContext,
        collection_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Stufe 2: Meta-Extraktion (Text, Zahlen, Bilder)"""
        console.print(f"\n[bold cyan]🔍 Stufe 2: Meta-Extraktion für {city_name}[/bold cyan]")
        
        extraction_results = {
            'text_chunks': [],
            'numerical_data': {},
            'image_urls': [],
            'extracted_numbers': {}
        }
        
        # 2.1: Text-Extraktion
        all_text = []
        
        # Aus Research-Daten
        for research_item in collection_data.get('research_data', []):
            if research_item.get('markdown'):
                all_text.append(research_item['markdown'])
            if research_item.get('description'):
                all_text.append(research_item['description'])
        
        # Aus gecrawlten Records
        records = self.enrichment_pipeline.db.get_records(limit=100)
        city_records = [
            r for r in records
            if city_name.lower() in (r.get('region', '') or '').lower() or
               city_name.lower() in (r.get('title', '') or '').lower()
        ]
        
        for record in city_records:
            if record.get('title'):
                all_text.append(record['title'])
            if record.get('summary'):
                all_text.append(record['summary'])
            if record.get('full_text'):
                all_text.append(record['full_text'][:2000])  # Limit
        
        # Wenn keine Text-Daten gefunden, versuche dynamische Suche
        if not all_text:
            console.print(f"[yellow]⚠️  Keine Text-Daten gefunden, starte dynamische Suche...[/yellow]")
            try:
                from dynamic_data_search import DynamicDataSearcher
                
                dynamic_searcher = DynamicDataSearcher()
                await dynamic_searcher.__aenter__()
                
                search_result = await dynamic_searcher.search_until_found(
                    location=city_name,
                    country_code=city_context.country_code,
                    location_type='city',
                    max_iterations=10,
                    min_data_threshold=1  # Mindestens 1 Text-Chunk
                )
                
                if search_result['found']:
                    # Verwende gefundene Text-Daten
                    found_texts = search_result['data'].get('text_chunks', [])
                    all_text.extend(found_texts)
                    console.print(f"[green]✅ {len(found_texts)} Text-Chunks durch dynamische Suche gefunden[/green]")
                else:
                    console.print(f"[yellow]⚠️  Keine Text-Daten nach umfassender Suche gefunden[/yellow]")
                    extraction_results['search_note'] = 'Umfassende Suche durchgeführt - keine Text-Daten gefunden'
                
                await dynamic_searcher.__aexit__(None, None, None)
            
            except Exception as e:
                console.print(f"[yellow]⚠️  Dynamische Suche fehlgeschlagen: {e}[/yellow]")
        
        # KEINE Fallback-Daten - nur echte Daten verwenden
        extraction_results['text_chunks'] = all_text
        city_context.text_chunks = all_text
        
        # 2.2: Zahlen-Extraktion
        combined_text = " ".join(all_text)
        extracted_numbers = self.number_extractor.extract_all(combined_text)
        
        # Strukturiere numerische Daten
        numerical_data = {
            'temperatures': extracted_numbers.temperatures[:5] if extracted_numbers.temperatures else [],
            'precipitation': extracted_numbers.precipitation[:5] if extracted_numbers.precipitation else [],
            'population_numbers': extracted_numbers.population_numbers[:5] if extracted_numbers.population_numbers else [],
            'financial_amounts': extracted_numbers.financial_amounts[:5] if extracted_numbers.financial_amounts else [],
            'affected_people': extracted_numbers.affected_people if extracted_numbers.affected_people else None,
            'funding_amount': extracted_numbers.funding_amount if extracted_numbers.funding_amount else None
        }
        
        # Füge berechnete Metriken hinzu
        numerical_data.update(collection_data.get('calculated_metrics', {}))
        
        # KEINE Fallback-Daten - nur echte Daten verwenden
        extraction_results['numerical_data'] = numerical_data
        extraction_results['extracted_numbers'] = asdict(extracted_numbers)
        city_context.numerical_data = numerical_data
        
        # 2.3: Bild-Extraktion
        image_urls = []
        
        # Aus Research-Daten
        for research_item in collection_data.get('research_data', []):
            if research_item.get('images'):
                image_urls.extend(research_item['images'])
        
        # Aus Records
        for record in city_records:
            if record.get('images'):
                image_urls.extend(record['images'])
        
        # Wenn keine Bilder gefunden, versuche dynamische Suche
        if not image_urls:
            console.print(f"[yellow]⚠️  Keine Bilder gefunden, versuche dynamische Suche...[/yellow]")
            # Bilder werden normalerweise in Research-Daten gefunden
            # Wenn keine vorhanden, bleibt Liste leer
        
        # KEINE Fallback-Daten - nur echte Bilder verwenden
        extraction_results['image_urls'] = list(set(image_urls))  # Deduplizieren
        city_context.image_urls = list(set(image_urls))
        
        return extraction_results
    
    async def stage_3_vector_context(
        self,
        city_name: str,
        city_context: CityContext,
        extraction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Stufe 3: Vektorkontextraum-Erstellung"""
        console.print(f"\n[bold cyan]🧠 Stufe 3: Vektorkontextraum für {city_name}[/bold cyan]")
        
        vector_results = {
            'chunks_created': 0,
            'embeddings_generated': 0
        }
        
        # Erstelle Multi-Modal Chunks
        text_chunks = extraction_data.get('text_chunks', [])
        numerical_data = extraction_data.get('numerical_data', {})
        image_urls = extraction_data.get('image_urls', [])
        
        # Chunk Text (in sinnvolle Abschnitte)
        chunked_texts = self._chunk_text(text_chunks, chunk_size=1000, overlap=200)
        
        vector_chunks = []
        
        for i, text_chunk in enumerate(chunked_texts[:10]):  # Limit auf 10 Chunks
            chunk_id = f"{city_name}_{i}_{datetime.now().strftime('%Y%m%d')}"
            
            # Erstelle Multi-Modal Chunk
            chunk = MultiModalChunk(
                chunk_id=chunk_id,
                city=city_name,
                coordinates=city_context.coordinates,
                text_content=text_chunk,
                numerical_data=numerical_data,
                image_urls=image_urls[:5],  # Limit auf 5 Bilder pro Chunk
                sources=[f"collection_{city_name}"],
                timestamp=datetime.now()
            )
            
            # TODO: Generiere Embeddings (OpenAI, CLIP)
            # Für jetzt: Placeholder
            # chunk.text_embedding = await self._generate_text_embedding(text_chunk)
            # chunk.image_embeddings = await self._generate_image_embeddings(image_urls[:5])
            
            vector_chunks.append(chunk)
            self.vector_space.add_chunk(chunk)
        
        vector_results['chunks_created'] = len(vector_chunks)
        city_context.vector_chunks = vector_chunks
        
        return vector_results
    
    async def stage_4_sensor_fusion(
        self,
        city_name: str,
        city_context: CityContext
    ) -> Dict[str, Any]:
        """Stufe 4: Sensorfusion"""
        console.print(f"\n[bold cyan]🔀 Stufe 4: Sensorfusion für {city_name}[/bold cyan]")
        
        # Fusioniere Daten für diese Stadt
        fused_data = self.sensor_fusion.fuse_by_location(city_name)
        
        if not fused_data:
            # Fallback: Erstelle FusedDataPoint aus Stadt-Kontext
            fused_data = self._create_fused_data_from_context(city_name, city_context)
        
        city_context.fused_data = fused_data
        
        return {
            'fused_data': asdict(fused_data) if fused_data else {},
            'risk_score': fused_data.risk_score if fused_data else 0.0,
            'risk_level': fused_data.risk_level if fused_data else 'UNKNOWN'
        }
    
    async def stage_5_llm_inference(
        self,
        city_name: str,
        city_context: CityContext
    ) -> Dict[str, Any]:
        """Stufe 5: LLM-Inference & Predictions"""
        console.print(f"\n[bold cyan]🤖 Stufe 5: LLM-Inference für {city_name}[/bold cyan]")
        
        # Bereite Kontext für LLM vor
        llm_context = self._prepare_llm_context(city_name, city_context)
        
        # LLM-Predictions (falls verfügbar)
        predictions = {}
        
        if self.llm_predictor:
            try:
                predictions = await self.llm_predictor.predict(
                    context=llm_context,
                    city=city_name
                )
            except Exception as e:
                console.print(f"[yellow]⚠️  LLM-Prediction-Fehler: {e}[/yellow]")
        else:
            # Fallback: Basis-Predictions basierend auf Risk Factors
            predictions = self._generate_basic_predictions(city_context)
        
        city_context.llm_predictions = predictions
        
        return predictions
    
    async def stage_6_early_warning(
        self,
        city_name: str,
        city_context: CityContext
    ) -> Dict[str, Any]:
        """Stufe 6: Frühwarnsystem"""
        console.print(f"\n[bold cyan]⚠️  Stufe 6: Frühwarnsystem für {city_name}[/bold cyan]")
        
        warning_signals = []
        
        # Analysiere verschiedene Indikatoren
        fused_data = city_context.fused_data
        
        if fused_data:
            # 1. Risk Score Check
            if fused_data.risk_score > 0.7:
                warning_signals.append({
                    'type': 'HIGH_RISK',
                    'severity': 'HIGH',
                    'message': f"Hohes Risiko erkannt: {fused_data.risk_score:.2f}",
                    'indicators': fused_data.climate_indicators + fused_data.conflict_indicators
                })
            
            # 2. Urgency Check
            if fused_data.urgency > 0.6:
                warning_signals.append({
                    'type': 'HIGH_URGENCY',
                    'severity': 'MEDIUM',
                    'message': f"Hohe Dringlichkeit: {fused_data.urgency:.2f}",
                    'factors': {
                        'crisis_type': fused_data.crisis_type,
                        'affected_population': fused_data.affected_population
                    }
                })
            
            # 3. Trend Check
            if fused_data.trend == 'increasing':
                warning_signals.append({
                    'type': 'INCREASING_TREND',
                    'severity': 'MEDIUM',
                    'message': "Zunehmender Trend erkannt",
                    'data_sources': fused_data.data_sources_count
                })
        
        # 4. Risk Factors Check
        for risk_factor, level in city_context.risk_factors.items():
            if level in ['extreme', 'high']:
                warning_signals.append({
                    'type': f'RISK_FACTOR_{risk_factor.upper()}',
                    'severity': 'HIGH' if level == 'extreme' else 'MEDIUM',
                    'message': f"{risk_factor}: {level}",
                    'risk_factor': risk_factor,
                    'level': level
                })
        
        city_context.early_warning_signals = warning_signals
        
        return {
            'signals': warning_signals,
            'total_signals': len(warning_signals),
            'high_severity': sum(1 for s in warning_signals if s['severity'] == 'HIGH')
        }
    
    async def stage_7_dynamic_update(
        self,
        city_name: str,
        city_context: CityContext
    ) -> Dict[str, Any]:
        """Stufe 7: Dynamische Updates"""
        console.print(f"\n[bold cyan]🔄 Stufe 7: Dynamische Updates für {city_name}[/bold cyan]")
        
        # Prüfe ob Update nötig
        hours_since_update = (datetime.now() - city_context.last_update).total_seconds() / 3600
        
        if hours_since_update < city_context.update_frequency_hours:
            return {
                'update_needed': False,
                'hours_since_update': hours_since_update,
                'next_update_in_hours': city_context.update_frequency_hours - hours_since_update
            }
        
        # Update durchführen
        update_results = {
            'update_needed': True,
            'update_timestamp': datetime.now().isoformat(),
            'stages_executed': []
        }
        
        # Führe kritische Stufen erneut aus
        try:
            # Stufe 1: Neue Daten sammeln
            collection_data = await self.stage_1_data_collection(city_name, city_context)
            update_results['stages_executed'].append('data_collection')
            
            # Stufe 2: Meta-Extraktion
            extraction_data = await self.stage_2_meta_extraction(
                city_name, city_context, collection_data
            )
            update_results['stages_executed'].append('meta_extraction')
            
            # Stufe 4: Sensorfusion (aktualisiert)
            fusion_data = await self.stage_4_sensor_fusion(city_name, city_context)
            update_results['stages_executed'].append('sensor_fusion')
            
            # Stufe 6: Frühwarnsystem (neu evaluieren)
            warning_data = await self.stage_6_early_warning(city_name, city_context)
            update_results['stages_executed'].append('early_warning')
            
            city_context.last_update = datetime.now()
            
        except Exception as e:
            console.print(f"[red]❌ Update-Fehler: {e}[/red]")
            update_results['error'] = str(e)
        
        return update_results
    
    async def process_city_full_pipeline(
        self,
        city_name: str
    ) -> Dict[str, Any]:
        """Führe vollständige Pipeline für eine Stadt aus"""
        if city_name not in self.city_contexts:
            raise ValueError(f"Stadt {city_name} nicht gefunden")
        
        city_context = self.city_contexts[city_name]
        
        console.print(Panel.fit(
            f"[bold green]🚀 Mehrstufige Verarbeitung: {city_name}[/bold green]",
            border_style="green"
        ))
        
        results = {
            'city': city_name,
            'stages': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Stufe 1: Datensammlung
            collection_data = await self.stage_1_data_collection(city_name, city_context)
            results['stages']['data_collection'] = collection_data
            
            # Stufe 2: Meta-Extraktion
            extraction_data = await self.stage_2_meta_extraction(
                city_name, city_context, collection_data
            )
            results['stages']['meta_extraction'] = extraction_data
            
            # Stufe 3: Vektorkontextraum
            vector_data = await self.stage_3_vector_context(
                city_name, city_context, extraction_data
            )
            results['stages']['vector_context'] = vector_data
            
            # Stufe 4: Sensorfusion
            fusion_data = await self.stage_4_sensor_fusion(city_name, city_context)
            results['stages']['sensor_fusion'] = fusion_data
            
            # Stufe 5: LLM-Inference
            llm_data = await self.stage_5_llm_inference(city_name, city_context)
            results['stages']['llm_inference'] = llm_data
            
            # Stufe 6: Frühwarnsystem
            warning_data = await self.stage_6_early_warning(city_name, city_context)
            results['stages']['early_warning'] = warning_data
            
            # Zusammenfassung
            results['summary'] = {
                'text_chunks': len(city_context.text_chunks),
                'numerical_data_points': len(city_context.numerical_data),
                'images': len(city_context.image_urls),
                'vector_chunks': len(city_context.vector_chunks),
                'risk_score': city_context.fused_data.risk_score if city_context.fused_data else 0.0,
                'warning_signals': len(city_context.early_warning_signals)
            }
        
        except Exception as e:
            console.print(f"[red]❌ Pipeline-Fehler für {city_name}: {e}[/red]")
            results['error'] = str(e)
            import traceback
            results['traceback'] = traceback.format_exc()
        
        return results
    
    # Helper-Methoden
    
    def _get_city_urls(self, city_name: str, city_context: CityContext) -> List[str]:
        """Generiere URLs für eine Stadt oder ein Land"""
        urls = []
        
        # Basis-URLs
        country_code_lower = city_context.country_code.lower() if hasattr(city_context, 'country_code') else ''
        
        base_urls = [
            f"https://www.eea.europa.eu/themes/climate/urban-adaptation",
            f"https://climateknowledgeportal.worldbank.org/country/{country_code_lower}" if country_code_lower else "https://climateknowledgeportal.worldbank.org",
            f"https://interactive-atlas.ipcc.ch",
            f"https://www.unhcr.org/refugee-statistics",
            f"https://acleddata.com"
        ]
        
        urls.extend(base_urls)
        
        return urls
    
    def _generate_research_keywords(self, city_name: str, city_context: CityContext) -> List[str]:
        """Generiere Research-Keywords für eine Stadt"""
        keywords = [city_name]
        
        # Basierend auf Risk Factors
        for risk_factor, level in city_context.risk_factors.items():
            if level in ['extreme', 'high']:
                keywords.append(f"{city_name} {risk_factor}")
                keywords.append(f"{risk_factor} {city_context.country_code}")
        
        # IPCC-Keywords
        ipcc_keywords = self.ipcc_engine.get_firecrawl_context({}).get('keywords', [])
        keywords.extend(ipcc_keywords[:5])
        
        return keywords
    
    def _calculate_city_metrics(self, city_context: CityContext) -> Dict[str, float]:
        """Berechne Metriken basierend auf Risk Factors"""
        metrics = {}
        
        # Risk Factor Scoring
        risk_score = 0.0
        for risk_factor, level in city_context.risk_factors.items():
            if level == 'extreme':
                risk_score += 0.3
            elif level == 'high':
                risk_score += 0.2
            elif level == 'medium':
                risk_score += 0.1
        
        metrics['risk_factor_score'] = min(1.0, risk_score)
        metrics['priority_score'] = city_context.priority / 2.0  # Normalisiert
        
        return metrics
    
    def _chunk_text(self, texts: List[str], chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Chunk Text in sinnvolle Abschnitte"""
        chunks = []
        
        for text in texts:
            words = text.split()
            for i in range(0, len(words), chunk_size - overlap):
                chunk = " ".join(words[i:i + chunk_size])
                if chunk.strip():
                    chunks.append(chunk)
        
        return chunks
    
    def _create_fused_data_from_context(
        self,
        city_name: str,
        city_context: CityContext
    ) -> FusedDataPoint:
        """Erstelle FusedDataPoint aus Stadt-Kontext"""
        from sensor_fusion import FusedDataPoint
        
        # Berechne Risk Score basierend auf Risk Factors
        risk_score = sum(
            0.3 if level == 'extreme' else 0.2 if level == 'high' else 0.1
            for level in city_context.risk_factors.values()
        ) / len(city_context.risk_factors) if city_context.risk_factors else 0.0
        
        return FusedDataPoint(
            location=city_name,
            latitude=city_context.coordinates[0],
            longitude=city_context.coordinates[1],
            country_code=city_context.country_code,
            climate_indicators=list(city_context.risk_factors.keys()),
            satellite_data={},
            temperature_anomaly=None,
            precipitation_anomaly=None,
            conflict_indicators=[],
            security_council_mentions=0,
            meeting_frequency=0,
            economic_indicators={},
            project_count=0,
            sectors=[],
            crisis_type=None,
            affected_population=None,
            risk_score=risk_score,
            risk_level=self.risk_scorer.get_risk_level(risk_score),
            confidence=0.5,  # Mittlere Confidence für berechnete Daten
            data_sources_count=1,
            last_updated=datetime.now(),
            trend='stable',
            urgency=risk_score
        )
    
    def _prepare_llm_context(self, city_name: str, city_context: CityContext) -> Dict[str, Any]:
        """Bereite Kontext für LLM vor"""
        return {
            'city': city_name,
            'country': city_context.country_code,
            'coordinates': city_context.coordinates,
            'risk_factors': city_context.risk_factors,
            'text_chunks': city_context.text_chunks[:5],  # Limit
            'numerical_data': city_context.numerical_data,
            'fused_data': asdict(city_context.fused_data) if city_context.fused_data else {}
        }
    
    def _generate_basic_predictions(self, city_context: CityContext) -> Dict[str, Any]:
        """Generiere Basis-Predictions basierend auf echten Daten"""
        predictions = {}
        
        # Nur Predictions wenn echte Daten vorhanden
        if city_context.fused_data:
            predictions['risk_trend'] = city_context.fused_data.trend
            predictions['urgency_level'] = city_context.fused_data.urgency
            predictions['risk_score'] = city_context.fused_data.risk_score
            predictions['risk_level'] = city_context.fused_data.risk_level
        
        # Key Concerns nur wenn Risk Factors vorhanden
        if city_context.risk_factors:
            predictions['key_concerns'] = list(city_context.risk_factors.keys())[:5]
        
        # Predictions nur wenn numerische Daten vorhanden
        if city_context.numerical_data:
            if city_context.numerical_data.get('temperatures'):
                avg_temp = sum(city_context.numerical_data['temperatures']) / len(city_context.numerical_data['temperatures'])
                predictions['temperature_analysis'] = {
                    'current_avg': avg_temp,
                    'data_points': len(city_context.numerical_data['temperatures'])
                }
            
            if city_context.numerical_data.get('precipitation'):
                avg_precip = sum(city_context.numerical_data['precipitation']) / len(city_context.numerical_data['precipitation'])
                predictions['precipitation_analysis'] = {
                    'current_avg': avg_precip,
                    'data_points': len(city_context.numerical_data['precipitation'])
                }
        
        # Confidence basierend auf verfügbaren Daten
        data_sources_count = sum([
            len(city_context.text_chunks) > 0,
            len(city_context.numerical_data) > 0,
            len(city_context.image_urls) > 0,
            city_context.fused_data is not None
        ])
        predictions['prediction_confidence'] = min(1.0, data_sources_count / 4.0)
        
        return predictions
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.crawler:
            await self.crawler.__aexit__(exc_type, exc_val, exc_tb)


async def main():
    """Hauptfunktion"""
    console.print(Panel.fit(
        "[bold green]🌍 Mehrstufige Verarbeitungspipeline[/bold green]\n"
        "[cyan]Meta-Extraktion → Vektorkontextraum → Sensorfusion → LLM → Frühwarnsystem[/cyan]",
        border_style="green"
    ))
    
    # Fokus auf höchste Priorität Städte
    priority_cities = [
        name for name, data in CRITICAL_EUROPEAN_CITIES.items()
        if data['priority'] == 1
    ]
    
    console.print(f"\n[bold yellow]📋 Verarbeite {len(priority_cities)} Städte mit höchster Priorität:[/bold yellow]")
    for city in priority_cities:
        console.print(f"  • {city}")
    
    async with MultiStageProcessor() as processor:
        results = {}
        
        for city_name in priority_cities[:3]:  # Test mit 3 Städten
            try:
                result = await processor.process_city_full_pipeline(city_name)
                results[city_name] = result
            except Exception as e:
                console.print(f"[red]❌ Fehler bei {city_name}: {e}[/red]")
        
        # Zusammenfassung
        console.print("\n[bold green]📊 Pipeline-Zusammenfassung:[/bold green]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Stadt", style="cyan")
        table.add_column("Text-Chunks", style="green")
        table.add_column("Zahlen", style="yellow")
        table.add_column("Bilder", style="blue")
        table.add_column("Risk Score", style="red")
        table.add_column("Warnsignale", style="magenta")
        
        for city_name, result in results.items():
            summary = result.get('summary', {})
            table.add_row(
                city_name,
                str(summary.get('text_chunks', 0)),
                str(summary.get('numerical_data_points', 0)),
                str(summary.get('images', 0)),
                f"{summary.get('risk_score', 0):.2f}",
                str(summary.get('warning_signals', 0))
            )
        
        console.print(table)
        
        # Speichere Ergebnisse
        output_file = Path("./data/multi_stage_processing_results.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        console.print(f"\n[bold green]💾 Ergebnisse gespeichert: {output_file}[/bold green]")


if __name__ == "__main__":
    asyncio.run(main())

