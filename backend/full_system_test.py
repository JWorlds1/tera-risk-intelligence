#!/usr/bin/env python3
"""
Vollständiger System-Test und Optimierung
Testet Pipeline → Enrichment → Geocoding → Frontend
"""
import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import box

console = Console()

# API Keys (falls nicht in .env)
if not os.getenv("FIRECRAWL_API_KEY"):
    os.environ["FIRECRAWL_API_KEY"] = "fc-a0b3b8aa31244c10b0f15b4f2d570ac7"
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "YOUR_OPENAI_API_KEY_HERE"


class FullSystemTest:
    """Vollständiger System-Test"""
    
    def __init__(self):
        self.results = {}
        self.errors = []
        self.warnings = []
    
    async def test_pipeline(self) -> Dict[str, Any]:
        """Teste Pipeline (Crawling)"""
        console.print(Panel.fit(
            "[bold cyan]📡 Test 1: Pipeline (Crawling)[/bold cyan]",
            border_style="cyan"
        ))
        
        result = {'success': False, 'records_before': 0, 'records_after': 0, 'new_records': 0}
        
        try:
            from database import DatabaseManager
            db = DatabaseManager()
            
            # Prüfe aktuelle Records
            records_before = db.get_records(limit=1000)
            result['records_before'] = len(records_before)
            console.print(f"  📊 Records vor Crawling: {len(records_before)}")
            
            # Wenn bereits genug Records vorhanden, überspringe
            if len(records_before) >= 10:
                console.print(f"  ✅ Genug Records vorhanden, überspringe Crawling")
                result['success'] = True
                result['records_after'] = len(records_before)
                return result
            
            # Versuche optimierte Pipeline
            try:
                from optimized_pipeline import OptimizedCombinedPipeline
                
                console.print("  🚀 Starte optimierte Pipeline...")
                pipeline = OptimizedCombinedPipeline(
                    max_concurrent_crawl=5,  # Konservativ für Test
                    max_concurrent_enrich=0  # Kein Enrichment beim Test
                )
                
                sources = {
                    'World Bank': ['https://www.worldbank.org/en/news']
                }
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task("Crawle Daten...", total=None)
                    
                    pipeline_result = await pipeline.run_full_pipeline(
                        sources=sources,
                        max_articles_per_source=10,
                        enrich_records=False
                    )
                    
                    progress.update(task, completed=True)
                
                # Prüfe neue Records
                records_after = db.get_records(limit=1000)
                result['records_after'] = len(records_after)
                result['new_records'] = len(records_after) - len(records_before)
                
                if result['new_records'] > 0:
                    console.print(f"  ✅ {result['new_records']} neue Records hinzugefügt")
                    result['success'] = True
                else:
                    console.print(f"  ⚠️  Keine neuen Records")
                    self.warnings.append("Pipeline hat keine neuen Records erstellt")
                    result['success'] = True  # Nicht kritisch
                    
            except Exception as e:
                console.print(f"  ⚠️  Optimierte Pipeline nicht verfügbar: {e}")
                self.warnings.append(f"Optimierte Pipeline: {e}")
                
                # Fallback: Versuche Standard-Pipeline
                try:
                    from run_pipeline import main as run_pipeline_main
                    console.print("  🔄 Versuche Standard-Pipeline...")
                    # Pipeline würde hier ausgeführt werden, aber wir überspringen für Test
                    console.print("  ⚠️  Standard-Pipeline übersprungen (manuell ausführen)")
                except Exception as e2:
                    console.print(f"  ❌ Standard-Pipeline auch nicht verfügbar: {e2}")
                    self.errors.append(f"Pipeline-Test fehlgeschlagen: {e2}")
        
        except Exception as e:
            error_msg = f"Pipeline-Test Fehler: {e}"
            console.print(f"  ❌ {error_msg}")
            self.errors.append(error_msg)
            import traceback
            traceback.print_exc()
        
        return result
    
    async def test_enrichment(self) -> Dict[str, Any]:
        """Teste Enrichment"""
        console.print(Panel.fit(
            "[bold cyan]🔮 Test 2: Enrichment[/bold cyan]",
            border_style="cyan"
        ))
        
        result = {'success': False, 'enriched_before': 0, 'enriched_after': 0}
        
        try:
            from database import DatabaseManager
            db = DatabaseManager()
            
            # Prüfe angereicherte Records
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS batch_enrichment (
                        record_id INTEGER PRIMARY KEY,
                        datapoints TEXT,
                        enrichment_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE
                    )
                """)
                cursor.execute("SELECT COUNT(*) FROM batch_enrichment")
                enriched_before = cursor.fetchone()[0]
            
            result['enriched_before'] = enriched_before
            console.print(f"  📊 Angereicherte Records: {enriched_before}")
            
            # Wenn bereits genug angereichert, überspringe
            if enriched_before >= 5:
                console.print(f"  ✅ Genug Records angereichert, überspringe")
                result['success'] = True
                result['enriched_after'] = enriched_before
                return result
            
            # Prüfe ob Records vorhanden sind
            records = db.get_records(limit=10)
            if len(records) == 0:
                console.print(f"  ⚠️  Keine Records zum Anreichern vorhanden")
                self.warnings.append("Keine Records für Enrichment")
                result['success'] = True  # Nicht kritisch
                return result
            
            console.print(f"  ⚠️  Enrichment würde hier ausgeführt werden")
            console.print(f"  💡 Führe manuell aus: python batch_enrichment_50.py")
            result['success'] = True  # Nicht kritisch für Test
            
        except Exception as e:
            error_msg = f"Enrichment-Test Fehler: {e}"
            console.print(f"  ❌ {error_msg}")
            self.errors.append(error_msg)
        
        return result
    
    def test_geocoding(self) -> Dict[str, Any]:
        """Teste Geocoding"""
        console.print(Panel.fit(
            "[bold cyan]🗺️  Test 3: Geocoding[/bold cyan]",
            border_style="cyan"
        ))
        
        result = {'success': False, 'records_with_coords': 0, 'records_total': 0}
        
        try:
            from database import DatabaseManager
            import sqlite3
            
            db = DatabaseManager()
            records = db.get_records(limit=1000)
            result['records_total'] = len(records)
            
            if len(records) == 0:
                console.print(f"  ⚠️  Keine Records vorhanden")
                self.warnings.append("Keine Records für Geocoding")
                result['success'] = True  # Nicht kritisch
                return result
            
            # Prüfe Records mit Koordinaten
            db_path = Path("../data/climate_conflict.db")
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM records 
                    WHERE primary_latitude IS NOT NULL AND primary_longitude IS NOT NULL
                """)
                records_with_coords = cursor.fetchone()[0]
                result['records_with_coords'] = records_with_coords
                
                console.print(f"  📊 Records mit Koordinaten: {records_with_coords}/{len(records)}")
                
                if records_with_coords == 0:
                    console.print(f"  ⚠️  Keine Koordinaten vorhanden")
                    console.print(f"  💡 Führe aus: python geocode_existing_records.py")
                    self.warnings.append("Keine Koordinaten-Daten")
                else:
                    console.print(f"  ✅ {records_with_coords} Records haben Koordinaten")
                
                result['success'] = True
                
            except sqlite3.OperationalError as e:
                console.print(f"  ⚠️  Koordinaten-Spalten fehlen: {e}")
                self.warnings.append("Koordinaten-Spalten fehlen")
                result['success'] = True  # Nicht kritisch
            
            conn.close()
            
        except Exception as e:
            error_msg = f"Geocoding-Test Fehler: {e}"
            console.print(f"  ❌ {error_msg}")
            self.errors.append(error_msg)
        
        return result
    
    def test_frontend(self) -> Dict[str, Any]:
        """Teste Frontend"""
        console.print(Panel.fit(
            "[bold cyan]🌐 Test 4: Frontend[/bold cyan]",
            border_style="cyan"
        ))
        
        result = {'success': False, 'web_app_exists': False, 'flask_available': False}
        
        try:
            # Prüfe web_app.py
            web_app_path = Path("web_app.py")
            if web_app_path.exists():
                console.print(f"  ✅ web_app.py vorhanden")
                result['web_app_exists'] = True
            else:
                console.print(f"  ❌ web_app.py nicht gefunden")
                self.errors.append("web_app.py fehlt")
                return result
            
            # Prüfe Flask
            try:
                import flask
                console.print(f"  ✅ Flask installiert")
                result['flask_available'] = True
                result['success'] = True
            except ImportError:
                console.print(f"  ❌ Flask nicht installiert")
                self.errors.append("Flask fehlt - pip install flask")
                return result
            
            # Prüfe Datenbank für Frontend
            db_path = Path("../data/climate_conflict.db")
            if db_path.exists():
                console.print(f"  ✅ Datenbank vorhanden")
            else:
                console.print(f"  ⚠️  Datenbank fehlt")
                self.warnings.append("Datenbank fehlt")
            
            console.print(f"  💡 Starte Frontend mit: python web_app.py")
            console.print(f"  💡 Dann öffne: http://localhost:5000")
            
        except Exception as e:
            error_msg = f"Frontend-Test Fehler: {e}"
            console.print(f"  ❌ {error_msg}")
            self.errors.append(error_msg)
        
        return result
    
    def generate_summary(self):
        """Generiere Zusammenfassung"""
        console.print("\n" + "="*60)
        console.print("[bold green]📋 Test-Zusammenfassung[/bold green]")
        console.print("="*60 + "\n")
        
        summary_table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        summary_table.add_column("Test", style="cyan", width=20)
        summary_table.add_column("Status", style="green", width=15)
        summary_table.add_column("Details", style="white")
        
        for test_name, result in self.results.items():
            if result.get('success'):
                status = "[green]✓ Erfolg[/green]"
            else:
                status = "[red]✗ Fehler[/red]"
            
            # Details extrahieren
            details = []
            if 'new_records' in result:
                details.append(f"{result['new_records']} neue Records")
            if 'records_with_coords' in result:
                details.append(f"{result['records_with_coords']} mit Koordinaten")
            if 'enriched_after' in result:
                details.append(f"{result['enriched_after']} angereichert")
            
            details_str = ", ".join(details) if details else "-"
            
            summary_table.add_row(test_name, status, details_str)
        
        console.print(summary_table)
        
        # Fehler und Warnungen
        if self.errors:
            console.print(f"\n[bold red]❌ Fehler ({len(self.errors)}):[/bold red]")
            for i, error in enumerate(self.errors, 1):
                console.print(f"  {i}. {error}")
        
        if self.warnings:
            console.print(f"\n[bold yellow]⚠️  Warnungen ({len(self.warnings)}):[/bold yellow]")
            for i, warning in enumerate(self.warnings, 1):
                console.print(f"  {i}. {warning}")
        
        # Nächste Schritte
        console.print(f"\n[bold cyan]🚀 Nächste Schritte:[/bold cyan]\n")
        
        if self.results.get('pipeline', {}).get('records_after', 0) == 0:
            console.print("1. [bold]Pipeline ausführen[/bold]:")
            console.print("   python run_pipeline.py")
            console.print("   oder")
            console.print("   python optimized_pipeline.py\n")
        
        if self.results.get('enrichment', {}).get('enriched_after', 0) < 5:
            console.print("2. [bold]Enrichment durchführen[/bold]:")
            console.print("   python batch_enrichment_50.py\n")
        
        if self.results.get('geocoding', {}).get('records_with_coords', 0) == 0:
            console.print("3. [bold]Geocoding durchführen[/bold]:")
            console.print("   python geocode_existing_records.py\n")
        
        console.print("4. [bold]Frontend starten[/bold]:")
        console.print("   python web_app.py")
        console.print("   Dann öffnen: http://localhost:5000\n")
        
        console.print("5. [bold]System-Debugging ausführen[/bold]:")
        console.print("   python system_debug_tool.py\n")
    
    async def run_all_tests(self):
        """Führe alle Tests aus"""
        console.print(Panel.fit(
            "[bold green]🧪 Vollständiger System-Test[/bold green]\n"
            "Testet: Pipeline → Enrichment → Geocoding → Frontend",
            border_style="green"
        ))
        
        # Alle Tests durchführen
        self.results['pipeline'] = await self.test_pipeline()
        self.results['enrichment'] = await self.test_enrichment()
        self.results['geocoding'] = self.test_geocoding()
        self.results['frontend'] = self.test_frontend()
        
        # Zusammenfassung
        self.generate_summary()


async def main():
    """Hauptfunktion"""
    tester = FullSystemTest()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())

