#!/usr/bin/env python3
"""
Optimierte kombinierte Pipeline: Crawling + Enrichment
Nutzt alle Optimierungen: Parallelisierung, Caching, Batch-Processing
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

sys.path.append(str(Path(__file__).parent))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel

console = Console()

from optimized_crawler import OptimizedCrawler
from optimized_enrichment import OptimizedEnrichmentPipeline
from optimized_database import OptimizedDatabaseManager


class OptimizedCombinedPipeline:
    """Kombinierte optimierte Pipeline für Crawling + Enrichment"""
    
    def __init__(
        self,
        max_concurrent_crawl: int = 10,
        max_concurrent_enrich: int = 5,
        cache_ttl_hours: int = 24
    ):
        self.max_concurrent_crawl = max_concurrent_crawl
        self.max_concurrent_enrich = max_concurrent_enrich
        self.cache_ttl_hours = cache_ttl_hours
        
        self.db = OptimizedDatabaseManager()
    
    async def run_full_pipeline(
        self,
        sources: Dict[str, List[str]],
        max_articles_per_source: int = 20,
        enrich_records: bool = True,
        enrich_limit: int = 50
    ) -> Dict[str, Any]:
        """Führe vollständige Pipeline aus: Crawling + Enrichment"""
        console.print(Panel.fit(
            "[bold green]🚀 Optimierte kombinierte Pipeline[/bold green]\n"
            "[cyan]Crawling + Enrichment mit allen Optimierungen[/cyan]",
            border_style="green"
        ))
        
        start_time = datetime.now()
        results = {
            'crawling': {},
            'enrichment': {},
            'summary': {}
        }
        
        # Phase 1: Optimiertes Crawling
        console.print("\n[bold cyan]📡 Phase 1: Optimiertes Crawling[/bold cyan]")
        
        async with OptimizedCrawler(
            max_concurrent=self.max_concurrent_crawl,
            cache_ttl_hours=self.cache_ttl_hours
        ) as crawler:
            crawling_results = {}
            
            for source_name, urls in sources.items():
                try:
                    result = await crawler.crawl_source_optimized(
                        source_name,
                        urls,
                        max_articles=max_articles_per_source
                    )
                    crawling_results[source_name] = result
                except Exception as e:
                    console.print(f"[red]❌ Fehler beim Crawling von {source_name}: {e}[/red]")
                    crawling_results[source_name] = {'error': str(e)}
            
            results['crawling'] = crawling_results
        
        crawling_time = (datetime.now() - start_time).total_seconds()
        
        # Phase 2: Optimiertes Enrichment (optional)
        if enrich_records:
            console.print("\n[bold cyan]🔄 Phase 2: Optimiertes Enrichment[/bold cyan]")
            
            enrichment_pipeline = OptimizedEnrichmentPipeline(
                max_concurrent=self.max_concurrent_enrich
            )
            
            enrichment_result = await enrichment_pipeline.run_optimized_enrichment(
                limit=enrich_limit,
                max_concurrent=self.max_concurrent_enrich
            )
            
            results['enrichment'] = enrichment_result
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        # Zusammenfassung
        results['summary'] = {
            'total_time_seconds': total_time,
            'crawling_time_seconds': crawling_time,
            'enrichment_time_seconds': total_time - crawling_time if enrich_records else 0,
            'total_records_crawled': sum(
                r.get('records_extracted', 0) for r in crawling_results.values()
                if 'records_extracted' in r
            ),
            'total_records_enriched': results.get('enrichment', {}).get('enriched', 0) if enrich_records else 0,
            'cache_stats': crawling_results.get(list(crawling_results.keys())[0], {}).get('cache_stats', {}) if crawling_results else {}
        }
        
        return results
    
    def print_summary(self, results: Dict[str, Any]):
        """Zeige Zusammenfassung der Ergebnisse"""
        console.print("\n[bold green]📊 Pipeline-Zusammenfassung[/bold green]\n")
        
        # Crawling-Ergebnisse
        console.print("[bold cyan]📡 Crawling-Ergebnisse:[/bold cyan]")
        crawl_table = Table(show_header=True, header_style="bold magenta")
        crawl_table.add_column("Quelle", style="cyan")
        crawl_table.add_column("URLs gefunden", style="green")
        crawl_table.add_column("Records extrahiert", style="yellow")
        crawl_table.add_column("Zeit (s)", style="blue")
        
        for source, result in results['crawling'].items():
            if 'error' not in result:
                crawl_table.add_row(
                    source,
                    str(result.get('urls_discovered', 0)),
                    str(result.get('records_extracted', 0)),
                    f"{result.get('elapsed_seconds', 0):.1f}"
                )
        
        console.print(crawl_table)
        
        # Enrichment-Ergebnisse
        if results.get('enrichment'):
            console.print("\n[bold cyan]🔄 Enrichment-Ergebnisse:[/bold cyan]")
            enrich_table = Table(show_header=True, header_style="bold magenta")
            enrich_table.add_column("Metrik", style="cyan")
            enrich_table.add_column("Wert", style="green")
            
            enrich = results['enrichment']
            enrich_table.add_row("Records verarbeitet", str(enrich.get('total_records', 0)))
            enrich_table.add_row("Records angereichert", str(enrich.get('enriched', 0)))
            enrich_table.add_row("Records gespeichert", str(enrich.get('saved', 0)))
            enrich_table.add_row("Zeit (s)", f"{enrich.get('elapsed_seconds', 0):.1f}")
            enrich_table.add_row("Durchschnitt pro Record (s)", f"{enrich.get('avg_time_per_record', 0):.2f}")
            
            console.print(enrich_table)
            
            # Kosten
            costs = enrich.get('costs', {})
            console.print(f"\n[bold yellow]💰 Kosten:[/bold yellow]")
            console.print(f"  Firecrawl Credits: {costs.get('firecrawl_credits_used', 0):.1f}")
            console.print(f"  Verbleibend: {costs.get('firecrawl_credits_remaining', 20000):,.0f}")
        
        # Gesamt-Zusammenfassung
        summary = results['summary']
        console.print("\n[bold green]📈 Gesamt-Zusammenfassung:[/bold green]")
        console.print(f"  Gesamtzeit: {summary['total_time_seconds']:.1f}s")
        console.print(f"  Crawling-Zeit: {summary['crawling_time_seconds']:.1f}s")
        if summary['enrichment_time_seconds'] > 0:
            console.print(f"  Enrichment-Zeit: {summary['enrichment_time_seconds']:.1f}s")
        console.print(f"  Records gecrawlt: {summary['total_records_crawled']}")
        console.print(f"  Records angereichert: {summary['total_records_enriched']}")
        
        # Cache-Statistiken
        cache_stats = summary.get('cache_stats', {})
        if cache_stats:
            console.print(f"\n[bold cyan]💾 Cache-Statistiken:[/bold cyan]")
            console.print(f"  Gecachte URLs: {cache_stats.get('total_cached', 0)}")
            console.print(f"  Gültige Einträge: {cache_stats.get('valid_entries', 0)}")
            console.print(f"  Abgelaufene Einträge: {cache_stats.get('expired_entries', 0)}")
        
        # Datenbank-Statistiken
        db_stats = self.db.get_statistics()
        console.print(f"\n[bold cyan]🗄️  Datenbank-Statistiken:[/bold cyan]")
        console.print(f"  Gesamt Records: {db_stats.get('total_records', 0)}")
        console.print(f"  Records mit Region: {db_stats.get('records_with_region', 0)}")
        console.print(f"  Enrichments: {db_stats.get('total_enrichments', 0)}")
        
        if db_stats.get('records_by_source'):
            console.print(f"\n  Records pro Quelle:")
            for source, count in db_stats['records_by_source'].items():
                console.print(f"    {source}: {count}")


async def main():
    """Hauptfunktion"""
    # Konfiguration
    sources = {
        'NASA': [
            'https://earthobservatory.nasa.gov/images',
            'https://earthobservatory.nasa.gov/features',
        ],
        'UN Press': [
            'https://press.un.org/en/content/press-releases',
        ],
        'World Bank': [
            'https://www.worldbank.org/en/news',
        ]
    }
    
    # Erstelle Pipeline
    pipeline = OptimizedCombinedPipeline(
        max_concurrent_crawl=10,
        max_concurrent_enrich=5,
        cache_ttl_hours=24
    )
    
    # Führe Pipeline aus
    results = await pipeline.run_full_pipeline(
        sources=sources,
        max_articles_per_source=20,
        enrich_records=True,
        enrich_limit=50
    )
    
    # Zeige Zusammenfassung
    pipeline.print_summary(results)
    
    # Speichere Ergebnisse
    output_file = Path("./data/optimized_pipeline_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Konvertiere datetime zu String für JSON
    def json_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=json_serializer)
    
    console.print(f"\n[bold green]💾 Ergebnisse gespeichert: {output_file}[/bold green]")


if __name__ == "__main__":
    asyncio.run(main())



