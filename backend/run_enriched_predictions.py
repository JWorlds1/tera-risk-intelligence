#!/usr/bin/env python3
"""
Demo: Enriched Predictions mit Firecrawl
"""
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import json

sys.path.append(str(Path(__file__).parent))

from enriched_predictions import EnrichedPredictionPipeline
from database import DatabaseManager

console = Console()

# API Keys
FIRECRAWL_API_KEY = "fc-a0b3b8aa31244c10b0f15b4f2d570ac7"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY_HERE"

# Setze Environment Variables
os.environ["FIRECRAWL_API_KEY"] = FIRECRAWL_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


def main():
    """Hauptfunktion"""
    console.print(Panel.fit(
        "[bold green]🔮 Enriched Predictions mit Firecrawl[/bold green]",
        border_style="green"
    ))
    
    # Initialisiere Pipeline
    console.print("\n[yellow]Initialisiere Pipeline...[/yellow]")
    try:
        pipeline = EnrichedPredictionPipeline(
            firecrawl_api_key=FIRECRAWL_API_KEY,
            openai_api_key=OPENAI_API_KEY,
            llm_provider="openai",
            llm_model="gpt-4o-mini"
        )
        console.print("[green]✅ Pipeline initialisiert[/green]")
    except Exception as e:
        console.print(f"[red]Fehler: {e}[/red]")
        return
    
    # Hole Records
    db = DatabaseManager()
    records = db.get_records(limit=5)
    
    if not records:
        console.print("[red]Keine Records gefunden![/red]")
        return
    
    console.print(f"\n[green]Gefunden: {len(records)} Records[/green]")
    
    # Zeige initiale Kosten
    initial_costs = pipeline.cost_tracker.get_summary()
    console.print(f"\n[yellow]Initiale Credits: {initial_costs['firecrawl_credits_remaining']:,}[/yellow]")
    
    # Verarbeite ersten Record als Demo
    console.print("\n[bold cyan]1. Enrichment & Prediction für ersten Record...[/bold cyan]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Verarbeite Record...", total=None)
        
        try:
            result = pipeline.enrich_and_predict(
                record_id=records[0]['id'],
                use_search=True,
                use_extract=True,
                use_llm=True
            )
            progress.update(task, completed=True)
        except Exception as e:
            console.print(f"[red]Fehler: {e}[/red]")
            return
    
    # Zeige Ergebnisse
    console.print("\n[bold green]✅ Ergebnisse:[/bold green]")
    
    # Original Record
    console.print(f"\n[cyan]Original Record:[/cyan]")
    console.print(f"  Titel: {result['original_record']['title']}")
    console.print(f"  Region: {result['original_record']['region'] or 'N/A'}")
    console.print(f"  Quelle: {result['original_record']['source']}")
    
    # Enrichment
    enrichment = result.get('enrichment', {})
    console.print(f"\n[cyan]Firecrawl Enrichment:[/cyan]")
    console.print(f"  Methoden: {', '.join(enrichment.get('methods_used', []))}")
    
    if enrichment.get('search_results'):
        console.print(f"  🔍 Search Results: {len(enrichment['search_results'])} gefunden")
        for i, sr in enumerate(enrichment['search_results'][:3], 1):
            console.print(f"    {i}. {sr.get('title', 'N/A')[:60]}...")
    
    if enrichment.get('extracted_data'):
        console.print(f"  🤖 Extracted Data: {len(enrichment['extracted_data'])} Felder")
        extract_data = enrichment['extracted_data']
        if extract_data.get('temperatures'):
            console.print(f"    Temperaturen: {extract_data['temperatures']}")
        if extract_data.get('affected_population'):
            console.print(f"    Betroffene: {extract_data['affected_population']:,}")
    
    # Predictions
    predictions = result.get('predictions', {})
    console.print(f"\n[cyan]Predictions:[/cyan]")
    
    # Extracted Numbers
    if predictions.get('extracted_numbers'):
        nums = predictions['extracted_numbers']
        console.print(f"  📊 Extrahierte Zahlen:")
        if nums.get('temperatures'):
            console.print(f"    🌡️  Temperaturen: {nums['temperatures']}")
        if nums.get('precipitation'):
            console.print(f"    🌧️  Niederschlag: {nums['precipitation']}")
        if nums.get('affected_people'):
            console.print(f"    👥  Betroffene: {nums['affected_people']:,}")
        if nums.get('funding_amount'):
            console.print(f"    💰  Finanzierung: ${nums['funding_amount']:,.0f}")
    
    # Risk Score
    if predictions.get('risk_score'):
        risk = predictions['risk_score']
        level_colors = {
            'CRITICAL': 'red',
            'HIGH': 'orange',
            'MEDIUM': 'yellow',
            'LOW': 'lightblue',
            'MINIMAL': 'lightgray'
        }
        level = risk.get('level', 'UNKNOWN')
        color = level_colors.get(level, 'white')
        console.print(f"\n  [{color}]⚠️  Risk Score: {level} ({risk.get('total', 0):.2f})[/{color}]")
        console.print(f"    Climate Risk: {risk.get('climate_risk', 0):.2f}")
        console.print(f"    Conflict Risk: {risk.get('conflict_risk', 0):.2f}")
        console.print(f"    Urgency: {risk.get('urgency', 0):.2f}")
    
    # LLM Prediction
    if predictions.get('llm_prediction'):
        llm = predictions['llm_prediction']
        console.print(f"\n  🤖 LLM Prediction:")
        console.print(f"    {llm.get('prediction_text', 'N/A')}")
        console.print(f"    Konfidenz: {llm.get('confidence', 0):.2f}")
        if llm.get('key_factors'):
            console.print(f"    Faktoren: {', '.join(llm['key_factors'][:3])}")
        if llm.get('recommendations'):
            console.print(f"    Empfehlungen:")
            for rec in llm['recommendations'][:2]:
                console.print(f"      • {rec}")
    
    # Kosten
    costs = result.get('costs', {})
    console.print(f"\n[bold yellow]💰 Kosten-Tracking:[/bold yellow]")
    
    cost_table = Table(show_header=True, header_style="bold yellow")
    cost_table.add_column("Metrik", style="cyan")
    cost_table.add_column("Wert", style="green")
    
    cost_table.add_row("Firecrawl Credits verwendet", f"{costs.get('firecrawl_credits_used', 0):.1f}")
    cost_table.add_row("Firecrawl Credits verbleibend", f"{costs.get('firecrawl_credits_remaining', 20000):,.0f}")
    cost_table.add_row("OpenAI Tokens", f"{costs.get('openai_tokens_used', 0):,}")
    cost_table.add_row("OpenAI Kosten (USD)", f"${costs.get('openai_cost_usd', 0):.4f}")
    cost_table.add_row("Requests", str(costs.get('requests_made', 0)))
    
    console.print(cost_table)
    
    # Warnung bei hohen Kosten
    if costs.get('firecrawl_credits_used', 0) > 100:
        console.print("\n[yellow]⚠️  Warnung: Hoher Firecrawl Credit-Verbrauch![/yellow]")
    
    if costs.get('openai_cost_usd', 0) > 0.10:
        console.print("\n[yellow]⚠️  Warnung: Hohe OpenAI-Kosten![/yellow]")
    
    console.print("\n[bold green]✅ Demo abgeschlossen![/bold green]")
    console.print("\n[yellow]Nächste Schritte:[/yellow]")
    console.print("  1. Nutze batch_enrich_and_predict() für mehrere Records")
    console.print("  2. Passe use_search/use_extract/use_llm Parameter an")
    console.print("  3. Überwache Kosten regelmäßig")


if __name__ == "__main__":
    main()

