#!/usr/bin/env python3
"""
Umfassendes System-Debugging-Tool
Testet alle Komponenten und identifiziert Probleme
"""
import os
import sys
import asyncio
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import traceback

sys.path.append(str(Path(__file__).parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.tree import Tree
from rich import box

console = Console()

# Farben für Status
STATUS_OK = "[green]✓[/green]"
STATUS_WARN = "[yellow]⚠[/yellow]"
STATUS_ERROR = "[red]✗[/red]"
STATUS_INFO = "[cyan]ℹ[/cyan]"


class SystemDebugger:
    """Umfassendes Debugging-Tool für das gesamte System"""
    
    def __init__(self):
        self.results = {
            'database': {},
            'pipeline': {},
            'crawling': {},
            'enrichment': {},
            'frontend': {},
            'visualization': {},
            'api': {},
            'overall': {}
        }
        self.errors = []
        self.warnings = []
        self.suggestions = []
    
    def print_header(self, title: str):
        """Drucke Header"""
        console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
        console.print(f"[bold cyan]{title}[/bold cyan]")
        console.print(f"[bold cyan]{'='*60}[/bold cyan]\n")
    
    def check_database(self) -> Dict[str, Any]:
        """Teste Datenbank"""
        self.print_header("📊 Datenbank-Check")
        
        result = {
            'exists': False,
            'tables': [],
            'record_count': 0,
            'records_with_coords': 0,
            'enriched_records': 0,
            'errors': []
        }
        
        db_path = Path("../data/climate_conflict.db")
        
        # Prüfe ob Datenbank existiert
        if not db_path.exists():
            console.print(f"{STATUS_ERROR} Datenbank existiert nicht: {db_path}")
            result['errors'].append("Datenbank existiert nicht")
            self.errors.append("Datenbank fehlt")
            return result
        
        result['exists'] = True
        console.print(f"{STATUS_OK} Datenbank existiert: {db_path}")
        
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Prüfe Tabellen
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            result['tables'] = tables
            
            console.print(f"{STATUS_OK} {len(tables)} Tabellen gefunden")
            
            # Prüfe Records
            if 'records' in tables:
                cursor.execute("SELECT COUNT(*) FROM records")
                record_count = cursor.fetchone()[0]
                result['record_count'] = record_count
                
                if record_count == 0:
                    console.print(f"{STATUS_WARN} Keine Records in Datenbank!")
                    self.warnings.append("Datenbank ist leer - Pipeline muss ausgeführt werden")
                else:
                    console.print(f"{STATUS_OK} {record_count} Records gefunden")
                
                # Prüfe Records mit Koordinaten
                try:
                    cursor.execute("""
                        SELECT COUNT(*) FROM records 
                        WHERE primary_latitude IS NOT NULL AND primary_longitude IS NOT NULL
                    """)
                    records_with_coords = cursor.fetchone()[0]
                    result['records_with_coords'] = records_with_coords
                    
                    if records_with_coords == 0:
                        console.print(f"{STATUS_WARN} Keine Records mit Koordinaten!")
                        self.suggestions.append("Geocoding ausführen: python geocode_existing_records.py")
                    else:
                        console.print(f"{STATUS_OK} {records_with_coords} Records mit Koordinaten")
                except sqlite3.OperationalError as e:
                    console.print(f"{STATUS_WARN} Koordinaten-Spalten fehlen: {e}")
                    self.warnings.append("Koordinaten-Spalten fehlen in records-Tabelle")
            
            # Prüfe Enrichment
            if 'batch_enrichment' in tables:
                cursor.execute("SELECT COUNT(*) FROM batch_enrichment")
                enriched_count = cursor.fetchone()[0]
                result['enriched_records'] = enriched_count
                
                if enriched_count == 0:
                    console.print(f"{STATUS_WARN} Keine angereicherten Records!")
                    self.suggestions.append("Enrichment ausführen: python batch_enrichment_50.py")
                else:
                    console.print(f"{STATUS_OK} {enriched_count} angereicherte Records")
            
            # Prüfe Quellen-Verteilung
            if 'records' in tables:
                cursor.execute("""
                    SELECT source_name, COUNT(*) as count 
                    FROM records 
                    GROUP BY source_name
                """)
                source_dist = {row[0]: row[1] for row in cursor.fetchall()}
                
                if source_dist:
                    console.print(f"\n{STATUS_INFO} Quellen-Verteilung:")
                    for source, count in source_dist.items():
                        console.print(f"  - {source}: {count} Records")
                    result['source_distribution'] = source_dist
            
            conn.close()
            
        except Exception as e:
            error_msg = f"Datenbank-Fehler: {e}"
            console.print(f"{STATUS_ERROR} {error_msg}")
            result['errors'].append(error_msg)
            self.errors.append(error_msg)
            traceback.print_exc()
        
        self.results['database'] = result
        return result
    
    async def check_crawling(self) -> Dict[str, Any]:
        """Teste Crawling-System"""
        self.print_header("🕷️  Crawling-Check")
        
        result = {
            'modules_available': {},
            'url_discovery': {},
            'extraction': {},
            'errors': []
        }
        
        # Prüfe Module
        modules_to_check = [
            ('orchestrator', 'ScrapingOrchestrator'),
            ('optimized_crawler', 'OptimizedCrawler'),
            ('smart_crawler', 'SmartCrawler'),
            ('crawl4ai_integration', 'Crawl4AIIntegration'),
            ('firecrawl_enrichment', 'FirecrawlEnrichment')
        ]
        
        for module_name, class_name in modules_to_check:
            try:
                module = __import__(module_name, fromlist=[class_name])
                cls = getattr(module, class_name)
                result['modules_available'][module_name] = True
                console.print(f"{STATUS_OK} {module_name}.{class_name} verfügbar")
            except Exception as e:
                result['modules_available'][module_name] = False
                console.print(f"{STATUS_WARN} {module_name}.{class_name} nicht verfügbar: {e}")
        
        # Test URL-Discovery
        try:
            from batch_enrichment_50 import BatchEnrichmentPipeline
            pipeline = BatchEnrichmentPipeline()
            
            # Test World Bank (funktioniert zuverlässig)
            console.print(f"\n{STATUS_INFO} Teste URL-Discovery für World Bank...")
            urls = await pipeline.discover_article_urls(
                "World Bank",
                ["https://www.worldbank.org/en/news"],
                target_count=5
            )
            
            if urls:
                console.print(f"{STATUS_OK} {len(urls)} URLs gefunden")
                result['url_discovery']['world_bank'] = len(urls)
            else:
                console.print(f"{STATUS_WARN} Keine URLs gefunden für World Bank")
                result['url_discovery']['world_bank'] = 0
                self.warnings.append("URL-Discovery findet keine Artikel")
            
        except Exception as e:
            error_msg = f"Crawling-Test Fehler: {e}"
            console.print(f"{STATUS_ERROR} {error_msg}")
            result['errors'].append(error_msg)
            self.errors.append(error_msg)
            traceback.print_exc()
        
        self.results['crawling'] = result
        return result
    
    def check_enrichment(self) -> Dict[str, Any]:
        """Teste Enrichment-System"""
        self.print_header("🔮 Enrichment-Check")
        
        result = {
            'modules_available': {},
            'api_keys': {},
            'errors': []
        }
        
        # Prüfe API Keys
        firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if firecrawl_key:
            console.print(f"{STATUS_OK} Firecrawl API Key vorhanden")
            result['api_keys']['firecrawl'] = True
        else:
            console.print(f"{STATUS_WARN} Firecrawl API Key fehlt")
            result['api_keys']['firecrawl'] = False
            self.warnings.append("FIRECRAWL_API_KEY nicht gesetzt")
        
        if openai_key:
            console.print(f"{STATUS_OK} OpenAI API Key vorhanden")
            result['api_keys']['openai'] = True
        else:
            console.print(f"{STATUS_WARN} OpenAI API Key fehlt")
            result['api_keys']['openai'] = False
            self.warnings.append("OPENAI_API_KEY nicht gesetzt")
        
        # Prüfe Module
        enrichment_modules = [
            ('batch_enrichment_50', 'BatchEnrichmentPipeline'),
            ('firecrawl_enrichment', 'FirecrawlEnrichment'),
            ('ipcc_context_engine', 'IPCCContextEngine'),
            ('enriched_predictions', 'EnrichedPredictionPipeline')
        ]
        
        for module_name, class_name in enrichment_modules:
            try:
                module = __import__(module_name, fromlist=[class_name])
                cls = getattr(module, class_name)
                result['modules_available'][module_name] = True
                console.print(f"{STATUS_OK} {module_name}.{class_name} verfügbar")
            except Exception as e:
                result['modules_available'][module_name] = False
                console.print(f"{STATUS_WARN} {module_name}.{class_name} nicht verfügbar: {e}")
        
        self.results['enrichment'] = result
        return result
    
    def check_frontend(self) -> Dict[str, Any]:
        """Teste Frontend"""
        self.print_header("🌐 Frontend-Check")
        
        result = {
            'web_app_exists': False,
            'templates': {},
            'api_endpoints': [],
            'errors': []
        }
        
        web_app_path = Path("web_app.py")
        if web_app_path.exists():
            console.print(f"{STATUS_OK} web_app.py existiert")
            result['web_app_exists'] = True
            
            # Prüfe ob Flask installiert ist
            try:
                import flask
                console.print(f"{STATUS_OK} Flask installiert (Version: {flask.__version__})")
            except ImportError:
                console.print(f"{STATUS_ERROR} Flask nicht installiert!")
                result['errors'].append("Flask nicht installiert")
                self.errors.append("Flask fehlt - pip install flask")
        else:
            console.print(f"{STATUS_ERROR} web_app.py nicht gefunden!")
            result['errors'].append("web_app.py fehlt")
            self.errors.append("Frontend-Datei fehlt")
        
        # Prüfe Templates-Verzeichnis
        templates_dir = Path("templates")
        if templates_dir.exists():
            templates = list(templates_dir.glob("*.html"))
            console.print(f"{STATUS_OK} {len(templates)} Templates gefunden")
            result['templates']['count'] = len(templates)
        else:
            console.print(f"{STATUS_WARN} Templates-Verzeichnis nicht gefunden")
            result['templates']['count'] = 0
        
        self.results['frontend'] = result
        return result
    
    def check_api(self) -> Dict[str, Any]:
        """Teste API-Endpoints"""
        self.print_header("🔌 API-Check")
        
        result = {
            'endpoints': [],
            'database_connection': False,
            'errors': []
        }
        
        # Prüfe Datenbank-Verbindung für API
        db_path = Path("../data/climate_conflict.db")
        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                conn.close()
                console.print(f"{STATUS_OK} Datenbank-Verbindung funktioniert")
                result['database_connection'] = True
            except Exception as e:
                console.print(f"{STATUS_ERROR} Datenbank-Verbindung fehlgeschlagen: {e}")
                result['errors'].append(f"Datenbank-Verbindung: {e}")
        else:
            console.print(f"{STATUS_WARN} Datenbank existiert nicht")
        
        # Erwartete Endpoints
        expected_endpoints = [
            '/api/stats',
            '/api/records',
            '/api/regions',
            '/api/predictions',
            '/api/sources',
            '/api/batch-enrichment'
        ]
        
        console.print(f"\n{STATUS_INFO} Erwartete API-Endpoints:")
        for endpoint in expected_endpoints:
            console.print(f"  - {endpoint}")
            result['endpoints'].append(endpoint)
        
        self.results['api'] = result
        return result
    
    def check_visualization(self) -> Dict[str, Any]:
        """Teste Visualisierung"""
        self.print_header("🗺️  Visualisierung-Check")
        
        result = {
            'leaflet_available': False,
            'records_with_coords': 0,
            'map_data_ready': False,
            'errors': []
        }
        
        # Prüfe ob Leaflet im Frontend verwendet wird
        web_app_path = Path("web_app.py")
        if web_app_path.exists():
            content = web_app_path.read_text()
            if 'leaflet' in content.lower() or 'map' in content.lower():
                console.print(f"{STATUS_OK} Karten-Funktionalität im Code vorhanden")
                result['map_data_ready'] = True
            else:
                console.print(f"{STATUS_WARN} Keine Karten-Funktionalität gefunden")
        
        # Prüfe Daten für Visualisierung
        db_path = Path("../data/climate_conflict.db")
        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                
                # Prüfe Records mit Koordinaten
                try:
                    cursor.execute("""
                        SELECT COUNT(*) FROM records 
                        WHERE primary_latitude IS NOT NULL AND primary_longitude IS NOT NULL
                    """)
                    count = cursor.fetchone()[0]
                    result['records_with_coords'] = count
                    
                    if count > 0:
                        console.print(f"{STATUS_OK} {count} Records mit Koordinaten für Karte")
                    else:
                        console.print(f"{STATUS_WARN} Keine Records mit Koordinaten!")
                        self.suggestions.append("Geocoding ausführen für Visualisierung")
                except sqlite3.OperationalError:
                    console.print(f"{STATUS_WARN} Koordinaten-Spalten fehlen")
                    self.warnings.append("Koordinaten-Spalten fehlen")
                
                conn.close()
            except Exception as e:
                console.print(f"{STATUS_ERROR} Visualisierungs-Check Fehler: {e}")
                result['errors'].append(str(e))
        
        self.results['visualization'] = result
        return result
    
    def generate_report(self) -> str:
        """Generiere zusammenfassenden Report"""
        self.print_header("📋 System-Report")
        
        # Gesamt-Status
        total_errors = len(self.errors)
        total_warnings = len(self.warnings)
        total_suggestions = len(self.suggestions)
        
        # Status-Baum
        tree = Tree("🌍 Geospatial Intelligence System")
        
        # Datenbank
        db_branch = tree.add("📊 Datenbank")
        if self.results['database'].get('exists'):
            db_branch.add(f"{STATUS_OK} Existiert")
            db_branch.add(f"{STATUS_INFO} {self.results['database'].get('record_count', 0)} Records")
            if self.results['database'].get('record_count', 0) == 0:
                db_branch.add(f"{STATUS_WARN} Leer - Pipeline ausführen!")
        else:
            db_branch.add(f"{STATUS_ERROR} Fehlt")
        
        # Crawling
        crawl_branch = tree.add("🕷️  Crawling")
        if self.results['crawling'].get('modules_available'):
            available = sum(1 for v in self.results['crawling']['modules_available'].values() if v)
            total = len(self.results['crawling']['modules_available'])
            crawl_branch.add(f"{STATUS_INFO} {available}/{total} Module verfügbar")
        
        # Enrichment
        enrich_branch = tree.add("🔮 Enrichment")
        if self.results['enrichment'].get('api_keys'):
            if self.results['enrichment']['api_keys'].get('firecrawl'):
                enrich_branch.add(f"{STATUS_OK} Firecrawl API Key")
            else:
                enrich_branch.add(f"{STATUS_WARN} Firecrawl API Key fehlt")
        
        # Frontend
        frontend_branch = tree.add("🌐 Frontend")
        if self.results['frontend'].get('web_app_exists'):
            frontend_branch.add(f"{STATUS_OK} web_app.py vorhanden")
        else:
            frontend_branch.add(f"{STATUS_ERROR} web_app.py fehlt")
        
        # Visualisierung
        viz_branch = tree.add("🗺️  Visualisierung")
        coords = self.results['visualization'].get('records_with_coords', 0)
        if coords > 0:
            viz_branch.add(f"{STATUS_OK} {coords} Records mit Koordinaten")
        else:
            viz_branch.add(f"{STATUS_WARN} Keine Koordinaten-Daten")
        
        console.print(tree)
        
        # Fehler
        if self.errors:
            console.print(f"\n[bold red]❌ Fehler ({total_errors}):[/bold red]")
            for i, error in enumerate(self.errors, 1):
                console.print(f"  {i}. {error}")
        
        # Warnungen
        if self.warnings:
            console.print(f"\n[bold yellow]⚠️  Warnungen ({total_warnings}):[/bold yellow]")
            for i, warning in enumerate(self.warnings, 1):
                console.print(f"  {i}. {warning}")
        
        # Vorschläge
        if self.suggestions:
            console.print(f"\n[bold cyan]💡 Vorschläge ({total_suggestions}):[/bold cyan]")
            for i, suggestion in enumerate(self.suggestions, 1):
                console.print(f"  {i}. {suggestion}")
        
        # Zusammenfassung
        console.print(f"\n[bold green]{'='*60}[/bold green]")
        if total_errors == 0:
            console.print("[bold green]✅ System ist grundsätzlich funktionsfähig![/bold green]")
        else:
            console.print(f"[bold red]❌ {total_errors} kritische Fehler gefunden[/bold red]")
        
        if total_warnings > 0:
            console.print(f"[bold yellow]⚠️  {total_warnings} Warnungen[/bold yellow]")
        
        return "Report generiert"
    
    async def run_full_check(self):
        """Führe vollständigen System-Check durch"""
        console.print(Panel.fit(
            "[bold green]🔍 System-Debugging-Tool[/bold green]\n"
            "Umfassende System-Analyse und Problem-Identifikation",
            border_style="green"
        ))
        
        # Alle Checks durchführen
        self.check_database()
        await self.check_crawling()
        self.check_enrichment()
        self.check_frontend()
        self.check_api()
        self.check_visualization()
        
        # Report generieren
        self.generate_report()
        
        # Nächste Schritte
        console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
        console.print("[bold cyan]🚀 Nächste Schritte:[/bold cyan]\n")
        
        if self.results['database'].get('record_count', 0) == 0:
            console.print("1. [bold]Pipeline ausführen[/bold]:")
            console.print("   python run_pipeline.py")
            console.print("   oder")
            console.print("   python optimized_pipeline.py\n")
        
        if self.results['database'].get('enriched_records', 0) == 0:
            console.print("2. [bold]Enrichment durchführen[/bold]:")
            console.print("   python batch_enrichment_50.py\n")
        
        if self.results['visualization'].get('records_with_coords', 0) == 0:
            console.print("3. [bold]Geocoding durchführen[/bold]:")
            console.print("   python geocode_existing_records.py\n")
        
        console.print("4. [bold]Frontend starten[/bold]:")
        console.print("   python web_app.py")
        console.print("   Dann öffnen: http://localhost:5000\n")


async def main():
    """Hauptfunktion"""
    debugger = SystemDebugger()
    await debugger.run_full_check()


if __name__ == "__main__":
    asyncio.run(main())







