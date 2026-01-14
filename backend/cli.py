# cli.py - Command Line Interface for Climate Conflict Early Warning System
import asyncio
import argparse
import sys
import os
from pathlib import Path
from typing import Optional
import structlog
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from config import Config
from orchestrator import ScrapingOrchestrator

console = Console()


def display_help():
    """Display help information"""
    help_text = Text("Climate Conflict Early Warning System - Web Scraping Tool", style="bold blue")
    subtitle = Text("Multi-Agent Scraping for NASA, UN, WFP, and World Bank", style="italic green")
    
    console.print(Panel.fit(help_text, subtitle=subtitle, border_style="blue"))
    console.print()
    
    console.print("[bold cyan]Usage:[/bold cyan]")
    console.print("  python cli.py [OPTIONS]")
    console.print()
    
    console.print("[bold cyan]Options:[/bold cyan]")
    console.print("  -h, --help              Show this help message")
    console.print("  -s, --source SOURCE     Scrape specific source (nasa, un, wfp, worldbank)")
    console.print("  -a, --all               Scrape all sources (default)")
    console.print("  -c, --config FILE       Use custom config file")
    console.print("  -v, --verbose           Enable verbose logging")
    console.print("  -q, --quiet             Suppress output except errors")
    console.print("  --dry-run               Show what would be scraped without actually scraping")
    console.print("  --stats                 Show statistics only")
    console.print()
    
    console.print("[bold cyan]Examples:[/bold cyan]")
    console.print("  python cli.py                    # Scrape all sources")
    console.print("  python cli.py -s nasa            # Scrape only NASA")
    console.print("  python cli.py -v --dry-run       # Verbose dry run")
    console.print("  python cli.py --stats            # Show statistics only")
    console.print()


async def run_scraping(source: Optional[str] = None, dry_run: bool = False, verbose: bool = False):
    """Run the scraping process"""
    try:
        config = Config()
        
        if verbose:
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
                    structlog.dev.ConsoleRenderer()
                ],
                logger_factory=structlog.stdlib.LoggerFactory(),
                wrapper_class=structlog.stdlib.BoundLogger,
                cache_logger_on_first_use=True,
            )
        
        async with ScrapingOrchestrator(config) as orchestrator:
            if dry_run:
                console.print("[yellow]Dry run mode - no actual scraping will be performed[/yellow]")
                # Show what would be scraped
                from url_lists import URLManager
                url_manager = URLManager()
                all_urls = url_manager.get_all_urls()
                
                if source:
                    if source.lower() in all_urls:
                        console.print(f"[cyan]Would scrape {source}:[/cyan]")
                        for url in all_urls[source.lower()]:
                            console.print(f"  - {url}")
                    else:
                        console.print(f"[red]Unknown source: {source}[/red]")
                        return
                else:
                    console.print("[cyan]Would scrape all sources:[/cyan]")
                    for source_name, urls in all_urls.items():
                        console.print(f"[bold]{source_name}:[/bold] {len(urls)} URLs")
                        for url in urls[:3]:  # Show first 3 URLs
                            console.print(f"  - {url}")
                        if len(urls) > 3:
                            console.print(f"  ... and {len(urls) - 3} more")
                        console.print()
            else:
                if source:
                    # Filter URLs for specific source
                    from url_lists import URLManager
                    url_manager = URLManager()
                    all_urls = url_manager.get_all_urls()
                    
                    if source.lower() in all_urls:
                        filtered_urls = {source.lower(): all_urls[source.lower()]}
                        # Update orchestrator's URL manager
                        orchestrator.url_manager.sources = {source.lower(): {"base_url": "", "urls": all_urls[source.lower()]}}
                    else:
                        console.print(f"[red]Unknown source: {source}[/red]")
                        return
                
                await orchestrator.run_scraping_session()
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Scraping interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())


def show_stats():
    """Show statistics from previous runs"""
    console.print("[cyan]Statistics from previous runs:[/cyan]")
    
    # This would read from a stats file or database
    # For now, just show a placeholder
    console.print("No statistics available yet. Run a scraping session first.")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Climate Conflict Early Warning System - Web Scraping Tool",
        add_help=False
    )
    
    parser.add_argument('-h', '--help', action='store_true', help='Show help message')
    parser.add_argument('-s', '--source', choices=['nasa', 'un', 'wfp', 'worldbank'], 
                       help='Scrape specific source')
    parser.add_argument('-a', '--all', action='store_true', help='Scrape all sources (default)')
    parser.add_argument('-c', '--config', type=str, help='Use custom config file')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('-q', '--quiet', action='store_true', help='Suppress output except errors')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be scraped')
    parser.add_argument('--stats', action='store_true', help='Show statistics only')
    parser.add_argument('--ai', action='store_true', help='Enable AI-powered extraction')
    parser.add_argument('--model', choices=['llama2', 'mistral', 'codellama', 'llamacpp'], 
                       default='llama2', help='AI model to use')
    parser.add_argument('--setup-ai', action='store_true', help='Setup AI components')
    
    args = parser.parse_args()
    
    if args.help:
        display_help()
        return
    
    if args.stats:
        show_stats()
        return
    
    if args.setup_ai:
        import subprocess
        console.print("[bold blue]Setting up AI components...[/bold blue]")
        subprocess.run([sys.executable, "setup_ai.py"])
        return
    
    if args.quiet:
        # Suppress console output
        console = Console(file=open(os.devnull, 'w'))
    
    # Determine source
    source = args.source if args.source else None
    
    # Run the scraping process
    asyncio.run(run_scraping(
        source=source,
        dry_run=args.dry_run,
        verbose=args.verbose
    ))


if __name__ == "__main__":
    main()