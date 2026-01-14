#!/usr/bin/env python3
"""
Enrichment-Script: Reichert bestehende Records aus der Datenbank an
Falls Crawling nicht funktioniert, können wir bestehende Records verwenden
"""
import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

sys.path.append(str(Path(__file__).parent))

from database import DatabaseManager
from batch_enrichment_50 import BatchEnrichmentPipeline
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel

console = Console()

# API Keys
FIRECRAWL_API_KEY = "fc-a0b3b8aa31244c10b0f15b4f2d570ac7"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY_HERE"

os.environ["FIRECRAWL_API_KEY"] = FIRECRAWL_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


async def enrich_existing_records(limit: int = 50):
    """Reichere bestehende Records aus der Datenbank an"""
    console.print(Panel.fit(
        f"[bold green]🚀 Enrichment: {limit} bestehende Records mit 20 Datenpunkten[/bold green]",
        border_style="green"
    ))
    
    db = DatabaseManager()
    pipeline = BatchEnrichmentPipeline()
    
    # Hole bestehende Records
    records = db.get_records(limit=limit * 2)  # Hole mehr für Filterung
    
    if not records:
        console.print("[red]❌ Keine Records in der Datenbank gefunden![/red]")
        console.print("[yellow]Führe zuerst ein Crawling durch (z.B. test_http_pipeline.py)[/yellow]")
        return
    
    console.print(f"[green]✅ Gefunden: {len(records)} Records in der Datenbank[/green]")
    
    # Filtere Records die bereits angereichert wurden
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS batch_enrichment (
                record_id INTEGER PRIMARY KEY,
                datapoints TEXT,
                ipcc_metrics TEXT,
                extracted_numbers TEXT,
                firecrawl_data TEXT,
                enrichment_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("SELECT record_id FROM batch_enrichment")
        already_enriched = {row[0] for row in cursor.fetchall()}
    
    # Filtere Records die noch nicht angereichert wurden
    records_to_enrich = [r for r in records if r['id'] not in already_enriched][:limit]
    
    if not records_to_enrich:
        console.print(f"[yellow]⚠️  Alle {len(records)} Records sind bereits angereichert![/yellow]")
        return
    
    console.print(f"[cyan]📊 {len(records_to_enrich)} Records werden angereichert...[/cyan]")
    
    all_enriched_records = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task(
            "Reichere Records an...",
            total=len(records_to_enrich)
        )
        
        for record in records_to_enrich:
            try:
                # Konvertiere Record zu Dict-Format
                record_dict = {
                    'id': record['id'],
                    'url': record.get('url', ''),
                    'source_domain': record.get('source_domain', ''),
                    'source_name': record.get('source_name', ''),
                    'title': record.get('title'),
                    'summary': record.get('summary'),
                    'region': record.get('region'),
                    'publish_date': record.get('publish_date'),
                    'topics': record.get('topics', []),
                    'content_type': record.get('content_type'),
                    'language': record.get('language', 'en'),
                    'full_text': record.get('full_text')
                }
                
                # Reichere mit 20 Datenpunkten an
                enrichment = pipeline.enrich_with_20_datapoints(record_dict)
                
                # Speichere Anreicherung
                record_id = pipeline.save_enriched_record(record_dict, enrichment)
                
                if record_id:
                    all_enriched_records.append({
                        'record_id': record_id,
                        'url': record_dict['url'],
                        'source': record_dict['source_name'],
                        'datapoints_count': len(enrichment.get('datapoints', {})),
                        'enrichment': enrichment
                    })
                
                progress.update(task, advance=1, description=f"✅ {len(all_enriched_records)} angereichert")
                
                # Pause zwischen Requests
                await asyncio.sleep(1)
            
            except Exception as e:
                console.print(f"[red]Fehler bei Record {record.get('id', 'N/A')}: {e}[/red]")
                progress.update(task, advance=1)
                continue
    
    # Zusammenfassung
    console.print("\n[bold green]✅ Enrichment abgeschlossen![/bold green]\n")
    
    summary_table = Table(show_header=True, header_style="bold magenta")
    summary_table.add_column("Metrik", style="cyan")
    summary_table.add_column("Wert", style="green")
    
    summary_table.add_row("Angereicherte Records", str(len(all_enriched_records)))
    
    if all_enriched_records:
        total_datapoints = sum(r['datapoints_count'] for r in all_enriched_records)
        avg_datapoints = total_datapoints / len(all_enriched_records)
        summary_table.add_row("Gesamt Datenpunkte", str(total_datapoints))
        summary_table.add_row("Durchschnitt Datenpunkte", f"{avg_datapoints:.1f}")
        
        # Quellen-Verteilung
        sources = {}
        for r in all_enriched_records:
            source = r['source']
            sources[source] = sources.get(source, 0) + 1
        
        for source, count in sources.items():
            summary_table.add_row(f"Quelle: {source}", str(count))
    
    console.print(summary_table)
    
    # Kosten
    costs = pipeline.cost_tracker.get_summary()
    console.print(f"\n[bold yellow]💰 Kosten:[/bold yellow]")
    console.print(f"  Firecrawl Credits: {costs.get('firecrawl_credits_used', 0):.1f}")
    console.print(f"  Verbleibend: {costs.get('firecrawl_credits_remaining', 20000):,.0f}")
    console.print(f"  OpenAI Kosten: ${costs.get('openai_cost_usd', 0):.4f}")
    
    return {
        'total_enriched': len(all_enriched_records),
        'enriched_records': all_enriched_records,
        'costs': costs
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Reichere bestehende Records an')
    parser.add_argument('--limit', type=int, default=50, help='Anzahl Records zu anreichern (default: 50)')
    
    args = parser.parse_args()
    
    asyncio.run(enrich_existing_records(limit=args.limit))

