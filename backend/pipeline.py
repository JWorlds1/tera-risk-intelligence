# pipeline.py - Automatisierte Crawling-Pipeline mit Scheduler
import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import structlog
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from config import Config
from database import DatabaseManager
from orchestrator import ScrapingOrchestrator
from url_lists import URLManager

logger = structlog.get_logger(__name__)
console = Console()


class CrawlingPipeline:
    """Automatisierte Crawling-Pipeline mit Scheduler"""
    
    def __init__(self, config: Config):
        self.config = config
        self.db = DatabaseManager()
        self.url_manager = URLManager()
        self.is_running = False
        self.current_jobs = {}
        
    async def run_single_crawl(self, source_name: str, urls: List[str]) -> Dict[str, Any]:
        """Führe einen einzelnen Crawl für eine Quelle durch"""
        job_id = self.db.create_crawl_job(source_name, len(urls))
        self.current_jobs[source_name] = job_id
        
        try:
            # Update job status to running
            self.db.update_crawl_job(job_id, 'running')
            
            logger.info(f"Starting crawl for {source_name} with {len(urls)} URLs")
            
            # Try HTTP-only first, fallback to full orchestrator
            try:
                from http_only_orchestrator import HTTPOnlyOrchestrator
                async with HTTPOnlyOrchestrator(self.config) as orchestrator:
                    source_results = await orchestrator.scrape_source(source_name)
                    # Convert to expected format
                    source_stats = {
                        'valid_records': len(source_results.get('records', [])),
                        'successful_fetches': source_results.get('successful', 0),
                        'failed_fetches': source_results.get('failed', 0),
                        'successful_extractions': len(source_results.get('records', [])),
                        'failed_extractions': 0
                    }
                    # Store records in database
                    if source_results.get('records'):
                        db_stats = self.db.insert_records_batch(source_results['records'])
                        source_stats['records_new'] = db_stats.get('new', 0)
                        source_stats['records_updated'] = db_stats.get('updated', 0)
            except Exception as e:
                logger.warning(f"HTTP-only failed, trying full orchestrator: {e}")
                # Fallback to full orchestrator
                async with ScrapingOrchestrator(self.config, use_database=True) as orchestrator:
                    source_stats = await orchestrator.scrape_source(source_name, urls)
            
            # Records are already stored in database by orchestrator
            # Get stats from orchestrator which tracks new/updated
            records_new = source_stats.get('records_new', 0)
            records_updated = source_stats.get('records_updated', 0)
            
            # Update job status
            self.db.update_crawl_job(
                job_id,
                'completed',
                records_extracted=source_stats.get('valid_records', 0),
                records_new=records_new,
                records_updated=records_updated
            )
            
            logger.info(f"Completed crawl for {source_name}: {records_new} records")
            
            return {
                'job_id': job_id,
                'source_name': source_name,
                'status': 'completed',
                'records_extracted': records_new,
                'records_new': records_new,
                'records_updated': records_updated
            }
            
        except Exception as e:
            logger.error(f"Error in crawl for {source_name}: {e}", exc_info=True)
            self.db.update_crawl_job(
                job_id,
                'failed',
                error_message=str(e)
            )
            return {
                'job_id': job_id,
                'source_name': source_name,
                'status': 'failed',
                'error': str(e)
            }
        finally:
            if source_name in self.current_jobs:
                del self.current_jobs[source_name]
    
    async def run_full_crawl(self, sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """Führe einen vollständigen Crawl für alle oder spezifische Quellen durch"""
        all_urls = self.url_manager.get_all_urls()
        
        if sources:
            all_urls = {k: v for k, v in all_urls.items() if k in sources}
        
        results = {}
        
        console.print(f"[bold blue]Starting full crawl for {len(all_urls)} sources...[/bold blue]")
        
        for source_name, urls in all_urls.items():
            result = await self.run_single_crawl(source_name, urls)
            results[source_name] = result
            
            # Small delay between sources
            await asyncio.sleep(2)
        
        return results
    
    async def run_incremental_crawl(self, hours: int = 24) -> Dict[str, Any]:
        """Führe einen inkrementellen Crawl für neuere Inhalte durch"""
        # Get URLs that might have new content
        # This is a simplified version - in production, you'd track last crawl times per URL
        all_urls = self.url_manager.get_all_urls()
        
        results = {}
        
        console.print(f"[bold blue]Running incremental crawl (last {hours} hours)...[/bold blue]")
        
        for source_name, urls in all_urls.items():
            # For incremental, we could filter URLs or use different strategies
            # For now, we'll crawl all URLs but the database will handle duplicates
            result = await self.run_single_crawl(source_name, urls)
            results[source_name] = result
            
            await asyncio.sleep(2)
        
        return results


class PipelineScheduler:
    """Scheduler für automatisierte Pipeline-Ausführung"""
    
    def __init__(self, config: Config):
        self.config = config
        self.pipeline = CrawlingPipeline(config)
        self.scheduler = schedule
        self.is_running = False
    
    def schedule_daily_crawl(self, time_str: str = "02:00"):
        """Plane täglichen Crawl"""
        self.scheduler.every().day.at(time_str).do(
            lambda: asyncio.create_task(self.pipeline.run_full_crawl())
        )
        logger.info(f"Scheduled daily crawl at {time_str}")
    
    def schedule_hourly_crawl(self, minute: int = 0):
        """Plane stündlichen Crawl"""
        self.scheduler.every().hour.at(f":{minute:02d}").do(
            lambda: asyncio.create_task(self.pipeline.run_incremental_crawl(hours=1))
        )
        logger.info(f"Scheduled hourly crawl at minute {minute}")
    
    def schedule_interval_crawl(self, hours: int = 6):
        """Plane Crawl in regelmäßigen Intervallen"""
        self.scheduler.every(hours).hours.do(
            lambda: asyncio.create_task(self.pipeline.run_full_crawl())
        )
        logger.info(f"Scheduled crawl every {hours} hours")
    
    def run_scheduler_loop(self):
        """Führe den Scheduler-Loop aus"""
        self.is_running = True
        
        console.print(Panel(
            Text("🔄 Pipeline Scheduler Running", style="bold green"),
            title="Scheduler",
            border_style="green"
        ))
        
        while self.is_running:
            self.scheduler.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop(self):
        """Stoppe den Scheduler"""
        self.is_running = False
        logger.info("Scheduler stopped")


async def run_pipeline_once(config: Config, sources: Optional[List[str]] = None):
    """Führe Pipeline einmalig aus (für Testing/Prototyping)"""
    pipeline = CrawlingPipeline(config)
    return await pipeline.run_full_crawl(sources=sources)


async def run_pipeline_scheduled(config: Config):
    """Führe Pipeline mit Scheduler aus"""
    scheduler = PipelineScheduler(config)
    
    # Schedule daily crawl at 2 AM
    scheduler.schedule_daily_crawl("02:00")
    
    # Schedule incremental crawl every 6 hours
    scheduler.schedule_interval_crawl(6)
    
    # Run scheduler loop
    try:
        scheduler.run_scheduler_loop()
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping scheduler...[/yellow]")
        scheduler.stop()


if __name__ == "__main__":
    import sys
    
    config = Config()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--scheduled":
        asyncio.run(run_pipeline_scheduled(config))
    else:
        # Run once
        asyncio.run(run_pipeline_once(config))

