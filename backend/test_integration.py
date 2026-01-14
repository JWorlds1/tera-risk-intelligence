#!/usr/bin/env python3
"""
Integrationstest für das vollständige System
Testet alle Komponenten und deren Zusammenarbeit
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Füge backend zum Path hinzu
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from database import DatabaseManager
from master_orchestrator import MasterOrchestrator
from risk_scoring import RiskScorer
from geocoding import GeocodingService

console = Console()


class IntegrationTester:
    """Testet alle Komponenten des Systems"""
    
    def __init__(self):
        self.config = Config()
        self.db = DatabaseManager()
        self.risk_scorer = RiskScorer()
        self.geocoder = GeocodingService()
        self.results = {
            'database': {'status': 'pending', 'message': ''},
            'scraping': {'status': 'pending', 'message': ''},
            'enrichment': {'status': 'pending', 'message': ''},
            'geocoding': {'status': 'pending', 'message': ''},
            'prediction': {'status': 'pending', 'message': ''},
            'regional_data': {'status': 'pending', 'message': ''},
            'frontend_api': {'status': 'pending', 'message': ''}
        }
    
    def test_database(self) -> bool:
        """Teste Datenbank-Verbindung und Schema"""
        console.print("[cyan]Testing Database...[/cyan]")
        try:
            # Prüfe ob Datenbank existiert
            if not self.db.db_path.exists():
                self.results['database'] = {
                    'status': 'warning',
                    'message': 'Database file does not exist yet (will be created on first use)'
                }
                return True
            
            # Teste Verbindung
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM records")
                count = cursor.fetchone()[0]
            
            self.results['database'] = {
                'status': 'success',
                'message': f'Database connected, {count} records found'
            }
            return True
        except Exception as e:
            self.results['database'] = {
                'status': 'error',
                'message': f'Database error: {e}'
            }
            return False
    
    def test_scraping(self) -> bool:
        """Teste Scraping-Komponenten"""
        console.print("[cyan]Testing Scraping Components...[/cyan]")
        try:
            # Prüfe ob Records vorhanden sind
            records = self.db.get_records(limit=10)
            
            if len(records) == 0:
                self.results['scraping'] = {
                    'status': 'warning',
                    'message': 'No records found. Run scraping pipeline first.'
                }
                return True
            
            # Prüfe Record-Struktur
            sample_record = records[0]
            required_fields = ['id', 'url', 'source_name', 'title']
            missing_fields = [f for f in required_fields if f not in sample_record]
            
            if missing_fields:
                self.results['scraping'] = {
                    'status': 'error',
                    'message': f'Missing fields in records: {missing_fields}'
                }
                return False
            
            self.results['scraping'] = {
                'status': 'success',
                'message': f'{len(records)} records found, structure OK'
            }
            return True
        except Exception as e:
            self.results['scraping'] = {
                'status': 'error',
                'message': f'Scraping test error: {e}'
            }
            return False
    
    def test_enrichment(self) -> bool:
        """Teste Enrichment-Komponenten"""
        console.print("[cyan]Testing Enrichment Components...[/cyan]")
        try:
            # Prüfe ob enriched_data Tabelle existiert
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='enriched_data'
                """)
                
                if not cursor.fetchone():
                    self.results['enrichment'] = {
                        'status': 'warning',
                        'message': 'enriched_data table does not exist yet'
                    }
                    return True
                
                # Prüfe ob angereicherte Records vorhanden sind
                cursor.execute("SELECT COUNT(*) FROM enriched_data")
                enriched_count = cursor.fetchone()[0]
            
            if enriched_count == 0:
                self.results['enrichment'] = {
                    'status': 'warning',
                    'message': 'No enriched records found. Run enrichment pipeline.'
                }
                return True
            
            self.results['enrichment'] = {
                'status': 'success',
                'message': f'{enriched_count} enriched records found'
            }
            return True
        except Exception as e:
            self.results['enrichment'] = {
                'status': 'error',
                'message': f'Enrichment test error: {e}'
            }
            return False
    
    def test_geocoding(self) -> bool:
        """Teste Geocoding"""
        console.print("[cyan]Testing Geocoding...[/cyan]")
        try:
            records = self.db.get_records(limit=100)
            
            if len(records) == 0:
                self.results['geocoding'] = {
                    'status': 'warning',
                    'message': 'No records to geocode'
                }
                return True
            
            # Zähle Records mit Koordinaten
            records_with_coords = sum(
                1 for r in records 
                if r.get('primary_latitude') and r.get('primary_longitude')
            )
            
            # Teste Geocoding-Service
            test_region = "Germany"
            try:
                geo_result = self.geocoder.geocode(test_region)
                geocoding_works = geo_result is not None
            except:
                geocoding_works = False
            
            self.results['geocoding'] = {
                'status': 'success' if geocoding_works else 'warning',
                'message': f'{records_with_coords}/{len(records)} records geocoded. Service: {"OK" if geocoding_works else "Not available"}'
            }
            return True
        except Exception as e:
            self.results['geocoding'] = {
                'status': 'error',
                'message': f'Geocoding test error: {e}'
            }
            return False
    
    def test_prediction(self) -> bool:
        """Teste Prediction-Komponenten"""
        console.print("[cyan]Testing Prediction Components...[/cyan]")
        try:
            records = self.db.get_records(limit=10)
            
            if len(records) == 0:
                self.results['prediction'] = {
                    'status': 'warning',
                    'message': 'No records for prediction testing'
                }
                return True
            
            # Teste Risk Scoring
            test_record = records[0]
            risk = self.risk_scorer.calculate_risk(test_record)
            level = self.risk_scorer.get_risk_level(risk.score)
            
            if not level or risk.score < 0:
                self.results['prediction'] = {
                    'status': 'error',
                    'message': 'Risk scoring returned invalid results'
                }
                return False
            
            self.results['prediction'] = {
                'status': 'success',
                'message': f'Risk scoring OK. Sample: {level} (score: {risk.score:.2f})'
            }
            return True
        except Exception as e:
            self.results['prediction'] = {
                'status': 'error',
                'message': f'Prediction test error: {e}'
            }
            return False
    
    def test_regional_data(self) -> bool:
        """Teste regionale Daten-Aggregation"""
        console.print("[cyan]Testing Regional Data...[/cyan]")
        try:
            critical_regions = ['Germany', 'Europe']
            records = self.db.get_records(limit=1000)
            
            regional_counts = {}
            for region_name in critical_regions:
                if region_name == 'Germany':
                    keywords = ['Germany', 'Deutschland', 'German']
                    countries = ['DE']
                else:
                    keywords = ['Europe', 'Europa', 'European', 'EU']
                    countries = ['DE', 'FR', 'IT', 'ES', 'PL', 'NL', 'BE', 'AT', 'CH', 'CZ', 'SE', 'NO', 'DK', 'FI']
                
                count = sum(
                    1 for r in records
                    if any(kw.lower() in r.get('region', '').lower() for kw in keywords)
                    or r.get('primary_country_code') in countries
                )
                regional_counts[region_name] = count
            
            self.results['regional_data'] = {
                'status': 'success',
                'message': f'Germany: {regional_counts.get("Germany", 0)}, Europe: {regional_counts.get("Europe", 0)} records'
            }
            return True
        except Exception as e:
            self.results['regional_data'] = {
                'status': 'error',
                'message': f'Regional data test error: {e}'
            }
            return False
    
    def test_frontend_api(self) -> bool:
        """Teste Frontend API-Endpoints"""
        console.print("[cyan]Testing Frontend API...[/cyan]")
        try:
            # Simuliere API-Aufrufe
            stats = self.db.get_statistics()
            records = self.db.get_records(limit=10)
            
            # Prüfe ob alle benötigten Daten vorhanden sind
            required_stats = ['total_records', 'records_by_source']
            missing_stats = [s for s in required_stats if s not in stats]
            
            if missing_stats:
                self.results['frontend_api'] = {
                    'status': 'error',
                    'message': f'Missing statistics: {missing_stats}'
                }
                return False
            
            self.results['frontend_api'] = {
                'status': 'success',
                'message': f'API data available: {stats["total_records"]} records, {len(stats["records_by_source"])} sources'
            }
            return True
        except Exception as e:
            self.results['frontend_api'] = {
                'status': 'error',
                'message': f'Frontend API test error: {e}'
            }
            return False
    
    def run_all_tests(self):
        """Führe alle Tests aus"""
        console.print(Panel.fit(
            "[bold blue]Integration Test Suite[/bold blue]",
            subtitle="Testing all system components"
        ))
        console.print()
        
        tests = [
            ('database', self.test_database),
            ('scraping', self.test_scraping),
            ('enrichment', self.test_enrichment),
            ('geocoding', self.test_geocoding),
            ('prediction', self.test_prediction),
            ('regional_data', self.test_regional_data),
            ('frontend_api', self.test_frontend_api)
        ]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            for test_name, test_func in tests:
                task = progress.add_task(f"Testing {test_name}...", total=None)
                test_func()
                progress.remove_task(task)
        
        self.display_results()
    
    def display_results(self):
        """Zeige Testergebnisse"""
        console.print()
        console.print(Panel.fit("[bold]Test Results[/bold]"))
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Message", style="white")
        
        status_colors = {
            'success': '[green]✓[/green]',
            'warning': '[yellow]⚠[/yellow]',
            'error': '[red]✗[/red]',
            'pending': '[gray]-[/gray]'
        }
        
        for component, result in self.results.items():
            status_icon = status_colors.get(result['status'], '-')
            table.add_row(
                component.replace('_', ' ').title(),
                f"{status_icon} {result['status'].upper()}",
                result['message']
            )
        
        console.print(table)
        console.print()
        
        # Zusammenfassung
        success_count = sum(1 for r in self.results.values() if r['status'] == 'success')
        warning_count = sum(1 for r in self.results.values() if r['status'] == 'warning')
        error_count = sum(1 for r in self.results.values() if r['status'] == 'error')
        
        total = len(self.results)
        
        console.print(f"[green]Success:[/green] {success_count}/{total}")
        console.print(f"[yellow]Warnings:[/yellow] {warning_count}/{total}")
        console.print(f"[red]Errors:[/red] {error_count}/{total}")
        
        if error_count == 0:
            console.print("\n[bold green]✓ All critical tests passed![/bold green]")
        else:
            console.print("\n[bold red]✗ Some tests failed. Please check the errors above.[/bold red]")


async def main():
    """Main entry point"""
    tester = IntegrationTester()
    tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())

