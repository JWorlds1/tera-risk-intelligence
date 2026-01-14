#!/usr/bin/env python3
"""
Haupt-Pipeline für Geospatial-Analyse
Führt Firecrawl + Ollama Extraktion, Kontextraum-Erstellung und Karten-Visualisierung aus
"""
import asyncio
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from geospatial_context_pipeline import GeospatialContextPipeline
from interactive_risk_map import InteractiveRiskMap

console = Console()


async def main():
    """Haupt-Pipeline"""
    console.print(Panel.fit(
        "[bold cyan]🌍 Geospatial Intelligence Pipeline[/bold cyan]\n"
        "Firecrawl + Ollama → Kontexträume → Interaktive Karte",
        border_style="cyan"
    ))
    
    # Schritt 1: Kontextraum-Erstellung
    console.print("\n[bold yellow]Schritt 1: Erstelle Kontexträume für alle Länder...[/bold yellow]")
    pipeline = GeospatialContextPipeline()
    context_spaces = await pipeline.process_all_countries()
    
    console.print(f"\n[green]✅ {len(context_spaces)} Kontexträume erstellt und in Datenbank gespeichert[/green]")
    
    # Schritt 2: Interaktive Karte erstellen
    console.print("\n[bold yellow]Schritt 2: Erstelle interaktive Risiko-Karte...[/bold yellow]")
    map_creator = InteractiveRiskMap()
    map_path = map_creator.create_map()
    
    console.print(f"\n[green]✅ Interaktive Karte erstellt: {map_path}[/green]")
    
    # Zusammenfassung
    console.print(Panel(
        f"[bold green]Pipeline abgeschlossen![/bold green]\n\n"
        f"📊 Kontexträume: {len(context_spaces)}\n"
        f"🗺️  Karte: {map_path}\n\n"
        f"[dim]Öffne die Karte in einem Browser, um die Risiko-Zonen zu visualisieren.[/dim]",
        title="Ergebnis",
        border_style="green"
    ))


if __name__ == "__main__":
    asyncio.run(main())

