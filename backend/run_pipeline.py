#!/usr/bin/env python3
"""
Prototyp-Script für automatisierte Crawling-Pipeline
Führt Extraktion der drei Hauptwebseiten durch und speichert in Datenbank
"""
import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from datetime import datetime

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from config import Config
from pipeline import CrawlingPipeline
from database import DatabaseManager

console = Console()


def print_banner():
    """Print system banner"""
    banner = Text("""
🌍 Climate Conflict Early Warning System - Pipeline Prototype 🌍
    
    Automatisierte Extraktion & Datenbank-Speicherung
    Quellen: NASA, UN Press, World Bank
    """, style="bold green")
    
    console.print(Panel(banner, title="🚀 Pipeline Prototype", border_style="green"))


def print_database_stats(db: DatabaseManager):
    """Print database statistics"""
    stats = db.get_statistics()
    
    stats_table = Table(title="📊 Datenbank-Statistiken", show_header=True, header_style="bold magenta")
    stats_table.add_column("Metrik", style="cyan")
    stats_table.add_column("Wert", style="green")
    
    stats_table.add_row("Gesamt Records", str(stats.get('total_records', 0)))
    stats_table.add_row("Records (letzte 24h)", str(stats.get('records_last_24h', 0)))
    
    # Records per source
    records_by_source = stats.get('records_by_source', {})
    for source, count in records_by_source.items():
        stats_table.add_row(f"Records ({source})", str(count))
    
    # Crawl jobs
    crawl_jobs = stats.get('crawl_jobs_by_status', {})
    for status, count in crawl_jobs.items():
        stats_table.add_row(f"Crawl Jobs ({status})", str(count))
    
    console.print(stats_table)
    console.print()


async def main():
    """Main function"""
    print_banner()
    
    config = Config()
    db = DatabaseManager()
    
    # Show current database status
    console.print("[bold blue]📊 Aktuelle Datenbank-Statistiken:[/bold blue]")
    print_database_stats(db)
    
    # Initialize pipeline
    pipeline = CrawlingPipeline(config)
    
    # Run crawl for all three main sources
    console.print("[bold green]🚀 Starte Crawling für alle Quellen...[/bold green]")
    console.print()
    
    try:
        # Run full crawl
        results = await pipeline.run_full_crawl()
        
        # Display results
        console.print()
        console.print("[bold green]✅ Crawling abgeschlossen![/bold green]")
        console.print()
        
        results_table = Table(title="📈 Crawling-Ergebnisse", show_header=True, header_style="bold magenta")
        results_table.add_column("Quelle", style="cyan")
        results_table.add_column("Status", style="green")
        results_table.add_column("Records extrahiert", style="yellow")
        results_table.add_column("Neu", style="green")
        results_table.add_column("Aktualisiert", style="blue")
        
        for source_name, result in results.items():
            status = result.get('status', 'unknown')
            status_style = {
                'completed': '[green]✓[/green]',
                'failed': '[red]✗[/red]',
                'running': '[yellow]⟳[/yellow]'
            }.get(status, '?')
            
            results_table.add_row(
                source_name,
                f"{status_style} {status}",
                str(result.get('records_extracted', 0)),
                str(result.get('records_new', 0)),
                str(result.get('records_updated', 0))
            )
        
        console.print(results_table)
        console.print()
        
        # Show updated database stats
        console.print("[bold blue]📊 Aktualisierte Datenbank-Statistiken:[/bold blue]")
        print_database_stats(db)
        
        # Show recent records
        console.print("[bold blue]📄 Letzte Records (Beispiele):[/bold blue]")
        recent_records = db.get_records(limit=5)
        
        if recent_records:
            records_table = Table(show_header=True, header_style="bold cyan")
            records_table.add_column("Quelle", style="cyan")
            records_table.add_column("Titel", style="white")
            records_table.add_column("Datum", style="yellow")
            records_table.add_column("Region", style="green")
            
            for record in recent_records[:5]:
                title = (record.get('title', 'N/A') or 'N/A')[:50]
                if len(title) == 50:
                    title += "..."
                
                records_table.add_row(
                    record.get('source_name', 'N/A'),
                    title,
                    record.get('publish_date', 'N/A') or 'N/A',
                    record.get('region', 'N/A') or 'N/A'
                )
            
            console.print(records_table)
        else:
            console.print("[yellow]Keine Records gefunden[/yellow]")
        
        console.print()
        console.print("[bold green]✅ Pipeline erfolgreich ausgeführt![/bold green]")
        console.print()
        console.print("[bold blue]Nächste Schritte:[/bold blue]")
        console.print("  1. Datenbank prüfen: sqlite3 ./data/climate_conflict.db")
        console.print("  2. Automatisiertes Crawling starten: python pipeline.py --scheduled")
        console.print("  3. Daten analysieren: python example_analysis.py")
        
        return 0
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Pipeline durch Benutzer unterbrochen[/yellow]")
        return 1
    except Exception as e:
        console.print(f"\n[bold red]❌ Fehler: {e}[/bold red]")
        import traceback
        console.print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

