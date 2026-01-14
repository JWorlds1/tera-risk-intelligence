#!/usr/bin/env python3
"""
Intelligenter Crawler - Findet echte Artikel-URLs
"""
import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re

sys.path.append(str(Path(__file__).parent))

from config import Config
from fetchers import HTTPFetcher, FetchResult
from compliance import ComplianceAgent
from extractors import ExtractorFactory
from validators import ValidationAgent
from storage import StorageAgent
from database import DatabaseManager
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()


class SmartCrawler:
    """Intelligenter Crawler mit besserer Artikel-Discovery"""
    
    def __init__(self, config: Config):
        self.config = config
        self.compliance = ComplianceAgent(config)
        self.fetcher = HTTPFetcher(config, self.compliance)
        self.extractor_factory = ExtractorFactory(config)
        self.validator = ValidationAgent(config)
        self.storage = StorageAgent(config)
        self.db = DatabaseManager()
    
    async def __aenter__(self):
        await self.fetcher.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.fetcher.__aexit__(exc_type, exc_val, exc_tb)
    
    def find_article_links(self, html: str, base_url: str, source: str) -> Set[str]:
        """Finde Artikel-Links auf einer Seite"""
        soup = BeautifulSoup(html, 'lxml')
        article_urls = set()
        
        # NASA: Suche nach spezifischen Patterns
        if 'nasa' in base_url.lower():
            # Suche nach Links mit /images/ oder /features/ in der URL
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_url, href)
                
                # NASA Artikel haben oft diese Patterns
                if 'earthobservatory.nasa.gov' in full_url:
                    # Vermeide Übersichtsseiten
                    if any(x in full_url for x in ['/images/', '/features/', '/world-of-change/']):
                        # Aber nur wenn es nicht die Hauptseite ist
                        if full_url != base_url and full_url.count('/') >= 4:
                            article_urls.add(full_url)
        
        # UN Press: Suche nach Press Release Links
        elif 'press.un.org' in base_url.lower():
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_url, href)
                
                # UN Press Releases haben oft /en/content/ und eine ID
                if '/en/content/' in full_url and 'press.un.org' in full_url:
                    # Vermeide Übersichtsseiten
                    if not any(x in full_url for x in ['/content/press-releases', '/content/meetings-coverage', '/content/statements', '/content/briefings']):
                        # Suche nach numerischen IDs oder spezifischen Patterns
                        if re.search(r'/\d{4}/|/\d{2}/|/[a-z-]+$', full_url):
                            article_urls.add(full_url)
        
        # World Bank: Suche nach News-Artikel Links
        elif 'worldbank.org' in base_url.lower():
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_url, href)
                
                # World Bank News Artikel haben oft /en/news/ gefolgt von Jahr/Monat
                if '/en/news/' in full_url and 'worldbank.org' in full_url:
                    # Vermeide Übersichtsseiten und Filter-Seiten
                    if not any(x in full_url for x in ['/news/press-release', '/news/feature', '/news/speech', '/news/all', '/news/contacts']):
                        # Suche nach Datum-Patterns (YYYY/MM/DD)
                        if re.search(r'/\d{4}/\d{2}/', full_url) or '/news/' in full_url and full_url.count('/') >= 5:
                            article_urls.add(full_url)
        
        return article_urls
    
    async def crawl_with_discovery(self, source_name: str, start_urls: List[str], max_articles: int = 30) -> Dict:
        """Crawle mit Artikel-Discovery"""
        console.print(f"\n[bold blue]🌍 Smart Crawling: {source_name}[/bold blue]")
        
        all_records = []
        discovered_urls = set()
        
        # Schritt 1: Finde Artikel-URLs auf Start-Seiten
        console.print(f"[yellow]📡 Schritt 1: Artikel-Discovery...[/yellow]")
        
        for start_url in start_urls:
            try:
                result = await self.fetcher.fetch(start_url)
                if result and result.success and result.content:
                    urls = self.find_article_links(result.content, start_url, source_name)
                    discovered_urls.update(urls)
                    console.print(f"  ✅ {start_url}: {len(urls)} Artikel gefunden")
                await asyncio.sleep(1)
            except Exception as e:
                console.print(f"  ❌ {start_url}: {e}")
        
        console.print(f"[green]📊 Gesamt gefunden: {len(discovered_urls)} Artikel-URLs[/green]")
        
        # Schritt 2: Crawle Artikel (limit auf max_articles)
        articles_to_crawl = list(discovered_urls)[:max_articles]
        console.print(f"[yellow]📥 Schritt 2: Crawle {len(articles_to_crawl)} Artikel...[/yellow]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task(f"Crawling {source_name}...", total=len(articles_to_crawl))
            
            for article_url in articles_to_crawl:
                try:
                    result = await self.fetcher.fetch(article_url)
                    
                    if result and result.success and result.content:
                        extractor = self.extractor_factory.get_extractor(article_url)
                        record = extractor.extract(result)
                        
                        if record:
                            validation_result = self.validator.validate(record)
                            if validation_result.is_valid:
                                all_records.append(record)
                                progress.update(task, advance=1, description=f"✅ {len(all_records)} records")
                            else:
                                progress.update(task, advance=1)
                        else:
                            progress.update(task, advance=1)
                    else:
                        progress.update(task, advance=1)
                    
                    await asyncio.sleep(0.8)  # Rate limiting
                    
                except Exception as e:
                    progress.update(task, advance=1)
        
        # Schritt 3: Speichere in Datenbank
        if all_records:
            console.print(f"[yellow]💾 Schritt 3: Speichere {len(all_records)} Records...[/yellow]")
            db_stats = self.db.insert_records_batch(all_records)
            await self.storage.store_all_formats(all_records, source_name)
            console.print(f"[green]✅ Gespeichert: {db_stats['new']} neu, {db_stats['updated']} aktualisiert[/green]")
        
        return {
            'source': source_name,
            'records': all_records,
            'urls_discovered': len(discovered_urls),
            'urls_crawled': len(articles_to_crawl),
            'records_extracted': len(all_records)
        }


async def main():
    """Hauptfunktion"""
    config = Config()
    
    # Strategische URLs für bessere Ergebnisse
    sources = {
        'NASA': [
            'https://earthobservatory.nasa.gov/features',
            'https://earthobservatory.nasa.gov/images',
        ],
        'UN Press': [
            'https://press.un.org/en/content/press-releases',
        ],
        'World Bank': [
            'https://www.worldbank.org/en/news',
        ]
    }
    
    async with SmartCrawler(config) as crawler:
        results = {}
        
        for source_name, urls in sources.items():
            result = await crawler.crawl_with_discovery(source_name, urls, max_articles=20)
            results[source_name] = result
        
        # Zusammenfassung
        console.print("\n[bold green]📊 Crawling-Zusammenfassung:[/bold green]")
        for source, result in results.items():
            console.print(f"  {source}:")
            console.print(f"    URLs gefunden: {result['urls_discovered']}")
            console.print(f"    URLs gecrawlt: {result['urls_crawled']}")
            console.print(f"    Records extrahiert: {result['records_extracted']}")
        
        # Datenbank-Statistiken
        stats = crawler.db.get_statistics()
        console.print(f"\n[bold blue]📊 Datenbank:[/bold blue]")
        console.print(f"  Gesamt Records: {stats.get('total_records', 0)}")
        for source, count in stats.get('records_by_source', {}).items():
            console.print(f"    {source}: {count}")


if __name__ == "__main__":
    asyncio.run(main())



