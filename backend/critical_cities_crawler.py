#!/usr/bin/env python3
"""
Kritische europäische Städte - Echtzeit-Daten Crawling
Kombiniert Crawl4AI + Firecrawl für Vektorraum-Erstellung
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

sys.path.append(str(Path(__file__).parent))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.panel import Panel

console = Console()

# Kritische europäische Städte mit URLs
CRITICAL_CITIES = {
    "Athens": {
        "country_code": "GR",
        "coordinates": (37.9838, 23.7275),
        "urls": {
            "climate": [
                "https://www.eea.europa.eu/themes/climate/urban-adaptation",
                "https://climate.nasa.gov/effects",
                "https://www.worldbank.org/en/topic/climatechange",
                f"https://www.worldweatheronline.com/athens-weather/attica/gr.aspx"
            ],
            "ipcc": [
                "https://interactive-atlas.ipcc.ch",
                "https://climateknowledgeportal.worldbank.org/country/greece",
                "https://www.ipcc.ch/report/ar6/wg2"
            ],
            "conflict": [
                "https://acleddata.com",
                "https://www.unhcr.org/refugee-statistics/download?url=8e5c7f7",
                "https://www.iom.int/migration-data"
            ],
            "research": [
                "https://www.lancetcountdown.org",
                "https://www.nature.com/nclimate",
                "https://www.eea.europa.eu/publications"
            ]
        }
    },
    "Rome": {
        "country_code": "IT",
        "coordinates": (41.9028, 12.4964),
        "urls": {
            "climate": [
                "https://www.eea.europa.eu/themes/climate/urban-adaptation",
                "https://climate.nasa.gov/effects",
                "https://climateknowledgeportal.worldbank.org/country/italy"
            ],
            "ipcc": [
                "https://interactive-atlas.ipcc.ch",
                "https://www.ipcc.ch/report/ar6/wg2"
            ],
            "conflict": [
                "https://acleddata.com",
                "https://www.unhcr.org/refugee-statistics"
            ],
            "research": [
                "https://www.lancetcountdown.org",
                "https://www.nature.com/nclimate"
            ]
        }
    },
    "Madrid": {
        "country_code": "ES",
        "coordinates": (40.4168, -3.7038),
        "urls": {
            "climate": [
                "https://www.eea.europa.eu/themes/climate/urban-adaptation",
                "https://climateknowledgeportal.worldbank.org/country/spain"
            ],
            "ipcc": [
                "https://interactive-atlas.ipcc.ch",
                "https://www.ipcc.ch/report/ar6/wg2"
            ],
            "conflict": [
                "https://acleddata.com",
                "https://www.unhcr.org/refugee-statistics"
            ],
            "research": [
                "https://www.lancetcountdown.org"
            ]
        }
    },
    "Istanbul": {
        "country_code": "TR",
        "coordinates": (41.0082, 28.9784),
        "urls": {
            "climate": [
                "https://climateknowledgeportal.worldbank.org/country/turkey",
                "https://www.eea.europa.eu/themes/climate"
            ],
            "ipcc": [
                "https://interactive-atlas.ipcc.ch",
                "https://www.ipcc.ch/report/ar6/wg2"
            ],
            "conflict": [
                "https://acleddata.com",
                "https://www.unhcr.org/refugee-statistics/download?url=8e5c7f7"
            ],
            "research": [
                "https://www.lancetcountdown.org"
            ]
        }
    },
    "Berlin": {
        "country_code": "DE",
        "coordinates": (52.5200, 13.4050),
        "urls": {
            "climate": [
                "https://www.eea.europa.eu/themes/climate/urban-adaptation",
                "https://climateknowledgeportal.worldbank.org/country/germany"
            ],
            "ipcc": [
                "https://interactive-atlas.ipcc.ch",
                "https://www.ipcc.ch/report/ar6/wg2"
            ],
            "conflict": [
                "https://acleddata.com",
                "https://www.unhcr.org/refugee-statistics"
            ],
            "research": [
                "https://www.lancetcountdown.org",
                "https://www.nature.com/nclimate"
            ]
        }
    }
}


class CriticalCityCrawler:
    """Crawler für kritische Städte mit Crawl4AI + Firecrawl"""
    
    def __init__(self):
        # Prüfe Crawl4AI
        try:
            from crawl4ai import AsyncWebCrawler
            self.crawl4ai_available = True
        except ImportError:
            self.crawl4ai_available = False
            console.print("[yellow]⚠️  Crawl4AI nicht verfügbar[/yellow]")
        
        from config import Config
        from firecrawl_enrichment import FirecrawlEnricher, CostTracker
        from database import DatabaseManager
        
        self.config = Config()
        self.cost_tracker = CostTracker()
        self.firecrawl = FirecrawlEnricher(self.config.FIRECRAWL_API_KEY, self.cost_tracker)
        self.db = DatabaseManager()
    
    async def crawl_city_data(self, city_name: str, city_config: Dict) -> Dict[str, Any]:
        """Crawle alle Daten für eine kritische Stadt"""
        console.print(f"\n[bold cyan]🏙️  {city_name}, {city_config['country_code']}[/bold cyan]")
        console.print(f"Koordinaten: {city_config['coordinates']}")
        
        all_data = {
            'city': city_name,
            'country_code': city_config['country_code'],
            'coordinates': city_config['coordinates'],
            'timestamp': datetime.now().isoformat(),
            'climate_data': [],
            'ipcc_data': [],
            'conflict_data': [],
            'research_data': [],
            'vector_chunks': []
        }
        
        # Schritt 1: Klima-Daten mit Crawl4AI
        if 'climate' in city_config['urls']:
            console.print(f"\n[green]📊 Schritt 1: Klima-Daten crawlen...[/green]")
            climate_data = await self._crawl_category(
                city_name,
                city_config['urls']['climate'],
                'climate'
            )
            all_data['climate_data'] = climate_data
        
        # Schritt 2: IPCC-Daten mit Firecrawl (strukturierte Suche)
        if 'ipcc' in city_config['urls']:
            console.print(f"\n[green]🌡️  Schritt 2: IPCC-Daten suchen...[/green]")
            ipcc_data = await self._search_ipcc_data(city_name, city_config['country_code'])
            all_data['ipcc_data'] = ipcc_data
        
        # Schritt 3: Konflikt-Daten mit Firecrawl
        if 'conflict' in city_config['urls']:
            console.print(f"\n[green]⚔️  Schritt 3: Konflikt-Daten suchen...[/green]")
            conflict_data = await self._search_conflict_data(city_name, city_config['country_code'])
            all_data['conflict_data'] = conflict_data
        
        # Schritt 4: Forschungsdaten mit Firecrawl
        if 'research' in city_config['urls']:
            console.print(f"\n[green]🔬 Schritt 4: Forschungsdaten suchen...[/green]")
            research_data = await self._search_research_data(city_name, city_config['country_code'])
            all_data['research_data'] = research_data
        
        # Schritt 5: Erstelle Vektor-Chunks
        console.print(f"\n[green]🧠 Schritt 5: Erstelle Vektor-Chunks...[/green]")
        all_data['vector_chunks'] = self._create_vector_chunks(all_data)
        
        return all_data
    
    async def _crawl_category(self, city_name: str, urls: List[str], category: str) -> List[Dict]:
        """Crawle URLs einer Kategorie mit Crawl4AI"""
        results = []
        
        if not self.crawl4ai_available:
            console.print(f"[yellow]⚠️  Crawl4AI nicht verfügbar, überspringe {category}[/yellow]")
            return results
        
        from crawl4ai import AsyncWebCrawler
        
        for url in urls:
            try:
                console.print(f"  📡 {url[:60]}...")
                
                async with AsyncWebCrawler() as crawler:
                    result = await crawler.arun(
                        url=url,
                        word_count_threshold=50,
                        bypass_cache=True
                    )
                    
                    if result.markdown:
                        results.append({
                            'url': url,
                            'category': category,
                            'markdown': result.markdown[:2000],  # Erste 2000 Zeichen
                            'title': result.metadata.get('title', '') if hasattr(result, 'metadata') else '',
                            'timestamp': datetime.now().isoformat()
                        })
                        console.print(f"    ✅ {len(result.markdown)} Zeichen extrahiert")
                
                await asyncio.sleep(1)  # Rate Limiting
            
            except Exception as e:
                console.print(f"    ❌ Fehler: {e}")
                continue
        
        return results
    
    async def _search_ipcc_data(self, city_name: str, country_code: str) -> List[Dict]:
        """Suche IPCC-Daten mit Firecrawl - Verbesserte Suche"""
        # Verwende spezifischere Keywords
        keywords = [
            f"IPCC {city_name} climate",
            f"{city_name} temperature projections",
            f"{country_code} climate change IPCC"
        ]
        
        try:
            # Versuche mehrere Suchstrategien
            search_results = []
            
            # Strategie 1: Direkte Suche
            try:
                results, _ = self.firecrawl.enrich_with_search(
                    keywords=keywords[:2],
                    region=city_name,
                    limit=3,
                    scrape_content=True
                )
                search_results.extend(results)
            except Exception as e:
                console.print(f"    ⚠️  Suche 1 fehlgeschlagen: {e}")
            
            # Strategie 2: Alternative Keywords
            if not search_results:
                try:
                    alt_keywords = [
                        f"climate change {city_name}",
                        f"{city_name} global warming"
                    ]
                    results, _ = self.firecrawl.enrich_with_search(
                        keywords=alt_keywords,
                        region=None,  # Keine Region-Filterung
                        limit=3,
                        scrape_content=True
                    )
                    search_results.extend(results)
                except Exception as e:
                    console.print(f"    ⚠️  Suche 2 fehlgeschlagen: {e}")
            
            return [
                {
                    'url': r.get('url', ''),
                    'title': r.get('title', ''),
                    'description': r.get('description', ''),
                    'content': r.get('markdown', '')[:1000] if r.get('markdown') else '',
                    'category': 'ipcc',
                    'timestamp': datetime.now().isoformat()
                }
                for r in search_results
            ]
        except Exception as e:
            console.print(f"  ⚠️  Firecrawl-Fehler: {e}")
            return []
    
    async def _search_conflict_data(self, city_name: str, country_code: str) -> List[Dict]:
        """Suche Konflikt-Daten mit Firecrawl"""
        keywords = [
            f"{city_name} conflict",
            f"{city_name} migration",
            f"{city_name} refugees",
            f"{country_code} security"
        ]
        
        try:
            search_results, _ = self.firecrawl.enrich_with_search(
                keywords=keywords[:3],
                region=city_name,
                limit=5,
                scrape_content=True
            )
            
            return [
                {
                    'url': r.get('url', ''),
                    'title': r.get('title', ''),
                    'description': r.get('description', ''),
                    'content': r.get('markdown', '')[:1000] if r.get('markdown') else '',
                    'category': 'conflict',
                    'timestamp': datetime.now().isoformat()
                }
                for r in search_results
            ]
        except Exception as e:
            console.print(f"  ⚠️  Firecrawl-Fehler: {e}")
            return []
    
    async def _search_research_data(self, city_name: str, country_code: str) -> List[Dict]:
        """Suche Forschungsdaten mit Firecrawl"""
        keywords = [
            f"{city_name} climate research",
            f"{city_name} empirical data",
            f"{city_name} climate adaptation"
        ]
        
        try:
            search_results, _ = self.firecrawl.enrich_with_search(
                keywords=keywords[:2],
                region=city_name,
                limit=3,
                scrape_content=True
            )
            
            return [
                {
                    'url': r.get('url', ''),
                    'title': r.get('title', ''),
                    'description': r.get('description', ''),
                    'content': r.get('markdown', '')[:1000] if r.get('markdown') else '',
                    'category': 'research',
                    'timestamp': datetime.now().isoformat()
                }
                for r in search_results
            ]
        except Exception as e:
            console.print(f"  ⚠️  Firecrawl-Fehler: {e}")
            return []
    
    def _create_vector_chunks(self, city_data: Dict) -> List[Dict]:
        """Erstelle Vektor-Chunks für Vektorraum"""
        chunks = []
        
        # Chunk für Klima-Daten
        if city_data['climate_data']:
            climate_text = "\n\n".join([
                f"**{item['title']}**\n{item['markdown'][:500]}"
                for item in city_data['climate_data']
            ])
            chunks.append({
                'text': climate_text,
                'category': 'climate',
                'city': city_data['city'],
                'metadata': {
                    'sources': [item['url'] for item in city_data['climate_data']],
                    'timestamp': city_data['timestamp']
                }
            })
        
        # Chunk für IPCC-Daten
        if city_data['ipcc_data']:
            ipcc_text = "\n\n".join([
                f"**{item['title']}**\n{item['content']}"
                for item in city_data['ipcc_data']
            ])
            chunks.append({
                'text': ipcc_text,
                'category': 'ipcc',
                'city': city_data['city'],
                'metadata': {
                    'sources': [item['url'] for item in city_data['ipcc_data']],
                    'timestamp': city_data['timestamp']
                }
            })
        
        # Chunk für Konflikt-Daten
        if city_data['conflict_data']:
            conflict_text = "\n\n".join([
                f"**{item['title']}**\n{item['content']}"
                for item in city_data['conflict_data']
            ])
            chunks.append({
                'text': conflict_text,
                'category': 'conflict',
                'city': city_data['city'],
                'metadata': {
                    'sources': [item['url'] for item in city_data['conflict_data']],
                    'timestamp': city_data['timestamp']
                }
            })
        
        # Chunk für Forschungsdaten
        if city_data['research_data']:
            research_text = "\n\n".join([
                f"**{item['title']}**\n{item['content']}"
                for item in city_data['research_data']
            ])
            chunks.append({
                'text': research_text,
                'category': 'research',
                'city': city_data['city'],
                'metadata': {
                    'sources': [item['url'] for item in city_data['research_data']],
                    'timestamp': city_data['timestamp']
                }
            })
        
        return chunks


async def main():
    """Hauptfunktion - Crawle kritische Städte"""
    console.print(Panel.fit(
        "[bold green]🌍 Kritische europäische Städte - Echtzeit-Daten Crawling[/bold green]\n"
        "[cyan]Crawl4AI + Firecrawl für Vektorraum-Erstellung[/cyan]",
        border_style="green"
    ))
    
    crawler = CriticalCityCrawler()
    
    # Wähle Städte (starte mit 1-2 für Test)
    cities_to_crawl = list(CRITICAL_CITIES.items())[:2]  # Starte mit 2 Städten
    
    console.print(f"\n[yellow]📋 Werde {len(cities_to_crawl)} Städte crawlen:[/yellow]")
    for city_name, _ in cities_to_crawl:
        console.print(f"  • {city_name}")
    
    all_results = {}
    
    for city_name, city_config in cities_to_crawl:
        try:
            city_data = await crawler.crawl_city_data(city_name, city_config)
            all_results[city_name] = city_data
            
            # Zeige Zusammenfassung
            console.print(f"\n[bold green]✅ {city_name} abgeschlossen:[/bold green]")
            console.print(f"  📊 Klima-Daten: {len(city_data['climate_data'])}")
            console.print(f"  🌡️  IPCC-Daten: {len(city_data['ipcc_data'])}")
            console.print(f"  ⚔️  Konflikt-Daten: {len(city_data['conflict_data'])}")
            console.print(f"  🔬 Forschungsdaten: {len(city_data['research_data'])}")
            console.print(f"  🧠 Vektor-Chunks: {len(city_data['vector_chunks'])}")
        
        except Exception as e:
            console.print(f"[red]❌ Fehler bei {city_name}: {e}[/red]")
            import traceback
            console.print(traceback.format_exc())
            continue
    
    # Speichere Ergebnisse
    output_file = Path("./data/critical_cities_data.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    console.print(f"\n[bold green]💾 Ergebnisse gespeichert: {output_file}[/bold green]")
    
    # Zeige Kosten
    costs = crawler.cost_tracker.get_summary()
    console.print(f"\n[yellow]💰 Kosten:[/yellow]")
    console.print(f"  Firecrawl Credits: {costs.get('firecrawl_credits_used', 0):.1f}")
    console.print(f"  Verbleibend: {costs.get('firecrawl_credits_remaining', 20000):,.0f}")


if __name__ == "__main__":
    asyncio.run(main())

