# orchestrator.py - Main orchestrator to coordinate all agents
import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import structlog
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.text import Text

from config import Config
from compliance import ComplianceAgent
from fetchers import MultiAgentFetcher
from extractors import ExtractorFactory
from validators import ValidationAgent
from storage import StorageAgent, DataExporter
from url_lists import URLManager
from database import DatabaseManager

# Configure structured logging
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

logger = structlog.get_logger(__name__)
console = Console()


class ScrapingOrchestrator:
    """Main orchestrator for the climate conflict early warning system"""
    
    def __init__(self, config: Config, use_database: bool = True):
        self.config = config
        self.compliance_agent = None
        self.fetcher = None
        self.validator = None
        self.storage_agent = None
        self.db = DatabaseManager() if use_database else None
        self.url_manager = URLManager()
        self.extractor_factory = ExtractorFactory(config)
        
        # Statistics
        self.stats = {
            'start_time': None,
            'end_time': None,
            'total_urls_processed': 0,
            'successful_fetches': 0,
            'failed_fetches': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'duplicates_found': 0,
            'records_stored': 0,
            'sources_processed': {}
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.compliance_agent = ComplianceAgent(self.config)
        self.fetcher = MultiAgentFetcher(self.config, self.compliance_agent)
        self.validator = ValidationAgent(self.config)
        self.storage_agent = StorageAgent(self.config)
        
        await self.compliance_agent.__aenter__()
        await self.fetcher.__aenter__()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.compliance_agent:
            await self.compliance_agent.__aexit__(exc_type, exc_val, exc_tb)
        if self.fetcher:
            await self.fetcher.__aexit__(exc_type, exc_val, exc_tb)
    
    def display_banner(self):
        """Display startup banner"""
        banner = Text("🌍 Umweltfrieden - Climate Conflict Early Warning System", style="bold blue")
        subtitle = Text("Multi-Agent Web Scraping & Analysis Pipeline", style="italic green")
        
        console.print(Panel.fit(banner, subtitle=subtitle, border_style="blue"))
        console.print()
    
    def display_config(self):
        """Display configuration"""
        config_table = Table(title="Configuration", show_header=True, header_style="bold magenta")
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="green")
        
        config_table.add_row("Rate Limit", f"{self.config.RATE_LIMIT} req/s")
        config_table.add_row("Max Concurrent", str(self.config.MAX_CONCURRENT))
        config_table.add_row("Storage Directory", self.config.STORAGE_DIR)
        config_table.add_row("HTTP Timeout", f"{self.config.HTTP_TIMEOUT}s")
        config_table.add_row("Playwright Timeout", f"{self.config.PLAYWRIGHT_TIMEOUT}ms")
        
        console.print(config_table)
        console.print()
    
    async def scrape_source(self, source_name: str, urls: List[str]) -> Dict[str, Any]:
        """Scrape a single source"""
        console.print(f"[bold blue]Processing {source_name}...[/bold blue]")
        
        source_stats = {
            'source_name': source_name,
            'urls_count': len(urls),
            'successful_fetches': 0,
            'failed_fetches': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'duplicates_found': 0,
            'records_stored': 0
        }
        
        if not urls:
            console.print(f"[yellow]No URLs found for {source_name}[/yellow]")
            return source_stats
        
        # Process URLs in batches
        batch_size = 10
        batches = [urls[i:i + batch_size] for i in range(0, len(urls), batch_size)]
        
        all_records = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task(f"Processing {source_name}", total=len(urls))
            
            for batch_idx, batch_urls in enumerate(batches):
                # Fetch URLs in batch
                fetch_results = await self.fetcher.fetch_batch(batch_urls)
                
                # Process each result
                for fetch_result in fetch_results:
                    progress.advance(task)
                    
                    if fetch_result.success:
                        source_stats['successful_fetches'] += 1
                        
                        # Extract data (try AI first, fallback to traditional)
                        record = None
                        
                        # Try AI extraction first if enabled
                        if self.config.ENABLE_AI_EXTRACTION:
                            try:
                                record = await self.extractor_factory.extract_with_ai(
                                    fetch_result.url, 
                                    source_name
                                )
                                if record:
                                    logger.info(f"AI extraction successful for {fetch_result.url}")
                            except Exception as e:
                                logger.warning(f"AI extraction failed, falling back to traditional: {e}")
                        
                        # Fallback to traditional extraction
                        if not record:
                            extractor = self.extractor_factory.get_extractor(fetch_result.url)
                            record = extractor.extract(fetch_result)
                        
                        if record:
                            source_stats['successful_extractions'] += 1
                            
                            # Validate record
                            validation_result = self.validator.validate(record)
                            
                            if validation_result.is_valid:
                                source_stats['valid_records'] += 1
                                all_records.append(record)
                            else:
                                source_stats['invalid_records'] += 1
                                if validation_result.is_duplicate:
                                    source_stats['duplicates_found'] += 1
                        else:
                            source_stats['failed_extractions'] += 1
                    else:
                        source_stats['failed_fetches'] += 1
                
                # Small delay between batches
                await asyncio.sleep(1)
        
        # Store records
        if all_records:
            # Store in database if available
            if self.db:
                db_stats = self.db.insert_records_batch(all_records)
                source_stats['records_new'] = db_stats.get('new', 0)
                source_stats['records_updated'] = db_stats.get('updated', 0)
                logger.info(f"Stored {len(all_records)} records in database: {db_stats['new']} new, {db_stats['updated']} updated")
            
            # Also store in file formats
            stored_files = await self.storage_agent.store_all_formats(
                all_records, source_name, f"batch_{batch_idx}"
            )
            source_stats['records_stored'] = len(all_records)
            console.print(f"[green]Stored {len(all_records)} records for {source_name}[/green]")
        
        # Update global stats
        self.stats['sources_processed'][source_name] = source_stats
        self.stats['total_urls_processed'] += len(urls)
        self.stats['successful_fetches'] += source_stats['successful_fetches']
        self.stats['failed_fetches'] += source_stats['failed_fetches']
        self.stats['successful_extractions'] += source_stats['successful_extractions']
        self.stats['failed_extractions'] += source_stats['failed_extractions']
        self.stats['valid_records'] += source_stats['valid_records']
        self.stats['invalid_records'] += source_stats['invalid_records']
        self.stats['duplicates_found'] += source_stats['duplicates_found']
        self.stats['records_stored'] += source_stats['records_stored']
        
        return source_stats
    
    async def run_scraping_session(self) -> Dict[str, Any]:
        """Run a complete scraping session"""
        self.stats['start_time'] = datetime.now()
        self.display_banner()
        self.display_config()
        
        console.print("[bold green]Starting scraping session...[/bold green]")
        console.print()
        
        # Get URLs for all sources
        all_urls = self.url_manager.get_all_urls()
        
        if not all_urls:
            console.print("[red]No URLs found to scrape![/red]")
            return self.stats
        
        # Process each source
        for source_name, urls in all_urls.items():
            try:
                await self.scrape_source(source_name, urls)
                console.print()
            except Exception as e:
                logger.error(f"Error processing {source_name}: {e}")
                console.print(f"[red]Error processing {source_name}: {e}[/red]")
        
        # Create consolidated dataset
        if self.stats['records_stored'] > 0:
            console.print("[bold blue]Creating consolidated dataset...[/bold blue]")
            all_records = {}
            for source_name, source_stats in self.stats['sources_processed'].items():
                if source_stats['records_stored'] > 0:
                    # This would need to be implemented to retrieve stored records
                    # For now, we'll skip this step
                    pass
            
            # Create summary report
            exporter = DataExporter(self.storage_agent)
            # This would create a summary report
            # For now, we'll skip this step
        
        self.stats['end_time'] = datetime.now()
        self.display_final_stats()
        
        return self.stats
    
    def display_final_stats(self):
        """Display final statistics"""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        # Overall stats table
        stats_table = Table(title="Scraping Session Summary", show_header=True, header_style="bold magenta")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")
        
        stats_table.add_row("Duration", str(duration).split('.')[0])
        stats_table.add_row("Total URLs Processed", str(self.stats['total_urls_processed']))
        stats_table.add_row("Successful Fetches", str(self.stats['successful_fetches']))
        stats_table.add_row("Failed Fetches", str(self.stats['failed_fetches']))
        stats_table.add_row("Successful Extractions", str(self.stats['successful_extractions']))
        stats_table.add_row("Failed Extractions", str(self.stats['failed_extractions']))
        stats_table.add_row("Valid Records", str(self.stats['valid_records']))
        stats_table.add_row("Invalid Records", str(self.stats['invalid_records']))
        stats_table.add_row("Duplicates Found", str(self.stats['duplicates_found']))
        stats_table.add_row("Records Stored", str(self.stats['records_stored']))
        
        console.print(stats_table)
        console.print()
        
        # Source-specific stats
        if self.stats['sources_processed']:
            source_table = Table(title="Source-Specific Results", show_header=True, header_style="bold magenta")
            source_table.add_column("Source", style="cyan")
            source_table.add_column("URLs", style="green")
            source_table.add_column("Fetched", style="green")
            source_table.add_column("Extracted", style="green")
            source_table.add_column("Valid", style="green")
            source_table.add_column("Stored", style="green")
            
            for source_name, source_stats in self.stats['sources_processed'].items():
                source_table.add_row(
                    source_name,
                    str(source_stats['urls_count']),
                    str(source_stats['successful_fetches']),
                    str(source_stats['successful_extractions']),
                    str(source_stats['valid_records']),
                    str(source_stats['records_stored'])
                )
            
            console.print(source_table)
            console.print()
        
        # Performance metrics
        if self.stats['total_urls_processed'] > 0:
            fetch_rate = self.stats['successful_fetches'] / self.stats['total_urls_processed']
            extraction_rate = self.stats['successful_extractions'] / max(self.stats['successful_fetches'], 1)
            validation_rate = self.stats['valid_records'] / max(self.stats['successful_extractions'], 1)
            
            perf_table = Table(title="Performance Metrics", show_header=True, header_style="bold magenta")
            perf_table.add_column("Metric", style="cyan")
            perf_table.add_column("Rate", style="green")
            
            perf_table.add_row("Fetch Success Rate", f"{fetch_rate:.2%}")
            perf_table.add_row("Extraction Success Rate", f"{extraction_rate:.2%}")
            perf_table.add_row("Validation Success Rate", f"{validation_rate:.2%}")
            
            console.print(perf_table)
            console.print()
    
    def get_detailed_stats(self) -> Dict[str, Any]:
        """Get detailed statistics for monitoring"""
        stats = {
            'session_stats': self.stats,
            'compliance_stats': self.compliance_agent.get_stats() if self.compliance_agent else {},
            'fetcher_stats': self.fetcher.get_stats() if self.fetcher else {},
            'validator_stats': self.validator.get_stats() if self.validator else {},
            'storage_stats': self.storage_agent.get_storage_stats() if self.storage_agent else {}
        }
        
        # Add database stats if available
        if self.db:
            stats['database_stats'] = self.db.get_statistics()
        
        return stats


async def main():
    """Main entry point"""
    try:
        config = Config()
        
        async with ScrapingOrchestrator(config) as orchestrator:
            await orchestrator.run_scraping_session()
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Scraping interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        logger.error(f"Orchestrator error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())