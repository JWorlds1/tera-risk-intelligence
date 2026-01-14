#!/usr/bin/env python3
"""
Quick-Fix Script: Behebt die wichtigsten Probleme automatisch
1. Geocoding für alle Records ohne Koordinaten
2. Prüft und optimiert Datenbank-Struktur
3. Validiert System-Status
"""
import os
import sys
import asyncio
from pathlib import Path
import sqlite3

sys.path.append(str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

console = Console()


def fix_geocoding():
    """Führe Geocoding für alle Records ohne Koordinaten aus"""
    console.print(Panel.fit(
        "[bold cyan]🗺️  Geocoding-Fix[/bold cyan]",
        border_style="cyan"
    ))
    
    try:
        from database import DatabaseManager
        from geocoding import GeocodingService
        
        db = DatabaseManager()
        geocoding = GeocodingService()
        
        # Hole Records ohne Koordinaten
        db_path = Path("../data/climate_conflict.db")
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Prüfe ob Spalten existieren
        cursor.execute("PRAGMA table_info(records)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'primary_latitude' not in columns:
            console.print("  ⚠️  Koordinaten-Spalten fehlen, füge hinzu...")
            cursor.execute("ALTER TABLE records ADD COLUMN primary_latitude REAL")
            cursor.execute("ALTER TABLE records ADD COLUMN primary_longitude REAL")
            cursor.execute("ALTER TABLE records ADD COLUMN country_code TEXT")
            conn.commit()
            console.print("  ✅ Koordinaten-Spalten hinzugefügt")
        
        # Hole Records ohne Koordinaten
        cursor.execute("""
            SELECT id, title, summary, region, source_name 
            FROM records 
            WHERE primary_latitude IS NULL OR primary_longitude IS NULL
        """)
        records_to_geocode = cursor.fetchall()
        
        if not records_to_geocode:
            console.print("  ✅ Alle Records haben bereits Koordinaten")
            conn.close()
            return
        
        console.print(f"  📊 {len(records_to_geocode)} Records ohne Koordinaten gefunden")
        
        # Geocode Records
        geocoded_count = 0
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Geocode Records...", total=len(records_to_geocode))
            
            for record in records_to_geocode:
                try:
                    # Versuche Region zu geocoden
                    location_text = record['region'] or record['title'] or record['summary']
                    
                    if location_text:
                        # Extrahiere Location-Keywords
                        location = geocoding.extract_location(location_text)
                        
                        if location:
                            # Geocode
                            geo_result = geocoding.geocode(location)
                            
                            if geo_result and geo_result.latitude and geo_result.longitude:
                                # Update Record
                                cursor.execute("""
                                    UPDATE records 
                                    SET primary_latitude = ?, 
                                        primary_longitude = ?,
                                        country_code = ?
                                    WHERE id = ?
                                """, (
                                    geo_result.latitude,
                                    geo_result.longitude,
                                    geo_result.country_code,
                                    record['id']
                                ))
                                geocoded_count += 1
                    
                    progress.update(task, advance=1)
                    
                except Exception as e:
                    console.print(f"  ⚠️  Fehler bei Record {record['id']}: {e}")
                    progress.update(task, advance=1)
                    continue
        
        conn.commit()
        conn.close()
        
        console.print(f"  ✅ {geocoded_count} Records geocodiert")
        
    except Exception as e:
        console.print(f"  ❌ Geocoding-Fehler: {e}")
        import traceback
        traceback.print_exc()


def validate_system():
    """Validiere System-Status"""
    console.print(Panel.fit(
        "[bold cyan]✅ System-Validierung[/bold cyan]",
        border_style="cyan"
    ))
    
    db_path = Path("../data/climate_conflict.db")
    
    if not db_path.exists():
        console.print("  ❌ Datenbank existiert nicht!")
        return False
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Prüfe Records
    cursor.execute("SELECT COUNT(*) FROM records")
    record_count = cursor.fetchone()[0]
    console.print(f"  📊 Records: {record_count}")
    
    # Prüfe Koordinaten
    cursor.execute("""
        SELECT COUNT(*) FROM records 
        WHERE primary_latitude IS NOT NULL AND primary_longitude IS NOT NULL
    """)
    coords_count = cursor.fetchone()[0]
    console.print(f"  🗺️  Records mit Koordinaten: {coords_count}")
    
    # Prüfe Enrichment
    try:
        cursor.execute("SELECT COUNT(*) FROM batch_enrichment")
        enriched_count = cursor.fetchone()[0]
        console.print(f"  🔮 Angereicherte Records: {enriched_count}")
    except sqlite3.OperationalError:
        console.print(f"  ⚠️  batch_enrichment Tabelle existiert nicht")
        enriched_count = 0
    
    conn.close()
    
    # Status
    if record_count > 0 and coords_count > 0:
        console.print("  ✅ System ist bereit für Visualisierung!")
        return True
    elif record_count > 0:
        console.print("  ⚠️  Records vorhanden, aber keine Koordinaten")
        return False
    else:
        console.print("  ⚠️  Keine Records vorhanden")
        return False


def main():
    """Hauptfunktion"""
    console.print(Panel.fit(
        "[bold green]🔧 Quick-Fix System[/bold green]\n"
        "Behebt die wichtigsten Probleme automatisch",
        border_style="green"
    ))
    
    # 1. Geocoding
    fix_geocoding()
    
    # 2. Validierung
    console.print()
    is_ready = validate_system()
    
    # Zusammenfassung
    console.print()
    console.print("="*60)
    if is_ready:
        console.print("[bold green]✅ System ist bereit![/bold green]")
        console.print()
        console.print("🚀 Nächste Schritte:")
        console.print("  1. Frontend starten: python web_app.py")
        console.print("  2. Öffne: http://localhost:5000")
    else:
        console.print("[bold yellow]⚠️  System benötigt noch Aufmerksamkeit[/bold yellow]")
        console.print()
        console.print("💡 Empfehlungen:")
        if not is_ready:
            console.print("  - Mehr Daten crawlen: python run_pipeline.py")
            console.print("  - Geocoding erneut ausführen falls nötig")
    console.print("="*60)


if __name__ == "__main__":
    main()

