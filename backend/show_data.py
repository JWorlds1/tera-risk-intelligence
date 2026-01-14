#!/usr/bin/env python3
"""
Zeige alle gecrawlten Daten aus der Datenbank
"""
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

sys.path.append(str(Path(__file__).parent))

from database import DatabaseManager
from risk_scoring import RiskScorer

console = Console()
scorer = RiskScorer()


def show_all_data():
    """Zeige alle Daten aus der Datenbank"""
    db = DatabaseManager()
    
    console.print(Panel.fit(
        "[bold green]📊 Gecrawlte Daten - Übersicht[/bold green]",
        border_style="green"
    ))
    
    # Hole alle Records
    records = db.get_records(limit=1000)
    
    if not records:
        console.print("[yellow]Keine Daten in der Datenbank gefunden.[/yellow]")
        return
    
    # Gruppiere nach Quelle
    by_source = {}
    for record in records:
        source = record.get('source_name', 'Unknown')
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(record)
    
    # Zeige für jede Quelle
    for source, source_records in by_source.items():
        console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
        console.print(f"[bold blue]📡 {source} - {len(source_records)} Records[/bold blue]")
        console.print(f"[bold cyan]{'='*60}[/bold cyan]\n")
        
        for i, record in enumerate(source_records, 1):
            # Berechne Risiko
            risk = scorer.calculate_risk(record)
            level = scorer.get_risk_level(risk.score)
            
            # Farben für Risiko-Level
            colors = {
                'CRITICAL': 'red',
                'HIGH': 'orange',
                'MEDIUM': 'yellow',
                'LOW': 'lightblue',
                'MINIMAL': 'lightgray'
            }
            color = colors.get(level, 'white')
            
            console.print(f"[bold]{i}. {record.get('title', 'N/A') or 'N/A'}[/bold]")
            console.print(f"   [cyan]URL:[/cyan] {record.get('url', 'N/A')}")
            console.print(f"   [cyan]Datum:[/cyan] {record.get('publish_date', 'N/A') or 'N/A'}")
            console.print(f"   [cyan]Region:[/cyan] {record.get('region', 'N/A') or 'N/A'}")
            
            if record.get('summary'):
                summary = record['summary'][:150] + "..." if len(record['summary']) > 150 else record['summary']
                console.print(f"   [cyan]Zusammenfassung:[/cyan] {summary}")
            
            # Risiko-Score
            console.print(f"   [{color}]Risiko: {level} (Score: {risk.score:.2f})[/{color}]")
            console.print(f"   [yellow]Climate Risk: {risk.climate_risk:.2f} | Conflict Risk: {risk.conflict_risk:.2f} | Urgency: {risk.urgency:.2f}[/yellow]")
            
            if risk.indicators:
                console.print(f"   [green]Indikatoren: {', '.join(risk.indicators[:5])}[/green]")
            
            # Source-specific data
            if source == 'NASA' and record.get('nasa_data'):
                nasa = record['nasa_data']
                if nasa.get('satellite_source'):
                    console.print(f"   [magenta]Satellit: {nasa['satellite_source']}[/magenta]")
                if nasa.get('environmental_indicators'):
                    indicators = nasa['environmental_indicators']
                    if isinstance(indicators, str):
                        import json
                        try:
                            indicators = json.loads(indicators)
                        except:
                            pass
                    if isinstance(indicators, list):
                        console.print(f"   [magenta]Umwelt-Indikatoren: {', '.join(indicators)}[/magenta]")
            
            if source == 'UN Press' and record.get('un_data'):
                un = record['un_data']
                if un.get('security_council'):
                    console.print(f"   [magenta]Security Council: Ja[/magenta]")
                if un.get('meeting_coverage'):
                    console.print(f"   [magenta]Meeting Coverage: Ja[/magenta]")
            
            if source == 'World Bank' and record.get('worldbank_data'):
                wb = record['worldbank_data']
                if wb.get('country'):
                    console.print(f"   [magenta]Land: {wb['country']}[/magenta]")
                if wb.get('sector'):
                    console.print(f"   [magenta]Sektor: {wb['sector']}[/magenta]")
            
            console.print()
    
    # Zusammenfassung
    stats = db.get_statistics()
    console.print(f"\n[bold green]{'='*60}[/bold green]")
    console.print(f"[bold green]📊 Zusammenfassung[/bold green]")
    console.print(f"[bold green]{'='*60}[/bold green]\n")
    
    summary_table = Table(show_header=True, header_style="bold magenta")
    summary_table.add_column("Quelle", style="cyan")
    summary_table.add_column("Records", style="green")
    
    for source, count in stats.get('records_by_source', {}).items():
        summary_table.add_row(source, str(count))
    
    summary_table.add_row("GESAMT", str(stats.get('total_records', 0)), style="bold")
    
    console.print(summary_table)
    
    # Risiko-Verteilung
    risk_dist = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'MINIMAL': 0}
    for record in records:
        risk = scorer.calculate_risk(record)
        level = scorer.get_risk_level(risk.score)
        risk_dist[level] += 1
    
    console.print(f"\n[bold yellow]⚠️  Risiko-Verteilung:[/bold yellow]")
    risk_table = Table(show_header=True, header_style="bold yellow")
    risk_table.add_column("Risiko-Level", style="cyan")
    risk_table.add_column("Anzahl", style="green")
    
    for level, count in risk_dist.items():
        risk_table.add_row(level, str(count))
    
    console.print(risk_table)


if __name__ == "__main__":
    show_all_data()



