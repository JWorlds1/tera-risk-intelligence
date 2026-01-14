#!/usr/bin/env python3
"""
Test-Script für Extraktion - Zeigt extrahierte Daten an
"""
import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

sys.path.append(str(Path(__file__).parent))

from config import Config
from database import DatabaseManager
from pipeline import CrawlingPipeline

console = Console()


def print_banner():
    """Print test banner"""
    banner = Text("""
🧪 Test der Extraktion
    Zeigt extrahierte Daten aus der Datenbank
    """, style="bold yellow")
    
    console.print(Panel(banner, title="Test", border_style="yellow"))


def show_database_records(db: DatabaseManager, limit: int = 10):
    """Zeige Records aus der Datenbank"""
    records = db.get_records(limit=limit)
    
    if not records:
        console.print("[yellow]Keine Records in der Datenbank gefunden.[/yellow]")
        console.print("[blue]Führe zuerst die Pipeline aus: python run_pipeline.py[/blue]")
        return
    
    console.print(f"\n[bold green]📊 Zeige {len(records)} Records:[/bold green]\n")
    
    for i, record in enumerate(records, 1):
        # Source Badge
        source_colors = {
            'NASA': 'blue',
            'UN Press': 'yellow',
            'World Bank': 'green',
            'WFP': 'magenta'
        }
        source_color = source_colors.get(record.get('source_name', ''), 'white')
        
        console.print(f"\n[bold {source_color}][{i}] {record.get('source_name', 'Unknown')}[/bold {source_color}]")
        console.print(f"  [cyan]URL:[/cyan] {record.get('url', 'N/A')}")
        console.print(f"  [cyan]Titel:[/cyan] {record.get('title', 'N/A') or 'N/A'}")
        console.print(f"  [cyan]Datum:[/cyan] {record.get('publish_date', 'N/A') or 'N/A'}")
        console.print(f"  [cyan]Region:[/cyan] {record.get('region', 'N/A') or 'N/A'}")
        
        if record.get('summary'):
            summary = record['summary'][:200] + "..." if len(record['summary']) > 200 else record['summary']
            console.print(f"  [cyan]Zusammenfassung:[/cyan] {summary}")
        
        if record.get('topics'):
            topics_str = ", ".join(record['topics'])
            console.print(f"  [cyan]Topics:[/cyan] {topics_str}")
        
        # Source-specific data
        if record.get('nasa_data'):
            nasa = record['nasa_data']
            if nasa.get('satellite_source'):
                console.print(f"  [cyan]Satellit:[/cyan] {nasa['satellite_source']}")
            if nasa.get('environmental_indicators'):
                indicators = nasa['environmental_indicators']
                if isinstance(indicators, str):
                    import json
                    indicators = json.loads(indicators)
                console.print(f"  [cyan]Indikatoren:[/cyan] {', '.join(indicators)}")
        
        if record.get('un_data'):
            un = record['un_data']
            if un.get('security_council'):
                console.print(f"  [cyan]Security Council:[/cyan] Ja")
            if un.get('meeting_coverage'):
                console.print(f"  [cyan]Meeting Coverage:[/cyan] Ja")
        
        if record.get('worldbank_data'):
            wb = record['worldbank_data']
            if wb.get('country'):
                console.print(f"  [cyan]Land:[/cyan] {wb['country']}")
            if wb.get('sector'):
                console.print(f"  [cyan]Sektor:[/cyan] {wb['sector']}")


def show_statistics(db: DatabaseManager):
    """Zeige Datenbank-Statistiken"""
    stats = db.get_statistics()
    
    stats_table = Table(title="📊 Datenbank-Statistiken", show_header=True, header_style="bold magenta")
    stats_table.add_column("Metrik", style="cyan")
    stats_table.add_column("Wert", style="green")
    
    stats_table.add_row("Gesamt Records", str(stats.get('total_records', 0)))
    stats_table.add_row("Records (letzte 24h)", str(stats.get('records_last_24h', 0)))
    
    records_by_source = stats.get('records_by_source', {})
    for source, count in records_by_source.items():
        stats_table.add_row(f"Records ({source})", str(count))
    
    console.print(stats_table)
    console.print()


async def test_extraction():
    """Teste die Extraktion"""
    print_banner()
    
    config = Config()
    db = DatabaseManager()
    
    # Zeige aktuelle Statistiken
    console.print("[bold blue]📊 Aktuelle Datenbank-Statistiken:[/bold blue]")
    show_statistics(db)
    
    # Prüfe ob Daten vorhanden sind
    stats = db.get_statistics()
    if stats.get('total_records', 0) == 0:
        console.print("[yellow]⚠️ Keine Daten in der Datenbank gefunden.[/yellow]")
        console.print("[blue]Möchtest du jetzt einen Crawl durchführen? (j/n)[/blue]")
        
        # In Docker/CI kann man das automatisch machen
        import os
        if os.getenv('AUTO_RUN', 'false').lower() == 'true':
            console.print("[green]Auto-Run aktiviert, starte Crawl...[/green]")
            pipeline = CrawlingPipeline(config)
            await pipeline.run_full_crawl()
            console.print("[green]✅ Crawl abgeschlossen![/green]")
        else:
            console.print("[yellow]Führe manuell aus: python run_pipeline.py[/yellow]")
            return
    
    # Zeige Records
    console.print("[bold blue]📄 Extrahiere Records:[/bold blue]")
    show_database_records(db, limit=20)
    
    # Zeige Crawl-Jobs
    jobs = db.get_crawl_jobs(limit=5)
    if jobs:
        console.print("\n[bold blue]📋 Letzte Crawl-Jobs:[/bold blue]")
        jobs_table = Table(show_header=True, header_style="bold cyan")
        jobs_table.add_column("ID", style="cyan")
        jobs_table.add_column("Quelle", style="white")
        jobs_table.add_column("Status", style="green")
        jobs_table.add_column("Records", style="yellow")
        jobs_table.add_column("Erstellt", style="blue")
        
        for job in jobs:
            status_color = {
                'completed': 'green',
                'failed': 'red',
                'running': 'yellow',
                'pending': 'blue'
            }.get(job.get('status', ''), 'white')
            
            jobs_table.add_row(
                str(job.get('id', 'N/A')),
                job.get('source_name', 'N/A'),
                f"[{status_color}]{job.get('status', 'N/A')}[/{status_color}]",
                str(job.get('records_extracted', 0)),
                job.get('created_at', 'N/A')[:19] if job.get('created_at') else 'N/A'
            )
        
        console.print(jobs_table)
    
    console.print("\n[bold green]✅ Test abgeschlossen![/bold green]")
    console.print("\n[bold blue]Nächste Schritte:[/bold blue]")
    console.print("  • Dashboard anzeigen: python dashboard_viewer.py")
    console.print("  • Weitere Daten crawlen: python run_pipeline.py")
    console.print("  • Datenbank abfragen: sqlite3 ./data/climate_conflict.db")


if __name__ == "__main__":
    asyncio.run(test_extraction())

