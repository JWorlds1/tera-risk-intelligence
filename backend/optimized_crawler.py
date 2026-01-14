#!/usr/bin/env python3
"""
Optimierter Crawler mit Parallelisierung, Caching und verbesserter Fehlerbehandlung
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import json
import hashlib
from functools import lru_cache
import time

sys.path.append(str(Path(__file__).parent))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel

console = Console()

from config import Config
from fetchers import HTTPFetcher, FetchResult
from compliance import ComplianceAgent
from extractors import ExtractorFactory
from validators import ValidationAgent
from database import DatabaseManager
from firecrawl_enrichment import FirecrawlEnricher, CostTracker


class URLCache:
    """Caching-Mechanismus für URLs mit TTL"""
    
    def __init__(self, ttl_hours: int = 24):
        self.cache: Dict[str, Tuple[Any, datetime]] = {}
        self.ttl = timedelta(hours=ttl_hours)
    
    def get(self, url: str) -> Optional[Any]:
        """Hole gecachte Daten wenn noch gültig"""
        if url in self.cache:
            data, timestamp = self.cache[url]
            if datetime.now() - timestamp < self.ttl:
                return data
            else:
                del self.cache[url]
        return None
    
    def set(self, url: str, data: Any):
        """Speichere Daten im Cache"""
        self.cache[url] = (data, datetime.now())
    
    def clear(self):
        """Leere Cache"""
        self.cache.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """Gebe Cache-Statistiken"""
        valid = sum(1 for _, (_, ts) in self.cache.items() if datetime.now() - ts < self.ttl)
        return {
            'total_cached': len(self.cache),
            'valid_entries': valid,
            'expired_entries': len(self.cache) - valid
        }


class RateLimiter:
    """Intelligenter Rate Limiter mit Token Bucket"""
    
    def __init__(self, rate: float = 1.0, burst: int = 5):
        self.rate = rate  # Requests per second
        self.burst = burst  # Burst capacity
        self.tokens = burst
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Warte bis ein Token verfügbar ist"""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # Füge Tokens basierend auf vergangener Zeit hinzu
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return
            else:
                # Warte bis ein Token verfügbar ist
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0


class RetryHandler:
    """Retry-Handler mit exponentieller Backoff"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    async def execute(self, func, *args, **kwargs):
        """Führe Funktion mit Retry-Logik aus"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    console.print(f"[yellow]⚠️  Retry {attempt + 1}/{self.max_retries} nach {delay:.1f}s: {e}[/yellow]")
                    await asyncio.sleep(delay)
                else:
                    console.print(f"[red]❌ Fehler nach {self.max_retries} Versuchen: {e}[/red]")
        
        raise last_error


class OptimizedCrawler:
    """Optimierter Crawler mit Parallelisierung und Caching"""
    
    def __init__(self, max_concurrent: int = 10, cache_ttl_hours: int = 24):
        self.config = Config()
        self.compliance = ComplianceAgent(self.config)
        self.db = DatabaseManager()
        self.extractor_factory = ExtractorFactory(self.config)
        self.validator = ValidationAgent(self.config)
        
        self.max_concurrent = max_concurrent
        self.url_cache = URLCache(ttl_hours=cache_ttl_hours)
        self.rate_limiter = RateLimiter(rate=self.config.RATE_LIMIT, burst=5)
        self.retry_handler = RetryHandler(max_retries=3)
        
        self.fetcher: Optional[HTTPFetcher] = None
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def __aenter__(self):
        self.fetcher = HTTPFetcher(self.config, self.compliance)
        await self.fetcher.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.fetcher:
            await self.fetcher.__aexit__(exc_type, exc_val, exc_tb)
    
    async def fetch_url(self, url: str, use_cache: bool = True) -> Optional[FetchResult]:
        """Fetch URL mit Caching und Retry"""
        # Prüfe Cache
        if use_cache:
            cached = self.url_cache.get(url)
            if cached:
                return cached
        
        # Rate Limiting
        await self.rate_limiter.acquire()
        
        # Fetch mit Retry
        async with self.semaphore:
            result = await self.retry_handler.execute(
                self.fetcher.fetch,
                url
            )
            
            # Cache Ergebnis
            if result and result.success and use_cache:
                self.url_cache.set(url, result)
            
            return result
    
    def find_article_links(self, html: str, base_url: str, source: str) -> Set[str]:
        """Finde Artikel-Links auf einer Seite (optimiert)"""
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin, urlparse
        import re
        
        soup = BeautifulSoup(html, 'lxml')
        article_urls = set()
        
        # Optimierte Patterns für verschiedene Quellen
        patterns = {
            'nasa': {
                'domain': 'earthobservatory.nasa.gov',
                'include': ['/images/', '/features/', '/world-of-change/'],
                'exclude': ['?page=', '?filter=', '/images', '/features'],  # Ohne trailing slash = Übersichtsseite
                'min_path_parts': 3
            },
            'press.un.org': {
                'domain': 'press.un.org',
                'include': ['/en/content/'],
                'exclude': ['/content/press-releases', '/content/meetings-coverage'],
                'min_path_parts': 4,
                'pattern': r'/\d{4}/|/\d{2}/|/[a-z-]+/[a-z-]+'
            },
            'wfp.org': {
                'domain': 'wfp.org',
                'include': ['/news/', '/stories/'],
                'exclude': ['/news/all', '/news/press-release', '/news/archive', '?page=', '?filter='],
                'pattern': r'/news/\d{4}/\d{2}/\d{2}/[a-z0-9-]+|/stories/[a-z0-9-]+|/news/[a-z0-9-]+'
            },
            'worldbank.org': {
                'domain': 'worldbank.org',
                'include': ['/en/news/'],
                'exclude': ['/news/all', '/news/press-release', '/news/feature'],
                'pattern': r'/\d{4}/\d{2}/\d{2}/|/news/[a-z0-9-]+'
            }
        }
        
        # Finde passendes Pattern
        pattern_config = None
        for key, config in patterns.items():
            if key in base_url.lower():
                pattern_config = config
                break
        
        if not pattern_config:
            return article_urls
        
        # Extrahiere Links
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Domain-Check
            if pattern_config['domain'] not in full_url:
                continue
            
            # Exclude-Check
            if any(exc in full_url for exc in pattern_config['exclude']):
                continue
            
            # Include-Check
            if not any(inc in full_url for inc in pattern_config['include']):
                continue
            
            # Pattern-Check (falls vorhanden)
            if 'pattern' in pattern_config:
                if not re.search(pattern_config['pattern'], full_url, re.I):
                    continue
            
            # Path-Parts-Check
            parsed = urlparse(full_url)
            path_parts = [p for p in parsed.path.split('/') if p]
            if len(path_parts) < pattern_config['min_path_parts']:
                continue
            
            article_urls.add(full_url)
        
        return article_urls
    
    async def discover_article_urls_parallel(
        self,
        start_urls: List[str],
        source: str,
        max_urls: int = 50
    ) -> Set[str]:
        """Entdecke Artikel-URLs parallel"""
        discovered_urls = set()
        visited_urls = set()
        to_visit = list(start_urls)
        
        async def process_url(url: str) -> Set[str]:
            """Verarbeite eine URL und finde Links"""
            if url in visited_urls:
                return set()
            
            visited_urls.add(url)
            
            try:
                result = await self.fetch_url(url, use_cache=True)
                
                if result and result.success and result.content:
                    links = self.find_article_links(result.content, url, source)
                    return links
            except Exception as e:
                console.print(f"[yellow]⚠️  Fehler bei {url}: {e}[/yellow]")
            
            return set()
        
        # Parallel Discovery mit Progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"Entdecke Artikel-URLs...", total=None)
            
            while len(discovered_urls) < max_urls and to_visit:
                # Batch von URLs parallel verarbeiten
                batch_size = min(5, len(to_visit), max_urls - len(discovered_urls))
                batch = to_visit[:batch_size]
                to_visit = to_visit[batch_size:]
                
                # Parallel verarbeiten
                tasks = [process_url(url) for url in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Sammle neue URLs
                new_urls = set()
                for result in results:
                    if isinstance(result, set):
                        new_urls.update(result)
                
                # Füge neue URLs hinzu
                for url in new_urls:
                    if url not in discovered_urls and len(discovered_urls) < max_urls:
                        discovered_urls.add(url)
                        # Füge auch zu to_visit hinzu für weitere Discovery
                        if url not in visited_urls and len(to_visit) < 20:
                            to_visit.append(url)
                
                progress.update(task, completed=len(discovered_urls))
                
                # Kleine Pause zwischen Batches
                await asyncio.sleep(0.5)
        
        return discovered_urls
    
    async def crawl_articles_parallel(
        self,
        urls: List[str],
        source: str
    ) -> List[Any]:
        """Crawle Artikel parallel"""
        all_records = []
        
        async def crawl_single_article(url: str) -> Optional[Any]:
            """Crawle einen einzelnen Artikel"""
            try:
                result = await self.fetch_url(url, use_cache=True)
                
                if not result or not result.success or not result.content:
                    return None
                
                extractor = self.extractor_factory.get_extractor(url)
                if not extractor:
                    return None
                
                record = extractor.extract(result)
                
                if record:
                    validation_result = self.validator.validate(record)
                    if validation_result.is_valid:
                        return record
                
                return None
            except Exception as e:
                console.print(f"[yellow]⚠️  Fehler beim Crawlen von {url}: {e}[/yellow]")
                return None
        
        # Parallel crawlen mit Progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"Crawle {source} Artikel...", total=len(urls))
            
            # Batch-Processing für bessere Kontrolle
            batch_size = min(self.max_concurrent, len(urls))
            
            for i in range(0, len(urls), batch_size):
                batch = urls[i:i + batch_size]
                
                # Parallel verarbeiten
                tasks = [crawl_single_article(url) for url in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Sammle erfolgreiche Records
                for result in results:
                    if result and not isinstance(result, Exception):
                        all_records.append(result)
                
                progress.update(task, completed=min(i + batch_size, len(urls)))
                
                # Kleine Pause zwischen Batches
                await asyncio.sleep(0.5)
        
        return all_records
    
    async def crawl_source_optimized(
        self,
        source_name: str,
        start_urls: List[str],
        max_articles: int = 50
    ) -> Dict[str, Any]:
        """Optimiertes Crawling für eine Quelle"""
        console.print(f"\n[bold cyan]🚀 Optimiertes Crawling: {source_name}[/bold cyan]")
        
        start_time = datetime.now()
        
        # Schritt 1: Parallel Discovery
        console.print(f"[green]📡 Schritt 1: Parallel Discovery...[/green]")
        article_urls = await self.discover_article_urls_parallel(
            start_urls,
            source_name,
            max_urls=max_articles
        )
        
        console.print(f"[green]✅ {len(article_urls)} Artikel-URLs gefunden[/green]")
        
        # Schritt 2: Parallel Crawling
        console.print(f"[green]📥 Schritt 2: Parallel Crawling...[/green]")
        records = await self.crawl_articles_parallel(
            list(article_urls)[:max_articles],
            source_name
        )
        
        console.print(f"[green]✅ {len(records)} Records extrahiert[/green]")
        
        # Schritt 3: Batch Database Insert
        if records:
            console.print(f"[green]💾 Schritt 3: Batch Database Insert...[/green]")
            db_stats = self.db.insert_records_batch(records)
            console.print(f"[green]✅ Gespeichert: {db_stats['new']} neu, {db_stats['updated']} aktualisiert[/green]")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        return {
            'source': source_name,
            'urls_discovered': len(article_urls),
            'records_extracted': len(records),
            'db_stats': db_stats if records else {},
            'elapsed_seconds': elapsed,
            'cache_stats': self.url_cache.get_stats()
        }


async def main():
    """Hauptfunktion"""
    console.print(Panel.fit(
        "[bold green]🚀 Optimierter Crawler[/bold green]\n"
        "[cyan]Mit Parallelisierung, Caching und Retry-Logik[/cyan]",
        border_style="green"
    ))
    
    # Test-Quellen
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
    
    async with OptimizedCrawler(max_concurrent=10, cache_ttl_hours=24) as crawler:
        results = {}
        
        for source_name, urls in sources.items():
            try:
                result = await crawler.crawl_source_optimized(
                    source_name,
                    urls,
                    max_articles=20  # Test mit 20 Artikeln
                )
                results[source_name] = result
            except Exception as e:
                console.print(f"[red]❌ Fehler bei {source_name}: {e}[/red]")
                import traceback
                console.print(traceback.format_exc())
        
        # Zusammenfassung
        console.print("\n[bold green]📊 Zusammenfassung:[/bold green]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Quelle", style="cyan")
        table.add_column("URLs gefunden", style="green")
        table.add_column("Records extrahiert", style="yellow")
        table.add_column("Zeit (s)", style="blue")
        table.add_column("Cache Hits", style="magenta")
        
        total_time = 0
        for source, result in results.items():
            table.add_row(
                source,
                str(result['urls_discovered']),
                str(result['records_extracted']),
                f"{result['elapsed_seconds']:.1f}",
                str(result['cache_stats'].get('valid_entries', 0))
            )
            total_time += result['elapsed_seconds']
        
        console.print(table)
        console.print(f"\n[bold cyan]Gesamtzeit: {total_time:.1f}s[/bold cyan]")
        console.print(f"[bold cyan]Durchschnitt: {total_time / len(results):.1f}s pro Quelle[/bold cyan]")


if __name__ == "__main__":
    asyncio.run(main())



