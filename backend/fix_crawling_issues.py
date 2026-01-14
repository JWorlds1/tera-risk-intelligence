#!/usr/bin/env python3
"""
Fix Crawling Issues - Teste und behebe Crawling-Probleme
"""
import asyncio
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent))

from config import Config
from compliance import ComplianceAgent
from fetchers import HTTPFetcher
from rich.console import Console

console = Console()


async def test_url_fetching():
    """Teste ob URLs erfolgreich gefetcht werden können"""
    config = Config()
    compliance = ComplianceAgent(config)
    fetcher = HTTPFetcher(config, compliance)
    
    await fetcher.__aenter__()
    
    test_urls = {
        "NASA": [
            "https://earthobservatory.nasa.gov/images",
            "https://earthobservatory.nasa.gov/features",
        ],
        "UN Press": [
            "https://press.un.org/en/content/press-releases",
            "https://press.un.org/en/content/meetings-coverage",
        ],
        "World Bank": [
            "https://www.worldbank.org/en/news",
            "https://www.worldbank.org/en/news/all",
        ]
    }
    
    console.print("[bold cyan]Teste URL-Fetching...[/bold cyan]\n")
    
    for source, urls in test_urls.items():
        console.print(f"[yellow]{source}:[/yellow]")
        for url in urls:
            try:
                result = await fetcher.fetch(url)
                if result.success and result.content:
                    content_length = len(result.content)
                    console.print(f"  ✅ {url}: {content_length} Bytes")
                else:
                    console.print(f"  ❌ {url}: Kein Content (success={result.success})")
            except Exception as e:
                console.print(f"  ❌ {url}: Fehler - {e}")
    
    await fetcher.__aexit__(None, None, None)


if __name__ == "__main__":
    asyncio.run(test_url_fetching())

