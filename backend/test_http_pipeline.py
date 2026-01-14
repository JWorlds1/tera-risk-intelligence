#!/usr/bin/env python3
"""
Test HTTP-only Pipeline (ohne Playwright)
"""
import asyncio
import sys
from pathlib import Path
from rich.console import Console

sys.path.append(str(Path(__file__).parent))

from config import Config
from http_only_orchestrator import HTTPOnlyOrchestrator
from database import DatabaseManager

console = Console()


async def test_http_pipeline():
    """Test HTTP-only Pipeline"""
    console.print("[bold blue]🧪 Teste HTTP-only Pipeline...[/bold blue]")
    
    config = Config()
    db = DatabaseManager()
    
    async with HTTPOnlyOrchestrator(config) as orchestrator:
        # Test NASA
        console.print("\n[bold green]1. Teste NASA...[/bold green]")
        nasa_results = await orchestrator.scrape_source("NASA")
        console.print(f"   Records: {len(nasa_results.get('records', []))}")
        
        # Test UN Press
        console.print("\n[bold green]2. Teste UN Press...[/bold green]")
        un_results = await orchestrator.scrape_source("UN Press")
        console.print(f"   Records: {len(un_results.get('records', []))}")
        
        # Test World Bank
        console.print("\n[bold green]3. Teste World Bank...[/bold green]")
        wb_results = await orchestrator.scrape_source("World Bank")
        console.print(f"   Records: {len(wb_results.get('records', []))}")
        
        # Speichere in Datenbank
        all_records = []
        for results in [nasa_results, un_results, wb_results]:
            all_records.extend(results.get('records', []))
        
        if all_records:
            db_stats = db.insert_records_batch(all_records)
            console.print(f"\n[bold green]✅ Gespeichert: {db_stats['new']} neu, {db_stats['updated']} aktualisiert[/bold green]")
        
        # Zeige Statistiken
        stats = db.get_statistics()
        console.print(f"\n[bold blue]📊 Datenbank-Statistiken:[/bold blue]")
        console.print(f"   Gesamt Records: {stats.get('total_records', 0)}")
        console.print(f"   Mit Koordinaten: {stats.get('records_with_coordinates', 0)}")
        
        if stats.get('records_by_source'):
            console.print(f"\n   Nach Quelle:")
            for source, count in stats['records_by_source'].items():
                console.print(f"     {source}: {count}")


if __name__ == "__main__":
    asyncio.run(test_http_pipeline())

