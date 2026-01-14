#!/usr/bin/env python3
"""
Importiere bestehende Daten aus JSON-Dateien in die Datenbank
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console

sys.path.append(str(Path(__file__).parent))

from database import DatabaseManager
from schemas import PageRecord, NASARecord, UNPressRecord, WorldBankRecord

console = Console()


def import_json_data():
    """Importiere Daten aus JSON-Dateien"""
    console.print("[bold blue]📥 Importiere bestehende Daten...[/bold blue]")
    
    db = DatabaseManager()
    data_dir = Path("./data")
    
    imported = 0
    
    # NASA Daten
    nasa_file = data_dir / "nasa_data.json"
    if nasa_file.exists():
        console.print(f"\n[yellow]Importiere NASA Daten...[/yellow]")
        with open(nasa_file, 'r') as f:
            nasa_data = json.load(f)
        
        records = []
        for item in nasa_data:
            try:
                record = NASARecord(
                    url=item.get('url', ''),
                    source_domain='earthobservatory.nasa.gov',
                    source_name='NASA',
                    fetched_at=datetime.fromisoformat(item.get('extracted_at', datetime.now().isoformat())),
                    title=item.get('title'),
                    summary=item.get('description'),
                    publish_date=item.get('date'),
                    region=item.get('region'),
                    topics=[],
                    content_type='article'
                )
                records.append(record)
            except Exception as e:
                console.print(f"  ⚠️  Fehler bei {item.get('url', 'N/A')}: {e}")
        
        if records:
            db_stats = db.insert_records_batch(records)
            imported += db_stats['new']
            console.print(f"  ✅ {db_stats['new']} neue Records")
    
    # UN Daten
    un_file = data_dir / "un_data.json"
    if un_file.exists():
        console.print(f"\n[yellow]Importiere UN Press Daten...[/yellow]")
        with open(un_file, 'r') as f:
            un_data = json.load(f)
        
        records = []
        for item in un_data:
            try:
                record = UNPressRecord(
                    url=item.get('url', ''),
                    source_domain='press.un.org',
                    source_name='UN Press',
                    fetched_at=datetime.fromisoformat(item.get('extracted_at', datetime.now().isoformat())),
                    title=item.get('title'),
                    summary=item.get('description'),
                    publish_date=item.get('date'),
                    region=None,
                    topics=[item.get('topics')] if item.get('topics') else [],
                    content_type='press-release',
                    meeting_coverage='meeting' in (item.get('title', '') + item.get('description', '')).lower(),
                    security_council='security council' in (item.get('title', '') + item.get('description', '')).lower()
                )
                records.append(record)
            except Exception as e:
                console.print(f"  ⚠️  Fehler bei {item.get('url', 'N/A')}: {e}")
        
        if records:
            db_stats = db.insert_records_batch(records)
            imported += db_stats['new']
            console.print(f"  ✅ {db_stats['new']} neue Records")
    
    # World Bank Daten
    wb_file = data_dir / "worldbank_data.json"
    if wb_file.exists():
        console.print(f"\n[yellow]Importiere World Bank Daten...[/yellow]")
        with open(wb_file, 'r') as f:
            wb_data = json.load(f)
        
        records = []
        for item in wb_data:
            try:
                record = WorldBankRecord(
                    url=item.get('url', ''),
                    source_domain='worldbank.org',
                    source_name='World Bank',
                    fetched_at=datetime.fromisoformat(item.get('extracted_at', datetime.now().isoformat())),
                    title=item.get('title'),
                    summary=item.get('description'),
                    publish_date=item.get('date'),
                    region=item.get('country'),
                    topics=[item.get('sector')] if item.get('sector') else [],
                    content_type='news',
                    country=item.get('country'),
                    sector=item.get('sector')
                )
                records.append(record)
            except Exception as e:
                console.print(f"  ⚠️  Fehler bei {item.get('url', 'N/A')}: {e}")
        
        if records:
            db_stats = db.insert_records_batch(records)
            imported += db_stats['new']
            console.print(f"  ✅ {db_stats['new']} neue Records")
    
    # Zeige Statistiken
    stats = db.get_statistics()
    console.print(f"\n[bold green]✅ Import abgeschlossen![/bold green]")
    console.print(f"[bold blue]📊 Datenbank-Statistiken:[/bold blue]")
    console.print(f"  Gesamt Records: {stats.get('total_records', 0)}")
    console.print(f"  Nach Quelle:")
    for source, count in stats.get('records_by_source', {}).items():
        console.print(f"    {source}: {count}")


if __name__ == "__main__":
    import_json_data()



