#!/usr/bin/env python3
"""
Demo: IPCC-basierte Anreicherung mit Agenten
"""
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import json

sys.path.append(str(Path(__file__).parent))

from ipcc_enrichment_agent import DynamicEnrichmentOrchestrator
from database import DatabaseManager

console = Console()

# API Keys
FIRECRAWL_API_KEY = "fc-a0b3b8aa31244c10b0f15b4f2d570ac7"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY_HERE"

os.environ["FIRECRAWL_API_KEY"] = FIRECRAWL_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


def main():
    """Hauptfunktion"""
    console.print(Panel.fit(
        "[bold green]🌍 IPCC-basierte Anreicherung mit Agenten[/bold green]",
        border_style="green"
    ))
    
    # Initialisiere Orchestrator
    console.print("\n[yellow]Initialisiere Agenten-System...[/yellow]")
    orchestrator = DynamicEnrichmentOrchestrator(FIRECRAWL_API_KEY, OPENAI_API_KEY)
    console.print("[green]✅ Agenten-System bereit[/green]")
    
    # Hole Records
    db = DatabaseManager()
    records = db.get_records(limit=3)
    
    if not records:
        console.print("[red]Keine Records gefunden![/red]")
        return
    
    console.print(f"\n[green]Gefunden: {len(records)} Records[/green]")
    
    # Verarbeite ersten Record
    record = records[0]
    console.print(f"\n[bold cyan]Verarbeite Record: {record.get('title', 'N/A')[:60]}...[/bold cyan]")
    console.print(f"Region: {record.get('region', 'N/A')}")
    
    # Umfassende Anreicherung
    result = orchestrator.enrich_record_comprehensive(
        record,
        use_ipcc=True,
        use_satellite=True,
        use_real_time=True
    )
    
    # Zeige Ergebnisse
    console.print("\n[bold green]✅ Anreicherungs-Ergebnisse:[/bold green]")
    
    # IPCC-Daten
    if result.get('ipcc_data'):
        ipcc = result['ipcc_data']
        console.print("\n[cyan]📊 IPCC-Daten:[/cyan]")
        
        if ipcc.get('temperature_anomaly'):
            console.print(f"  🌡️  Temperatur-Anomalie: {ipcc['temperature_anomaly']:.2f}°C")
        if ipcc.get('precipitation_anomaly'):
            console.print(f"  🌧️  Niederschlags-Anomalie: {ipcc['precipitation_anomaly']:.2f}%")
        if ipcc.get('ndvi_anomaly'):
            console.print(f"  🌱  NDVI-Anomalie: {ipcc['ndvi_anomaly']:.2f}")
        if ipcc.get('co2_concentration'):
            console.print(f"  💨  CO2-Konzentration: {ipcc['co2_concentration']:.0f} ppm")
        
        if ipcc.get('trends'):
            console.print(f"  📈  Trends: {ipcc['trends']}")
        
        if ipcc.get('ipcc_findings'):
            console.print(f"  🔬  IPCC-Findings: {len(ipcc['ipcc_findings'])} gefunden")
            for finding in ipcc['ipcc_findings'][:3]:
                console.print(f"    • {finding[:80]}...")
    
    # Satelliten-Daten
    if result.get('satellite_data'):
        satellite = result['satellite_data']
        console.print("\n[cyan]🛰️  Satelliten-Daten:[/cyan]")
        console.print(f"  Bilder gefunden: {len(satellite.get('satellite_images', []))}")
        console.print(f"  NDVI-Karten: {len(satellite.get('ndvi_maps', []))}")
    
    # Echtzeit-Daten
    if result.get('real_time_data'):
        realtime = result['real_time_data']
        console.print("\n[cyan]⏱️  Echtzeit-Daten:[/cyan]")
        console.print(f"  Quellen: {realtime.get('sources_count', 0)}")
        console.print(f"  Updates: {len(realtime.get('updates', []))}")
        
        for update in realtime.get('updates', [])[:2]:
            console.print(f"    • {update.get('title', 'N/A')[:60]}...")
    
    # Kombinierte Anreicherung
    if result.get('combined_enrichment'):
        combined = result['combined_enrichment']
        console.print("\n[cyan]🔗 Kombinierte Anreicherung:[/cyan]")
        
        if combined.get('metrics'):
            console.print(f"  Metriken: {len(combined['metrics'])}")
        if combined.get('visualizations'):
            console.print(f"  Visualisierungen: {len(combined['visualizations'])}")
        if combined.get('facts'):
            console.print(f"  Fakten: {len(combined['facts'])}")
        if combined.get('trends'):
            console.print(f"  Trends: {combined['trends']}")
    
    # Kosten
    costs = result.get('costs', {})
    console.print("\n[bold yellow]💰 Kosten:[/bold yellow]")
    
    cost_table = Table(show_header=True, header_style="bold yellow")
    cost_table.add_column("Metrik", style="cyan")
    cost_table.add_column("Wert", style="green")
    
    cost_table.add_row("Firecrawl Credits", f"{costs.get('firecrawl_credits_used', 0):.1f}")
    cost_table.add_row("Verbleibend", f"{costs.get('firecrawl_credits_remaining', 20000):,.0f}")
    cost_table.add_row("OpenAI Kosten", f"${costs.get('openai_cost_usd', 0):.4f}")
    
    console.print(cost_table)
    
    console.print("\n[bold green]✅ Demo abgeschlossen![/bold green]")


if __name__ == "__main__":
    main()

