#!/usr/bin/env python3
"""
Test und Validierung der globalen Pipeline
Stellt sicher, dass für jedes Land Daten in allen Kategorien vorhanden sind
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

sys.path.append(str(Path(__file__).parent))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

from global_climate_analysis import GlobalClimateAnalyzer, GLOBAL_COUNTRIES
from multi_stage_processing import MultiStageProcessor


class PipelineValidator:
    """Validiert Pipeline-Output für jedes Land"""
    
    REQUIRED_CATEGORIES = {
        'data_collection': ['crawled_urls', 'research_data', 'calculated_metrics'],
        'meta_extraction': ['text_chunks', 'numerical_data', 'image_urls'],
        'vector_context': ['chunks_created', 'embeddings_generated'],
        'sensor_fusion': ['fused_data', 'risk_score', 'risk_level'],
        'llm_inference': ['predictions'],
        'early_warning': ['signals', 'total_signals']
    }
    
    REQUIRED_NUMERICAL_FIELDS = [
        'temperatures', 'precipitation', 'population_numbers',
        'financial_amounts', 'risk_score', 'urgency'
    ]
    
    def validate_country_output(self, country_code: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validiere Output für ein Land"""
        validation = {
            'country_code': country_code,
            'country_name': result.get('country_name', 'Unknown'),
            'valid': True,
            'missing_categories': [],
            'missing_fields': [],
            'data_quality': {},
            'warnings': []
        }
        
        stages = result.get('stages', {})
        
        # Prüfe jede Kategorie
        for category, required_fields in self.REQUIRED_CATEGORIES.items():
            if category not in stages:
                validation['missing_categories'].append(category)
                validation['valid'] = False
                continue
            
            category_data = stages[category]
            
            # Prüfe erforderliche Felder
            for field in required_fields:
                if field not in category_data or not category_data[field]:
                    validation['missing_fields'].append(f"{category}.{field}")
                    validation['valid'] = False
            
            # Datenqualität prüfen
            if category == 'meta_extraction':
                text_count = len(category_data.get('text_chunks', []))
                numerical_count = len(category_data.get('numerical_data', {}))
                image_count = len(category_data.get('image_urls', []))
                
                validation['data_quality'][category] = {
                    'text_chunks': text_count,
                    'numerical_data_points': numerical_count,
                    'images': image_count
                }
                
                if text_count == 0:
                    validation['warnings'].append(f"Keine Text-Daten in {category}")
                if numerical_count == 0:
                    validation['warnings'].append(f"Keine numerischen Daten in {category}")
            
            elif category == 'sensor_fusion':
                risk_score = category_data.get('risk_score', 0)
                risk_level = category_data.get('risk_level', 'UNKNOWN')
                
                validation['data_quality'][category] = {
                    'risk_score': risk_score,
                    'risk_level': risk_level
                }
                
                if risk_score == 0:
                    validation['warnings'].append(f"Risk Score ist 0 in {category}")
        
        return validation
    
    def validate_all_countries(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Validiere alle Länder"""
        validations = {}
        total_valid = 0
        total_invalid = 0
        
        for country_code, result in results.items():
            validation = self.validate_country_output(country_code, result)
            validations[country_code] = validation
            
            if validation['valid']:
                total_valid += 1
            else:
                total_invalid += 1
        
        return {
            'validations': validations,
            'summary': {
                'total_countries': len(validations),
                'valid': total_valid,
                'invalid': total_invalid,
                'validation_rate': total_valid / len(validations) if validations else 0
            }
        }


class PipelineTester:
    """Testet die globale Pipeline"""
    
    def __init__(self):
        self.analyzer = GlobalClimateAnalyzer()
        self.validator = PipelineValidator()
    
    async def test_pipeline(
        self,
        max_countries: int = 10,
        show_detailed_output: bool = True
    ) -> Dict[str, Any]:
        """Teste Pipeline mit detailliertem Output"""
        console.print(Panel.fit(
            "[bold green]🧪 Pipeline-Test & Validierung[/bold green]\n"
            f"[cyan]Teste {max_countries} Länder mit vollständiger Validierung[/cyan]",
            border_style="green"
        ))
        
        # Hole Prioritäts-Länder
        priority_countries = self.analyzer.get_priority_countries(max_countries)
        
        console.print(f"\n[bold yellow]📋 Teste {len(priority_countries)} Länder:[/bold yellow]")
        for i, country_code in enumerate(priority_countries[:10], 1):
            country = self.analyzer.country_contexts[country_code]
            console.print(f"  {i}. {country.country_name} ({country_code}) - {country.risk_level}")
        
        # Führe Pipeline aus
        results = {}
        
        async with MultiStageProcessor() as processor:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                task = progress.add_task("Verarbeite Länder...", total=len(priority_countries))
                
                for country_code in priority_countries:
                    try:
                        country = self.analyzer.country_contexts[country_code]
                        
                        # Analysiere kritische Städte in diesem Land
                        city_results = {}
                        
                        for city_name in country.critical_cities[:2]:  # Limit auf 2 Städte für Test
                            try:
                                # Erstelle CityContext
                                from multi_stage_processing import CityContext
                                
                                city_context = CityContext(
                                    city_name=city_name,
                                    country_code=country_code,
                                    coordinates=(0, 0),  # Wird später geocodiert
                                    risk_factors={'general': 'high'},
                                    priority=country.priority
                                )
                                
                                # Führe Pipeline für Stadt aus
                                city_result = await processor.process_city_full_pipeline(city_name)
                                city_results[city_name] = city_result
                                
                            except Exception as e:
                                console.print(f"  [yellow]⚠️  Stadt {city_name}: {e}[/yellow]")
                                city_results[city_name] = {'error': str(e)}
                        
                        # Land-weite Analyse
                        result = {
                            'country_code': country_code,
                            'country_name': country.country_name,
                            'region': country.region,
                            'priority': country.priority,
                            'risk_level': country.risk_level,
                            'critical_cities': country.critical_cities,
                            'city_results': city_results,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        results[country_code] = result
                        progress.update(task, advance=1)
                        
                    except Exception as e:
                        console.print(f"[red]❌ Fehler bei {country_code}: {e}[/red]")
                        results[country_code] = {'error': str(e)}
                        progress.update(task, advance=1)
        
        # Validiere Ergebnisse
        validation_results = self.validator.validate_all_countries(results)
        
        # Zeige detaillierten Output
        if show_detailed_output:
            self.show_detailed_output(results, validation_results)
        
        return {
            'results': results,
            'validation': validation_results
        }
    
    def show_detailed_output(
        self,
        results: Dict[str, Any],
        validation_results: Dict[str, Any]
    ):
        """Zeige detaillierten Output für jedes Land"""
        console.print("\n[bold green]📊 Detaillierter Output pro Land:[/bold green]\n")
        
        validations = validation_results.get('validations', {})
        
        for country_code, result in results.items():
            if 'error' in result:
                console.print(f"\n[red]❌ {country_code}: Fehler - {result['error']}[/red]")
                continue
            
            validation = validations.get(country_code, {})
            country_name = result.get('country_name', 'Unknown')
            
            # Land-Header
            console.print(Panel.fit(
                f"[bold cyan]{country_name} ({country_code})[/bold cyan]\n"
                f"Region: {result.get('region', 'Unknown')} | "
                f"Priority: {result.get('priority', 'N/A')} | "
                f"Risk Level: {result.get('risk_level', 'N/A')}",
                border_style="cyan" if validation.get('valid') else "red"
            ))
            
            # Stadt-Ergebnisse
            city_results = result.get('city_results', {})
            if city_results:
                console.print(f"\n[bold yellow]🏙️  Kritische Städte ({len(city_results)}):[/bold yellow]")
                
                for city_name, city_result in city_results.items():
                    if 'error' in city_result:
                        console.print(f"  [red]❌ {city_name}: {city_result['error']}[/red]")
                        continue
                    
                    summary = city_result.get('summary', {})
                    console.print(f"  [green]✅ {city_name}:[/green]")
                    console.print(f"    • Text-Chunks: {summary.get('text_chunks', 0)}")
                    console.print(f"    • Zahlen: {summary.get('numerical_data_points', 0)}")
                    console.print(f"    • Bilder: {summary.get('images', 0)}")
                    console.print(f"    • Risk Score: {summary.get('risk_score', 0):.2f}")
                    console.print(f"    • Warnsignale: {summary.get('warning_signals', 0)}")
                    
                    # Zeige Stages
                    stages = city_result.get('stages', {})
                    if stages:
                        console.print(f"    [dim]Stages: {', '.join(stages.keys())}[/dim]")
                    
                    # Zeige dynamische Suche-Info
                    data_collection = stages.get('data_collection', {})
                    dynamic_search = data_collection.get('dynamic_search', {})
                    if dynamic_search:
                        if dynamic_search.get('found'):
                            console.print(f"    [green]✓ Dynamische Suche: {dynamic_search.get('total_searches', 0)} Versuche, {len(dynamic_search.get('sources_searched', []))} Quellen[/green]")
                        else:
                            console.print(f"    [yellow]⚠️  Umfassende Suche durchgeführt: {dynamic_search.get('total_searches', 0)} Versuche, keine Daten gefunden[/yellow]")
                            console.print(f"    [dim]Quellen: {', '.join(dynamic_search.get('sources_searched', [])[:5])}...[/dim]")
            
            # Dynamische Suche-Status
            stages = result.get('stages', {})
            data_collection = stages.get('data_collection', {})
            dynamic_search = data_collection.get('dynamic_search', {})
            
            if dynamic_search:
                console.print(f"\n[bold cyan]🔍 Dynamische Suche:[/bold cyan]")
                if dynamic_search.get('found'):
                    console.print(f"  [green]✅ Daten gefunden nach {dynamic_search.get('total_searches', 0)} Versuchen[/green]")
                    console.print(f"  [green]Quellen durchsucht: {len(dynamic_search.get('sources_searched', []))}[/green]")
                else:
                    console.print(f"  [yellow]⚠️  Umfassende Suche durchgeführt[/yellow]")
                    console.print(f"  [yellow]Versuche: {dynamic_search.get('total_searches', 0)}[/yellow]")
                    console.print(f"  [yellow]Quellen: {len(dynamic_search.get('sources_searched', []))}[/yellow]")
                    if dynamic_search.get('comprehensive_search'):
                        console.print(f"  [yellow]✓ Komplette Suche durchgeführt - keine passenden Daten verfügbar[/yellow]")
            
            # Validierung
            if validation:
                console.print(f"\n[bold magenta]✓ Validierung:[/bold magenta]")
                
                if validation.get('valid'):
                    console.print("  [green]✅ Alle Kategorien vorhanden[/green]")
                else:
                    console.print("  [red]❌ Fehlende Kategorien:[/red]")
                    for missing in validation.get('missing_categories', []):
                        console.print(f"    • {missing}")
                    for missing in validation.get('missing_fields', []):
                        console.print(f"    • {missing}")
                
                # Datenqualität
                data_quality = validation.get('data_quality', {})
                if data_quality:
                    console.print(f"  [cyan]Datenqualität:[/cyan]")
                    for category, quality in data_quality.items():
                        console.print(f"    • {category}: {quality}")
                
                # Warnungen
                warnings = validation.get('warnings', [])
                if warnings:
                    console.print(f"  [yellow]⚠️  Warnungen:[/yellow]")
                    for warning in warnings:
                        console.print(f"    • {warning}")
            
            console.print()  # Leerzeile zwischen Ländern
        
        # Zusammenfassung
        summary = validation_results.get('summary', {})
        console.print("\n[bold green]📈 Validierungs-Zusammenfassung:[/bold green]\n")
        
        summary_table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        summary_table.add_column("Metrik", style="cyan")
        summary_table.add_column("Wert", style="green")
        
        summary_table.add_row("Gesamt Länder", str(summary.get('total_countries', 0)))
        summary_table.add_row("✅ Valide", str(summary.get('valid', 0)))
        summary_table.add_row("❌ Ungültig", str(summary.get('invalid', 0)))
        summary_table.add_row("Validierungsrate", f"{summary.get('validation_rate', 0)*100:.1f}%")
        
        console.print(summary_table)
    
    def show_data_coverage_table(self, results: Dict[str, Any]):
        """Zeige Datenabdeckung-Tabelle für alle Länder"""
        console.print("\n[bold green]📋 Datenabdeckung pro Land:[/bold green]\n")
        
        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        table.add_column("Land", style="cyan", width=20)
        table.add_column("Code", style="yellow", width=5)
        table.add_column("Text", style="green", justify="center")
        table.add_column("Zahlen", style="green", justify="center")
        table.add_column("Bilder", style="green", justify="center")
        table.add_column("Risk Score", style="red", justify="center")
        table.add_column("Warnsignale", style="magenta", justify="center")
        table.add_column("Status", style="blue", justify="center")
        
        for country_code, result in results.items():
            if 'error' in result:
                table.add_row(
                    result.get('country_name', 'Unknown'),
                    country_code,
                    "❌", "❌", "❌", "❌", "❌", "[red]ERROR[/red]"
                )
                continue
            
            # Sammle Daten aus allen Stadt-Ergebnissen
            total_text = 0
            total_numerical = 0
            total_images = 0
            avg_risk_score = 0.0
            total_warnings = 0
            
            city_results = result.get('city_results', {})
            valid_cities = 0
            
            for city_name, city_result in city_results.items():
                if 'error' not in city_result:
                    summary = city_result.get('summary', {})
                    total_text += summary.get('text_chunks', 0)
                    total_numerical += summary.get('numerical_data_points', 0)
                    total_images += summary.get('images', 0)
                    avg_risk_score += summary.get('risk_score', 0)
                    total_warnings += summary.get('warning_signals', 0)
                    valid_cities += 1
            
            if valid_cities > 0:
                avg_risk_score = avg_risk_score / valid_cities
            
            # Status basierend auf Datenverfügbarkeit
            has_data = total_text > 0 or total_numerical > 0 or total_images > 0
            status = "[green]✅[/green]" if has_data else "[yellow]⚠️[/yellow]"
            
            table.add_row(
                result.get('country_name', 'Unknown')[:18],
                country_code,
                "✅" if total_text > 0 else "❌",
                "✅" if total_numerical > 0 else "❌",
                "✅" if total_images > 0 else "❌",
                f"{avg_risk_score:.2f}" if avg_risk_score > 0 else "N/A",
                str(total_warnings),
                status
            )
        
        console.print(table)


async def main():
    """Hauptfunktion"""
    tester = PipelineTester()
    
    # Teste Pipeline mit 10 Ländern
    test_results = await tester.test_pipeline(
        max_countries=10,
        show_detailed_output=True
    )
    
    # Zeige Datenabdeckung-Tabelle
    tester.show_data_coverage_table(test_results['results'])
    
    # Speichere Ergebnisse
    output_file = Path("./data/pipeline_test_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)
    
    console.print(f"\n[bold green]💾 Test-Ergebnisse gespeichert: {output_file}[/bold green]")
    
    # Zeige Validierungs-Zusammenfassung
    validation = test_results.get('validation', {})
    summary = validation.get('summary', {})
    
    if summary.get('validation_rate', 0) < 1.0:
        console.print(f"\n[yellow]⚠️  Validierungsrate: {summary.get('validation_rate', 0)*100:.1f}%[/yellow]")
        console.print("[yellow]Einige Länder haben fehlende Daten. Prüfe Output oben.[/yellow]")
    else:
        console.print(f"\n[green]✅ Alle Länder haben vollständige Daten![/green]")


if __name__ == "__main__":
    asyncio.run(main())

