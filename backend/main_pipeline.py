#!/usr/bin/env python3
"""
Haupt-Pipeline: Führt alle Komponenten zusammen
- IPCC-Kontext als Grundlage
- Firecrawl für Datenanreicherung
- LLM für Predictions
- Time Series für Trends
"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

sys.path.append(str(Path(__file__).parent))

from database import DatabaseManager
from ipcc_context_engine import IPCCContextEngine
from enriched_predictions import EnrichedPredictionPipeline
from prediction_pipeline import PredictionPipeline
from time_series_predictions import TimeSeriesPredictor
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# API Keys
FIRECRAWL_API_KEY = "fc-a0b3b8aa31244c10b0f15b4f2d570ac7"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY_HERE"

os.environ["FIRECRAWL_API_KEY"] = FIRECRAWL_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


class MainPipeline:
    """Haupt-Pipeline die alle Komponenten zusammenführt"""
    
    def __init__(self):
        """Initialisiere alle Komponenten"""
        console.print("[yellow]Initialisiere Pipeline-Komponenten...[/yellow]")
        
        # 1. IPCC Context Engine
        self.ipcc_engine = IPCCContextEngine()
        console.print("[green]✓[/green] IPCC Context Engine")
        
        # 2. Enriched Predictions Pipeline (nutzt IPCC-Kontext)
        self.enriched_pipeline = EnrichedPredictionPipeline(
            firecrawl_api_key=FIRECRAWL_API_KEY,
            openai_api_key=OPENAI_API_KEY,
            llm_provider="openai",
            llm_model="gpt-4o-mini"
        )
        console.print("[green]✓[/green] Enriched Predictions Pipeline")
        
        # 3. Standard Prediction Pipeline
        self.prediction_pipeline = PredictionPipeline(
            llm_provider="openai",
            llm_model="gpt-4o-mini"
        )
        console.print("[green]✓[/green] Prediction Pipeline")
        
        # 4. Time Series Predictor
        self.time_series_predictor = TimeSeriesPredictor()
        console.print("[green]✓[/green] Time Series Predictor")
        
        # 5. Database
        self.db = DatabaseManager()
        console.print("[green]✓[/green] Database")
        
        console.print("\n[bold green]✅ Alle Komponenten initialisiert![/bold green]\n")
    
    def process_record_complete(
        self,
        record_id: int,
        use_firecrawl: bool = True,
        use_llm: bool = True,
        use_time_series: bool = True
    ) -> Dict[str, Any]:
        """Vollständige Verarbeitung eines Records"""
        console.print(f"[cyan]Verarbeite Record {record_id}...[/cyan]")
        
        # Hole Record
        records = self.db.get_records(limit=1000)
        record = next((r for r in records if r.get('id') == record_id), None)
        
        if not record:
            return {"error": f"Record {record_id} not found"}
        
        result = {
            "record_id": record_id,
            "record": {
                "title": record.get('title'),
                "region": record.get('region'),
                "source": record.get('source_name')
            },
            "ipcc_context": {},
            "enrichment": {},
            "predictions": {},
            "time_series": {},
            "combined_analysis": {},
            "costs": {}
        }
        
        # 1. IPCC-Kontext erstellen
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task("Erstelle IPCC-Kontext...", total=None)
            firecrawl_context = self.ipcc_engine.get_firecrawl_context(record)
            llm_context = self.ipcc_engine.get_llm_context(record)
            result["ipcc_context"] = {
                "firecrawl_keywords": firecrawl_context.get('keywords', [])[:10],
                "focus_areas": firecrawl_context.get('focus_areas', []),
                "baseline": firecrawl_context.get('ipcc_context', {})
            }
            progress.update(task, completed=True)
        
        # 2. Firecrawl-Anreicherung (IPCC-basiert)
        if use_firecrawl:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
                task = progress.add_task("Firecrawl-Anreicherung (IPCC-basiert)...", total=None)
                try:
                    enrichment_result = self.enriched_pipeline.enrich_and_predict(
                        record_id=record_id,
                        use_search=True,
                        use_extract=True,
                        use_llm=False  # LLM separat
                    )
                    result["enrichment"] = enrichment_result.get('enrichment', {})
                    result["predictions"]["extracted_numbers"] = enrichment_result.get('predictions', {}).get('extracted_numbers', {})
                    result["predictions"]["risk_score"] = enrichment_result.get('predictions', {}).get('risk_score', {})
                except Exception as e:
                    console.print(f"[red]Firecrawl-Fehler: {e}[/red]")
                progress.update(task, completed=True)
        
        # 3. LLM-Predictions (IPCC-basiert)
        if use_llm:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
                task = progress.add_task("LLM-Predictions (IPCC-basiert)...", total=None)
                try:
                    llm_result = self.enriched_pipeline.enrich_and_predict(
                        record_id=record_id,
                        use_search=False,  # Bereits gemacht
                        use_extract=False,
                        use_llm=True
                    )
                    result["predictions"]["llm_prediction"] = llm_result.get('predictions', {}).get('llm_prediction', {})
                except Exception as e:
                    console.print(f"[red]LLM-Fehler: {e}[/red]")
                progress.update(task, completed=True)
        
        # 4. Time Series Predictions
        if use_time_series:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
                task = progress.add_task("Time Series Predictions...", total=None)
                try:
                    # Hole historische Records für Trend-Analyse
                    all_records = self.db.get_records(limit=100)
                    region_records = [r for r in all_records if r.get('region') == record.get('region')]
                    
                    if len(region_records) >= 3:
                        trend_prediction = self.time_series_predictor.predict_risk_score_trend(
                            region_records,
                            days_back=90
                        )
                        if trend_prediction:
                            result["time_series"] = {
                                "current_value": trend_prediction.current_value,
                                "predictions": trend_prediction.predictions,
                                "trend": trend_prediction.trend,
                                "confidence": trend_prediction.confidence
                            }
                except Exception as e:
                    console.print(f"[red]Time Series-Fehler: {e}[/red]")
                progress.update(task, completed=True)
        
        # 5. Kombinierte Analyse
        result["combined_analysis"] = self._create_combined_analysis(result)
        
        # 6. Kosten
        result["costs"] = self.enriched_pipeline.cost_tracker.get_summary()
        
        return result
    
    def process_all_records(
        self,
        limit: int = 10,
        use_firecrawl: bool = True,
        use_llm: bool = True
    ) -> Dict[str, Any]:
        """Verarbeite mehrere Records"""
        records = self.db.get_records(limit=limit)
        
        results = {
            "processed": 0,
            "errors": 0,
            "results": [],
            "summary": {}
        }
        
        for record in records:
            try:
                result = self.process_record_complete(
                    record['id'],
                    use_firecrawl=use_firecrawl,
                    use_llm=use_llm,
                    use_time_series=False  # Nur für einzelne Records
                )
                results["results"].append(result)
                results["processed"] += 1
                
                # Pause zwischen Requests
                import time
                time.sleep(2)
            
            except Exception as e:
                console.print(f"[red]Fehler bei Record {record.get('id')}: {e}[/red]")
                results["errors"] += 1
        
        # Zusammenfassung
        results["summary"] = self._create_summary(results["results"])
        
        return results
    
    def _create_combined_analysis(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Erstelle kombinierte Analyse"""
        analysis = {
            "overall_risk": "UNKNOWN",
            "ipcc_assessment": {},
            "key_insights": [],
            "recommendations": [],
            "trends": {}
        }
        
        # Risk Score
        if result.get('predictions', {}).get('risk_score'):
            risk = result['predictions']['risk_score']
            analysis["overall_risk"] = risk.get('level', 'UNKNOWN')
        
        # IPCC-Assessment
        if result.get('ipcc_context'):
            analysis["ipcc_assessment"] = {
                "baseline_period": result['ipcc_context'].get('baseline', {}).get('baseline_period', '1850-1900'),
                "current_anomaly": result['ipcc_context'].get('baseline', {}).get('current_anomaly', '1.1°C'),
                "focus_areas": result['ipcc_context'].get('focus_areas', [])
            }
        
        # LLM Insights
        if result.get('predictions', {}).get('llm_prediction'):
            llm = result['predictions']['llm_prediction']
            analysis["key_insights"] = llm.get('key_factors', [])
            analysis["recommendations"] = llm.get('recommendations', [])
        
        # Trends
        if result.get('time_series'):
            ts = result['time_series']
            analysis["trends"] = {
                "risk_trend": ts.get('trend'),
                "predictions": ts.get('predictions', {})
            }
        
        return analysis
    
    def _create_summary(self, results: List[Dict]) -> Dict[str, Any]:
        """Erstelle Zusammenfassung"""
        summary = {
            "total_records": len(results),
            "risk_distribution": {},
            "regions": set(),
            "sources": set(),
            "total_costs": {}
        }
        
        risk_counts = {}
        for result in results:
            risk = result.get('combined_analysis', {}).get('overall_risk', 'UNKNOWN')
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
            
            if result.get('record', {}).get('region'):
                summary["regions"].add(result['record']['region'])
            if result.get('record', {}).get('source'):
                summary["sources"].add(result['record']['source'])
        
        summary["risk_distribution"] = risk_counts
        summary["regions"] = list(summary["regions"])
        summary["sources"] = list(summary["sources"])
        
        # Kosten
        if results:
            last_costs = results[-1].get('costs', {})
            summary["total_costs"] = last_costs
        
        return summary


def main():
    """Hauptfunktion"""
    console.print(Panel.fit(
        "[bold green]🌍 Haupt-Pipeline: IPCC-basierte Geospatial Intelligence[/bold green]",
        border_style="green"
    ))
    
    # Initialisiere Pipeline
    pipeline = MainPipeline()
    
    # Hole Records
    db = DatabaseManager()
    records = db.get_records(limit=5)
    
    if not records:
        console.print("[red]Keine Records gefunden![/red]")
        console.print("[yellow]Führe zuerst den Crawler aus: python3 smart_crawler.py[/yellow]")
        return
    
    console.print(f"\n[green]Gefunden: {len(records)} Records[/green]")
    
    # Verarbeite ersten Record vollständig
    console.print("\n[bold cyan]Vollständige Verarbeitung (Beispiel):[/bold cyan]\n")
    
    result = pipeline.process_record_complete(
        record_id=records[0]['id'],
        use_firecrawl=True,
        use_llm=True,
        use_time_series=True
    )
    
    # Zeige Ergebnisse
    console.print("\n[bold green]✅ Ergebnisse:[/bold green]\n")
    
    # Record-Info
    console.print(f"[cyan]Record:[/cyan] {result['record']['title']}")
    console.print(f"Region: {result['record']['region'] or 'N/A'}")
    console.print(f"Quelle: {result['record']['source']}")
    
    # IPCC-Kontext
    if result.get('ipcc_context'):
        ipcc = result['ipcc_context']
        console.print(f"\n[cyan]IPCC-Kontext:[/cyan]")
        console.print(f"  Fokus-Bereiche: {', '.join(ipcc.get('focus_areas', []))}")
        console.print(f"  Baseline: {ipcc.get('baseline', {}).get('baseline_period', 'N/A')}")
        console.print(f"  Aktuelle Anomalie: {ipcc.get('baseline', {}).get('current_anomaly', 'N/A')}")
    
    # Enrichment
    if result.get('enrichment'):
        enrich = result['enrichment']
        console.print(f"\n[cyan]Firecrawl-Anreicherung:[/cyan]")
        console.print(f"  Methoden: {', '.join(enrich.get('methods_used', []))}")
        if enrich.get('search_results'):
            console.print(f"  Search Results: {len(enrich['search_results'])}")
        if enrich.get('extracted_data'):
            console.print(f"  Extracted Data: Ja")
    
    # Predictions
    if result.get('predictions'):
        preds = result['predictions']
        
        # Risk Score
        if preds.get('risk_score'):
            risk = preds['risk_score']
            level_colors = {
                'CRITICAL': 'red',
                'HIGH': 'orange',
                'MEDIUM': 'yellow',
                'LOW': 'lightblue',
                'MINIMAL': 'lightgray'
            }
            level = risk.get('level', 'UNKNOWN')
            color = level_colors.get(level, 'white')
            console.print(f"\n[cyan]Risk Score:[/cyan]")
            console.print(f"  [{color}]{level} ({risk.get('total', 0):.2f})[/{color}]")
            console.print(f"  Climate Risk: {risk.get('climate_risk', 0):.2f}")
            console.print(f"  Conflict Risk: {risk.get('conflict_risk', 0):.2f}")
        
        # LLM Prediction
        if preds.get('llm_prediction'):
            llm = preds['llm_prediction']
            console.print(f"\n[cyan]LLM Prediction (IPCC-basiert):[/cyan]")
            console.print(f"  {llm.get('prediction_text', 'N/A')}")
            console.print(f"  Konfidenz: {llm.get('confidence', 0):.2f}")
            if llm.get('key_factors'):
                console.print(f"  Faktoren: {len(llm['key_factors'])}")
    
    # Time Series
    if result.get('time_series'):
        ts = result['time_series']
        console.print(f"\n[cyan]Time Series Predictions:[/cyan]")
        console.print(f"  Aktuell: {ts.get('current_value', 0):.2f}")
        console.print(f"  Trend: {ts.get('trend', 'unknown')}")
        if ts.get('predictions'):
            console.print(f"  Vorhersagen: {ts['predictions']}")
    
    # Kombinierte Analyse
    if result.get('combined_analysis'):
        combined = result['combined_analysis']
        console.print(f"\n[cyan]Kombinierte Analyse:[/cyan]")
        console.print(f"  Gesamt-Risiko: {combined.get('overall_risk', 'UNKNOWN')}")
        if combined.get('key_insights'):
            console.print(f"  Erkenntnisse: {len(combined['key_insights'])}")
        if combined.get('recommendations'):
            console.print(f"  Empfehlungen: {len(combined['recommendations'])}")
    
    # Kosten
    costs = result.get('costs', {})
    console.print(f"\n[bold yellow]💰 Kosten:[/bold yellow]")
    
    cost_table = Table(show_header=True, header_style="bold yellow")
    cost_table.add_column("Metrik", style="cyan")
    cost_table.add_column("Wert", style="green")
    
    cost_table.add_row("Firecrawl Credits", f"{costs.get('firecrawl_credits_used', 0):.1f}")
    cost_table.add_row("Verbleibend", f"{costs.get('firecrawl_credits_remaining', 20000):,.0f}")
    cost_table.add_row("OpenAI Kosten", f"${costs.get('openai_cost_usd', 0):.4f}")
    cost_table.add_row("Requests", str(costs.get('requests_made', 0)))
    
    console.print(cost_table)
    
    console.print("\n[bold green]✅ Pipeline erfolgreich abgeschlossen![/bold green]")


if __name__ == "__main__":
    main()



