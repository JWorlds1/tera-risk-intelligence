#!/usr/bin/env python3
"""
Intelligente URL-Discovery mit Firecrawl und Ollama
- Generiert automatisch gute Suchqueries mit Ollama
- Findet relevante URLs mit Firecrawl Search
- Crawlt und extrahiert Daten für Geospatial Intelligence
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
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from config import Config
from database import DatabaseManager
from firecrawl_enrichment import FirecrawlEnricher, CostTracker
from ipcc_context_engine import IPCCContextEngine
from schemas import PageRecord
from free_llm_extractor import FreeLLMExtractor

console = Console()


class IntelligentURLDiscovery:
    """Intelligente URL-Discovery mit automatischer Prompt-Generierung"""
    
    def __init__(self):
        self.config = Config()
        self.db = DatabaseManager()
        self.cost_tracker = CostTracker()
        self.firecrawl = FirecrawlEnricher(self.config.FIRECRAWL_API_KEY, self.cost_tracker)
        self.ipcc_engine = IPCCContextEngine()
        self.llm_extractor = FreeLLMExtractor(
            ollama_host=self.config.OLLAMA_HOST,
            model=self.config.OLLAMA_MODEL
        )
        
        # Basis-Themen für Geospatial Intelligence
        self.base_topics = {
            "Germany": {
                "climate_events": ["flood", "drought", "heat wave", "extreme weather"],
                "regions": ["Rhein", "Elbe", "Nordsee", "Ostsee", "Alpen", "Bayern", "Nordrhein-Westfalen"],
                "topics": ["climate change", "klimawandel", "temperature", "precipitation", "sea level"]
            }
        }
    
    def generate_search_queries_with_llm(self, topic: str, region: str = "Germany") -> List[str]:
        """Generiere Suchqueries automatisch mit Ollama"""
        console.print(f"\n[bold cyan]🤖 Generiere Suchqueries für {topic}...[/bold cyan]")
        
        base_info = self.base_topics.get(region, {})
        
        prompt = f"""Generiere 10 spezifische Suchqueries für Geospatial Intelligence zum Thema "{topic}" in {region}.

Fokus auf:
- Klimaereignisse: {', '.join(base_info.get('climate_events', []))}
- Regionen: {', '.join(base_info.get('regions', []))}
- Themen: {', '.join(base_info.get('topics', []))}

Die Queries sollten:
1. Spezifisch sein (Stadt, Region, Ereignis)
2. IPCC-relevant sein
3. Geospatial-Daten enthalten (Koordinaten, Orte, Regionen)
4. Auf Deutsch und Englisch sein

Antworte NUR als JSON-Array von Strings:
["query 1", "query 2", "query 3", ...]
"""
        
        try:
            if self.llm_extractor.ollama_available:
                response = requests.post(
                    f"{self.config.OLLAMA_HOST}/api/generate",
                    json={
                        "model": self.config.OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    queries_text = result.get('response', '')
                    try:
                        queries = json.loads(queries_text)
                        if isinstance(queries, list):
                            console.print(f"  [green]✅ {len(queries)} Queries generiert[/green]")
                            return queries[:10]  # Max 10
                    except:
                        pass
        except Exception as e:
            console.print(f"  [yellow]⚠️  LLM-Fehler: {e}[/yellow]")
        
        # Fallback: Manuelle Queries
        fallback_queries = [
            f"{topic} {region} climate",
            f"{topic} {region} klimawandel",
            f"{topic} {region} extreme weather",
            f"{topic} {region} IPCC",
            f"{topic} {region} temperature",
            f"{topic} {region} flood",
            f"{topic} {region} drought"
        ]
        console.print(f"  [dim]Verwende Fallback-Queries: {len(fallback_queries)}[/dim]")
        return fallback_queries
    
    async def discover_urls_with_firecrawl_search(
        self,
        queries: List[str],
        max_results_per_query: int = 10
    ) -> List[Dict[str, Any]]:
        """Finde URLs mit Firecrawl Search"""
        console.print(f"\n[bold cyan]🔍 Suche URLs mit Firecrawl...[/bold cyan]")
        
        all_urls = []
        discovered_urls = set()
        
        for i, query in enumerate(queries, 1):
            console.print(f"  [dim]Query {i}/{len(queries)}: {query[:60]}...[/dim]")
            
            try:
                # Firecrawl Search API (direkter Call)
                response = await asyncio.to_thread(
                    requests.post,
                    "https://api.firecrawl.dev/v0/search",
                    headers={
                        "Authorization": f"Bearer {self.config.FIRECRAWL_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "query": query,
                        "limit": max_results_per_query,
                        "scrapeOptions": {
                            "formats": ["markdown"],
                            "onlyMainContent": True
                        }
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('data', {}).get('web', [])
                    
                    for result in results:
                        url = result.get('url')
                        if url and url not in discovered_urls:
                            discovered_urls.add(url)
                            all_urls.append({
                                'url': url,
                                'title': result.get('title', ''),
                                'description': result.get('description', ''),
                                'query': query,
                                'markdown': result.get('markdown', '')
                            })
                    
                    console.print(f"    [green]✅ {len(results)} URLs gefunden[/green]")
                else:
                    console.print(f"    [yellow]⚠️  Status {response.status_code}[/yellow]")
            
            except Exception as e:
                console.print(f"    [yellow]⚠️  Fehler: {e}[/yellow]")
                continue
        
        console.print(f"\n  [green]✅ Gesamt: {len(all_urls)} einzigartige URLs gefunden[/green]")
        return all_urls
    
    async def crawl_urls_with_firecrawl(
        self,
        start_urls: List[str],
        max_pages_per_url: int = 5
    ) -> List[Dict[str, Any]]:
        """Crawle URLs mit Firecrawl (korrekte API-Syntax)"""
        console.print(f"\n[bold cyan]🕷️  Crawle {len(start_urls)} URLs...[/bold cyan]")
        
        all_pages = []
        
        for url in start_urls:
            try:
                # Firecrawl Crawl API (direkter Call mit korrekter Syntax)
                response = await asyncio.to_thread(
                    requests.post,
                    "https://api.firecrawl.dev/v0/crawl",
                    headers={
                        "Authorization": f"Bearer {self.config.FIRECRAWL_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "url": url,
                        "maxDepth": 1,  # Nur 1 Ebene tief
                        "limit": max_pages_per_url,
                        "scrapeOptions": {
                            "formats": ["markdown"],
                            "onlyMainContent": True
                        }
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    pages = data.get('data', [])
                    
                    for page in pages:
                        if isinstance(page, dict):
                            page_url = page.get('url') or page.get('sourceURL', '')
                            if page_url:
                                all_pages.append({
                                    'url': page_url,
                                    'markdown': page.get('markdown', ''),
                                    'metadata': page.get('metadata', {})
                                })
                    
                    console.print(f"  [green]✅ {url[:50]}... → {len(pages)} Seiten[/green]")
                else:
                    console.print(f"  [yellow]⚠️  {url[:50]}... → Status {response.status_code}[/yellow]")
            
            except Exception as e:
                console.print(f"  [yellow]⚠️  {url[:50]}... → Fehler: {e}[/yellow]")
                continue
        
        console.print(f"\n  [green]✅ Gesamt: {len(all_pages)} Seiten gecrawlt[/green]")
        return all_pages
    
    async def extract_and_save_records(
        self,
        urls_data: List[Dict[str, Any]],
        region: str = "Germany"
    ) -> Dict[str, Any]:
        """Extrahiere und speichere Records"""
        console.print(f"\n[bold cyan]📊 Extrahiere Daten aus {len(urls_data)} URLs...[/bold cyan]")
        
        records = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task(
                "[cyan]Extrahiere...",
                total=len(urls_data)
            )
            
            for url_data in urls_data:
                url = url_data.get('url')
                markdown = url_data.get('markdown', '')
                metadata = url_data.get('metadata', {})
                
                if not markdown:
                    # Versuche Scrape falls kein Markdown vorhanden
                    try:
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
                            scrape_data = response.json().get('data', {})
                            markdown = scrape_data.get('markdown', '')
                            metadata = scrape_data.get('metadata', {})
                    except:
                        pass
                
                if not markdown:
                    progress.update(task, advance=1)
                    continue
                
                # Extrahiere mit Pattern-Matching (schnell)
                extracted_data = self.llm_extractor.extract_with_llm(
                    text=markdown,
                    schema=self._get_extraction_schema(),
                    use_llm=False  # Pattern-Matching (schnell)
                )
                
                # Erstelle Record
                record = {
                    'url': url,
                    'source_domain': self._extract_domain(url),
                    'source_name': self._extract_source_name(url),
                    'fetched_at': datetime.now(),
                    'title': extracted_data.get('title') or url_data.get('title', '') or metadata.get('title', ''),
                    'summary': extracted_data.get('summary') or url_data.get('description', '') or metadata.get('description', ''),
                    'publish_date': extracted_data.get('publish_date') or metadata.get('publishedTime', ''),
                    'region': extracted_data.get('location') or region,
                    'topics': list(set(extracted_data.get('ipcc_risks', []))),
                    'content_type': 'research',
                    'full_text': markdown[:5000] if markdown else '',
                }
                
                records.append(record)
                progress.update(task, advance=1)
        
        # Speichere in Datenbank
        if records:
            console.print(f"\n[bold green]💾 Speichere {len(records)} Records...[/bold green]")
            
            page_records = []
            for record_dict in records:
                try:
                    page_record = PageRecord(**record_dict)
                    page_records.append(page_record)
                except Exception as e:
                    console.print(f"  [yellow]⚠️  Konvertierungsfehler: {e}[/yellow]")
                    continue
            
            db_result = self.db.insert_records_batch(page_records)
            
            console.print(f"  [green]✅ {db_result.get('new', 0)} neue Records[/green]")
            console.print(f"  [blue]🔄 {db_result.get('updated', 0)} aktualisierte Records[/blue]")
        
        return {
            'records_extracted': len(records),
            'records_saved': db_result.get('new', 0) if records else 0
        }
    
    def _get_extraction_schema(self) -> Dict[str, Any]:
        """IPCC-Extraktionsschema"""
        return {
            "title": {"type": "string"},
            "summary": {"type": "string"},
            "publish_date": {"type": "string"},
            "location": {"type": "string"},
            "ipcc_risks": {"type": "array"}
        }
    
    def _extract_domain(self, url: str) -> str:
        """Extrahiere Domain"""
        from urllib.parse import urlparse
        return urlparse(url).netloc
    
    def _extract_source_name(self, url: str) -> str:
        """Extrahiere Source-Name"""
        domain = self._extract_domain(url)
        if 'dwd.de' in domain:
            return 'DWD'
        elif 'umweltbundesamt.de' in domain:
            return 'Umweltbundesamt'
        elif 'bmuv.de' in domain:
            return 'BMUV'
        elif 'pik-potsdam.de' in domain:
            return 'PIK'
        elif 'de-ipcc.de' in domain:
            return 'IPCC Deutschland'
        else:
            return 'Other'
    
    async def run_intelligent_discovery(
        self,
        topics: List[str],
        region: str = "Germany",
        target_records: int = 100
    ) -> Dict[str, Any]:
        """Führe intelligente URL-Discovery aus"""
        console.print(Panel.fit(
            "[bold green]🧠 Intelligente URL-Discovery[/bold green]\n"
            f"[cyan]Region: {region} | Ziel: {target_records} Records[/cyan]\n"
            f"[dim]Nutzt Ollama + Firecrawl für automatische URL-Findung[/dim]",
            border_style="green"
        ))
        
        all_discovered_urls = []
        
        # Für jedes Topic
        for topic in topics:
            console.print(f"\n[bold yellow]📌 Thema: {topic}[/bold yellow]")
            
            # 1. Generiere Suchqueries mit Ollama
            queries = self.generate_search_queries_with_llm(topic, region)
            
            # 2. Finde URLs mit Firecrawl Search
            search_urls = await self.discover_urls_with_firecrawl_search(queries)
            all_discovered_urls.extend(search_urls)
            
            # 3. Crawle Top-URLs für mehr Seiten
            top_urls = [u['url'] for u in search_urls[:5]]  # Top 5 URLs crawlen
            if top_urls:
                crawled_pages = await self.crawl_urls_with_firecrawl(top_urls, max_pages_per_url=3)
                all_discovered_urls.extend([{'url': p['url'], 'markdown': p.get('markdown', ''), 'metadata': p.get('metadata', {})} for p in crawled_pages])
        
        # Entferne Duplikate
        unique_urls = {}
        for url_data in all_discovered_urls:
            url = url_data['url']
            if url not in unique_urls:
                unique_urls[url] = url_data
        
        console.print(f"\n[bold green]✅ {len(unique_urls)} einzigartige URLs gefunden[/bold green]")
        
        # 4. Extrahiere und speichere Records
        results = await self.extract_and_save_records(
            list(unique_urls.values())[:target_records * 2],  # Mehr URLs für bessere Erfolgsrate
            region=region
        )
        
        # Kosten-Zusammenfassung
        cost_summary = self.cost_tracker.get_summary()
        console.print(f"\n[bold yellow]💰 Kosten-Zusammenfassung:[/bold yellow]")
        console.print(f"  Firecrawl Credits verwendet: {cost_summary['firecrawl_credits_used']:.1f}")
        console.print(f"  Firecrawl Credits verbleibend: {cost_summary['firecrawl_credits_remaining']:.1f}")
        
        return results


async def main():
    """Hauptfunktion"""
    discovery = IntelligentURLDiscovery()
    
    # Themen für Deutschland
    topics = [
        "climate change Germany",
        "extreme weather events Germany",
        "flood risk Germany",
        "drought Germany",
        "temperature increase Germany",
        "precipitation changes Germany",
        "sea level rise Germany",
        "climate adaptation Germany"
    ]
    
    # Führe Discovery aus
    results = await discovery.run_intelligent_discovery(
        topics=topics,
        region="Germany",
        target_records=100
    )
    
    console.print("\n[bold green]✅ Intelligente Discovery abgeschlossen![/bold green]")
    console.print(f"\n[bold blue]Ergebnisse:[/bold blue]")
    console.print(f"  Records extrahiert: {results.get('records_extracted', 0)}")
    console.print(f"  Records gespeichert: {results.get('records_saved', 0)}")


if __name__ == "__main__":
    asyncio.run(main())

