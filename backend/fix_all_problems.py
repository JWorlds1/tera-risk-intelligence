#!/usr/bin/env python3
"""
Script zum Beheben aller identifizierten Probleme
"""
import asyncio
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from database import DatabaseManager
from geocode_existing_records import geocode_all_records
from batch_enrichment_50 import BatchEnrichmentPipeline
from config import Config

console = Console()


async def fix_all_problems():
    """Behebe alle identifizierten Probleme"""
    console.print("[bold blue]🔧 BEHEBE ALLE PROBLEME[/bold blue]")
    console.print("=" * 60)
    
    db = DatabaseManager()
    config = Config()
    
    # 1. Geocoding für alle Records
    console.print("\n[cyan]1️⃣  Geocoding für alle Records...[/cyan]")
    try:
        await geocode_all_records()
        console.print("[green]✅ Geocoding abgeschlossen[/green]")
    except Exception as e:
        console.print(f"[red]❌ Geocoding-Fehler: {e}[/red]")
    
    # 2. Enrichment für alle Records
    console.print("\n[cyan]2️⃣  Enrichment für alle Records...[/cyan]")
    try:
        pipeline = BatchEnrichmentPipeline()
        records = db.get_records(limit=100)
        console.print(f"   Gefunden: {len(records)} Records")
        
        # Prüfe welche Records bereits angereichert sind
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT record_id FROM batch_enrichment")
            enriched_ids = {row[0] for row in cursor.fetchall()}
        
        # Filtere Records die noch nicht angereichert sind
        records_to_enrich = [r for r in records if r['id'] not in enriched_ids]
        console.print(f"   Noch zu anreichern: {len(records_to_enrich)} Records")
        
        if records_to_enrich:
            # Verwende enrich_with_20_datapoints für jeden Record
            enriched = 0
            for record in records_to_enrich[:50]:  # Limit auf 50 für Test
                try:
                    record_dict = {
                        'url': record.get('url', ''),
                        'source_name': record.get('source_name', ''),
                        'title': record.get('title'),
                        'summary': record.get('summary'),
                        'region': record.get('region'),
                        'publish_date': record.get('publish_date'),
                        'topics': record.get('topics', []),
                        'full_text': record.get('full_text')
                    }
                    
                    enrichment = pipeline.enrich_with_20_datapoints(record_dict)
                    record_id = pipeline.save_enriched_record(record_dict, enrichment)
                    
                    if record_id:
                        enriched += 1
                        console.print(f"   ✅ Record {record['id']} angereichert ({len(enrichment.get('datapoints', {}))} Datenpunkte)")
                except Exception as e:
                    console.print(f"   [yellow]Warnung bei Record {record['id']}: {e}[/yellow]")
            
            console.print(f"[green]✅ {enriched} Records angereichert[/green]")
        else:
            console.print("[yellow]⚠️  Alle Records sind bereits angereichert[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Enrichment-Fehler: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
    
    # 3. Prüfe Status
    console.print("\n[cyan]3️⃣  Finaler Status-Check...[/cyan]")
    stats = db.get_statistics()
    
    console.print(f"\n   Records: {stats['total_records']}")
    console.print(f"   Mit Koordinaten: {stats['records_with_coordinates']}")
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM batch_enrichment')
        batch_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM enriched_data')
        enriched_count = cursor.fetchone()[0]
    
    console.print(f"   Batch-Enrichment: {batch_count}")
    console.print(f"   Vollständig angereichert: {enriched_count}")
    
    console.print("\n[bold green]✅ Alle Fixes abgeschlossen![/bold green]")


if __name__ == "__main__":
    asyncio.run(fix_all_problems())

