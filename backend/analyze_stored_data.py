#!/usr/bin/env python3
"""
Analyse-Script: Prüft welche Daten aktuell in der Datenbank gespeichert sind
Zeigt Datenpunkte aus batch_enrichment Tabelle und analysiert Vollständigkeit
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict, Counter
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from database import DatabaseManager
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress

console = Console()


class DataAnalyzer:
    """Analysiert gespeicherte Daten in der Datenbank"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def analyze_batch_enrichment(self) -> Dict[str, Any]:
        """Analysiere batch_enrichment Tabelle"""
        console.print("\n[bold cyan]📊 Analysiere batch_enrichment Daten...[/bold cyan]\n")
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Prüfe ob Tabelle existiert
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='batch_enrichment'
            """)
            
            if not cursor.fetchone():
                console.print("[yellow]⚠️  Tabelle 'batch_enrichment' existiert noch nicht[/yellow]")
                console.print("[cyan]Führe zuerst batch_enrichment_50.py aus[/cyan]")
                return {
                    'table_exists': False,
                    'total_records': 0
                }
            
            # Hole alle Enrichment-Daten
            cursor.execute("""
                SELECT record_id, datapoints, ipcc_metrics, 
                       extracted_numbers, firecrawl_data, enrichment_timestamp
                FROM batch_enrichment
                ORDER BY enrichment_timestamp DESC
            """)
            
            enrichments = cursor.fetchall()
            
            if not enrichments:
                console.print("[yellow]⚠️  Keine Enrichment-Daten gefunden[/yellow]")
                return {
                    'table_exists': True,
                    'total_records': 0
                }
            
            # Analysiere Datenpunkte
            analysis = {
                'total_records': len(enrichments),
                'datapoints_analysis': defaultdict(list),
                'datapoint_types': Counter(),
                'missing_datapoints': defaultdict(int),
                'ipcc_metrics_analysis': defaultdict(int),
                'extracted_numbers_analysis': defaultdict(int),
                'firecrawl_data_analysis': defaultdict(int),
                'completeness': {}
            }
            
            # Analysiere jeden Record
            for enrich in enrichments:
                record_id, datapoints_json, ipcc_json, numbers_json, firecrawl_json, timestamp = enrich
                
                # Parse JSON
                try:
                    datapoints = json.loads(datapoints_json) if datapoints_json else {}
                    ipcc_metrics = json.loads(ipcc_json) if ipcc_json else {}
                    extracted_numbers = json.loads(numbers_json) if numbers_json else {}
                    firecrawl_data = json.loads(firecrawl_json) if firecrawl_json else {}
                except json.JSONDecodeError as e:
                    console.print(f"[red]JSON Parse Error bei Record {record_id}: {e}[/red]")
                    continue
                
                # Analysiere Datenpunkte
                analysis['datapoint_types'][len(datapoints)] += 1
                
                for key, value in datapoints.items():
                    analysis['datapoints_analysis'][key].append(value)
                    datapoint_type = key.split('_')[0] if '_' in key else key
                    analysis['datapoint_types'][datapoint_type] += 1
                
                # Prüfe fehlende Datenpunkte (sollten 20 sein)
                if len(datapoints) < 20:
                    analysis['missing_datapoints'][record_id] = 20 - len(datapoints)
                
                # Analysiere IPCC-Metriken
                if ipcc_metrics:
                    for key in ipcc_metrics.keys():
                        analysis['ipcc_metrics_analysis'][key] += 1
                
                # Analysiere extrahierte Zahlen
                if extracted_numbers:
                    for key in extracted_numbers.keys():
                        if isinstance(extracted_numbers[key], list):
                            if extracted_numbers[key]:
                                analysis['extracted_numbers_analysis'][key] += len(extracted_numbers[key])
                        elif extracted_numbers[key] is not None:
                            analysis['extracted_numbers_analysis'][key] += 1
                
                # Analysiere Firecrawl-Daten
                if firecrawl_data:
                    for key in firecrawl_data.keys():
                        analysis['firecrawl_data_analysis'][key] += 1
            
            # Berechne Vollständigkeit
            total_expected = analysis['total_records'] * 20
            total_actual = sum(len(dps) for dps in analysis['datapoints_analysis'].values())
            analysis['completeness'] = {
                'total_expected_datapoints': total_expected,
                'total_actual_datapoints': total_actual,
                'completeness_percentage': (total_actual / total_expected * 100) if total_expected > 0 else 0,
                'records_with_20_datapoints': sum(1 for count in analysis['datapoint_types'].items() if isinstance(count, tuple) and count[0] == 20),
                'average_datapoints_per_record': total_actual / analysis['total_records'] if analysis['total_records'] > 0 else 0
            }
            
            return analysis
    
    def show_analysis_results(self, analysis: Dict[str, Any]):
        """Zeige Analyse-Ergebnisse"""
        if not analysis.get('table_exists'):
            return
        
        if analysis['total_records'] == 0:
            return
        
        # Übersicht
        console.print(Panel.fit(
            f"[bold green]📊 Analyse-Ergebnisse[/bold green]\n"
            f"Gesamt Records: {analysis['total_records']}\n"
            f"Durchschnitt Datenpunkte: {analysis['completeness']['average_datapoints_per_record']:.1f}\n"
            f"Vollständigkeit: {analysis['completeness']['completeness_percentage']:.1f}%",
            border_style="green"
        ))
        
        # Datenpunkt-Typen
        console.print("\n[bold cyan]📈 Datenpunkt-Typen (Häufigkeit):[/bold cyan]\n")
        
        datapoint_table = Table(show_header=True, header_style="bold magenta")
        datapoint_table.add_column("Datenpunkt-Typ", style="cyan")
        datapoint_table.add_column("Anzahl Records", style="green")
        datapoint_table.add_column("Beispiel-Wert", style="yellow")
        
        # Sortiere nach Häufigkeit
        sorted_types = sorted(
            analysis['datapoints_analysis'].items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        for datapoint_type, values in sorted_types[:20]:  # Top 20
            count = len(values)
            example = str(values[0])[:30] if values else "N/A"
            datapoint_table.add_row(datapoint_type, str(count), example)
        
        console.print(datapoint_table)
        
        # Vollständigkeit pro Record
        console.print("\n[bold cyan]📊 Vollständigkeit pro Record:[/bold cyan]\n")
        
        completeness_table = Table(show_header=True, header_style="bold magenta")
        completeness_table.add_column("Anzahl Datenpunkte", style="cyan")
        completeness_table.add_column("Anzahl Records", style="green")
        completeness_table.add_column("Prozent", style="yellow")
        
        # Zähle Records nach Anzahl Datenpunkte
        records_by_count = Counter()
        for enrich in self._get_all_enrichments():
            datapoints = json.loads(enrich[1]) if enrich[1] else {}
            records_by_count[len(datapoints)] += 1
        
        total = sum(records_by_count.values())
        for count in sorted(records_by_count.keys(), reverse=True):
            num_records = records_by_count[count]
            percentage = (num_records / total * 100) if total > 0 else 0
            completeness_table.add_row(
                str(count),
                str(num_records),
                f"{percentage:.1f}%"
            )
        
        console.print(completeness_table)
        
        # IPCC-Metriken
        if analysis['ipcc_metrics_analysis']:
            console.print("\n[bold cyan]🌍 IPCC-Metriken:[/bold cyan]\n")
            
            ipcc_table = Table(show_header=True, header_style="bold magenta")
            ipcc_table.add_column("Metrik", style="cyan")
            ipcc_table.add_column("Anzahl Records", style="green")
            
            for metric, count in sorted(analysis['ipcc_metrics_analysis'].items(), key=lambda x: x[1], reverse=True):
                ipcc_table.add_row(metric, str(count))
            
            console.print(ipcc_table)
        
        # Extrahierte Zahlen
        if analysis['extracted_numbers_analysis']:
            console.print("\n[bold cyan]🔢 Extrahierte Zahlen:[/bold cyan]\n")
            
            numbers_table = Table(show_header=True, header_style="bold magenta")
            numbers_table.add_column("Typ", style="cyan")
            numbers_table.add_column("Anzahl Vorkommen", style="green")
            
            for num_type, count in sorted(analysis['extracted_numbers_analysis'].items(), key=lambda x: x[1], reverse=True):
                numbers_table.add_row(num_type, str(count))
            
            console.print(numbers_table)
        
        # Fehlende Datenpunkte
        if analysis['missing_datapoints']:
            console.print("\n[bold yellow]⚠️  Records mit weniger als 20 Datenpunkten:[/bold yellow]\n")
            
            missing_table = Table(show_header=True, header_style="bold magenta")
            missing_table.add_column("Record ID", style="cyan")
            missing_table.add_column("Fehlende Datenpunkte", style="red")
            
            for record_id, missing_count in sorted(analysis['missing_datapoints'].items(), key=lambda x: x[1], reverse=True)[:10]:
                missing_table.add_row(str(record_id), str(missing_count))
            
            console.print(missing_table)
    
    def _get_all_enrichments(self) -> List:
        """Hole alle Enrichment-Daten"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT record_id, datapoints, ipcc_metrics, 
                       extracted_numbers, firecrawl_data, enrichment_timestamp
                FROM batch_enrichment
            """)
            return cursor.fetchall()
    
    def show_detailed_record(self, record_id: int):
        """Zeige detaillierte Daten eines Records"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT record_id, datapoints, ipcc_metrics,
                       extracted_numbers, firecrawl_data, enrichment_timestamp
                FROM batch_enrichment
                WHERE record_id = ?
            """, (record_id,))
            
            enrich = cursor.fetchone()
            if not enrich:
                console.print(f"[red]Record {record_id} nicht gefunden[/red]")
                return
            
            record_id_val, datapoints_json, ipcc_json, numbers_json, firecrawl_json, timestamp = enrich
            
            # Parse JSON
            datapoints = json.loads(datapoints_json) if datapoints_json else {}
            ipcc_metrics = json.loads(ipcc_json) if ipcc_json else {}
            extracted_numbers = json.loads(numbers_json) if numbers_json else {}
            firecrawl_data = json.loads(firecrawl_json) if firecrawl_json else {}
            
            console.print(f"\n[bold cyan]📄 Detaillierte Daten für Record {record_id}:[/bold cyan]\n")
            
            # Datenpunkte
            console.print(f"[green]Datenpunkte ({len(datapoints)}/20):[/green]")
            for key, value in sorted(datapoints.items()):
                console.print(f"  {key}: {value}")
            
            # IPCC-Metriken
            if ipcc_metrics:
                console.print(f"\n[green]IPCC-Metriken:[/green]")
                for key, value in ipcc_metrics.items():
                    console.print(f"  {key}: {value}")
            
            # Extrahierte Zahlen
            if extracted_numbers:
                console.print(f"\n[green]Extrahierte Zahlen:[/green]")
                for key, value in extracted_numbers.items():
                    if isinstance(value, list):
                        console.print(f"  {key}: {len(value)} Werte - {value[:3]}...")
                    else:
                        console.print(f"  {key}: {value}")
            
            # Firecrawl-Daten
            if firecrawl_data:
                console.print(f"\n[green]Firecrawl-Daten:[/green]")
                for key, value in firecrawl_data.items():
                    if isinstance(value, list):
                        console.print(f"  {key}: {len(value)} Ergebnisse")
                    else:
                        console.print(f"  {key}: {value}")


def main():
    """Hauptfunktion"""
    analyzer = DataAnalyzer()
    
    # Analysiere Daten
    analysis = analyzer.analyze_batch_enrichment()
    
    # Zeige Ergebnisse
    analyzer.show_analysis_results(analysis)
    
    # Zeige Beispiel-Record wenn vorhanden
    if analysis.get('total_records', 0) > 0:
        console.print("\n[bold yellow]💡 Tipp: Verwende analyzer.show_detailed_record(record_id) für Details[/bold yellow]")


if __name__ == "__main__":
    main()

