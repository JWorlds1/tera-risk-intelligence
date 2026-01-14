#!/usr/bin/env python3
"""
Demo-Script: Zeigt wie man Predictions erstellt
"""
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import json

sys.path.append(str(Path(__file__).parent))

from prediction_pipeline import PredictionPipeline
from database import DatabaseManager

console = Console()


def main():
    """Hauptfunktion"""
    console.print(Panel.fit(
        "[bold green]🔮 Prediction Pipeline Demo[/bold green]",
        border_style="green"
    ))
    
    # Initialisiere Pipeline
    console.print("\n[yellow]Initialisiere Prediction Pipeline...[/yellow]")
    try:
        pipeline = PredictionPipeline(llm_provider="openai", llm_model="gpt-4o-mini")
    except Exception as e:
        console.print(f"[red]Warning: LLM nicht konfiguriert: {e}[/red]")
        console.print("[yellow]Verwende Mock-Predictions...[/yellow]")
        pipeline = PredictionPipeline(llm_provider="openai", llm_model="gpt-4o-mini")
    
    # Hole Records aus DB
    db = DatabaseManager()
    records = db.get_records(limit=10)
    
    if not records:
        console.print("[red]Keine Records in der Datenbank gefunden![/red]")
        console.print("[yellow]Führe zuerst den Crawler aus: python3 smart_crawler.py[/yellow]")
        return
    
    console.print(f"\n[green]Gefunden: {len(records)} Records[/green]")
    
    # 1. Verarbeite einzelne Records
    console.print("\n[bold cyan]1. Verarbeite Records und extrahiere Daten...[/bold cyan]")
    
    for i, record in enumerate(records[:3], 1):  # Nur erste 3
        console.print(f"\n[cyan]Record {i}: {record.get('title', 'N/A')[:60]}...[/cyan]")
        
        try:
            result = pipeline.process_record(record['id'])
            
            # Zeige extrahierte Zahlen
            if result.get('extracted_numbers'):
                nums = result['extracted_numbers']
                if nums.get('temperatures'):
                    console.print(f"  🌡️  Temperaturen: {nums['temperatures']}")
                if nums.get('precipitation'):
                    console.print(f"  🌧️  Niederschlag: {nums['precipitation']}")
                if nums.get('affected_people'):
                    console.print(f"  👥  Betroffene: {nums['affected_people']:,}")
                if nums.get('funding_amount'):
                    console.print(f"  💰  Finanzierung: ${nums['funding_amount']:,.0f}")
            
            # Zeige Risk Score
            if result.get('risk_score'):
                risk = result['risk_score']
                level_colors = {
                    'CRITICAL': 'red',
                    'HIGH': 'orange',
                    'MEDIUM': 'yellow',
                    'LOW': 'lightblue',
                    'MINIMAL': 'lightgray'
                }
                level = risk.get('level', 'UNKNOWN')
                color = level_colors.get(level, 'white')
                console.print(f"  [{color}]⚠️  Risiko: {level} (Score: {risk.get('total', 0):.2f})[/{color}]")
            
            # Zeige LLM Prediction
            if result.get('llm_prediction'):
                llm = result['llm_prediction']
                console.print(f"  🤖  LLM Prediction: {llm.get('prediction_text', 'N/A')}")
                console.print(f"  📊  Konfidenz: {llm.get('confidence', 0):.2f}")
                if llm.get('key_factors'):
                    console.print(f"  🔑  Faktoren: {', '.join(llm['key_factors'][:3])}")
        
        except Exception as e:
            console.print(f"  [red]Fehler: {e}[/red]")
    
    # 2. Erstelle Trend-Predictions
    console.print("\n[bold cyan]2. Erstelle Trend-Predictions...[/bold cyan]")
    
    try:
        trends = pipeline.create_trend_predictions(days_back=90)
        
        console.print(f"\n[green]Analysiert: {trends['records_analyzed']} Records[/green]")
        
        # Zeige Predictions
        predictions = trends.get('predictions', {})
        
        if predictions.get('risk_score'):
            risk_pred = predictions['risk_score']
            console.print(f"\n[yellow]📈 Risk Score Trend:[/yellow]")
            console.print(f"  Aktuell: {risk_pred.get('current_value', 0):.2f}")
            console.print(f"  Trend: {risk_pred.get('trend', 'unknown')}")
            console.print(f"  Konfidenz: {risk_pred.get('confidence', 0):.2f}")
            if risk_pred.get('predictions'):
                console.print(f"  Vorhersagen: {risk_pred['predictions']}")
        
        if predictions.get('temperature'):
            temp_pred = predictions['temperature']
            console.print(f"\n[yellow]🌡️  Temperatur Trend:[/yellow]")
            console.print(f"  Aktuell: {temp_pred.get('current_value', 0):.2f}°C")
            console.print(f"  Trend: {temp_pred.get('trend', 'unknown')}")
            if temp_pred.get('predictions'):
                console.print(f"  Vorhersagen: {temp_pred['predictions']}")
        
        if predictions.get('llm_trend_analysis'):
            llm_trend = predictions['llm_trend_analysis']
            console.print(f"\n[yellow]🤖 LLM Trend-Analyse:[/yellow]")
            if llm_trend.get('trends'):
                console.print(f"  Identifizierte Trends: {len(llm_trend['trends'])}")
            if llm_trend.get('hotspots'):
                console.print(f"  Hotspots: {', '.join(llm_trend['hotspots'][:5])}")
    
    except Exception as e:
        console.print(f"[red]Fehler bei Trend-Predictions: {e}[/red]")
    
    # 3. Zeige kombinierte Prediction für einen Record
    console.print("\n[bold cyan]3. Kombinierte Prediction (Beispiel)...[/bold cyan]")
    
    if records:
        try:
            combined = pipeline.get_combined_prediction(records[0]['id'])
            
            if combined.get('combined_prediction'):
                cp = combined['combined_prediction']
                console.print(f"\n[green]Gesamt-Risiko: {cp.get('overall_risk', 'UNKNOWN')}[/green]")
                console.print(f"Konfidenz: {cp.get('confidence', 0):.2f}")
                console.print(f"Zeithorizont: {cp.get('predicted_timeline', 'unknown')}")
                
                if cp.get('key_insights'):
                    console.print("\n[yellow]Wichtige Erkenntnisse:[/yellow]")
                    for insight in cp['key_insights'][:5]:
                        console.print(f"  • {insight}")
                
                if cp.get('recommendations'):
                    console.print("\n[yellow]Empfehlungen:[/yellow]")
                    for rec in cp['recommendations'][:5]:
                        console.print(f"  • {rec}")
        
        except Exception as e:
            console.print(f"[red]Fehler: {e}[/red]")
    
    console.print("\n[bold green]✅ Demo abgeschlossen![/bold green]")
    console.print("\n[yellow]Nächste Schritte:[/yellow]")
    console.print("  1. Konfiguriere OPENAI_API_KEY für echte LLM-Predictions")
    console.print("  2. Installiere scikit-learn für bessere Zeitreihenvorhersagen: pip install scikit-learn")
    console.print("  3. Nutze die Pipeline in deiner Anwendung")


if __name__ == "__main__":
    main()

