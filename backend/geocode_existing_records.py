#!/usr/bin/env python3
"""
Geocode bestehende Records in der Datenbank
Fügt Koordinaten und Länder-Codes hinzu für Visualisierung
"""
import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

sys.path.append(str(Path(__file__).parent))

from database import DatabaseManager
from geocoding import GeocodingService, GeoLocation

console = Console()


def extract_location_from_text(text: str) -> str:
    """Extrahiere Location aus Text (Title/Summary)"""
    if not text:
        return None
    
    import re
    
    # Liste bekannter Regionen und Länder
    regions = [
        'East Africa', 'West Africa', 'Central Africa', 'Southern Africa',
        'North Africa', 'Sub-Saharan Africa', 'Horn of Africa',
        'Middle East', 'South Asia', 'Southeast Asia', 'East Asia',
        'Central Asia', 'Latin America', 'Caribbean', 'Central America',
        'South America', 'North America', 'Europe', 'Oceania',
        'Pacific Islands', 'Arctic', 'Antarctic'
    ]
    
    # Bekannte Länder (Top 50)
    countries = [
        'Kenya', 'Ethiopia', 'Somalia', 'Sudan', 'South Sudan',
        'Uganda', 'Tanzania', 'Rwanda', 'Burundi', 'Djibouti',
        'Eritrea', 'Yemen', 'Syria', 'Iraq', 'Afghanistan',
        'Pakistan', 'Bangladesh', 'India', 'Nepal', 'Myanmar',
        'Philippines', 'Indonesia', 'Malaysia', 'Thailand', 'Vietnam',
        'China', 'Japan', 'South Korea', 'North Korea', 'Mongolia',
        'Brazil', 'Mexico', 'Argentina', 'Colombia', 'Venezuela',
        'Chile', 'Peru', 'Ecuador', 'Bolivia', 'Paraguay',
        'United States', 'Canada', 'Germany', 'France', 'Italy',
        'Spain', 'Poland', 'United Kingdom', 'Russia', 'Ukraine'
    ]
    
    text_lower = text.lower()
    
    # Suche zuerst nach Regionen
    for region in regions:
        if region.lower() in text_lower:
            return region
    
    # Dann nach Ländern
    for country in countries:
        if country.lower() in text_lower:
            return country
    
    # Versuche Pattern-Matching für Länder-Namen
    # Pattern: "in Country" oder "Country's" oder "Country,"
    country_patterns = [
        r'\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\'s',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),'
    ]
    
    for pattern in country_patterns:
        matches = re.findall(pattern, text)
        if matches:
            # Filtere häufige False Positives
            false_positives = ['The', 'This', 'That', 'These', 'Those', 'United', 'New', 'South', 'North', 'East', 'West']
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                if match not in false_positives and len(match) > 3:
                    return match
    
    return None


async def geocode_record(db: DatabaseManager, geocoder: GeocodingService, record_id: int, record: dict):
    """Geocode einen einzelnen Record"""
    region = record.get('region')
    country = None
    
    # Prüfe World Bank Records für Länder
    if record.get('source_name') == 'World Bank':
        # Hole World Bank spezifische Daten
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT country FROM worldbank_records WHERE record_id = ?", (record_id,))
            wb_data = cursor.fetchone()
            if wb_data and wb_data['country']:
                country = wb_data['country']
    
    # Wenn keine Region/Country vorhanden, extrahiere aus Title/Summary
    if not region and not country:
        title = record.get('title', '')
        summary = record.get('summary', '')
        combined_text = f"{title} {summary}".strip()
        
        if combined_text:
            extracted_location = extract_location_from_text(combined_text)
            if extracted_location:
                # Prüfe ob es eine Region oder ein Land ist
                regions_list = [
                    'East Africa', 'West Africa', 'Central Africa', 'Southern Africa',
                    'North Africa', 'Sub-Saharan Africa', 'Horn of Africa',
                    'Middle East', 'South Asia', 'Southeast Asia', 'East Asia',
                    'Central Asia', 'Latin America', 'Caribbean', 'Central America',
                    'South America', 'North America', 'Europe', 'Oceania'
                ]
                if extracted_location in regions_list:
                    region = extracted_location
                else:
                    country = extracted_location
    
    # Priorität: Country > Region
    location_to_geocode = country or region
    
    if not location_to_geocode:
        return None
    
    # Geocode
    if country:
        geo_location = await geocoder.geocode(country, "country")
    elif region:
        geo_location = await geocoder.geocode_region(region)
    else:
        return None
    
    if not geo_location or not geo_location.latitude:
        return None
    
    # Speichere in geo_locations Tabelle
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Prüfe ob bereits vorhanden
        cursor.execute("SELECT id FROM geo_locations WHERE record_id = ?", (record_id,))
        if cursor.fetchone():
            # Update
            cursor.execute("""
                UPDATE geo_locations SET
                    location_type = ?,
                    name = ?,
                    country_code = ?,
                    latitude = ?,
                    longitude = ?,
                    confidence = ?
                WHERE record_id = ?
            """, (
                geo_location.location_type,
                location_to_geocode,
                geo_location.country_code,
                geo_location.latitude,
                geo_location.longitude,
                geo_location.confidence,
                record_id
            ))
        else:
            # Insert
            cursor.execute("""
                INSERT INTO geo_locations (
                    record_id, location_type, name, country_code,
                    latitude, longitude, confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                record_id,
                geo_location.location_type,
                location_to_geocode,
                geo_location.country_code,
                geo_location.latitude,
                geo_location.longitude,
                geo_location.confidence
            ))
        
        # Update records Tabelle mit primary coordinates
        cursor.execute("""
            UPDATE records SET
                primary_country_code = ?,
                primary_latitude = ?,
                primary_longitude = ?,
                geo_confidence = ?
            WHERE id = ?
        """, (
            geo_location.country_code,
            geo_location.latitude,
            geo_location.longitude,
            geo_location.confidence,
            record_id
        ))
    
    return geo_location


async def geocode_all_records():
    """Geocode alle Records ohne Koordinaten"""
    console.print("[bold blue]🌍 Starte Geocoding für alle Records...[/bold blue]")
    
    db = DatabaseManager()
    geocoder = GeocodingService()
    
    # Hole alle Records ohne Koordinaten (inkl. summary für Location-Extraktion)
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, source_name, title, summary, region
            FROM records
            WHERE primary_latitude IS NULL OR primary_longitude IS NULL
            ORDER BY fetched_at DESC
        """)
        records = [dict(row) for row in cursor.fetchall()]
    
    if not records:
        console.print("[green]✅ Alle Records haben bereits Koordinaten![/green]")
        return
    
    console.print(f"[yellow]Gefunden: {len(records)} Records ohne Koordinaten[/yellow]")
    console.print()
    
    stats = {
        'total': len(records),
        'successful': 0,
        'failed': 0,
        'skipped': 0
    }
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        
        task = progress.add_task("Geocoding...", total=len(records))
        
        for record in records:
            record_id = record['id']
            
            try:
                geo_location = await geocode_record(db, geocoder, record_id, record)
                
                if geo_location:
                    stats['successful'] += 1
                    progress.update(task, advance=1, description=f"✅ {record.get('title', 'N/A')[:30]}...")
                else:
                    stats['skipped'] += 1
                    progress.update(task, advance=1, description=f"⏭️  Keine Location: {record.get('title', 'N/A')[:30]}...")
            except Exception as e:
                stats['failed'] += 1
                progress.update(task, advance=1, description=f"❌ Fehler: {str(e)[:30]}...")
                console.print(f"[red]Fehler bei Record {record_id}: {e}[/red]")
    
    # Zeige Statistiken
    console.print()
    stats_table = Table(title="📊 Geocoding-Statistiken", show_header=True)
    stats_table.add_column("Metrik", style="cyan")
    stats_table.add_column("Wert", style="green")
    
    stats_table.add_row("Gesamt", str(stats['total']))
    stats_table.add_row("Erfolgreich", str(stats['successful']))
    stats_table.add_row("Übersprungen", str(stats['skipped']))
    stats_table.add_row("Fehlgeschlagen", str(stats['failed']))
    
    console.print(stats_table)
    console.print()
    console.print("[bold green]✅ Geocoding abgeschlossen![/bold green]")


if __name__ == "__main__":
    asyncio.run(geocode_all_records())

