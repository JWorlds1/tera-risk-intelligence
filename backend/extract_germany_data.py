#!/usr/bin/env python3
"""
Extrahiere 100 Deutschland-Daten mit Firecrawl und IPCC-Kriterien
Speichert in SQLite-Datenbank: data/climate_conflict.db
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import requests

sys.path.append(str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from config import Config
from database import DatabaseManager
from firecrawl_enrichment import FirecrawlEnricher, CostTracker
from ipcc_context_engine import IPCCContextEngine
from extractors import ExtractorFactory
from schemas import PageRecord
from free_llm_extractor import FreeLLMExtractor

console = Console()


class GermanyDataExtractor:
    """Extrahiert Deutschland-Daten mit IPCC-Kriterien"""
    
    def __init__(self):
        self.config = Config()
        self.db = DatabaseManager()  # SQLite: data/climate_conflict.db
        self.cost_tracker = CostTracker()
        self.firecrawl = FirecrawlEnricher(self.config.FIRECRAWL_API_KEY, self.cost_tracker)
        self.ipcc_engine = IPCCContextEngine()
        self.extractor_factory = ExtractorFactory(self.config)
        self.llm_extractor = FreeLLMExtractor(
            ollama_host=self.config.OLLAMA_HOST,
            model=self.config.OLLAMA_MODEL
        )
        
        # Deutschland-spezifische URLs und IPCC-Kriterien
        self.germany_urls = [
            # DWD (Deutscher Wetterdienst)
            "https://www.dwd.de/DE/klimaumwelt/klimawandel/klimawandel_node.html",
            "https://www.dwd.de/DE/klimaumwelt/klimawandel/klimawandel_node.html",
            "https://www.dwd.de/DE/klimaumwelt/klimawandel/klimawandel_node.html",
            
            # Umweltbundesamt
            "https://www.umweltbundesamt.de/themen/klima-energie/klimawandel",
            "https://www.umweltbundesamt.de/themen/klima-energie/klimafolgen-anpassung",
            "https://www.umweltbundesamt.de/themen/klima-energie/klimaschutz",
            
            # BMUV (Bundesministerium)
            "https://www.bmuv.de/themen/klimaschutz/klimaschutz",
            "https://www.bmuv.de/themen/klimaschutz/klimaanpassung",
            
            # IPCC Deutschland
            "https://www.de-ipcc.de/",
            "https://www.de-ipcc.de/de/aktuelles.html",
            
            # Klimafolgenforschung
            "https://www.klimafolgenforschung.de/",
            "https://www.pik-potsdam.de/de",
            
            # Weitere Quellen
            "https://www.bmuv.de/themen/klimaschutz/klimaschutz/klimaschutz-in-deutschland",
            "https://www.umweltbundesamt.de/themen/klima-energie/klimawandel/auswirkungen-des-klimawandels",
        ]
        
        self.germany_ipcc_config = {
            "region": "Germany",
            "country_code": "DE",
            "ipcc_risks": [
                "Heavy precipitation",
                "Extreme heat events",
                "Drought",
                "Flooding",
                "Biodiversity loss"
            ],
            "focus_areas": ["temperature", "precipitation", "emissions", "human_impacts"]
        }
    
    def get_ipcc_extraction_schema(self) -> Dict[str, Any]:
        """IPCC-basiertes Extraktionsschema für Deutschland"""
        return {
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
            "location": {
                "type": "string",
                "description": "Spezifischer Ort in Deutschland (z.B. Stadt, Region)"
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
            "climate_event": {
                "type": "string",
                "description": "Art des Klimaereignisses (flood, drought, heat wave, etc.)"
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
                "description": "Klima-Indikatoren"
            }
        }
    
    async def extract_germany_data(self, target_count: int = 100) -> Dict[str, Any]:
        """Extrahiere Deutschland-Daten bis zum Ziel erreicht ist"""
        console.print(Panel.fit(
            f"[bold green]🇩🇪 Deutschland-Daten Extraktion[/bold green]\n"
            f"[cyan]Ziel: {target_count} Records mit IPCC-Kriterien[/cyan]\n"
            f"[dim]Datenbank: data/climate_conflict.db[/dim]",
            border_style="green"
        ))
        
        all_records = []
        discovered_urls = set()
        search_iterations = 0
        max_iterations = 20  # Maximal 20 Suchiterationen
        
        # Erstelle IPCC-Kontext für Deutschland
        mock_record = {
            'region': 'Germany',
            'title': 'Climate data for Germany',
            'summary': 'IPCC-relevant climate information for Germany'
        }
        
        ipcc_context = self.ipcc_engine.get_firecrawl_context(
            mock_record,
            focus_areas=self.germany_ipcc_config['focus_areas']
        )
        
        console.print(f"\n[bold cyan]📊 IPCC-Kontext erstellt:[/bold cyan]")
        console.print(f"  Keywords: {len(ipcc_context['keywords'])}")
        console.print(f"  Focus Areas: {', '.join(self.germany_ipcc_config['focus_areas'])}")
        console.print(f"  IPCC-Risiken: {', '.join(self.germany_ipcc_config['ipcc_risks'][:3])}...\n")
        
        # Zeige aktuelle DB-Statistiken
        stats = self.db.get_statistics()
        initial_count = stats.get('total_records', 0)
        console.print(f"[bold blue]📊 Aktuelle Datenbank: {initial_count} Records[/bold blue]\n")
        
        # Verwende direkte URLs und Crawl für Discovery
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task(
                f"[cyan]Extrahiere Daten... ({len(all_records)}/{target_count})",
                total=target_count
            )
            
            # Schritt 1: Verwende direkte URLs (Crawl hat API-Probleme)
            console.print(f"\n[bold cyan]📡 Phase 1: Verwende direkte URLs...[/bold cyan]")
            
            all_urls_to_process = set(self.germany_urls)
            
            # Erweitere URL-Liste mit weiteren bekannten Deutschland-Klima-URLs
            additional_urls = [
                "https://www.dwd.de/DE/klimaumwelt/klimawandel/klimawandel_node.html",
                "https://www.umweltbundesamt.de/themen/klima-energie/klimawandel/auswirkungen-des-klimawandels",
                "https://www.umweltbundesamt.de/themen/klima-energie/klimafolgen-anpassung/klimafolgen",
                "https://www.bmuv.de/themen/klimaschutz/klimaschutz/klimaschutz-in-deutschland",
                "https://www.pik-potsdam.de/de/aktuelles/nachrichten",
                "https://www.de-ipcc.de/de/aktuelles.html",
            ]
            all_urls_to_process.update(additional_urls)
            
            console.print(f"  [green]✅ {len(all_urls_to_process)} URLs zum Verarbeiten[/green]")
            
            console.print(f"\n[bold cyan]📊 Phase 2: Extrahiere {len(all_urls_to_process)} URLs...[/bold cyan]")
            
            # Schritt 2: Extrahiere jede URL
            for url in list(all_urls_to_process)[:target_count * 2]:  # Mehr URLs für bessere Erfolgsrate
                if len(all_records) >= target_count:
                    break
                
                if url in discovered_urls:
                    continue
                
                discovered_urls.add(url)
                
                try:
                    # Schritt 1: Scrape URL mit Firecrawl (direkter API-Call - funktioniert!)
                    scrape_result = None
                    try:
                        # Verwende direkten API-Call (funktioniert zuverlässig)
                        response = await asyncio.to_thread(
                            requests.post,
                            "https://api.firecrawl.dev/v0/scrape",
                            headers={
                                "Authorization": f"Bearer {self.config.FIRECRAWL_API_KEY}",
                                "Content-Type": "application/json"
                            },
                            json={
                                "url": url,
                                "formats": ["markdown"],
                                "onlyMainContent": True
                            },
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            scrape_result = response.json()
                            # Firecrawl gibt Daten in 'data' zurück
                            if 'data' in scrape_result:
                                scrape_result = scrape_result['data']
                        else:
                            console.print(f"    [yellow]⚠️  API Status {response.status_code} für {url[:50]}...[/yellow]")
                            continue
                    except Exception as scrape_error:
                        console.print(f"    [yellow]⚠️  Scrape-Fehler: {scrape_error}[/yellow]")
                        continue
                    
                    if not scrape_result:
                        continue
                    
                    # Extrahiere Markdown aus Firecrawl-Response
                    markdown = scrape_result.get('markdown', '') or scrape_result.get('content', '') or scrape_result.get('text', '')
                    
                    if not markdown:
                        continue
                    
                    # Schritt 2: Pattern-Matching Extraktion (schnell und zuverlässig)
                    # LLM ist optional und langsamer - Pattern-Matching ist Standard
                    extracted_data = self.llm_extractor.extract_with_llm(
                        text=markdown,
                        schema=self.get_ipcc_extraction_schema(),
                        use_llm=False  # Pattern-Matching verwenden (schneller)
                    )
                    
                    # Erstelle Record mit LLM-extrahierten Daten
                    record = self._create_record_from_llm_extraction(
                        extracted_data,
                        scrape_result,
                        url,
                        markdown
                    )
                    
                    if record:
                        all_records.append(record)
                        progress.update(task, completed=len(all_records))
                        llm_status = "🤖" if self.llm_extractor.ollama_available else "📝"
                        console.print(f"    [dim]{llm_status} [{len(all_records)}] {record.get('title', 'N/A')[:60]}...[/dim]")
                
                except Exception as e:
                    console.print(f"    [yellow]⚠️  Fehler bei {url}: {e}[/yellow]")
                    continue
        
        # Speichere alle Records in Datenbank
        console.print(f"\n[bold green]💾 Speichere {len(all_records)} Records in Datenbank...[/bold green]")
        
        if all_records:
            # Konvertiere Dicts zu PageRecord-Objekten
            page_records = []
            for record_dict in all_records:
                try:
                    page_record = PageRecord(**record_dict)
                    page_records.append(page_record)
                except Exception as e:
                    console.print(f"  [yellow]⚠️  Fehler bei Konvertierung: {e}[/yellow]")
                    continue
            
            db_result = self.db.insert_records_batch(page_records)
            new_count = db_result.get('new', 0)
            updated_count = db_result.get('updated', 0)
            
            console.print(f"  [green]✅ {new_count} neue Records[/green]")
            console.print(f"  [blue]🔄 {updated_count} aktualisierte Records[/blue]")
        
        # Zeige finale Statistiken
        final_stats = self.db.get_statistics()
        final_count = final_stats.get('total_records', 0)
        
        console.print(f"\n[bold blue]📊 Finale Datenbank-Statistiken:[/bold blue]")
        console.print(f"  Gesamt Records: {final_count} (+{final_count - initial_count})")
        console.print(f"  Deutschland Records: {len([r for r in all_records if r.get('region') == 'Germany'])}")
        
        # Kosten-Zusammenfassung
        cost_summary = self.cost_tracker.get_summary()
        console.print(f"\n[bold yellow]💰 Kosten-Zusammenfassung:[/bold yellow]")
        console.print(f"  Firecrawl Credits verwendet: {cost_summary['firecrawl_credits_used']:.1f}")
        console.print(f"  Firecrawl Credits verbleibend: {cost_summary['firecrawl_credits_remaining']:.1f}")
        console.print(f"  Requests: {cost_summary['requests_made']}")
        
        return {
            'records_extracted': len(all_records),
            'records_saved': new_count if all_records else 0,
            'urls_discovered': len(discovered_urls),
            'search_iterations': search_iterations,
            'cost_summary': cost_summary
        }
    
    def _create_record_from_llm_extraction(
        self,
        extracted_data: Dict[str, Any],
        scrape_result: Dict[str, Any],
        url: str,
        markdown: str
    ) -> Optional[Dict[str, Any]]:
        """Erstelle Record aus LLM-extrahierten Daten"""
        try:
            metadata = scrape_result.get('metadata', {})
            
            # Kombiniere LLM-Extraktion mit Scrape-Metadaten
            record = {
                'url': url,
                'source_domain': self._extract_domain(url),
                'source_name': self._extract_source_name(url),
                'fetched_at': datetime.now(),
                'title': extracted_data.get('title') or metadata.get('title', '') or self._extract_title_from_markdown(markdown),
                'summary': extracted_data.get('summary') or metadata.get('description', '') or self._extract_summary_from_markdown(markdown),
                'publish_date': extracted_data.get('publish_date') or metadata.get('publishedTime', ''),
                'region': extracted_data.get('location') or 'Germany',
                'topics': list(set(extracted_data.get('ipcc_risks', []) + self.germany_ipcc_config['ipcc_risks'])),  # Entferne Duplikate
                'content_type': 'research',
                'full_text': markdown[:5000] if markdown else '',
            }
            
            return record
            
        except Exception as e:
            console.print(f"      [yellow]⚠️  Fehler bei Record-Erstellung: {e}[/yellow]")
            return None
    
    def _create_record_from_scrape_result(
        self,
        scrape_result: Dict[str, Any],
        url: str
    ) -> Optional[Dict[str, Any]]:
        """Fallback: Erstelle Record direkt aus Scrape-Result"""
        try:
            markdown = scrape_result.get('markdown', '') or scrape_result.get('content', '')
            metadata = scrape_result.get('metadata', {})
            
            return {
                'url': url,
                'source_domain': self._extract_domain(url),
                'source_name': self._extract_source_name(url),
                'fetched_at': datetime.now(),  # datetime object
                'title': metadata.get('title', '') or self._extract_title_from_markdown(markdown),
                'summary': metadata.get('description', '') or self._extract_summary_from_markdown(markdown),
                'publish_date': metadata.get('publishedTime', ''),
                'region': 'Germany',
                'topics': self.germany_ipcc_config['ipcc_risks'],
                'content_type': 'research',
                'full_text': markdown[:5000] if markdown else '',
            }
        except Exception as e:
            return None
    
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
        sentences = markdown.split('.')[:3]
        summary = '. '.join(sentences).strip()
        return summary[:500] if summary else ''
    
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
        elif 'dwd.de' in domain or 'umweltbundesamt.de' in domain:
            return 'German Government'
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
            sentences = summary.split('.')[:3]
            return '. '.join(sentences).strip()[:500]
        return ''


async def main():
    """Hauptfunktion"""
    extractor = GermanyDataExtractor()
    
    # Extrahiere 100 Deutschland-Daten
    results = await extractor.extract_germany_data(target_count=100)
    
    console.print("\n[bold green]✅ Extraktion abgeschlossen![/bold green]")
    console.print("\n[bold blue]Datenbank-Info:[/bold blue]")
    console.print("  📁 Pfad: data/climate_conflict.db")
    console.print("  📊 Tabelle: records")
    console.print("  🔍 Prüfen: sqlite3 data/climate_conflict.db 'SELECT COUNT(*) FROM records WHERE region=\"Germany\" OR primary_country_code=\"DE\";'")
    console.print("\n[bold blue]Nächste Schritte:[/bold blue]")
    console.print("  1. Geocoding: python geocode_existing_records.py")
    console.print("  2. Frontend-Daten: python generate_frontend_data.py")
    console.print("  3. Web-App starten: python web_app.py")


if __name__ == "__main__":
    asyncio.run(main())

