#!/usr/bin/env python3
"""
Crawl4AI Integration für verbessertes Crawling
Kombiniert Crawl4AI mit Firecrawl für optimale Datenextraktion
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

console = Console()

# Crawl4AI Import (falls installiert)
try:
    from crawl4ai import AsyncWebCrawler
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False
    console.print("[yellow]⚠️  Crawl4AI nicht installiert. Installiere mit: pip install crawl4ai[/yellow]")

from firecrawl_enrichment import FirecrawlEnricher, CostTracker
from database import DatabaseManager
from extractors import ExtractorFactory
from config import Config


class Crawl4AICrawler:
    """Crawl4AI-basierter Crawler für komplexe Seiten"""
    
    def __init__(self):
        if not CRAWL4AI_AVAILABLE:
            raise ImportError("Crawl4AI nicht verfügbar. Installiere mit: pip install crawl4ai")
        
        self.config = Config()
    
    async def crawl_url(self, url: str, extract_markdown: bool = True) -> Dict[str, Any]:
        """Crawle eine URL mit Crawl4AI"""
        try:
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(
                    url=url,
                    word_count_threshold=10,
                    extraction_strategy=None,  # Keine LLM-Extraktion, nur Markdown
                    bypass_cache=True
                )
                
                return {
                    'success': result.success if hasattr(result, 'success') else True,
                    'url': url,
                    'markdown': result.markdown if hasattr(result, 'markdown') else '',
                    'html': result.html if hasattr(result, 'html') else '',
                    'links': result.links if hasattr(result, 'links') else [],
                    'images': result.images if hasattr(result, 'images') else [],
                    'metadata': result.metadata if hasattr(result, 'metadata') else {}
                }
        except Exception as e:
            console.print(f"[red]Crawl4AI Fehler für {url}: {e}[/red]")
            return {
                'success': False,
                'url': url,
                'error': str(e),
                'markdown': '',
                'html': '',
                'links': [],
                'images': []
            }
    
    async def discover_article_links(self, start_url: str, max_links: int = 50) -> List[str]:
        """Entdecke Artikel-Links auf einer Seite"""
        result = await self.crawl_url(start_url)
        
        if not result['success']:
            return []
        
        # Extrahiere Links aus Markdown oder HTML
        links = result.get('links', [])
        
        # Filtere relevante Artikel-Links
        article_links = []
        for link in links:
            if self._is_article_link(link, start_url):
                article_links.append(link)
                if len(article_links) >= max_links:
                    break
        
        return article_links
    
    def _is_article_link(self, link: str, base_url: str) -> bool:
        """Prüfe ob Link zu einem Artikel führt"""
        # WFP-spezifische Patterns
        if 'wfp.org' in base_url.lower():
            if '/news/' in link or '/stories/' in link:
                # Vermeide Übersichtsseiten
                exclude = ['/news/all', '/news/archive', '/news/press-release']
                if not any(x in link for x in exclude):
                    return True
        
        # NASA-spezifische Patterns
        elif 'nasa.gov' in base_url.lower():
            if '/images/' in link or '/features/' in link:
                return True
        
        # UN Press-spezifische Patterns
        elif 'press.un.org' in base_url.lower():
            if '/en/content/' in link:
                return True
        
        # World Bank-spezifische Patterns
        elif 'worldbank.org' in base_url.lower():
            if '/en/news/' in link:
                return True
        
        return False


class HybridCrawler:
    """Kombiniert Crawl4AI (Discovery) mit Firecrawl (Strukturierte Extraktion)"""
    
    def __init__(self):
        self.crawl4ai = Crawl4AICrawler() if CRAWL4AI_AVAILABLE else None
        self.config = Config()
        self.cost_tracker = CostTracker()
        self.firecrawl = FirecrawlEnricher(self.config.FIRECRAWL_API_KEY, self.cost_tracker)
        self.db = DatabaseManager()
        self.extractor_factory = ExtractorFactory(self.config)
    
    async def crawl_critical_city_data(
        self,
        city_name: str,
        country_code: str,
        urls: List[str]
    ) -> Dict[str, Any]:
        """Crawle Daten für eine kritische Stadt"""
        console.print(f"\n[bold cyan]🏙️  Crawle Daten für {city_name}, {country_code}[/bold cyan]")
        
        all_data = {
            'city': city_name,
            'country_code': country_code,
            'records': [],
            'climate_data': [],
            'conflict_data': [],
            'ipcc_data': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # 1. Crawle mit Crawl4AI (Discovery)
        if self.crawl4ai:
            console.print(f"[green]📡 Phase 1: Discovery mit Crawl4AI...[/green]")
            discovered_urls = []
            
            for url in urls:
                try:
                    links = await self.crawl4ai.discover_article_links(url, max_links=20)
                    discovered_urls.extend(links)
                    console.print(f"  ✅ {url}: {len(links)} Links gefunden")
                except Exception as e:
                    console.print(f"  ❌ {url}: {e}")
            
            # Kombiniere mit ursprünglichen URLs
            all_urls = list(set(urls + discovered_urls))
        else:
            all_urls = urls
        
        # 2. Extrahiere mit Firecrawl (Strukturierte Daten)
        console.print(f"\n[green]📊 Phase 2: Strukturierte Extraktion mit Firecrawl...[/green]")
        
        for url in all_urls[:50]:  # Limit auf 50 URLs
            try:
                # Firecrawl für strukturierte Extraktion
                search_results, _ = self.firecrawl.enrich_with_search(
                    keywords=[city_name, f"{city_name} climate", f"{city_name} conflict"],
                    region=city_name,
                    limit=3,
                    scrape_content=True
                )
                
                # Speichere Ergebnisse
                for result in search_results:
                    all_data['records'].append({
                        'url': result.get('url', url),
                        'title': result.get('title', ''),
                        'description': result.get('description', ''),
                        'content': result.get('markdown', '')[:1000] if result.get('markdown') else '',
                        'source': 'firecrawl'
                    })
            
            except Exception as e:
                console.print(f"  ⚠️  Fehler bei {url}: {e}")
        
        return all_data
    
    async def crawl_wfp_with_crawl4ai(self) -> List[Dict[str, Any]]:
        """Crawle WFP mit Crawl4AI"""
        console.print("\n[bold cyan]🌾 Crawle WFP mit Crawl4AI[/bold cyan]")
        
        if not self.crawl4ai:
            console.print("[red]❌ Crawl4AI nicht verfügbar[/red]")
            return []
        
        wfp_urls = [
            "https://www.wfp.org/news",
            "https://www.wfp.org/stories",
            "https://www.wfp.org/news/latest"
        ]
        
        all_articles = []
        
        for url in wfp_urls:
            try:
                console.print(f"\n[cyan]Crawle {url}...[/cyan]")
                
                # 1. Entdecke Artikel-Links
                article_links = await self.crawl4ai.discover_article_links(url, max_links=30)
                console.print(f"  ✅ {len(article_links)} Artikel gefunden")
                
                # 2. Crawle jeden Artikel
                for article_url in article_links[:20]:  # Limit auf 20
                    try:
                        result = await self.crawl4ai.crawl_url(article_url)
                        
                        if result['success'] and result['markdown']:
                            # Extrahiere mit Extractor
                            extractor = self.extractor_factory.get_extractor(article_url)
                            
                            # Erstelle FetchResult-ähnliches Objekt
                            from fetchers import FetchResult
                            fetch_result = FetchResult(
                                url=article_url,
                                success=True,
                                content=result['html'],
                                status_code=200
                            )
                            
                            record = extractor.extract(fetch_result)
                            
                            if record:
                                # Speichere in DB
                                record_id, is_new = self.db.insert_record(record)
                                all_articles.append({
                                    'record_id': record_id,
                                    'url': article_url,
                                    'title': record.title if hasattr(record, 'title') else '',
                                    'is_new': is_new
                                })
                                console.print(f"    ✅ {record.title[:50] if hasattr(record, 'title') and record.title else 'N/A'}")
                    
                    except Exception as e:
                        console.print(f"    ❌ Fehler bei {article_url}: {e}")
                        continue
                
                # Rate Limiting
                await asyncio.sleep(2)
            
            except Exception as e:
                console.print(f"[red]Fehler bei {url}: {e}[/red]")
                continue
        
        return all_articles


async def main():
    """Hauptfunktion"""
    console.print(Panel.fit(
        "[bold green]🚀 Crawl4AI + Firecrawl Hybrid Crawler[/bold green]",
        border_style="green"
    ))
    
    # Prüfe Crawl4AI Installation
    if not CRAWL4AI_AVAILABLE:
        console.print("\n[yellow]📦 Installiere Crawl4AI...[/yellow]")
        import subprocess
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "crawl4ai"], check=True)
            console.print("[green]✅ Crawl4AI installiert![/green]")
            # Reload
            from crawl4ai import AsyncWebCrawler
        except Exception as e:
            console.print(f"[red]❌ Installation fehlgeschlagen: {e}[/red]")
            console.print("[yellow]Bitte manuell installieren: pip install crawl4ai[/yellow]")
            return
    
    crawler = HybridCrawler()
    
    # Option 1: WFP-Crawling reparieren
    console.print("\n[bold yellow]Option 1: WFP-Crawling mit Crawl4AI[/bold yellow]")
    wfp_articles = await crawler.crawl_wfp_with_crawl4ai()
    
    console.print(f"\n[green]✅ {len(wfp_articles)} WFP-Artikel gecrawlt[/green]")
    
    # Option 2: Kritische Städte crawlen
    console.print("\n[bold yellow]Option 2: Kritische Städte crawlen[/bold yellow]")
    
    critical_cities = [
        {
            'name': 'Athens',
            'country_code': 'GR',
            'urls': [
                'https://www.eea.europa.eu/themes/climate',
                'https://climate.nasa.gov',
                'https://www.unhcr.org/refugee-statistics'
            ]
        }
    ]
    
    for city in critical_cities[:1]:  # Test mit einer Stadt
        data = await crawler.crawl_critical_city_data(
            city['name'],
            city['country_code'],
            city['urls']
        )
        
        console.print(f"\n[green]✅ Daten für {city['name']}: {len(data['records'])} Records[/green]")


if __name__ == "__main__":
    asyncio.run(main())



