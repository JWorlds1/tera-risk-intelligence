#!/usr/bin/env python3
"""
Zeige alle extrahierten Daten aus der Datenbank
"""
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
import json

sys.path.append(str(Path(__file__).parent))

from database import DatabaseManager

console = Console()


def show_all_tables():
    """Zeige alle Tabellen und deren Inhalt"""
    db = DatabaseManager()
    
    console.print(Panel.fit(
        "[bold green]📊 Datenbank-Inhalte - Extrahierte Daten[/bold green]",
        border_style="green"
    ))
    
    # 1. Haupttabelle: records
    console.print("\n[bold cyan]1️⃣  Haupttabelle: records[/bold cyan]")
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Zeige Schema
        cursor.execute("PRAGMA table_info(records)")
        columns = cursor.fetchall()
        
        table_info = Table(title="Tabellen-Struktur: records", box=box.ROUNDED)
        table_info.add_column("Spalte", style="cyan")
        table_info.add_column("Typ", style="yellow")
        table_info.add_column("Null?", style="green")
        
        for col in columns:
            table_info.add_row(
                col[1],  # column name
                col[2],  # type
                "✓" if col[3] == 0 else "✗"  # not null
            )
        console.print(table_info)
        
        # Zeige Records
        cursor.execute("SELECT COUNT(*) FROM records")
        total_count = cursor.fetchone()[0]
        
        console.print(f"\n[green]Gesamt: {total_count} Records[/green]")
        
        if total_count > 0:
            cursor.execute("""
                SELECT id, url, source_name, title, region, 
                       primary_country_code, primary_latitude, primary_longitude,
                       fetched_at
                FROM records
                ORDER BY fetched_at DESC
                LIMIT 20
            """)
            
            records_table = Table(title=f"Records (letzte 20 von {total_count})", box=box.ROUNDED)
            records_table.add_column("ID", style="cyan", width=5)
            records_table.add_column("Quelle", style="yellow", width=12)
            records_table.add_column("Titel", style="white", width=40, no_wrap=False)
            records_table.add_column("Region", style="blue", width=15)
            records_table.add_column("Land", style="magenta", width=5)
            records_table.add_column("Koordinaten", style="green", width=15)
            records_table.add_column("Datum", style="dim", width=19)
            
            for row in cursor.fetchall():
                coords = ""
                if row[6] and row[7]:
                    coords = f"{row[6]:.2f}, {row[7]:.2f}"
                else:
                    coords = "[red]keine[/red]"
                
                records_table.add_row(
                    str(row[0]),
                    row[2] or "N/A",
                    (row[3] or "N/A")[:40],
                    row[4] or "[red]keine[/red]",
                    row[5] or "[red]keine[/red]",
                    coords,
                    row[8][:19] if row[8] else "N/A"
                )
            
            console.print(records_table)
    
    # 2. NASA-spezifische Daten
    console.print("\n[bold cyan]2️⃣  NASA-spezifische Daten[/bold cyan]")
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM nasa_records")
        nasa_count = cursor.fetchone()[0]
        
        console.print(f"[green]Gesamt: {nasa_count} NASA Records[/green]")
        
        if nasa_count > 0:
            cursor.execute("""
                SELECT r.record_id, r.environmental_indicators, r.satellite_source,
                       rec.title, rec.region
                FROM nasa_records r
                JOIN records rec ON r.record_id = rec.id
                LIMIT 10
            """)
            
            nasa_table = Table(title="NASA Records", box=box.ROUNDED)
            nasa_table.add_column("Record ID", style="cyan", width=8)
            nasa_table.add_column("Titel", style="white", width=35, no_wrap=False)
            nasa_table.add_column("Region", style="blue", width=15)
            nasa_table.add_column("Indikatoren", style="green", width=30, no_wrap=False)
            nasa_table.add_column("Satellit", style="yellow", width=15)
            
            for row in cursor.fetchall():
                indicators = "N/A"
                if row[1]:
                    try:
                        ind_list = json.loads(row[1]) if isinstance(row[1], str) else row[1]
                        indicators = ", ".join(ind_list[:3]) if isinstance(ind_list, list) else str(ind_list)
                    except:
                        indicators = str(row[1])[:30]
                
                nasa_table.add_row(
                    str(row[0]),
                    (row[3] or "N/A")[:35],
                    row[4] or "[red]keine[/red]",
                    indicators,
                    row[2] or "[red]keine[/red]"
                )
            
            console.print(nasa_table)
    
    # 3. UN Press-spezifische Daten
    console.print("\n[bold cyan]3️⃣  UN Press-spezifische Daten[/bold cyan]")
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM un_press_records")
        un_count = cursor.fetchone()[0]
        
        console.print(f"[green]Gesamt: {un_count} UN Press Records[/green]")
        
        if un_count > 0:
            cursor.execute("""
                SELECT r.record_id, r.meeting_coverage, r.security_council, r.speakers,
                       rec.title, rec.region
                FROM un_press_records r
                JOIN records rec ON r.record_id = rec.id
                LIMIT 10
            """)
            
            un_table = Table(title="UN Press Records", box=box.ROUNDED)
            un_table.add_column("Record ID", style="cyan", width=8)
            un_table.add_column("Titel", style="white", width=35, no_wrap=False)
            un_table.add_column("Region", style="blue", width=15)
            un_table.add_column("Meeting", style="green", width=8)
            un_table.add_column("Security Council", style="yellow", width=15)
            un_table.add_column("Speakers", style="magenta", width=20, no_wrap=False)
            
            for row in cursor.fetchall():
                speakers = "N/A"
                if row[3]:
                    try:
                        speakers_list = json.loads(row[3]) if isinstance(row[3], str) else row[3]
                        speakers = ", ".join(speakers_list[:2]) if isinstance(speakers_list, list) else str(speakers_list)
                    except:
                        speakers = str(row[3])[:20]
                
                un_table.add_row(
                    str(row[0]),
                    (row[4] or "N/A")[:35],
                    row[5] or "[red]keine[/red]",
                    "✓" if row[1] else "✗",
                    "✓" if row[2] else "✗",
                    speakers
                )
            
            console.print(un_table)
    
    # 4. World Bank-spezifische Daten
    console.print("\n[bold cyan]4️⃣  World Bank-spezifische Daten[/bold cyan]")
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM worldbank_records")
        wb_count = cursor.fetchone()[0]
        
        console.print(f"[green]Gesamt: {wb_count} World Bank Records[/green]")
        
        if wb_count > 0:
            cursor.execute("""
                SELECT r.record_id, r.country, r.sector, r.project_id,
                       rec.title, rec.region
                FROM worldbank_records r
                JOIN records rec ON r.record_id = rec.id
                LIMIT 10
            """)
            
            wb_table = Table(title="World Bank Records", box=box.ROUNDED)
            wb_table.add_column("Record ID", style="cyan", width=8)
            wb_table.add_column("Titel", style="white", width=35, no_wrap=False)
            wb_table.add_column("Region", style="blue", width=15)
            wb_table.add_column("Land", style="magenta", width=15)
            wb_table.add_column("Sektor", style="green", width=15)
            wb_table.add_column("Project ID", style="yellow", width=15)
            
            for row in cursor.fetchall():
                wb_table.add_row(
                    str(row[0]),
                    (row[4] or "N/A")[:35],
                    row[5] or "[red]keine[/red]",
                    row[1] or "[red]keine[/red]",
                    row[2] or "[red]keine[/red]",
                    row[3] or "[red]keine[/red]"
                )
            
            console.print(wb_table)
    
    # 5. WFP-spezifische Daten
    console.print("\n[bold cyan]5️⃣  WFP-spezifische Daten[/bold cyan]")
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM wfp_records")
        wfp_count = cursor.fetchone()[0]
        
        console.print(f"[green]Gesamt: {wfp_count} WFP Records[/green]")
        
        if wfp_count > 0:
            cursor.execute("""
                SELECT r.record_id, r.crisis_type, r.affected_population,
                       rec.title, rec.region
                FROM wfp_records r
                JOIN records rec ON r.record_id = rec.id
                LIMIT 10
            """)
            
            wfp_table = Table(title="WFP Records", box=box.ROUNDED)
            wfp_table.add_column("Record ID", style="cyan", width=8)
            wfp_table.add_column("Titel", style="white", width=35, no_wrap=False)
            wfp_table.add_column("Region", style="blue", width=15)
            wfp_table.add_column("Crisis Type", style="red", width=15)
            wfp_table.add_column("Betroffene", style="yellow", width=15)
            
            for row in cursor.fetchall():
                wfp_table.add_row(
                    str(row[0]),
                    (row[3] or "N/A")[:35],
                    row[4] or "[red]keine[/red]",
                    row[1] or "[red]keine[/red]",
                    row[2] or "[red]keine[/red]"
                )
            
            console.print(wfp_table)
        else:
            console.print("[yellow]⚠️  Keine WFP Records gefunden[/yellow]")
    
    # 6. Batch Enrichment Daten
    console.print("\n[bold cyan]6️⃣  Batch Enrichment Daten[/bold cyan]")
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Prüfe ob Tabelle existiert
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='batch_enrichment'
        """)
        
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM batch_enrichment")
            enrich_count = cursor.fetchone()[0]
            
            console.print(f"[green]Gesamt: {enrich_count} angereicherte Records[/green]")
            
            if enrich_count > 0:
                cursor.execute("""
                    SELECT be.record_id, be.datapoints, be.ipcc_metrics,
                           rec.title, rec.source_name
                    FROM batch_enrichment be
                    JOIN records rec ON be.record_id = rec.id
                    ORDER BY be.enrichment_timestamp DESC
                    LIMIT 10
                """)
                
                enrich_table = Table(title="Batch Enrichment (letzte 10)", box=box.ROUNDED)
                enrich_table.add_column("Record ID", style="cyan", width=8)
                enrich_table.add_column("Quelle", style="yellow", width=12)
                enrich_table.add_column("Titel", style="white", width=30, no_wrap=False)
                enrich_table.add_column("Datenpunkte", style="green", width=8)
                enrich_table.add_column("IPCC Metriken", style="magenta", width=15)
                
                for row in cursor.fetchall():
                    datapoints_count = 0
                    if row[1]:
                        try:
                            dp = json.loads(row[1]) if isinstance(row[1], str) else row[1]
                            datapoints_count = len(dp) if isinstance(dp, dict) else 0
                        except:
                            pass
                    
                    ipcc_info = "N/A"
                    if row[2]:
                        try:
                            ipcc = json.loads(row[2]) if isinstance(row[2], str) else row[2]
                            if isinstance(ipcc, dict):
                                baseline = ipcc.get('baseline_period', 'N/A')
                                anomaly = ipcc.get('current_anomaly', 'N/A')
                                ipcc_info = f"{baseline} / {anomaly}"[:15]
                        except:
                            pass
                    
                    enrich_table.add_row(
                        str(row[0]),
                        row[4] or "N/A",
                        (row[3] or "N/A")[:30],
                        str(datapoints_count),
                        ipcc_info
                    )
                
                console.print(enrich_table)
        else:
            console.print("[yellow]⚠️  Tabelle 'batch_enrichment' existiert nicht[/yellow]")
    
    # 7. Geocoding-Status
    console.print("\n[bold cyan]7️⃣  Geocoding-Status[/bold cyan]")
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM records WHERE primary_latitude IS NOT NULL AND primary_longitude IS NOT NULL")
        with_coords = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM records")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM records WHERE region IS NOT NULL")
        with_region = cursor.fetchone()[0]
        
        stats_table = Table(title="Geocoding-Statistiken", box=box.ROUNDED)
        stats_table.add_column("Metrik", style="cyan")
        stats_table.add_column("Wert", style="green")
        
        stats_table.add_row("Gesamt Records", str(total))
        stats_table.add_row("Mit Region", str(with_region))
        stats_table.add_row("Mit Koordinaten", str(with_coords))
        stats_table.add_row("Geocoding Rate", f"{(with_coords/total*100):.1f}%" if total > 0 else "0%")
        
        console.print(stats_table)
    
    # 8. Quellen-Verteilung
    console.print("\n[bold cyan]8️⃣  Quellen-Verteilung[/bold cyan]")
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT source_name, COUNT(*) as count
            FROM records
            GROUP BY source_name
            ORDER BY count DESC
        """)
        
        source_table = Table(title="Records nach Quelle", box=box.ROUNDED)
        source_table.add_column("Quelle", style="cyan", width=20)
        source_table.add_column("Anzahl", style="green", width=10)
        source_table.add_column("Prozent", style="yellow", width=10)
        
        total = sum(row[1] for row in cursor.fetchall())
        cursor.execute("""
            SELECT source_name, COUNT(*) as count
            FROM records
            GROUP BY source_name
            ORDER BY count DESC
        """)
        
        for row in cursor.fetchall():
            percent = (row[1] / total * 100) if total > 0 else 0
            source_table.add_row(
                row[0] or "Unknown",
                str(row[1]),
                f"{percent:.1f}%"
            )
        
        console.print(source_table)


if __name__ == "__main__":
    try:
        show_all_tables()
    except Exception as e:
        console.print(f"[red]Fehler: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())



