#!/usr/bin/env python3
"""
Agenten-Orchestrierung basierend auf fire-enrich Architektur
Sequenzielle Agenten mit kontextuellem Aufbau
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json

sys.path.append(str(Path(__file__).parent))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

console = Console()


class AgentPhase(Enum):
    """Phasen der Agenten-Ausführung"""
    DISCOVERY = "discovery"  # Phase 1: Grundlegende Daten finden
    CRAWL = "crawl"  # Phase 2: Daten crawlen
    ENRICH = "enrich"  # Phase 3: Daten anreichern
    UPDATE = "update"  # Phase 4: Daten aktualisieren
    PREDICT = "predict"  # Phase 5: Prognosen erstellen
    SEARCH = "search"  # Phase 6: Suche im Vektorraum


@dataclass
class AgentContext:
    """Kontext zwischen Agenten-Phasen"""
    city: str
    country_code: str
    coordinates: tuple
    
    # Phase 1: Discovery
    discovered_urls: List[str] = field(default_factory=list)
    basic_info: Dict[str, Any] = field(default_factory=dict)
    
    # Phase 2: Crawl
    crawled_data: Dict[str, Any] = field(default_factory=dict)
    images_found: List[str] = field(default_factory=list)
    
    # Phase 3: Enrich
    enriched_data: Dict[str, Any] = field(default_factory=dict)
    numerical_data: Dict[str, float] = field(default_factory=dict)
    
    # Phase 4: Update
    updated_records: List[str] = field(default_factory=list)
    
    # Phase 5: Predict
    predictions: Dict[str, Any] = field(default_factory=dict)
    
    # Phase 6: Search
    search_results: List[Any] = field(default_factory=list)
    
    # Metadaten
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0


class BaseAgent:
    """Basis-Klasse für alle Agenten"""
    
    def __init__(self, name: str, phase: AgentPhase):
        self.name = name
        self.phase = phase
        self.dependencies: List[AgentPhase] = []
    
    async def execute(self, context: AgentContext) -> AgentContext:
        """Führe Agent aus - muss überschrieben werden"""
        raise NotImplementedError
    
    def can_execute(self, context: AgentContext) -> bool:
        """Prüfe ob Agent ausgeführt werden kann"""
        return all(
            dep in [p for p in AgentPhase] 
            for dep in self.dependencies
        )


class DiscoveryAgent(BaseAgent):
    """Phase 1: Entdecke grundlegende Daten und URLs"""
    
    def __init__(self):
        super().__init__("DiscoveryAgent", AgentPhase.DISCOVERY)
        self.dependencies = []
    
    async def execute(self, context: AgentContext) -> AgentContext:
        """Entdecke URLs und grundlegende Informationen"""
        console.print(f"[cyan]🔍 {self.name}: Entdecke Daten für {context.city}...[/cyan]")
        
        # Verwende Crawl4AI für Discovery
        try:
            from crawl4ai_integration import Crawl4AICrawler
            
            crawler = Crawl4AICrawler()
            
            # Entdecke URLs aus verschiedenen Quellen
            discovery_urls = [
                f"https://www.eea.europa.eu/themes/climate/urban-adaptation",
                f"https://climate.nasa.gov/effects",
                f"https://www.worldbank.org/en/topic/climatechange"
            ]
            
            for url in discovery_urls:
                try:
                    links = await crawler.discover_article_links(url, max_links=10)
                    context.discovered_urls.extend(links)
                    console.print(f"  ✅ {url}: {len(links)} Links gefunden")
                except Exception as e:
                    console.print(f"  ⚠️  {url}: {e}")
            
            # Grundlegende Informationen
            context.basic_info = {
                'city': context.city,
                'country_code': context.country_code,
                'coordinates': context.coordinates,
                'urls_discovered': len(context.discovered_urls)
            }
        
        except Exception as e:
            console.print(f"[red]❌ Discovery-Fehler: {e}[/red]")
        
        return context


class CrawlAgent(BaseAgent):
    """Phase 2: Crawle Daten und Bilder"""
    
    def __init__(self):
        super().__init__("CrawlAgent", AgentPhase.CRAWL)
        self.dependencies = [AgentPhase.DISCOVERY]
    
    async def execute(self, context: AgentContext) -> AgentContext:
        """Crawle Daten und extrahiere Bilder"""
        console.print(f"[cyan]🕷️  {self.name}: Crawle Daten für {context.city}...[/cyan]")
        
        try:
            from crawl4ai import AsyncWebCrawler
            
            crawled_items = []
            images_found = []
            
            # Crawle alle entdeckten URLs
            for url in context.discovered_urls[:20]:  # Limit auf 20
                try:
                    async with AsyncWebCrawler() as crawler:
                        result = await crawler.arun(
                            url=url,
                            word_count_threshold=50,
                            cache_mode="none"
                        )
                        
                        if result.markdown:
                            crawled_items.append({
                                'url': url,
                                'markdown': result.markdown[:2000],
                                'title': result.metadata.get('title', '') if hasattr(result, 'metadata') else ''
                            })
                        
                        # Extrahiere Bilder
                        if hasattr(result, 'images') and result.images:
                            images_found.extend(result.images[:5])  # Max 5 Bilder pro URL
                    
                    await asyncio.sleep(0.5)  # Rate Limiting
                
                except Exception as e:
                    console.print(f"  ⚠️  {url}: {e}")
                    continue
            
            context.crawled_data = {
                'items': crawled_items,
                'total': len(crawled_items)
            }
            context.images_found = images_found[:50]  # Max 50 Bilder
            
            console.print(f"  ✅ {len(crawled_items)} Items gecrawlt, {len(context.images_found)} Bilder gefunden")
        
        except Exception as e:
            console.print(f"[red]❌ Crawl-Fehler: {e}[/red]")
        
        return context


class EnrichAgent(BaseAgent):
    """Phase 3: Reichere Daten an (Zahlen, IPCC, etc.)"""
    
    def __init__(self):
        super().__init__("EnrichAgent", AgentPhase.ENRICH)
        self.dependencies = [AgentPhase.CRAWL]
    
    async def execute(self, context: AgentContext) -> AgentContext:
        """Reichere Daten mit Firecrawl an"""
        console.print(f"[cyan]📊 {self.name}: Reichere Daten für {context.city} an...[/cyan]")
        
        try:
            from config import Config
            from firecrawl_enrichment import FirecrawlEnricher, CostTracker
            from data_extraction import NumberExtractor
            
            config = Config()
            cost_tracker = CostTracker()
            firecrawl = FirecrawlEnricher(config.FIRECRAWL_API_KEY, cost_tracker)
            number_extractor = NumberExtractor()
            
            # Kombiniere alle Text-Inhalte
            all_text = "\n\n".join([
                item.get('markdown', '') + " " + item.get('title', '')
                for item in context.crawled_data.get('items', [])
            ])
            
            # Extrahiere Zahlen
            extracted = number_extractor.extract_all(all_text)
            
            context.numerical_data = {
                'temperatures': extracted.temperatures[:3] if extracted.temperatures else [],
                'precipitation': extracted.precipitation[:3] if extracted.precipitation else [],
                'population': extracted.population_numbers[:3] if extracted.population_numbers else [],
                'financial': extracted.financial_amounts[:3] if extracted.financial_amounts else []
            }
            
            # Firecrawl-Suche für IPCC-Daten
            keywords = [
                f"{context.city} climate",
                f"{context.city} IPCC",
                f"{context.country_code} climate projections"
            ]
            
            try:
                search_results, _ = firecrawl.enrich_with_search(
                    keywords=keywords[:2],
                    region=context.city,
                    limit=3,
                    scrape_content=True
                )
                
                context.enriched_data = {
                    'ipcc_results': [
                        {
                            'url': r.get('url', ''),
                            'title': r.get('title', ''),
                            'content': r.get('markdown', '')[:500] if r.get('markdown') else ''
                        }
                        for r in search_results
                    ]
                }
            except Exception as e:
                console.print(f"  ⚠️  Firecrawl-Suche fehlgeschlagen: {e}")
            
            console.print(f"  ✅ Zahlen extrahiert, {len(context.enriched_data.get('ipcc_results', []))} IPCC-Ergebnisse")
        
        except Exception as e:
            console.print(f"[red]❌ Enrich-Fehler: {e}[/red]")
        
        return context


class UpdateAgent(BaseAgent):
    """Phase 4: Aktualisiere bestehende Daten"""
    
    def __init__(self):
        super().__init__("UpdateAgent", AgentPhase.UPDATE)
        self.dependencies = [AgentPhase.ENRICH]
    
    async def execute(self, context: AgentContext) -> AgentContext:
        """Aktualisiere Datenbank mit neuen Daten"""
        console.print(f"[cyan]🔄 {self.name}: Aktualisiere Daten für {context.city}...[/cyan]")
        
        try:
            from database import DatabaseManager
            
            db = DatabaseManager()
            
            # Finde bestehende Records für diese Stadt
            all_records = db.get_records(limit=1000)
            city_records = [
                r for r in all_records
                if context.city.lower() in (r.get('title', '') + ' ' + r.get('summary', '')).lower()
                or context.country_code == r.get('primary_country_code', '')
            ]
            
            # Update mit neuen Daten
            updated_count = 0
            for record in city_records[:10]:  # Limit auf 10
                # Hier könnte man Records mit neuen Daten aktualisieren
                context.updated_records.append(str(record.get('id')))
                updated_count += 1
            
            console.print(f"  ✅ {updated_count} Records aktualisiert")
        
        except Exception as e:
            console.print(f"[red]❌ Update-Fehler: {e}[/red]")
        
        return context


class PredictAgent(BaseAgent):
    """Phase 5: Erstelle Prognosen"""
    
    def __init__(self):
        super().__init__("PredictAgent", AgentPhase.PREDICT)
        self.dependencies = [AgentPhase.ENRICH]
    
    async def execute(self, context: AgentContext) -> AgentContext:
        """Erstelle Prognosen basierend auf angereicherten Daten"""
        console.print(f"[cyan]🔮 {self.name}: Erstelle Prognosen für {context.city}...[/cyan]")
        
        try:
            from risk_scoring import RiskScorer
            
            scorer = RiskScorer()
            
            # Erstelle Record-ähnliches Dict für Risk-Scoring
            record_dict = {
                'title': f"{context.city} Climate Analysis",
                'summary': json.dumps(context.enriched_data),
                'region': context.city,
                'numerical_data': context.numerical_data
            }
            
            risk = scorer.calculate_risk(record_dict)
            
            context.predictions = {
                'risk_score': risk.score,
                'risk_level': scorer.get_risk_level(risk.score),
                'climate_risk': risk.climate_risk,
                'conflict_risk': risk.conflict_risk,
                'urgency': risk.urgency,
                'indicators': risk.indicators
            }
            
            console.print(f"  ✅ Risiko-Score: {risk.score:.2f} ({scorer.get_risk_level(risk.score)})")
        
        except Exception as e:
            console.print(f"[red]❌ Predict-Fehler: {e}[/red]")
        
        return context


class SearchAgent(BaseAgent):
    """Phase 6: Suche im Vektorraum"""
    
    def __init__(self, vector_space):
        super().__init__("SearchAgent", AgentPhase.SEARCH)
        self.dependencies = [AgentPhase.ENRICH]
        self.vector_space = vector_space
    
    async def execute(self, context: AgentContext) -> AgentContext:
        """Suche ähnliche Daten im Vektorraum"""
        console.print(f"[cyan]🔍 {self.name}: Suche ähnliche Daten für {context.city}...[/cyan]")
        
        try:
            from multimodal_vector_space import MultiModalChunk
            
            # Erstelle Query-Chunk
            query_chunk = MultiModalChunk(
                chunk_id=f"query_{context.city}_{datetime.now().timestamp()}",
                city=context.city,
                coordinates=context.coordinates,
                text_content=json.dumps(context.enriched_data),
                numerical_data=context.numerical_data,
                image_urls=context.images_found[:5],
                sources=context.discovered_urls[:5]
            )
            
            # Suche ähnliche Chunks
            similar_chunks = self.vector_space.search_similar(
                query_chunk,
                top_k=5,
                similarity_threshold=0.3
            )
            
            context.search_results = [
                {
                    'chunk_id': chunk.chunk_id,
                    'city': chunk.city,
                    'similarity': float(sim),
                    'sources': chunk.sources
                }
                for chunk, sim in similar_chunks
            ]
            
            console.print(f"  ✅ {len(context.search_results)} ähnliche Chunks gefunden")
        
        except Exception as e:
            console.print(f"[red]❌ Search-Fehler: {e}[/red]")
        
        return context


class AgentOrchestrator:
    """Orchestriert alle Agenten sequenziell"""
    
    def __init__(self):
        self.agents: List[BaseAgent] = []
        self.vector_space = None  # Wird später initialisiert
    
    def register_agent(self, agent: BaseAgent):
        """Registriere einen Agenten"""
        self.agents.append(agent)
    
    def setup_default_agents(self, vector_space=None):
        """Setup Standard-Agenten"""
        self.vector_space = vector_space
        
        self.agents = [
            DiscoveryAgent(),
            CrawlAgent(),
            EnrichAgent(),
            UpdateAgent(),
            PredictAgent(),
            SearchAgent(vector_space) if vector_space else None
        ]
        
        # Filtere None-Agenten
        self.agents = [a for a in self.agents if a is not None]
    
    async def execute_pipeline(self, context: AgentContext) -> AgentContext:
        """Führe alle Agenten sequenziell aus"""
        console.print(f"\n[bold green]🚀 Starte Agenten-Pipeline für {context.city}[/bold green]")
        
        # Sortiere Agenten nach Phase
        sorted_agents = sorted(self.agents, key=lambda a: list(AgentPhase).index(a.phase))
        
        for agent in sorted_agents:
            if not agent.can_execute(context):
                console.print(f"[yellow]⏭️  Überspringe {agent.name} (Dependencies nicht erfüllt)[/yellow]")
                continue
            
            try:
                context = await agent.execute(context)
                await asyncio.sleep(0.5)  # Pause zwischen Agenten
            except Exception as e:
                console.print(f"[red]❌ Fehler in {agent.name}: {e}[/red]")
                continue
        
        return context
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Hole Status der Pipeline"""
        return {
            'total_agents': len(self.agents),
            'agents': [
                {
                    'name': agent.name,
                    'phase': agent.phase.value,
                    'dependencies': [d.value for d in agent.dependencies]
                }
                for agent in self.agents
            ]
        }


async def main():
    """Test der Agenten-Orchestrierung"""
    from multimodal_vector_space import MultiModalVectorSpace
    
    # Initialisiere Vektorraum
    vector_space = MultiModalVectorSpace()
    
    # Initialisiere Orchestrator
    orchestrator = AgentOrchestrator()
    orchestrator.setup_default_agents(vector_space)
    
    # Zeige Pipeline-Status
    status = orchestrator.get_pipeline_status()
    console.print("\n[bold cyan]Agenten-Pipeline:[/bold cyan]")
    table = Table()
    table.add_column("Agent", style="cyan")
    table.add_column("Phase", style="yellow")
    table.add_column("Dependencies", style="green")
    
    for agent_info in status['agents']:
        deps = ", ".join(agent_info['dependencies']) if agent_info['dependencies'] else "keine"
        table.add_row(agent_info['name'], agent_info['phase'], deps)
    
    console.print(table)
    
    # Test mit einer Stadt
    context = AgentContext(
        city="Athens",
        country_code="GR",
        coordinates=(37.9838, 23.7275)
    )
    
    # Führe Pipeline aus
    result_context = await orchestrator.execute_pipeline(context)
    
    # Zeige Ergebnisse
    console.print(f"\n[bold green]✅ Pipeline abgeschlossen![/bold green]")
    console.print(f"  URLs entdeckt: {len(result_context.discovered_urls)}")
    console.print(f"  Items gecrawlt: {result_context.crawled_data.get('total', 0)}")
    console.print(f"  Bilder gefunden: {len(result_context.images_found)}")
    console.print(f"  Ähnliche Chunks: {len(result_context.search_results)}")


if __name__ == "__main__":
    asyncio.run(main())



