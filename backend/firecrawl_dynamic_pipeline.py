#!/usr/bin/env python3
"""
Firecrawl Dynamic Pipeline - Dynamische URL-Generierung und Extraktion
Nutzt Firecrawl für:
1. URL-Discovery (crawl) von Start-URLs
2. Strukturierte Extraktion mit Schema
3. Automatische Speicherung in Datenbank
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

sys.path.append(str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from config import Config
from database import DatabaseManager
from firecrawl_enrichment import FirecrawlEnricher, CostTracker
from extractors import ExtractorFactory

console = Console()


class FirecrawlDynamicPipeline:
    """Dynamische Pipeline mit Firecrawl für URL-Discovery und Extraktion"""
    
    def __init__(self):
        self.config = Config()
        self.db = DatabaseManager()
        self.cost_tracker = CostTracker()
        self.firecrawl = FirecrawlEnricher(self.config.FIRECRAWL_API_KEY, self.cost_tracker)
        self.extractor_factory = ExtractorFactory(self.config)
        
        # Start-URLs für verschiedene Quellen
        self.source_urls = {
            "NASA": [
                "https://earthobservatory.nasa.gov",
                "https://earthobservatory.nasa.gov/images",
                "https://earthobservatory.nasa.gov/global-maps"
            ],
            "UN Press": [
                "https://press.un.org/en/content/press-releases",
                "https://press.un.org/en/content/meetings-coverage"
            ],
            "World Bank": [
                "https://www.worldbank.org/en/news",
                "https://www.worldbank.org/en/topic/climatechange"
            ],
            "WFP": [
                "https://www.wfp.org/news",
                "https://www.wfp.org/stories"
            ]
        }
    
    def get_extraction_schema(self, source: str) -> Dict[str, Any]:
        """Extraktionsschema für verschiedene Quellen"""
        base_schema = {
            "title": {
                "type": "string",
                "description": "Titel des Artikels oder Berichts"
            },
            "summary": {
                "type": "string",
                "description": "Zusammenfassung oder Beschreibung"
            },
            "publish_date": {
                "type": "string",
                "description": "Veröffentlichungsdatum"
            },
            "region": {
                "type": "string",
                "description": "Geografische Region oder Land"
            },
            "topics": {
                "type": "array",
                "description": "Themen oder Kategorien"
            }
        }
        
        # Quelle-spezifische Schemas
        if source == "NASA":
            base_schema.update({
                "climate_indicators": {
                    "type": "array",
                    "description": "Klima-Indikatoren wie Temperatur, Niederschlag, Dürre"
                },
                "satellite_data": {
                    "type": "string",
                    "description": "Satelliten-Quelle (Landsat, MODIS, etc.)"
                }
            })
        elif source == "UN Press":
            base_schema.update({
                "meeting_type": {
                    "type": "string",
                    "description": "Art des Meetings"
                },
                "security_council": {
                    "type": "boolean",
                    "description": "Ist Security Council betroffen"
                }
            })
        elif source == "World Bank":
            base_schema.update({
                "country": {
                    "type": "string",
                    "description": "Betroffenes Land"
                },
                "sector": {
                    "type": "string",
                    "description": "Sektor (Climate, Agriculture, etc.)"
                },
                "project_id": {
                    "type": "string",
                    "description": "Projekt-ID falls vorhanden"
                }
            })
        elif source == "WFP":
            base_schema.update({
                "affected_population": {
                    "type": "string",
                    "description": "Betroffene Bevölkerungsgruppe"
                },
                "crisis_type": {
                    "type": "string",
                    "description": "Art der Krise"
                }
            })
        
        return base_schema
    
    async def crawl_and_extract_source(
        self,
        source: str,
        start_urls: List[str],
        max_pages: int = 20
    ) -> Dict[str, Any]:
        """Crawle eine Quelle und extrahiere Daten"""
        console.print(f"\n[bold cyan]🌍 Verarbeite {source}...[/bold cyan]")
        
        all_records = []
        discovered_urls = set()
        
        for start_url in start_urls:
            try:
                console.print(f"  [dim]Crawle: {start_url}[/dim]")
                
                # 1. Crawle Website mit Firecrawl (URL-Discovery)
                # Führe synchron aus (Firecrawl API ist synchron)
                crawled_data, credits = await asyncio.to_thread(
                    self.firecrawl.enrich_with_crawl,
                    start_url=start_url,
                    max_depth=2,
                    limit=max_pages,
                    scrape_options={
                        "formats": ["markdown"],
                        "onlyMainContent": True,
                        "extract": self.get_extraction_schema(source)
                    }
                )
                
                console.print(f"  [green]✅ {len(crawled_data)} Seiten gefunden[/green]")
                
                # 2. Verarbeite jede gecrawlte Seite
                for page_data in crawled_data:
                    if isinstance(page_data, dict):
                        url = page_data.get('url') or page_data.get('sourceURL', '')
                        if url and url not in discovered_urls:
                            discovered_urls.add(url)
                            
                            # Extrahiere strukturierte Daten
                            record = self._process_crawled_page(page_data, source, url)
                            if record:
                                all_records.append(record)
                
            except Exception as e:
                console.print(f"  [red]❌ Fehler bei {start_url}: {e}[/red]")
                continue
        
        return {
            'source': source,
            'records': all_records,
            'urls_discovered': len(discovered_urls),
            'records_extracted': len(all_records)
        }
    
    def _process_crawled_page(
        self,
        page_data: Dict[str, Any],
        source: str,
        url: str
    ) -> Optional[Dict[str, Any]]:
        """Verarbeite eine gecrawlte Seite zu einem Record"""
        try:
            # Extrahiere Daten aus Firecrawl-Ergebnis
            extracted = page_data.get('extract', {})
            markdown = page_data.get('markdown', '')
            metadata = page_data.get('metadata', {})
            
            # Verwende Extraktor für strukturierte Daten
            extractor = self.extractor_factory.get_extractor(source)
            
            # Erstelle Record
            record = {
                'url': url,
                'source_domain': self._extract_domain(url),
                'source_name': source,
                'fetched_at': datetime.now().isoformat(),
                'title': extracted.get('title') or metadata.get('title', '') or self._extract_title_from_markdown(markdown),
                'summary': extracted.get('summary') or metadata.get('description', '') or self._extract_summary_from_markdown(markdown),
                'publish_date': extracted.get('publish_date') or metadata.get('publishedTime', ''),
                'region': extracted.get('region') or '',
                'topics': extracted.get('topics', []),
                'content_type': 'article',
                'full_text': markdown[:5000] if markdown else '',  # Limit auf 5000 Zeichen
            }
            
            # Quelle-spezifische Felder
            if source == "NASA":
                record['climate_indicators'] = extracted.get('climate_indicators', [])
                record['satellite_data'] = extracted.get('satellite_data', '')
            elif source == "UN Press":
                record['meeting_type'] = extracted.get('meeting_type', '')
                record['security_council'] = extracted.get('security_council', False)
            elif source == "World Bank":
                record['country'] = extracted.get('country', '')
                record['sector'] = extracted.get('sector', '')
                record['project_id'] = extracted.get('project_id', '')
            elif source == "WFP":
                record['affected_population'] = extracted.get('affected_population', '')
                record['crisis_type'] = extracted.get('crisis_type', '')
            
            return record
            
        except Exception as e:
            console.print(f"    [yellow]⚠️  Fehler bei Verarbeitung: {e}[/yellow]")
            return None
    
    def _extract_domain(self, url: str) -> str:
        """Extrahiere Domain aus URL"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    
    def _extract_title_from_markdown(self, markdown: str) -> str:
        """Extrahiere Titel aus Markdown"""
        if not markdown:
            return ''
        lines = markdown.split('\n')
        for line in lines[:10]:
            line = line.strip()
            if line and not line.startswith('#') and len(line) < 200:
                return line
        return ''
    
    def _extract_summary_from_markdown(self, markdown: str) -> str:
        """Extrahiere Zusammenfassung aus Markdown"""
        if not markdown:
            return ''
        # Nimm erste 3 Sätze
        sentences = markdown.split('.')[:3]
        summary = '. '.join(sentences).strip()
        return summary[:500] if summary else ''
    
    async def run_full_pipeline(self, max_pages_per_source: int = 20) -> Dict[str, Any]:
        """Führe vollständige Pipeline aus"""
        console.print(Panel.fit(
            "[bold green]🚀 Firecrawl Dynamic Pipeline[/bold green]\n"
            "[cyan]Dynamische URL-Generierung und Extraktion[/cyan]",
            border_style="green"
        ))
        
        results = {}
        
        # Zeige aktuelle DB-Statistiken
        stats = self.db.get_statistics()
        console.print(f"\n[bold blue]📊 Aktuelle Datenbank: {stats.get('total_records', 0)} Records[/bold blue]\n")
        
        # Verarbeite jede Quelle
        for source, urls in self.source_urls.items():
            try:
                result = await self.crawl_and_extract_source(
                    source=source,
                    start_urls=urls,
                    max_pages=max_pages_per_source
                )
                
                # Speichere Records in Datenbank
                if result['records']:
                    db_result = self.db.insert_records_batch(result['records'])
                    result['db_new'] = db_result.get('new', 0)
                    result['db_updated'] = db_result.get('updated', 0)
                
                results[source] = result
                
            except Exception as e:
                console.print(f"[red]❌ Fehler bei {source}: {e}[/red]")
                results[source] = {
                    'source': source,
                    'error': str(e),
                    'records': []
                }
        
        # Zeige Ergebnisse
        self._print_results(results)
        
        # Zeige Kosten-Zusammenfassung
        cost_summary = self.cost_tracker.get_summary()
        console.print(f"\n[bold yellow]💰 Kosten-Zusammenfassung:[/bold yellow]")
        console.print(f"  Firecrawl Credits verwendet: {cost_summary['firecrawl_credits_used']:.1f}")
        console.print(f"  Firecrawl Credits verbleibend: {cost_summary['firecrawl_credits_remaining']:.1f}")
        console.print(f"  Requests: {cost_summary['requests_made']}")
        
        return results
    
    def _print_results(self, results: Dict[str, Any]):
        """Zeige Ergebnisse in Tabelle"""
        console.print("\n[bold green]✅ Pipeline abgeschlossen![/bold green]\n")
        
        results_table = Table(title="📈 Ergebnisse", show_header=True, header_style="bold magenta")
        results_table.add_column("Quelle", style="cyan")
        results_table.add_column("URLs gefunden", style="yellow")
        results_table.add_column("Records extrahiert", style="green")
        results_table.add_column("Neu in DB", style="green")
        results_table.add_column("Aktualisiert", style="blue")
        
        total_urls = 0
        total_records = 0
        total_new = 0
        total_updated = 0
        
        for source, result in results.items():
            if 'error' in result:
                results_table.add_row(source, "❌", "Fehler", "-", "-")
            else:
                urls = result.get('urls_discovered', 0)
                records = result.get('records_extracted', 0)
                new = result.get('db_new', 0)
                updated = result.get('db_updated', 0)
                
                results_table.add_row(
                    source,
                    str(urls),
                    str(records),
                    str(new),
                    str(updated)
                )
                
                total_urls += urls
                total_records += records
                total_new += new
                total_updated += updated
        
        results_table.add_row(
            "[bold]Gesamt[/bold]",
            f"[bold]{total_urls}[/bold]",
            f"[bold]{total_records}[/bold]",
            f"[bold]{total_new}[/bold]",
            f"[bold]{total_updated}[/bold]"
        )
        
        console.print(results_table)
        
        # Zeige aktualisierte DB-Statistiken
        stats = self.db.get_statistics()
        console.print(f"\n[bold blue]📊 Neue Datenbank-Statistiken: {stats.get('total_records', 0)} Records[/bold blue]")


async def main():
    """Hauptfunktion"""
    pipeline = FirecrawlDynamicPipeline()
    
    # Führe Pipeline aus
    results = await pipeline.run_full_pipeline(max_pages_per_source=20)
    
    console.print("\n[bold green]✅ Fertig![/bold green]")
    console.print("\n[bold blue]Nächste Schritte:[/bold blue]")
    console.print("  1. Geocoding: python geocode_existing_records.py")
    console.print("  2. Frontend-Daten: python generate_frontend_data.py")
    console.print("  3. Web-App starten: python web_app.py")


if __name__ == "__main__":
    asyncio.run(main())

