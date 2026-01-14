#!/usr/bin/env python3
"""
Vollständige Pipeline: Crawling → Geocoding → Visualisierung
"""
import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

sys.path.append(str(Path(__file__).parent))

from config import Config
from pipeline import CrawlingPipeline
from geocode_existing_records import geocode_all_records
from world_map_visualization import create_world_map
from database import DatabaseManager

console = Console()


def print_banner():
    """Print banner"""
    banner = Text("""
🌍 Vollständige Geospatial Intelligence Pipeline
    Crawling → Geocoding → Visualisierung
    """, style="bold green")
    
    console.print(Panel(banner, title="🚀 Pipeline", border_style="green"))


async def run_full_pipeline():
    """Führe vollständige Pipeline aus"""
    print_banner()
    
    config = Config()
    db = DatabaseManager()
    
    # Schritt 1: Crawling
    console.print("\n[bold blue]📡 Schritt 1: Crawling...[/bold blue]")
    pipeline = CrawlingPipeline(config)
    
    try:
        results = await pipeline.run_full_crawl()
        console.print("[green]✅ Crawling abgeschlossen![/green]")
    except Exception as e:
        console.print(f"[red]❌ Crawling Fehler: {e}[/red]")
        return
    
    # Schritt 2: Geocoding
    console.print("\n[bold blue]🌍 Schritt 2: Geocoding...[/bold blue]")
    try:
        await geocode_all_records()
        console.print("[green]✅ Geocoding abgeschlossen![/green]")
    except Exception as e:
        console.print(f"[red]❌ Geocoding Fehler: {e}[/red]")
        return
    
    # Schritt 3: Visualisierung
    console.print("\n[bold blue]🗺️  Schritt 3: Visualisierung...[/bold blue]")
    try:
        create_world_map()
        console.print("[green]✅ Visualisierung erstellt![/green]")
    except Exception as e:
        console.print(f"[red]❌ Visualisierung Fehler: {e}[/red]")
        return
    
    # Statistiken
    stats = db.get_statistics()
    console.print("\n[bold green]📊 Finale Statistiken:[/bold green]")
    console.print(f"   Gesamt Records: {stats.get('total_records', 0)}")
    console.print(f"   Records mit Koordinaten: {stats.get('records_with_coordinates', 0)}")
    
    console.print("\n[bold green]✅ Pipeline vollständig abgeschlossen![/bold green]")
    console.print("\n[bold blue]Nächste Schritte:[/bold blue]")
    console.print("   1. Öffne Karte: open ./data/world_map.html")
    console.print("   2. Prüfe Datenbank: sqlite3 ./data/climate_conflict.db")


if __name__ == "__main__":
    asyncio.run(run_full_pipeline())

