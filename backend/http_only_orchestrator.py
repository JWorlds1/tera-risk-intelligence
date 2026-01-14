#!/usr/bin/env python3
"""
HTTP-only Orchestrator für das Climate Conflict Scraping System
Ohne Playwright, nur mit HTTP-basiertem Scraping
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from config import Config
from compliance import ComplianceAgent
from fetchers import HTTPFetcher, FetchResult
from extractors import ExtractorFactory
from validators import ValidationAgent
from storage import StorageAgent
from url_lists import URLManager
from database import DatabaseManager
from rich.console import Console
from rich.progress import Progress, TaskID
import structlog

# Setup logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
console = Console()

class HTTPOnlyOrchestrator:
    """HTTP-only Scraping Orchestrator"""
    
    def __init__(self, config: Config):
        self.config = config
        self.compliance_agent = ComplianceAgent(config)
        self.fetcher = HTTPFetcher(config, self.compliance_agent)
        self.extractor_factory = ExtractorFactory(config)
        self.validator = ValidationAgent(config)
        self.storage = StorageAgent(config)
        self.url_manager = URLManager()
        self.db = DatabaseManager()
        
        self.stats = {
            'total_urls': 0,
            'successful': 0,
            'failed': 0,
            'extracted_records': 0,
            'start_time': None,
            'end_time': None
        }
    
    async def __aenter__(self):
        """Initialize orchestrator"""
        await self.fetcher.__aenter__()
        # Validator and storage don't need async context
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup orchestrator"""
        await self.fetcher.__aexit__(exc_type, exc_val, exc_tb)
    
    async def scrape_source(self, source: str) -> Dict:
        """Scrape a specific source"""
        console.print(f"🌍 [bold blue]Scraping {source.upper()}[/bold blue]")
        
        # Normalize source name
        source_normalized = source.replace(' ', '').lower()
        if 'un' in source_normalized and 'press' in source_normalized:
            source_normalized = 'un'
        elif 'world' in source_normalized and 'bank' in source_normalized:
            source_normalized = 'worldbank'
        
        urls = self.url_manager.get_urls_for_source(source_normalized)
        if not urls:
            # Try direct lookup
            urls = self.url_manager.get_source_urls(source)
        
        if not urls:
            console.print(f"❌ No URLs found for source: {source}")
            return {}
        
        console.print(f"📊 Found {len(urls)} URLs to scrape")
        
        results = []
        
        with Progress() as progress:
            task = progress.add_task(f"Scraping {source}...", total=len(urls))
            
            for i, url in enumerate(urls):
                try:
                    # Check compliance (simplified)
                    try:
                        if not self.compliance_agent.robots_allows(url):
                            console.print(f"⚠️  Skipping {url} (robots.txt check failed)")
                            progress.update(task, advance=1)
                            continue
                    except:
                        # If compliance check fails, continue anyway
                        pass
                    
                    # Fetch content
                    result = await self.fetcher.fetch(url)
                    
                    if result and result.success and result.content:
                        # Extract data using FetchResult
                        extractor = self.extractor_factory.get_extractor(result.url)
                        extracted_record = extractor.extract(result)
                        
                        if extracted_record:
                            # Convert single record to list for validation
                            records_to_validate = [extracted_record]
                            
                            # Validate data
                            validated_records = []
                            for record in records_to_validate:
                                validation_result = self.validator.validate(record)
                                if validation_result.is_valid:
                                    validated_records.append(record)
                            
                            if validated_records:
                                # Store in database
                                db_stats = self.db.insert_records_batch(validated_records)
                                
                                # Also store in file formats
                                await self.storage.store_all_formats(validated_records, source)
                                
                                results.extend(validated_records)
                                self.stats['extracted_records'] += len(validated_records)
                                self.stats['successful'] += 1
                                
                                console.print(f"✅ {url}: {len(validated_records)} record(s)")
                            else:
                                console.print(f"⚠️  {url}: No valid data after validation")
                                self.stats['failed'] += 1
                        else:
                            console.print(f"⚠️  {url}: No data extracted")
                            self.stats['failed'] += 1
                    else:
                        error_msg = result.error if result else "Unknown error"
                        console.print(f"❌ {url}: Failed to fetch - {error_msg}")
                        self.stats['failed'] += 1
                    
                    self.stats['successful'] += 1
                    
                except Exception as e:
                    console.print(f"❌ {url}: Error - {e}")
                    self.stats['failed'] += 1
                    logger.error("Scraping error", url=url, error=str(e))
                
                progress.update(task, advance=1)
                
                # Rate limiting
                await asyncio.sleep(1.0)
        
        return {
            'source': source,
            'urls_processed': len(urls),
            'records_extracted': len(results),
            'results': results
        }
    
    async def run_scraping_session(self, sources: Optional[List[str]] = None):
        """Run complete scraping session"""
        self.stats['start_time'] = datetime.now()
        
        if sources is None:
            sources = ['nasa', 'un', 'wfp', 'worldbank']
        
        console.print("🚀 [bold green]Starting Climate Conflict Scraping Session[/bold green]")
        console.print(f"📊 Sources: {', '.join(sources)}")
        
        all_results = {}
        
        for source in sources:
            try:
                result = await self.scrape_source(source)
                all_results[source] = result
            except Exception as e:
                console.print(f"❌ Error scraping {source}: {e}")
                logger.error("Source scraping error", source=source, error=str(e))
        
        self.stats['end_time'] = datetime.now()
        self.stats['total_urls'] = sum(r.get('urls_processed', 0) for r in all_results.values())
        
        # Print summary
        console.print("\n📊 [bold green]Scraping Summary[/bold green]")
        console.print(f"⏱️  Duration: {self.stats['end_time'] - self.stats['start_time']}")
        console.print(f"🌐 Total URLs: {self.stats['total_urls']}")
        console.print(f"✅ Successful: {self.stats['successful']}")
        console.print(f"❌ Failed: {self.stats['failed']}")
        console.print(f"📊 Records Extracted: {self.stats['extracted_records']}")
        
        return all_results

async def main():
    """Main function"""
    config = Config()
    
    async with HTTPOnlyOrchestrator(config) as orchestrator:
        # Test with NASA only
        results = await orchestrator.run_scraping_session(['nasa'])
        
        console.print("\n🎉 [bold green]Scraping completed![/bold green]")
        console.print(f"📁 Data saved to: {config.STORAGE_DIR}")

if __name__ == "__main__":
    asyncio.run(main())
