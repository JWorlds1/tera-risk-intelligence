#!/usr/bin/env python3
"""
Test-Script für Geospatial Pipeline
Testet die Pipeline mit einem einzelnen Land für schnelle Validierung
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from geospatial_context_pipeline import GeospatialContextPipeline
from interactive_risk_map import InteractiveRiskMap

console = Console()


async def test_single_country():
    """Teste Pipeline mit einem einzelnen Land"""
    console.print(Panel.fit(
        "[bold cyan]🧪 Test Geospatial Pipeline[/bold cyan]\n"
        "Teste mit einem einzelnen Land",
        border_style="cyan"
    ))
    
    pipeline = GeospatialContextPipeline()
    
    # Test mit Indien (hat wahrscheinlich Daten)
    console.print("\n[bold yellow]Teste mit Indien (IN)...[/bold yellow]")
    
    try:
        result = await pipeline.extract_country_data("IN", "India")
        
        console.print(f"\n[green]✅ Extraktion erfolgreich[/green]")
        console.print(f"  Bestehende Records: {result['existing_records']}")
        console.print(f"  Firecrawl Results: {result['firecrawl_results']}")
        console.print(f"  Risk Score: {result['context_space'].get('risk_score', 0.0):.2f}")
        console.print(f"  Risk Level: {result['context_space'].get('risk_level', 'UNKNOWN')}")
        console.print(f"  Climate Indicators: {len(result['context_space'].get('climate_indicators', []))}")
        console.print(f"  Conflict Indicators: {len(result['context_space'].get('conflict_indicators', []))}")
        
        # Teste Geocoding (async)
        geo_result = await pipeline.geocoding.geocode("India", "country")
        console.print(f"\n[green]✅ Geocoding erfolgreich[/green]")
        console.print(f"  Koordinaten: {geo_result.latitude if geo_result else 'N/A'}, {geo_result.longitude if geo_result else 'N/A'}")
        
        return True
        
    except Exception as e:
        console.print(f"\n[red]❌ Test fehlgeschlagen: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return False


def test_map_creation():
    """Teste Karten-Erstellung"""
    console.print("\n[bold yellow]Teste Karten-Erstellung...[/bold yellow]")
    
    try:
        map_creator = InteractiveRiskMap()
        map_path = map_creator.create_map("data/test_map.html")
        
        console.print(f"\n[green]✅ Karte erstellt: {map_path}[/green]")
        return True
        
    except Exception as e:
        console.print(f"\n[red]❌ Karten-Erstellung fehlgeschlagen: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return False


async def main():
    """Hauptfunktion"""
    console.print("\n[bold]🧪 Starte Pipeline-Tests...[/bold]\n")
    
    # Test 1: Einzelnes Land
    test1_result = await test_single_country()
    
    # Test 2: Karten-Erstellung
    test2_result = test_map_creation()
    
    # Zusammenfassung
    console.print("\n" + "="*60)
    console.print("[bold]Test-Zusammenfassung:[/bold]")
    console.print(f"  Einzelnes Land: {'✅' if test1_result else '❌'}")
    console.print(f"  Karten-Erstellung: {'✅' if test2_result else '❌'}")
    
    if test1_result and test2_result:
        console.print("\n[bold green]✅ Alle Tests erfolgreich![/bold green]")
        return 0
    else:
        console.print("\n[bold red]❌ Einige Tests fehlgeschlagen[/bold red]")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

