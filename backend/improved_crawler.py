#!/usr/bin/env python3
"""
Verbesserter Crawler mit besserer Strategie
- Findet Artikel-URLs auf Übersichtsseiten
- Crawlt dann die einzelnen Artikel
- Robustere Extraktion
"""
import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Optional
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
from rich.progress import Progress

console = Console()


class ImprovedCrawler:
    """Verbesserter Crawler mit Artikel-Discovery"""
    
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
    
    def find_article_urls(self, html: str, base_url: str, source: str) -> List[str]:
        """Finde Artikel-URLs auf einer Übersichtsseite"""
        soup = BeautifulSoup(html, 'lxml')
        article_urls = []
        
        # NASA: Suche nach Links zu Artikeln
        if 'nasa' in base_url.lower():
            # Suche nach Links die zu Artikeln führen
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_url, href)
                
                # NASA Artikel-Patterns
                if any(pattern in full_url.lower() for pattern in ['/images/', '/features/', '/world-of-change/', '/global-maps/']):
                    if full_url not in article_urls:
                        article_urls.append(full_url)
                
                # Direkte Artikel-Links
                if '/images/' in full_url and 'earthobservatory.nasa.gov' in full_url:
                    if full_url not in article_urls:
                        article_urls.append(full_url)
        
        # UN Press: Suche nach Press Release Links
        elif 'press.un.org' in base_url.lower():
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_url, href)
                
                # UN Press Release Patterns
                if '/en/content/' in full_url and 'press.un.org' in full_url:
                    # Vermeide Übersichtsseiten
                    if not any(x in full_url for x in ['/content/press-releases', '/content/meetings-coverage', '/content/statements']):
                        if full_url not in article_urls:
                            article_urls.append(full_url)
        
        # World Bank: Suche nach News-Artikel Links
        elif 'worldbank.org' in base_url.lower():
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_url, href)
                
                # World Bank News Patterns
                if '/en/news/' in full_url and 'worldbank.org' in full_url:
                    # Vermeide Übersichtsseiten
                    if not any(x in full_url for x in ['/news/press-release', '/news/feature', '/news/speech']):
                        if '/news/' in full_url and full_url.count('/') >= 5:  # Tiefere URLs sind meist Artikel
                            if full_url not in article_urls:
                                article_urls.append(full_url)
        
        return article_urls[:20]  # Limit auf 20 Artikel pro Seite
    
    async def crawl_source(self, source_name: str, start_urls: List[str]) -> Dict:
        """Crawle eine Quelle mit verbesserter Strategie"""
        console.print(f"\n[bold blue]🌍 Crawling {source_name}...[/bold blue]")
        
        all_records = []
        article_urls_found = set()
        
        # Schritt 1: Crawle Übersichtsseiten und finde Artikel-URLs
        console.print(f"[yellow]Schritt 1: Finde Artikel-URLs...[/yellow]")
        for start_url in start_urls:
            try:
                result = await self.fetcher.fetch(start_url)
                if result and result.success and result.content:
                    urls = self.find_article_urls(result.content, start_url, source_name)
                    article_urls_found.update(urls)
                    console.print(f"  ✅ {start_url}: {len(urls)} Artikel gefunden")
                await asyncio.sleep(1)
            except Exception as e:
                console.print(f"  ❌ {start_url}: {e}")
        
        console.print(f"[green]Gefunden: {len(article_urls_found)} Artikel-URLs[/green]")
        
        # Schritt 2: Crawle einzelne Artikel
        console.print(f"[yellow]Schritt 2: Crawle Artikel...[/yellow]")
        
        with Progress() as progress:
            task = progress.add_task(f"Crawling {source_name}...", total=len(article_urls_found))
            
            for article_url in list(article_urls_found)[:50]:  # Limit auf 50 Artikel
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
                    
                    await asyncio.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    console.print(f"  ❌ Fehler bei {article_url}: {e}")
                    progress.update(task, advance=1)
        
        # Schritt 3: Speichere in Datenbank
        if all_records:
            console.print(f"[yellow]Schritt 3: Speichere {len(all_records)} Records...[/yellow]")
            db_stats = self.db.insert_records_batch(all_records)
            await self.storage.store_all_formats(all_records, source_name)
            console.print(f"[green]✅ Gespeichert: {db_stats['new']} neu, {db_stats['updated']} aktualisiert[/green]")
        
        return {
            'source': source_name,
            'records': all_records,
            'total_found': len(article_urls_found),
            'total_extracted': len(all_records)
        }


async def main():
    """Hauptfunktion"""
    config = Config()
    
    # URLs für jede Quelle
    sources = {
        'NASA': [
            'https://earthobservatory.nasa.gov/features',
            'https://earthobservatory.nasa.gov/images',
        ],
        'UN Press': [
            'https://press.un.org/en/content/press-releases',
            'https://press.un.org/en/content/meetings-coverage',
        ],
        'World Bank': [
            'https://www.worldbank.org/en/news',
        ]
    }
    
    async with ImprovedCrawler(config) as crawler:
        results = {}
        
        for source_name, urls in sources.items():
            result = await crawler.crawl_source(source_name, urls)
            results[source_name] = result
        
        # Zeige Zusammenfassung
        console.print("\n[bold green]📊 Zusammenfassung:[/bold green]")
        for source, result in results.items():
            console.print(f"  {source}: {result['total_extracted']} Records extrahiert")
        
        # Zeige Datenbank-Statistiken
        stats = crawler.db.get_statistics()
        console.print(f"\n[bold blue]📊 Datenbank:[/bold blue]")
        console.print(f"  Gesamt Records: {stats.get('total_records', 0)}")
        console.print(f"  Nach Quelle:")
        for source, count in stats.get('records_by_source', {}).items():
            console.print(f"    {source}: {count}")


if __name__ == "__main__":
    asyncio.run(main())



