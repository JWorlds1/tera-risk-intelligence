#!/usr/bin/env python3
"""
Optimiertes Enrichment mit Parallelisierung und Batch-Processing
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import json
from collections import defaultdict

sys.path.append(str(Path(__file__).parent))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel

console = Console()

from database import DatabaseManager
from config import Config
from firecrawl_enrichment import FirecrawlEnricher, CostTracker
from ipcc_context_engine import IPCCContextEngine
from data_extraction import NumberExtractor
from risk_scoring import RiskScorer


class OptimizedEnrichmentPipeline:
    """Optimiertes Enrichment mit Parallelisierung"""
    
    def __init__(self, max_concurrent: int = 5):
        self.config = Config()
        self.db = DatabaseManager()
        self.ipcc_engine = IPCCContextEngine()
        self.cost_tracker = CostTracker()
        self.firecrawl_enricher = FirecrawlEnricher(
            self.config.FIRECRAWL_API_KEY,
            self.cost_tracker
        )
        self.number_extractor = NumberExtractor()
        self.risk_scorer = RiskScorer()
        
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def enrich_record_async(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Reichere einen Record asynchron an"""
        async with self.semaphore:
            try:
                # IPCC-Kontext erstellen
                ipcc_context = self.ipcc_engine.get_firecrawl_context(record)
                
                # Keywords extrahieren
                keywords = ipcc_context.get('keywords', [])
                keywords = [k for k in keywords[:5] if k and isinstance(k, str)]
                
                if not keywords and record.get('region'):
                    keywords = [record.get('region')]
                
                # Firecrawl-Suche (nur wenn Keywords vorhanden)
                search_results = []
                if keywords:
                    try:
                        results, _ = self.firecrawl_enricher.enrich_with_search(
                            keywords=keywords,
                            region=record.get('region'),
                            limit=5,
                            scrape_content=True,
                            ipcc_context=ipcc_context
                        )
                        search_results = results
                    except Exception as e:
                        console.print(f"[yellow]⚠️  Search-Fehler für Record {record.get('id')}: {e}[/yellow]")
                
                # Zahlen extrahieren
                text_content = f"{record.get('title', '')} {record.get('summary', '')} {record.get('full_text', '')}"
                for result in search_results:
                    text_content += f" {result.get('title', '')} {result.get('description', '')}"
                    if result.get('markdown'):
                        text_content += f" {result.get('markdown', '')[:500]}"
                
                extracted = self.number_extractor.extract_all(text_content)
                
                # Datenpunkte erstellen
                datapoints = self._create_datapoints(record, extracted, search_results)
                
                # Risk Scores berechnen
                risk = self.risk_scorer.calculate_risk(record)
                datapoints.update({
                    "risk_score": risk.score,
                    "climate_risk": risk.climate_risk,
                    "conflict_risk": risk.conflict_risk,
                    "urgency": risk.urgency
                })
                
                enrichment = {
                    'datapoints': datapoints,
                    'ipcc_metrics': {
                        'baseline_period': ipcc_context.get('ipcc_context', {}).get('baseline_period'),
                        'current_anomaly': ipcc_context.get('ipcc_context', {}).get('current_anomaly'),
                        'focus_areas': ipcc_context.get('focus_areas', [])
                    },
                    'extracted_numbers': {
                        'temperatures': extracted.temperatures,
                        'precipitation': extracted.precipitation,
                        'population_numbers': extracted.population_numbers,
                        'financial_amounts': extracted.financial_amounts
                    },
                    'firecrawl_data': {
                        'search_results': search_results
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
                return enrichment
                
            except Exception as e:
                console.print(f"[red]❌ Enrichment-Fehler für Record {record.get('id')}: {e}[/red]")
                return {
                    'datapoints': {},
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
    
    def _create_datapoints(
        self,
        record: Dict[str, Any],
        extracted: Any,
        search_results: List[Dict]
    ) -> Dict[str, Any]:
        """Erstelle Datenpunkte aus extrahierten Daten"""
        datapoints = {}
        
        # Temperatur-Datenpunkte
        if extracted.temperatures:
            for i, temp in enumerate(extracted.temperatures[:3], 1):
                datapoints[f"temperature_{i}"] = temp
        
        # Niederschlags-Datenpunkte
        if extracted.precipitation:
            for i, precip in enumerate(extracted.precipitation[:3], 1):
                datapoints[f"precipitation_{i}"] = precip
        
        # Bevölkerungs-Datenpunkte
        if extracted.population_numbers:
            for i, pop in enumerate(extracted.population_numbers[:3], 1):
                datapoints[f"population_{i}"] = pop
        
        # Finanz-Datenpunkte
        if extracted.financial_amounts:
            for i, amount in enumerate(extracted.financial_amounts[:3], 1):
                datapoints[f"financial_{i}"] = amount
        
        # Spezifische Metriken
        if extracted.affected_people:
            datapoints["affected_people"] = extracted.affected_people
        
        if extracted.funding_amount:
            datapoints["funding_amount"] = extracted.funding_amount
        
        # IPCC-Metriken
        if extracted.temperatures and len(extracted.temperatures) > 0:
            avg_temp = sum(extracted.temperatures) / len(extracted.temperatures)
            anomaly = avg_temp - 13.5  # IPCC Baseline
            datapoints["temperature_anomaly"] = round(anomaly, 2)
        
        if extracted.precipitation and len(extracted.precipitation) > 0:
            avg_precip = sum(extracted.precipitation) / len(extracted.precipitation)
            anomaly_percent = ((avg_precip - 100) / 100) * 100
            datapoints["precipitation_anomaly"] = round(anomaly_percent, 2)
        
        # Metadaten
        if record.get('title'):
            datapoints["has_title"] = 1
            datapoints["title_length"] = len(record.get('title', ''))
        
        if record.get('summary'):
            datapoints["has_summary"] = 1
            datapoints["summary_length"] = len(record.get('summary', ''))
        
        if record.get('region'):
            datapoints["has_region"] = 1
        
        if record.get('topics') and len(record.get('topics', [])) > 0:
            datapoints["has_topics"] = len(record.get('topics', []))
        
        if record.get('full_text'):
            datapoints["has_full_text"] = 1
        
        if record.get('source_name'):
            datapoints["source_type"] = record.get('source_name')
        
        return datapoints
    
    def save_enrichment_batch(self, enrichments: List[Dict[str, Any]]) -> int:
        """Speichere Enrichments in Batch"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Erstelle Tabelle falls nicht vorhanden
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
            
            # Batch Insert
            saved_count = 0
            for enrichment_data in enrichments:
                record_id = enrichment_data.get('record_id')
                if not record_id:
                    continue
                
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO batch_enrichment (
                            record_id, datapoints, ipcc_metrics,
                            extracted_numbers, firecrawl_data
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        record_id,
                        json.dumps(enrichment_data.get('enrichment', {}).get('datapoints', {})),
                        json.dumps(enrichment_data.get('enrichment', {}).get('ipcc_metrics', {})),
                        json.dumps(enrichment_data.get('enrichment', {}).get('extracted_numbers', {})),
                        json.dumps(enrichment_data.get('enrichment', {}).get('firecrawl_data', {}))
                    ))
                    saved_count += 1
                except Exception as e:
                    console.print(f"[yellow]⚠️  Fehler beim Speichern von Record {record_id}: {e}[/yellow]")
            
            conn.commit()
            return saved_count
    
    async def enrich_batch_parallel(
        self,
        records: List[Dict[str, Any]],
        batch_size: int = 10
    ) -> List[Dict[str, Any]]:
        """Reichere Records parallel in Batches an"""
        all_enrichments = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task(
                f"Reichere {len(records)} Records an...",
                total=len(records)
            )
            
            # Verarbeite in Batches
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                
                # Parallel verarbeiten
                tasks = [self.enrich_record_async(record) for record in batch]
                enrichments = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Sammle erfolgreiche Enrichments
                for j, (record, enrichment) in enumerate(zip(batch, enrichments)):
                    if not isinstance(enrichment, Exception) and enrichment:
                        all_enrichments.append({
                            'record_id': record.get('id'),
                            'record': record,
                            'enrichment': enrichment
                        })
                
                progress.update(task, completed=min(i + batch_size, len(records)))
                
                # Kleine Pause zwischen Batches
                await asyncio.sleep(0.5)
        
        return all_enrichments
    
    async def run_optimized_enrichment(
        self,
        limit: int = 50,
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """Führe optimiertes Batch-Enrichment durch"""
        console.print(Panel.fit(
            "[bold green]🚀 Optimiertes Enrichment[/bold green]\n"
            f"[cyan]Parallelisierung: {max_concurrent} concurrent[/cyan]",
            border_style="green"
        ))
        
        start_time = datetime.now()
        
        # Hole Records aus DB
        console.print(f"\n[cyan]📊 Hole {limit} Records aus Datenbank...[/cyan]")
        records = self.db.get_records(limit=limit)
        
        if not records:
            console.print("[yellow]⚠️  Keine Records gefunden[/yellow]")
            return {
                'total_records': 0,
                'enriched': 0,
                'elapsed_seconds': 0
            }
        
        console.print(f"[green]✅ {len(records)} Records gefunden[/green]")
        
        # Parallel Enrichment
        console.print(f"\n[cyan]🔄 Starte paralleles Enrichment...[/cyan]")
        enrichments = await self.enrich_batch_parallel(records, batch_size=max_concurrent)
        
        console.print(f"[green]✅ {len(enrichments)} Records angereichert[/green]")
        
        # Batch Save
        console.print(f"\n[cyan]💾 Speichere Enrichments...[/cyan]")
        saved_count = self.save_enrichment_batch(enrichments)
        console.print(f"[green]✅ {saved_count} Enrichments gespeichert[/green]")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # Kosten-Zusammenfassung
        costs = self.cost_tracker.get_summary()
        
        return {
            'total_records': len(records),
            'enriched': len(enrichments),
            'saved': saved_count,
            'elapsed_seconds': elapsed,
            'costs': costs,
            'avg_time_per_record': elapsed / len(records) if records else 0
        }


async def main():
    """Hauptfunktion"""
    pipeline = OptimizedEnrichmentPipeline(max_concurrent=5)
    
    result = await pipeline.run_optimized_enrichment(limit=50, max_concurrent=5)
    
    # Zeige Ergebnisse
    console.print("\n[bold green]📊 Ergebnisse:[/bold green]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metrik", style="cyan")
    table.add_column("Wert", style="green")
    
    table.add_row("Records verarbeitet", str(result['total_records']))
    table.add_row("Records angereichert", str(result['enriched']))
    table.add_row("Records gespeichert", str(result['saved']))
    table.add_row("Gesamtzeit (s)", f"{result['elapsed_seconds']:.1f}")
    table.add_row("Durchschnitt pro Record (s)", f"{result['avg_time_per_record']:.2f}")
    
    console.print(table)
    
    # Kosten
    costs = result['costs']
    console.print(f"\n[bold yellow]💰 Kosten:[/bold yellow]")
    console.print(f"  Firecrawl Credits: {costs.get('firecrawl_credits_used', 0):.1f}")
    console.print(f"  Verbleibend: {costs.get('firecrawl_credits_remaining', 20000):,.0f}")
    console.print(f"  Requests: {costs.get('requests_made', 0)}")
    console.print(f"  Runtime: {costs.get('runtime_seconds', 0):.1f}s")


if __name__ == "__main__":
    asyncio.run(main())



