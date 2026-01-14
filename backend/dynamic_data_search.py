#!/usr/bin/env python3
"""
Dynamische Datensuche - Sucht so lange bis echte Daten gefunden werden
Verschiedene Strategien, Keywords, URLs werden dynamisch durchprobiert
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
import json
import time

sys.path.append(str(Path(__file__).parent))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel

console = Console()

from optimized_crawler import OptimizedCrawler
from optimized_enrichment import OptimizedEnrichmentPipeline
from firecrawl_enrichment import FirecrawlEnricher
from database import DatabaseManager


class DynamicDataSearcher:
    """Dynamische Datensuche mit mehreren Strategien"""
    
    def __init__(self):
        self.enrichment_pipeline = OptimizedEnrichmentPipeline()
        self.db = DatabaseManager()
        self.crawler = None
        
        # Verschiedene Datenquellen
        self.data_sources = {
            'climate': [
                'https://climate.nasa.gov',
                'https://www.eea.europa.eu/themes/climate',
                'https://climateknowledgeportal.worldbank.org',
                'https://www.climate.gov',
                'https://www.noaa.gov/climate'
            ],
            'research': [
                'https://www.nature.com/nclimate',
                'https://www.lancetcountdown.org',
                'https://www.ipcc.ch',
                'https://interactive-atlas.ipcc.ch'
            ],
            'conflict': [
                'https://acleddata.com',
                'https://www.unhcr.org',
                'https://www.iom.int',
                'https://www.crisisgroup.org'
            ],
            'news': [
                'https://www.un.org/press',
                'https://www.worldbank.org/en/news',
                'https://www.wfp.org/news'
            ]
        }
        
        # Suchstrategien
        self.search_strategies = [
            'direct_search',
            'keyword_variations',
            'related_terms',
            'regional_search',
            'temporal_search',
            'category_search'
        ]
    
    async def search_until_found(
        self,
        location: str,
        country_code: str = None,
        location_type: str = 'city',  # 'city' or 'country'
        max_iterations: int = 20,
        min_data_threshold: int = 3  # Mindestens 3 Datenpunkte
    ) -> Dict[str, Any]:
        """
        Suche dynamisch bis echte Daten gefunden werden
        
        Returns:
            {
                'found': bool,
                'data': {...},
                'search_history': [...],
                'sources_searched': [...],
                'total_searches': int,
                'comprehensive_search': bool  # True wenn alles durchsucht wurde
            }
        """
        console.print(f"\n[bold cyan]🔍 Dynamische Suche für {location}[/bold cyan]")
        
        search_history = []
        sources_searched = set()
        found_data = {
            'text_chunks': [],
            'numerical_data': {},
            'image_urls': [],
            'records': []
        }
        
        iteration = 0
        comprehensive_search = False
        
        # Strategie 1: Direkte Suche mit verschiedenen Keywords
        keywords_list = self._generate_keyword_variations(location, country_code, location_type)
        
        for keyword_set in keywords_list[:max_iterations]:
            iteration += 1
            console.print(f"  [dim]Iteration {iteration}/{max_iterations}: {', '.join(keyword_set[:3])}...[/dim]")
            
            try:
                # Firecrawl Search
                search_results, _ = self.enrichment_pipeline.firecrawl_enricher.enrich_with_search(
                    keywords=keyword_set[:5],
                    region=location if location_type == 'city' else None,
                    limit=10,
                    scrape_content=True,
                    categories=["research", "github", "pdf"]
                )
                
                sources_searched.add('firecrawl_search')
                search_history.append({
                    'iteration': iteration,
                    'strategy': 'firecrawl_search',
                    'keywords': keyword_set,
                    'results_count': len(search_results)
                })
                
                # Verarbeite Ergebnisse
                for result in search_results:
                    if result.get('markdown') or result.get('description'):
                        found_data['text_chunks'].append(
                            result.get('markdown', '') or result.get('description', '')
                        )
                    
                    if result.get('url'):
                        sources_searched.add(result['url'])
                    
                    found_data['records'].append(result)
                
                # Prüfe ob genug Daten gefunden
                if self._has_sufficient_data(found_data, min_data_threshold):
                    console.print(f"  [green]✅ Genug Daten gefunden nach {iteration} Iterationen![/green]")
                    break
            
            except Exception as e:
                console.print(f"  [yellow]⚠️  Fehler: {e}[/yellow]")
                search_history.append({
                    'iteration': iteration,
                    'strategy': 'firecrawl_search',
                    'error': str(e)
                })
                continue
        
        # Strategie 2: Direktes Crawling verschiedener URLs
        if not self._has_sufficient_data(found_data, min_data_threshold):
            console.print(f"\n[yellow]📡 Versuche direktes Crawling...[/yellow]")
            
            if not self.crawler:
                self.crawler = OptimizedCrawler(max_concurrent=5)
                await self.crawler.__aenter__()
            
            # Generiere URLs basierend auf Location
            urls_to_try = self._generate_urls_for_location(location, country_code, location_type)
            
            for url in urls_to_try[:10]:  # Limit auf 10 URLs
                try:
                    crawl_result = await self.crawler.crawl_source_optimized(
                        location,
                        [url],
                        max_articles=5
                    )
                    
                    sources_searched.add(url)
                    search_history.append({
                        'strategy': 'direct_crawl',
                        'url': url,
                        'results_count': crawl_result.get('records_extracted', 0)
                    })
                    
                    # Hole Records aus DB
                    records = self.db.get_records(limit=50)
                    location_records = [
                        r for r in records
                        if location.lower() in (r.get('region', '') or '').lower() or
                           location.lower() in (r.get('title', '') or '').lower()
                    ]
                    
                    for record in location_records:
                        if record.get('title'):
                            found_data['text_chunks'].append(record['title'])
                        if record.get('summary'):
                            found_data['text_chunks'].append(record['summary'])
                        found_data['records'].append(record)
                    
                    if self._has_sufficient_data(found_data, min_data_threshold):
                        console.print(f"  [green]✅ Genug Daten durch Crawling gefunden![/green]")
                        break
                
                except Exception as e:
                    console.print(f"  [yellow]⚠️  Crawling-Fehler bei {url}: {e}[/yellow]")
                    continue
        
        # Strategie 3: Datenbank-Durchsuchung
        if not self._has_sufficient_data(found_data, min_data_threshold):
            console.print(f"\n[yellow]🗄️  Durchsuche Datenbank...[/yellow]")
            
            all_records = self.db.get_records(limit=1000)
            
            # Verschiedene Suchbegriffe
            search_terms = [
                location,
                country_code,
                f"{location} climate",
                f"{location} conflict",
                f"{country_code} climate" if country_code else None
            ]
            
            for term in search_terms:
                if not term:
                    continue
                
                matching_records = [
                    r for r in all_records
                    if term.lower() in (r.get('region', '') or '').lower() or
                       term.lower() in (r.get('title', '') or '').lower() or
                       term.lower() in (r.get('summary', '') or '').lower()
                ]
                
                for record in matching_records:
                    if record.get('title'):
                        found_data['text_chunks'].append(record['title'])
                    if record.get('summary'):
                        found_data['text_chunks'].append(record['summary'])
                    found_data['records'].append(record)
                
                if self._has_sufficient_data(found_data, min_data_threshold):
                    console.print(f"  [green]✅ Genug Daten in Datenbank gefunden![/green]")
                    break
        
        # Strategie 4: Erweiterte Suche mit verschiedenen Kategorien
        if not self._has_sufficient_data(found_data, min_data_threshold):
            console.print(f"\n[yellow]🌐 Erweiterte Suche in verschiedenen Kategorien...[/yellow]")
            
            categories_to_try = [
                ["research"],
                ["github"],
                ["pdf"],
                ["research", "github"],
                None  # Alle Kategorien
            ]
            
            for categories in categories_to_try:
                try:
                    search_results, _ = self.enrichment_pipeline.firecrawl_enricher.enrich_with_search(
                        keywords=[location, f"{location} climate", f"{location} data"],
                        region=location if location_type == 'city' else None,
                        limit=15,
                        scrape_content=True,
                        categories=categories
                    )
                    
                    for result in search_results:
                        if result.get('markdown') or result.get('description'):
                            found_data['text_chunks'].append(
                                result.get('markdown', '') or result.get('description', '')
                            )
                        found_data['records'].append(result)
                    
                    if self._has_sufficient_data(found_data, min_data_threshold):
                        console.print(f"  [green]✅ Genug Daten in Kategorien gefunden![/green]")
                        break
                
                except Exception as e:
                    continue
        
        # Prüfe ob umfassende Suche durchgeführt wurde
        if iteration >= max_iterations or len(sources_searched) >= 15:
            comprehensive_search = True
        
        # Extrahiere numerische Daten aus gefundenen Texten
        if found_data['text_chunks']:
            from data_extraction import NumberExtractor
            extractor = NumberExtractor()
            combined_text = " ".join(found_data['text_chunks'][:10])  # Limit
            extracted = extractor.extract_all(combined_text)
            
            found_data['numerical_data'] = {
                'temperatures': extracted.temperatures[:5] if extracted.temperatures else [],
                'precipitation': extracted.precipitation[:5] if extracted.precipitation else [],
                'population_numbers': extracted.population_numbers[:5] if extracted.population_numbers else [],
                'financial_amounts': extracted.financial_amounts[:5] if extracted.financial_amounts else []
            }
        
        # Finale Prüfung
        has_data = self._has_sufficient_data(found_data, min_data_threshold)
        
        result = {
            'found': has_data,
            'data': found_data,
            'search_history': search_history,
            'sources_searched': list(sources_searched),
            'total_searches': iteration,
            'comprehensive_search': comprehensive_search,
            'data_summary': {
                'text_chunks': len(found_data['text_chunks']),
                'numerical_data_points': sum(len(v) if isinstance(v, list) else 1 for v in found_data['numerical_data'].values() if v),
                'records': len(found_data['records']),
                'sources_count': len(sources_searched)
            }
        }
        
        if has_data:
            console.print(f"\n[bold green]✅ Daten gefunden: {result['data_summary']}[/bold green]")
        else:
            console.print(f"\n[bold yellow]⚠️  Keine ausreichenden Daten gefunden[/bold yellow]")
            console.print(f"[yellow]Umfassende Suche durchgeführt: {comprehensive_search}[/yellow]")
            console.print(f"[yellow]Quellen durchsucht: {len(sources_searched)}[/yellow]")
        
        return result
    
    def _generate_keyword_variations(
        self,
        location: str,
        country_code: str = None,
        location_type: str = 'city'
    ) -> List[List[str]]:
        """Generiere verschiedene Keyword-Kombinationen"""
        keywords_list = []
        
        # Basis-Keywords
        base_keywords = [location]
        if country_code:
            base_keywords.append(country_code)
        
        # Klima-bezogene Keywords
        climate_keywords = [
            f"{location} climate",
            f"{location} climate change",
            f"{location} global warming",
            f"{location} temperature",
            f"{location} precipitation",
            f"{location} drought",
            f"{location} flood",
            f"{location} heat wave",
            f"{location} IPCC",
            f"{location} climate data"
        ]
        
        # Konflikt-bezogene Keywords
        conflict_keywords = [
            f"{location} conflict",
            f"{location} migration",
            f"{location} refugees",
            f"{location} crisis",
            f"{location} security"
        ]
        
        # Research-Keywords
        research_keywords = [
            f"{location} research",
            f"{location} study",
            f"{location} data",
            f"{location} analysis",
            f"{location} report"
        ]
        
        # Kombiniere Keywords
        all_keyword_sets = [
            base_keywords + [climate_keywords[0]],
            base_keywords + [climate_keywords[1]],
            base_keywords + [climate_keywords[2]],
            [climate_keywords[0], climate_keywords[1]],
            [climate_keywords[2], climate_keywords[3]],
            base_keywords + conflict_keywords[:2],
            base_keywords + research_keywords[:2],
            [location, "climate", "data"],
            [location, "IPCC", "AR6"],
            [location, "temperature", "precipitation"]
        ]
        
        return all_keyword_sets
    
    def _generate_urls_for_location(
        self,
        location: str,
        country_code: str = None,
        location_type: str = 'city'
    ) -> List[str]:
        """Generiere URLs für eine Location"""
        urls = []
        
        # World Bank Climate Portal
        if country_code:
            urls.append(f"https://climateknowledgeportal.worldbank.org/country/{country_code.lower()}")
        
        # IPCC Interactive Atlas
        urls.append("https://interactive-atlas.ipcc.ch")
        
        # EEA Climate
        urls.append("https://www.eea.europa.eu/themes/climate")
        
        # NASA Climate
        urls.append("https://climate.nasa.gov")
        
        # UNHCR
        urls.append("https://www.unhcr.org/refugee-statistics")
        
        # ACLED
        urls.append("https://acleddata.com")
        
        # World Bank News
        if country_code:
            urls.append(f"https://www.worldbank.org/en/country/{country_code.lower()}")
        
        return urls
    
    def _has_sufficient_data(self, data: Dict[str, Any], threshold: int = 3) -> bool:
        """Prüfe ob genug Daten vorhanden sind"""
        text_count = len(data.get('text_chunks', []))
        numerical_count = sum(
            len(v) if isinstance(v, list) else (1 if v else 0)
            for v in data.get('numerical_data', {}).values()
        )
        records_count = len(data.get('records', []))
        
        total_data_points = text_count + numerical_count + records_count
        
        return total_data_points >= threshold
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.crawler:
            await self.crawler.__aexit__(exc_type, exc_val, exc_tb)


async def main():
    """Test-Funktion"""
    searcher = DynamicDataSearcher()
    
    test_locations = [
        ("Mumbai", "IN", "city"),
        ("Barcelona", "ES", "city"),
        ("Dhaka", "BD", "city")
    ]
    
    async with searcher:
        for location, country_code, location_type in test_locations:
            result = await searcher.search_until_found(
                location,
                country_code,
                location_type,
                max_iterations=10
            )
            
            console.print(f"\n[bold cyan]Ergebnis für {location}:[/bold cyan]")
            console.print(f"  Gefunden: {result['found']}")
            console.print(f"  Daten: {result['data_summary']}")
            console.print(f"  Quellen: {len(result['sources_searched'])}")
            console.print(f"  Umfassende Suche: {result['comprehensive_search']}")


if __name__ == "__main__":
    asyncio.run(main())



