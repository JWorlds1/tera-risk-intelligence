#!/usr/bin/env python3
"""
Vollständiger System-Test: Crawling + Enrichment + Predictions
Behebt alle bekannten Probleme und testet das gesamte System
"""
import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import json

sys.path.append(str(Path(__file__).parent))

from database import DatabaseManager
from batch_enrichment_50 import BatchEnrichmentPipeline
from enriched_predictions import EnrichedPredictionPipeline
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()

# API Keys
FIRECRAWL_API_KEY = "fc-a0b3b8aa31244c10b0f15b4f2d570ac7"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY_HERE"

os.environ["FIRECRAWL_API_KEY"] = FIRECRAWL_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


async def test_complete_system():
    """Teste das gesamte System: Crawling → Enrichment → Predictions"""
    
    console.print(Panel.fit(
        "[bold green]🧪 Vollständiger System-Test[/bold green]\n"
        "1. Crawling (50 neue Artikel)\n"
        "2. Enrichment (20 Datenpunkte pro Artikel)\n"
        "3. Predictions (für angereicherte Daten)",
        border_style="green"
    ))
    
    db = DatabaseManager()
    
    # Schritt 1: Prüfe bestehende Records
    console.print("\n[bold cyan]Schritt 1: Prüfe bestehende Records...[/bold cyan]")
    existing_records = db.get_records(limit=1000)
    console.print(f"  ✅ {len(existing_records)} Records in Datenbank")
    
    # Prüfe bereits angereicherte Records
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
        cursor.execute("SELECT COUNT(*) FROM batch_enrichment")
        enriched_count = cursor.fetchone()[0]
        console.print(f"  ✅ {enriched_count} Records bereits angereichert")
    
    # Schritt 2: Crawling (nur wenn nicht genug Records vorhanden)
    if len(existing_records) < 50:
        console.print("\n[bold cyan]Schritt 2: Crawle neue Artikel...[/bold cyan]")
        console.print("[yellow]⚠️  Crawling kann bei NASA/UN Press Probleme haben[/yellow]")
        console.print("[yellow]   World Bank funktioniert zuverlässig[/yellow]")
        
        pipeline = BatchEnrichmentPipeline()
        
        # Fokussiere auf World Bank da das funktioniert
        console.print("\n[yellow]Fokussiere auf World Bank (funktioniert zuverlässig)...[/yellow]")
        
        try:
            # Crawle nur World Bank für zuverlässige Ergebnisse
            article_urls = await pipeline.discover_article_urls(
                "World Bank",
                ["https://www.worldbank.org/en/news", "https://www.worldbank.org/en/news/all"],
                target_count=min(50, 50 - len(existing_records))
            )
            
            console.print(f"  ✅ {len(article_urls)} Artikel-URLs gefunden")
            
            if article_urls:
                # Crawle und extrahiere Artikel
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    console=console
                ) as progress:
                    task = progress.add_task("Crawle Artikel...", total=len(article_urls))
                    
                    new_records = []
                    for url in article_urls[:50]:
                        try:
                            article_data = await pipeline.crawl_and_extract_article(url, "World Bank")
                            if article_data:
                                record = article_data['record']
                                record_dict = {
                                    'url': url,
                                    'source_name': 'World Bank',
                                    'title': record.title if hasattr(record, 'title') else None,
                                    'summary': record.summary if hasattr(record, 'summary') else None,
                                    'region': record.region if hasattr(record, 'region') else None,
                                    'publish_date': record.publish_date if hasattr(record, 'publish_date') else None,
                                    'topics': record.topics if hasattr(record, 'topics') else [],
                                    'full_text': getattr(record, 'full_text', None)
                                }
                                
                                # Speichere Record
                                from schemas import PageRecord
                                page_record = PageRecord(
                                    url=url,
                                    source_domain="worldbank.org",
                                    source_name="World Bank",
                                    fetched_at=datetime.now(),
                                    title=record_dict['title'],
                                    summary=record_dict['summary'],
                                    publish_date=record_dict['publish_date'],
                                    region=record_dict['region'],
                                    topics=record_dict['topics'],
                                    content_type="article",
                                    language="en",
                                    full_text=record_dict['full_text']
                                )
                                
                                result = db.insert_record(page_record)
                                if result:
                                    record_id, _ = result
                                    new_records.append(record_id)
                                
                                progress.update(task, advance=1)
                                await asyncio.sleep(1)
                        except Exception as e:
                            console.print(f"[red]Fehler bei {url}: {e}[/red]")
                            progress.update(task, advance=1)
                    
                    console.print(f"  ✅ {len(new_records)} neue Records gespeichert")
        except Exception as e:
            console.print(f"[red]Crawling-Fehler: {e}[/red]")
            console.print("[yellow]Verwende bestehende Records für Enrichment...[/yellow]")
    else:
        console.print("\n[bold cyan]Schritt 2: Genug Records vorhanden, überspringe Crawling[/bold cyan]")
    
    # Schritt 3: Enrichment (20 Datenpunkte)
    console.print("\n[bold cyan]Schritt 3: Enrichment mit 20 Datenpunkten...[/bold cyan]")
    
    # Hole Records die noch nicht angereichert wurden
    all_records = db.get_records(limit=1000)
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT record_id FROM batch_enrichment")
        enriched_ids = {row[0] for row in cursor.fetchall()}
    
    records_to_enrich = [r for r in all_records if r['id'] not in enriched_ids][:50]
    
    if not records_to_enrich:
        console.print("[yellow]⚠️  Alle Records sind bereits angereichert[/yellow]")
    else:
        console.print(f"  📊 {len(records_to_enrich)} Records werden angereichert...")
        
        pipeline = BatchEnrichmentPipeline()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Reichere an...", total=len(records_to_enrich))
            
            enriched_count = 0
            for record in records_to_enrich:
                try:
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
                    
                    # Prüfe ob wirklich 20 Datenpunkte vorhanden sind
                    datapoints_count = len(enrichment.get('datapoints', {}))
                    if datapoints_count != 20:
                        console.print(f"[yellow]⚠️  Record {record['id']}: {datapoints_count} Datenpunkte (sollte 20 sein)[/yellow]")
                    
                    # Speichere
                    record_id = pipeline.save_enriched_record(record_dict, enrichment)
                    if record_id:
                        enriched_count += 1
                    
                    progress.update(task, advance=1, description=f"✅ {enriched_count} angereichert")
                    await asyncio.sleep(1)
                except Exception as e:
                    console.print(f"[red]Fehler bei Record {record.get('id', 'N/A')}: {e}[/red]")
                    progress.update(task, advance=1)
        
        console.print(f"  ✅ {enriched_count} Records angereichert")
    
    # Schritt 4: Predictions
    console.print("\n[bold cyan]Schritt 4: Predictions für angereicherte Records...[/bold cyan]")
    
    # Hole angereicherte Records
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT record_id FROM batch_enrichment LIMIT 5")
        enriched_record_ids = [row[0] for row in cursor.fetchall()]
    
    if not enriched_record_ids:
        console.print("[yellow]⚠️  Keine angereicherten Records für Predictions[/yellow]")
    else:
        console.print(f"  📊 Erstelle Predictions für {len(enriched_record_ids)} Records...")
        
        try:
            prediction_pipeline = EnrichedPredictionPipeline(
                firecrawl_api_key=FIRECRAWL_API_KEY,
                openai_api_key=OPENAI_API_KEY,
                llm_provider="openai",
                llm_model="gpt-4o-mini"
            )
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=console
            ) as progress:
                task = progress.add_task("Erstelle Predictions...", total=len(enriched_record_ids))
                
                prediction_count = 0
                for record_id in enriched_record_ids:
                    try:
                        result = prediction_pipeline.enrich_and_predict(
                            record_id=record_id,
                            use_search=False,  # Bereits angereichert
                            use_extract=False,  # Bereits angereichert
                            use_llm=True
                        )
                        
                        if result and not result.get('error'):
                            prediction_count += 1
                        
                        progress.update(task, advance=1, description=f"✅ {prediction_count} Predictions")
                    except Exception as e:
                        console.print(f"[red]Fehler bei Prediction für Record {record_id}: {e}[/red]")
                        progress.update(task, advance=1)
            
            console.print(f"  ✅ {prediction_count} Predictions erstellt")
        except Exception as e:
            console.print(f"[red]Prediction-Fehler: {e}[/red]")
    
    # Zusammenfassung
    console.print("\n[bold green]✅ System-Test abgeschlossen![/bold green]\n")
    
    summary_table = Table(show_header=True, header_style="bold magenta")
    summary_table.add_column("Metrik", style="cyan")
    summary_table.add_column("Wert", style="green")
    
    all_records = db.get_records(limit=1000)
    summary_table.add_row("Gesamt Records", str(len(all_records)))
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM batch_enrichment")
        enriched_total = cursor.fetchone()[0]
        
        cursor.execute("SELECT datapoints FROM batch_enrichment")
        rows = cursor.fetchall()
        total_datapoints = 0
        for row in rows:
            if row[0]:
                try:
                    datapoints = json.loads(row[0])
                    total_datapoints += len(datapoints)
                except:
                    pass
        
        avg_datapoints = total_datapoints / enriched_total if enriched_total > 0 else 0
        
        summary_table.add_row("Angereicherte Records", str(enriched_total))
        summary_table.add_row("Durchschnitt Datenpunkte", f"{avg_datapoints:.1f}")
    
    console.print(summary_table)
    
    # Kosten
    costs = pipeline.cost_tracker.get_summary()
    console.print(f"\n[bold yellow]💰 Kosten:[/bold yellow]")
    console.print(f"  Firecrawl Credits: {costs.get('firecrawl_credits_used', 0):.1f}")
    console.print(f"  Verbleibend: {costs.get('firecrawl_credits_remaining', 20000):,.0f}")
    console.print(f"  OpenAI Kosten: ${costs.get('openai_cost_usd', 0):.4f}")


if __name__ == "__main__":
    asyncio.run(test_complete_system())

