#!/usr/bin/env python3
"""
Firecrawl IPCC Pipeline - Dynamische URL-Generierung mit IPCC-Kriterien
Nutzt Firecrawl Search mit IPCC-Kontext für:
1. Dynamische URL-Discovery basierend auf IPCC-Kriterien
2. Strukturierte Extraktion mit IPCC-Schema
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
from ipcc_context_engine import IPCCContextEngine
from extractors import ExtractorFactory

console = Console()


class FirecrawlIPCCPipeline:
    """Dynamische Pipeline mit Firecrawl und IPCC-Kriterien"""
    
    def __init__(self):
        self.config = Config()
        self.db = DatabaseManager()
        self.cost_tracker = CostTracker()
        self.firecrawl = FirecrawlEnricher(self.config.FIRECRAWL_API_KEY, self.cost_tracker)
        self.ipcc_engine = IPCCContextEngine()
        self.extractor_factory = ExtractorFactory(self.config)
        
        # IPCC-basierte Suchkriterien für verschiedene Regionen
        self.ipcc_search_regions = {
            "East Africa": {
                "keywords": ["drought", "food security", "temperature anomaly", "precipitation"],
                "ipcc_risks": ["Drought", "Food insecurity", "Extreme heat events"],
                "focus_areas": ["temperature", "precipitation", "human_impacts"]
            },
            "Middle East": {
                "keywords": ["water scarcity", "extreme heat", "drought", "conflict"],
                "ipcc_risks": ["Water scarcity", "Extreme heat events", "Humanitarian crises"],
                "focus_areas": ["temperature", "precipitation", "human_impacts"]
            },
            "South Asia": {
                "keywords": ["monsoon", "flooding", "sea level rise", "extreme weather"],
                "ipcc_risks": ["Heavy precipitation", "Sea level rise", "Displacement"],
                "focus_areas": ["precipitation", "sea_level", "human_impacts"]
            },
            "Southeast Asia": {
                "keywords": ["typhoon", "sea level rise", "coastal flooding", "extreme weather"],
                "ipcc_risks": ["Heavy precipitation", "Sea level rise", "Biodiversity loss"],
                "focus_areas": ["precipitation", "sea_level", "ecosystems"]
            },
            "Central America": {
                "keywords": ["hurricane", "drought", "extreme weather", "displacement"],
                "ipcc_risks": ["Heavy precipitation", "Drought", "Displacement"],
                "focus_areas": ["precipitation", "temperature", "human_impacts"]
            },
            "West Africa": {
                "keywords": ["drought", "desertification", "food security", "temperature"],
                "ipcc_risks": ["Drought", "Food insecurity", "Extreme heat events"],
                "focus_areas": ["temperature", "precipitation", "ecosystems"]
            }
        }
    
    def get_ipcc_extraction_schema(self, focus_areas: List[str]) -> Dict[str, Any]:
        """IPCC-basiertes Extraktionsschema"""
        schema = {
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
            "temperature_data": {
                "type": "object",
                "description": "Temperatur-Daten",
                "properties": {
                    "value": {"type": "number"},
                    "anomaly": {"type": "number"},
                    "baseline_comparison": {"type": "string"}
                }
            },
            "precipitation_data": {
                "type": "object",
                "description": "Niederschlags-Daten",
                "properties": {
                    "value": {"type": "number"},
                    "anomaly": {"type": "number"},
                    "trend": {"type": "string"}
                }
            },
            "ipcc_relevance": {
                "type": "string",
                "description": "Relevanz für IPCC-Bewertungen (high/medium/low)"
            },
            "ipcc_risks": {
                "type": "array",
                "description": "IPCC-identifizierte Risiken"
            },
            "climate_indicators": {
                "type": "array",
                "description": "Klima-Indikatoren (drought, flood, heat wave, etc.)"
            }
        }
        
        return schema
    
    async def search_and_extract_region(
        self,
        region: str,
        region_config: Dict[str, Any],
        max_results: int = 15
    ) -> Dict[str, Any]:
        """Suche und extrahiere Daten für eine Region mit IPCC-Kriterien"""
        console.print(f"\n[bold cyan]🌍 Verarbeite {region} mit IPCC-Kriterien...[/bold cyan]")
        
        all_records = []
        discovered_urls = set()
        
        # Erstelle IPCC-Kontext für diese Region
        mock_record = {
            'region': region,
            'title': f"Climate data for {region}",
            'summary': f"IPCC-relevant climate information for {region}"
        }
        
        ipcc_context = self.ipcc_engine.get_firecrawl_context(
            mock_record,
            focus_areas=region_config.get('focus_areas', [])
        )
        
        # Kombiniere Keywords
        keywords = region_config['keywords'] + ipcc_context['keywords'][:5]
        keywords = list(set(keywords))[:10]  # Limit auf 10
        
        console.print(f"  [dim]IPCC-Keywords: {', '.join(keywords[:5])}...[/dim]")
        console.print(f"  [dim]IPCC-Risiken: {', '.join(region_config['ipcc_risks'][:3])}[/dim]")
        
        try:
            # 1. Firecrawl Search mit IPCC-Kontext
            search_results, credits = await asyncio.to_thread(
                self.firecrawl.enrich_with_search,
                keywords=keywords,
                region=region,
                limit=max_results,
                scrape_content=True,
                categories=["research"],  # Fokus auf wissenschaftliche Quellen
                ipcc_context=ipcc_context
            )
            
            console.print(f"  [green]✅ {len(search_results)} Ergebnisse gefunden[/green]")
            
            # 2. Verarbeite jedes Suchergebnis
            for result in search_results:
                url = result.get('url') or result.get('sourceURL', '')
                if not url or url in discovered_urls:
                    continue
                
                discovered_urls.add(url)
                
                # 3. Extrahiere strukturierte Daten mit IPCC-Schema
                try:
                    extracted_data, extract_credits = await asyncio.to_thread(
                        self.firecrawl.enrich_with_extract,
                        url=url,
                        extraction_schema=self.get_ipcc_extraction_schema(
                            region_config.get('focus_areas', [])
                        ),
                        location={'region': region}
                    )
                    
                    # 4. Erstelle Record aus extrahierten Daten
                    record = self._create_record_from_extraction(
                        extracted_data,
                        result,
                        region,
                        region_config,
                        url
                    )
                    
                    if record:
                        all_records.append(record)
                        console.print(f"    [dim]✓ {record.get('title', 'N/A')[:50]}...[/dim]")
                
                except Exception as e:
                    console.print(f"    [yellow]⚠️  Extraktion fehlgeschlagen für {url}: {e}[/yellow]")
                    # Fallback: Verwende Search-Result direkt
                    record = self._create_record_from_search_result(
                        result,
                        region,
                        region_config,
                        url
                    )
                    if record:
                        all_records.append(record)
            
        except Exception as e:
            console.print(f"  [red]❌ Fehler bei Suche: {e}[/red]")
            return {
                'region': region,
                'records': [],
                'error': str(e)
            }
        
        return {
            'region': region,
            'records': all_records,
            'urls_discovered': len(discovered_urls),
            'records_extracted': len(all_records)
        }
    
    def _create_record_from_extraction(
        self,
        extracted_data: Dict[str, Any],
        search_result: Dict[str, Any],
        region: str,
        region_config: Dict[str, Any],
        url: str
    ) -> Optional[Dict[str, Any]]:
        """Erstelle Record aus extrahierten Daten"""
        try:
            extract = extracted_data.get('extract', {}) if isinstance(extracted_data, dict) else {}
            
            record = {
                'url': url,
                'source_domain': self._extract_domain(url),
                'source_name': self._extract_source_name(url),
                'fetched_at': datetime.now().isoformat(),
                'title': extract.get('title') or search_result.get('title', '') or self._extract_title(search_result),
                'summary': extract.get('summary') or search_result.get('description', '') or self._extract_summary(search_result),
                'publish_date': extract.get('publish_date') or search_result.get('publishedTime', ''),
                'region': extract.get('region') or region,
                'topics': extract.get('ipcc_risks', []) + region_config.get('ipcc_risks', []),
                'content_type': 'research',
                'full_text': search_result.get('markdown', '')[:5000] if search_result.get('markdown') else '',
            }
            
            # IPCC-spezifische Daten
            if extract.get('temperature_data'):
                temp_data = extract['temperature_data']
                record['temperature_value'] = temp_data.get('value')
                record['temperature_anomaly'] = temp_data.get('anomaly')
            
            if extract.get('precipitation_data'):
                precip_data = extract['precipitation_data']
                record['precipitation_value'] = precip_data.get('value')
                record['precipitation_anomaly'] = precip_data.get('anomaly')
            
            record['ipcc_relevance'] = extract.get('ipcc_relevance', 'medium')
            record['climate_indicators'] = extract.get('climate_indicators', [])
            
            return record
            
        except Exception as e:
            console.print(f"      [yellow]⚠️  Fehler bei Record-Erstellung: {e}[/yellow]")
            return None
    
    def _create_record_from_search_result(
        self,
        search_result: Dict[str, Any],
        region: str,
        region_config: Dict[str, Any],
        url: str
    ) -> Optional[Dict[str, Any]]:
        """Fallback: Erstelle Record direkt aus Search-Result"""
        try:
            return {
                'url': url,
                'source_domain': self._extract_domain(url),
                'source_name': self._extract_source_name(url),
                'fetched_at': datetime.now().isoformat(),
                'title': search_result.get('title', '') or self._extract_title(search_result),
                'summary': search_result.get('description', '') or self._extract_summary(search_result),
                'publish_date': search_result.get('publishedTime', ''),
                'region': region,
                'topics': region_config.get('ipcc_risks', []),
                'content_type': 'research',
                'full_text': search_result.get('markdown', '')[:5000] if search_result.get('markdown') else '',
                'ipcc_relevance': 'medium',
                'climate_indicators': []
            }
        except Exception as e:
            return None
    
    def _extract_domain(self, url: str) -> str:
        """Extrahiere Domain aus URL"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    
    def _extract_source_name(self, url: str) -> str:
        """Extrahiere Source-Name aus URL"""
        domain = self._extract_domain(url)
        if 'nasa.gov' in domain:
            return 'NASA'
        elif 'un.org' in domain or 'ipcc.ch' in domain:
            return 'UN/IPCC'
        elif 'worldbank.org' in domain:
            return 'World Bank'
        elif 'wfp.org' in domain:
            return 'WFP'
        elif 'nature.com' in domain or 'science.org' in domain:
            return 'Research'
        else:
            return 'Other'
    
    def _extract_title(self, result: Dict[str, Any]) -> str:
        """Extrahiere Titel aus Result"""
        return result.get('title', '') or result.get('name', '') or ''
    
    def _extract_summary(self, result: Dict[str, Any]) -> str:
        """Extrahiere Zusammenfassung aus Result"""
        summary = result.get('description', '') or result.get('markdown', '')
        if summary:
            # Nimm erste 3 Sätze
            sentences = summary.split('.')[:3]
            return '. '.join(sentences).strip()[:500]
        return ''
    
    async def run_full_pipeline(self, max_results_per_region: int = 15) -> Dict[str, Any]:
        """Führe vollständige Pipeline aus"""
        console.print(Panel.fit(
            "[bold green]🚀 Firecrawl IPCC Pipeline[/bold green]\n"
            "[cyan]Dynamische URL-Generierung mit IPCC-Kriterien[/cyan]",
            border_style="green"
        ))
        
        results = {}
        
        # Zeige aktuelle DB-Statistiken
        stats = self.db.get_statistics()
        console.print(f"\n[bold blue]📊 Aktuelle Datenbank: {stats.get('total_records', 0)} Records[/bold blue]\n")
        
        # Verarbeite jede Region mit IPCC-Kriterien
        for region, region_config in self.ipcc_search_regions.items():
            try:
                result = await self.search_and_extract_region(
                    region=region,
                    region_config=region_config,
                    max_results=max_results_per_region
                )
                
                # Speichere Records in Datenbank
                if result.get('records'):
                    db_result = self.db.insert_records_batch(result['records'])
                    result['db_new'] = db_result.get('new', 0)
                    result['db_updated'] = db_result.get('updated', 0)
                
                results[region] = result
                
            except Exception as e:
                console.print(f"[red]❌ Fehler bei {region}: {e}[/red]")
                results[region] = {
                    'region': region,
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
        
        results_table = Table(title="📈 Ergebnisse (IPCC-basiert)", show_header=True, header_style="bold magenta")
        results_table.add_column("Region", style="cyan")
        results_table.add_column("URLs gefunden", style="yellow")
        results_table.add_column("Records extrahiert", style="green")
        results_table.add_column("Neu in DB", style="green")
        results_table.add_column("Aktualisiert", style="blue")
        
        total_urls = 0
        total_records = 0
        total_new = 0
        total_updated = 0
        
        for region, result in results.items():
            if 'error' in result:
                results_table.add_row(region, "❌", "Fehler", "-", "-")
            else:
                urls = result.get('urls_discovered', 0)
                records = result.get('records_extracted', 0)
                new = result.get('db_new', 0)
                updated = result.get('db_updated', 0)
                
                results_table.add_row(
                    region,
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
    pipeline = FirecrawlIPCCPipeline()
    
    # Führe Pipeline aus
    results = await pipeline.run_full_pipeline(max_results_per_region=15)
    
    console.print("\n[bold green]✅ Fertig![/bold green]")
    console.print("\n[bold blue]Nächste Schritte:[/bold blue]")
    console.print("  1. Geocoding: python geocode_existing_records.py")
    console.print("  2. Frontend-Daten: python generate_frontend_data.py")
    console.print("  3. Web-App starten: python web_app.py")


if __name__ == "__main__":
    asyncio.run(main())

