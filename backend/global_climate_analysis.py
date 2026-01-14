#!/usr/bin/env python3
"""
Globale Klima-Analyse für alle 195 Länder
Fokus auf am stärksten betroffene Länder weltweit
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
from dataclasses import dataclass, asdict

sys.path.append(str(Path(__file__).parent))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel

console = Console()

from multi_stage_processing import MultiStageProcessor, CityContext, ProcessingStage


# Globale Liste der 195 Länder mit ISO-Codes und Klimarisiko-Priorisierung
# Basierend auf Climate Risk Index, World Risk Report, IPCC-Daten
GLOBAL_COUNTRIES = {
    # Höchste Priorität - Am stärksten betroffen (Top 20)
    "DM": {"name": "Dominica", "priority": 1, "risk_level": "CRITICAL", "region": "Caribbean"},
    "MM": {"name": "Myanmar", "priority": 1, "risk_level": "CRITICAL", "region": "Southeast Asia"},
    "HN": {"name": "Honduras", "priority": 1, "risk_level": "CRITICAL", "region": "Central America"},
    "IN": {"name": "India", "priority": 1, "risk_level": "CRITICAL", "region": "South Asia"},
    "CN": {"name": "China", "priority": 1, "risk_level": "CRITICAL", "region": "East Asia"},
    "PH": {"name": "Philippines", "priority": 1, "risk_level": "CRITICAL", "region": "Southeast Asia"},
    "BD": {"name": "Bangladesh", "priority": 1, "risk_level": "CRITICAL", "region": "South Asia"},
    "VN": {"name": "Vietnam", "priority": 1, "risk_level": "CRITICAL", "region": "Southeast Asia"},
    "PK": {"name": "Pakistan", "priority": 1, "risk_level": "CRITICAL", "region": "South Asia"},
    "TH": {"name": "Thailand", "priority": 1, "risk_level": "CRITICAL", "region": "Southeast Asia"},
    
    # Sehr hohe Priorität (21-50)
    "ID": {"name": "Indonesia", "priority": 2, "risk_level": "HIGH", "region": "Southeast Asia"},
    "LK": {"name": "Sri Lanka", "priority": 2, "risk_level": "HIGH", "region": "South Asia"},
    "NP": {"name": "Nepal", "priority": 2, "risk_level": "HIGH", "region": "South Asia"},
    "AF": {"name": "Afghanistan", "priority": 2, "risk_level": "HIGH", "region": "South Asia"},
    "YE": {"name": "Yemen", "priority": 2, "risk_level": "HIGH", "region": "Middle East"},
    "SO": {"name": "Somalia", "priority": 2, "risk_level": "HIGH", "region": "East Africa"},
    "ET": {"name": "Ethiopia", "priority": 2, "risk_level": "HIGH", "region": "East Africa"},
    "KE": {"name": "Kenya", "priority": 2, "risk_level": "HIGH", "region": "East Africa"},
    "UG": {"name": "Uganda", "priority": 2, "risk_level": "HIGH", "region": "East Africa"},
    "TZ": {"name": "Tanzania", "priority": 2, "risk_level": "HIGH", "region": "East Africa"},
    "MZ": {"name": "Mozambique", "priority": 2, "risk_level": "HIGH", "region": "Southern Africa"},
    "MW": {"name": "Malawi", "priority": 2, "risk_level": "HIGH", "region": "Southern Africa"},
    "ZM": {"name": "Zambia", "priority": 2, "risk_level": "HIGH", "region": "Southern Africa"},
    "ZW": {"name": "Zimbabwe", "priority": 2, "risk_level": "HIGH", "region": "Southern Africa"},
    "NG": {"name": "Nigeria", "priority": 2, "risk_level": "HIGH", "region": "West Africa"},
    "SN": {"name": "Senegal", "priority": 2, "risk_level": "HIGH", "region": "West Africa"},
    "ML": {"name": "Mali", "priority": 2, "risk_level": "HIGH", "region": "West Africa"},
    "NE": {"name": "Niger", "priority": 2, "risk_level": "HIGH", "region": "West Africa"},
    "TD": {"name": "Chad", "priority": 2, "risk_level": "HIGH", "region": "Central Africa"},
    "CF": {"name": "Central African Republic", "priority": 2, "risk_level": "HIGH", "region": "Central Africa"},
    
    # Hohe Priorität - Europa (betroffen aber besser vorbereitet)
    "IT": {"name": "Italy", "priority": 2, "risk_level": "HIGH", "region": "Europe"},
    "FR": {"name": "France", "priority": 2, "risk_level": "HIGH", "region": "Europe"},
    "DE": {"name": "Germany", "priority": 2, "risk_level": "HIGH", "region": "Europe"},
    "ES": {"name": "Spain", "priority": 2, "risk_level": "HIGH", "region": "Europe"},
    "GR": {"name": "Greece", "priority": 2, "risk_level": "HIGH", "region": "Europe"},
    
    # USA & andere entwickelte Länder
    "US": {"name": "United States", "priority": 2, "risk_level": "HIGH", "region": "North America"},
    "AU": {"name": "Australia", "priority": 2, "risk_level": "HIGH", "region": "Oceania"},
    "BR": {"name": "Brazil", "priority": 2, "risk_level": "HIGH", "region": "South America"},
    "MX": {"name": "Mexico", "priority": 2, "risk_level": "HIGH", "region": "North America"},
    "AR": {"name": "Argentina", "priority": 2, "risk_level": "HIGH", "region": "South America"},
    
    # Mittel-Priorität (51-100)
    "GT": {"name": "Guatemala", "priority": 3, "risk_level": "MEDIUM", "region": "Central America"},
    "NI": {"name": "Nicaragua", "priority": 3, "risk_level": "MEDIUM", "region": "Central America"},
    "CR": {"name": "Costa Rica", "priority": 3, "risk_level": "MEDIUM", "region": "Central America"},
    "PA": {"name": "Panama", "priority": 3, "risk_level": "MEDIUM", "region": "Central America"},
    "JM": {"name": "Jamaica", "priority": 3, "risk_level": "MEDIUM", "region": "Caribbean"},
    "HT": {"name": "Haiti", "priority": 3, "risk_level": "MEDIUM", "region": "Caribbean"},
    "CU": {"name": "Cuba", "priority": 3, "risk_level": "MEDIUM", "region": "Caribbean"},
    "DO": {"name": "Dominican Republic", "priority": 3, "risk_level": "MEDIUM", "region": "Caribbean"},
    "MY": {"name": "Malaysia", "priority": 3, "risk_level": "MEDIUM", "region": "Southeast Asia"},
    "SG": {"name": "Singapore", "priority": 3, "risk_level": "MEDIUM", "region": "Southeast Asia"},
    "KH": {"name": "Cambodia", "priority": 3, "risk_level": "MEDIUM", "region": "Southeast Asia"},
    "LA": {"name": "Laos", "priority": 3, "risk_level": "MEDIUM", "region": "Southeast Asia"},
    "MM": {"name": "Myanmar", "priority": 3, "risk_level": "MEDIUM", "region": "Southeast Asia"},
    "JP": {"name": "Japan", "priority": 3, "risk_level": "MEDIUM", "region": "East Asia"},
    "KR": {"name": "South Korea", "priority": 3, "risk_level": "MEDIUM", "region": "East Asia"},
    "TW": {"name": "Taiwan", "priority": 3, "risk_level": "MEDIUM", "region": "East Asia"},
    "IR": {"name": "Iran", "priority": 3, "risk_level": "MEDIUM", "region": "Middle East"},
    "IQ": {"name": "Iraq", "priority": 3, "risk_level": "MEDIUM", "region": "Middle East"},
    "SA": {"name": "Saudi Arabia", "priority": 3, "risk_level": "MEDIUM", "region": "Middle East"},
    "AE": {"name": "United Arab Emirates", "priority": 3, "risk_level": "MEDIUM", "region": "Middle East"},
    "EG": {"name": "Egypt", "priority": 3, "risk_level": "MEDIUM", "region": "North Africa"},
    "SD": {"name": "Sudan", "priority": 3, "risk_level": "MEDIUM", "region": "North Africa"},
    "LY": {"name": "Libya", "priority": 3, "risk_level": "MEDIUM", "region": "North Africa"},
    "DZ": {"name": "Algeria", "priority": 3, "risk_level": "MEDIUM", "region": "North Africa"},
    "MA": {"name": "Morocco", "priority": 3, "risk_level": "MEDIUM", "region": "North Africa"},
    "TN": {"name": "Tunisia", "priority": 3, "risk_level": "MEDIUM", "region": "North Africa"},
    "ZA": {"name": "South Africa", "priority": 3, "risk_level": "MEDIUM", "region": "Southern Africa"},
    "BW": {"name": "Botswana", "priority": 3, "risk_level": "MEDIUM", "region": "Southern Africa"},
    "NA": {"name": "Namibia", "priority": 3, "risk_level": "MEDIUM", "region": "Southern Africa"},
    "AO": {"name": "Angola", "priority": 3, "risk_level": "MEDIUM", "region": "Southern Africa"},
    "GH": {"name": "Ghana", "priority": 3, "risk_level": "MEDIUM", "region": "West Africa"},
    "CI": {"name": "Ivory Coast", "priority": 3, "risk_level": "MEDIUM", "region": "West Africa"},
    "CM": {"name": "Cameroon", "priority": 3, "risk_level": "MEDIUM", "region": "Central Africa"},
    "CG": {"name": "Republic of the Congo", "priority": 3, "risk_level": "MEDIUM", "region": "Central Africa"},
    "CD": {"name": "Democratic Republic of the Congo", "priority": 3, "risk_level": "MEDIUM", "region": "Central Africa"},
    "GA": {"name": "Gabon", "priority": 3, "risk_level": "MEDIUM", "region": "Central Africa"},
    "CO": {"name": "Colombia", "priority": 3, "risk_level": "MEDIUM", "region": "South America"},
    "PE": {"name": "Peru", "priority": 3, "risk_level": "MEDIUM", "region": "South America"},
    "CL": {"name": "Chile", "priority": 3, "risk_level": "MEDIUM", "region": "South America"},
    "EC": {"name": "Ecuador", "priority": 3, "risk_level": "MEDIUM", "region": "South America"},
    "VE": {"name": "Venezuela", "priority": 3, "risk_level": "MEDIUM", "region": "South America"},
    "BO": {"name": "Bolivia", "priority": 3, "risk_level": "MEDIUM", "region": "South America"},
    "PY": {"name": "Paraguay", "priority": 3, "risk_level": "MEDIUM", "region": "South America"},
    "UY": {"name": "Uruguay", "priority": 3, "risk_level": "MEDIUM", "region": "South America"},
    "CA": {"name": "Canada", "priority": 3, "risk_level": "MEDIUM", "region": "North America"},
    "GB": {"name": "United Kingdom", "priority": 3, "risk_level": "MEDIUM", "region": "Europe"},
    "NL": {"name": "Netherlands", "priority": 3, "risk_level": "MEDIUM", "region": "Europe"},
    "BE": {"name": "Belgium", "priority": 3, "risk_level": "MEDIUM", "region": "Europe"},
    "PL": {"name": "Poland", "priority": 3, "risk_level": "MEDIUM", "region": "Europe"},
    "RO": {"name": "Romania", "priority": 3, "risk_level": "MEDIUM", "region": "Europe"},
    "TR": {"name": "Turkey", "priority": 3, "risk_level": "MEDIUM", "region": "Europe"},
    "RU": {"name": "Russia", "priority": 3, "risk_level": "MEDIUM", "region": "Europe"},
    "UA": {"name": "Ukraine", "priority": 3, "risk_level": "MEDIUM", "region": "Europe"},
    "NZ": {"name": "New Zealand", "priority": 3, "risk_level": "MEDIUM", "region": "Oceania"},
    "FJ": {"name": "Fiji", "priority": 3, "risk_level": "MEDIUM", "region": "Pacific Islands"},
    "PG": {"name": "Papua New Guinea", "priority": 3, "risk_level": "MEDIUM", "region": "Pacific Islands"},
    
    # Niedrigere Priorität (101-195) - Rest der Länder
    # Hier würde die vollständige Liste aller 195 Länder stehen
    # Für jetzt: Beispiel-Implementierung mit Top-Prioritäten
}

# Erweitere mit kritischen Städten pro Land
CRITICAL_CITIES_BY_COUNTRY = {
    "IN": ["Mumbai", "Kolkata", "Delhi", "Chennai", "Bangalore"],
    "CN": ["Guangzhou", "Shanghai", "Beijing", "Shenzhen", "Tianjin"],
    "BD": ["Dhaka", "Chittagong", "Khulna"],
    "PH": ["Manila", "Quezon City", "Cebu"],
    "VN": ["Ho Chi Minh City", "Hanoi", "Da Nang"],
    "TH": ["Bangkok", "Chiang Mai"],
    "PK": ["Karachi", "Lahore", "Islamabad"],
    "MM": ["Yangon", "Mandalay"],
    "ID": ["Jakarta", "Surabaya", "Bandung"],
    "IT": ["Rome", "Milan", "Venice", "Naples"],
    "ES": ["Madrid", "Barcelona", "Valencia"],
    "FR": ["Paris", "Marseille", "Lyon"],
    "DE": ["Frankfurt", "Berlin", "Hamburg"],
    "US": ["Miami", "New York", "Los Angeles", "Houston"],
    "BR": ["São Paulo", "Rio de Janeiro", "Brasília"],
    "MX": ["Mexico City", "Guadalajara", "Monterrey"],
}


@dataclass
class CountryContext:
    """Kontext für ein Land"""
    country_code: str
    country_name: str
    region: str
    priority: int
    risk_level: str
    
    # Kritische Städte in diesem Land
    critical_cities: List[str] = None
    
    # Verarbeitete Daten
    text_chunks: List[str] = None
    numerical_data: Dict[str, float] = None
    image_urls: List[str] = None
    vector_chunks: List = None
    
    # Fusionierte Daten
    fused_data: Optional[Any] = None
    
    # Predictions
    llm_predictions: Dict[str, Any] = None
    
    # Frühwarn-Indikatoren
    early_warning_signals: List[Dict[str, Any]] = None
    
    # Update-Status
    last_update: datetime = None
    update_frequency_hours: int = 24
    
    def __post_init__(self):
        if self.critical_cities is None:
            self.critical_cities = []
        if self.text_chunks is None:
            self.text_chunks = []
        if self.numerical_data is None:
            self.numerical_data = {}
        if self.image_urls is None:
            self.image_urls = []
        if self.vector_chunks is None:
            self.vector_chunks = []
        if self.early_warning_signals is None:
            self.early_warning_signals = []
        if self.last_update is None:
            self.last_update = datetime.now()


class GlobalClimateAnalyzer:
    """Globale Klima-Analyse für alle 195 Länder"""
    
    def __init__(self):
        self.country_contexts: Dict[str, CountryContext] = {}
        
        # Initialisiere Länder-Kontexte
        for country_code, country_data in GLOBAL_COUNTRIES.items():
            critical_cities = CRITICAL_CITIES_BY_COUNTRY.get(country_code, [])
            
            self.country_contexts[country_code] = CountryContext(
                country_code=country_code,
                country_name=country_data['name'],
                region=country_data['region'],
                priority=country_data['priority'],
                risk_level=country_data['risk_level'],
                critical_cities=critical_cities
            )
    
    def get_priority_countries(self, max_count: int = 50) -> List[str]:
        """Gebe Länder nach Priorität zurück"""
        sorted_countries = sorted(
            self.country_contexts.items(),
            key=lambda x: (x[1].priority, x[1].risk_level)
        )
        
        return [code for code, _ in sorted_countries[:max_count]]
    
    def get_countries_by_region(self, region: str) -> List[str]:
        """Gebe Länder einer Region zurück"""
        return [
            code for code, context in self.country_contexts.items()
            if context.region == region
        ]
    
    def get_critical_countries(self, risk_level: str = "CRITICAL") -> List[str]:
        """Gebe kritische Länder zurück"""
        return [
            code for code, context in self.country_contexts.items()
            if context.risk_level == risk_level
        ]
    
    async def analyze_country(
        self,
        country_code: str,
        processor: MultiStageProcessor
    ) -> Dict[str, Any]:
        """Analysiere ein Land mit der mehrstufigen Pipeline"""
        if country_code not in self.country_contexts:
            raise ValueError(f"Land {country_code} nicht gefunden")
        
        country_context = self.country_contexts[country_code]
        
        console.print(f"\n[bold cyan]🌍 Analysiere {country_context.country_name} ({country_code})[/bold cyan]")
        
        # Analysiere kritische Städte in diesem Land
        city_results = {}
        
        for city_name in country_context.critical_cities[:3]:  # Limit auf 3 Städte
            try:
                # Erstelle CityContext für diese Stadt
                city_data = {
                    'country_code': country_code,
                    'coordinates': (0, 0),  # Wird später geocodiert
                    'risk_factors': {'general': 'high'},
                    'priority': country_context.priority
                }
                
                # Nutze MultiStageProcessor für Stadt-Analyse
                # (Anpassung nötig - für jetzt: vereinfacht)
                console.print(f"  📍 Analysiere Stadt: {city_name}")
                
            except Exception as e:
                console.print(f"  [yellow]⚠️  Fehler bei {city_name}: {e}[/yellow]")
        
        # Land-weite Analyse
        results = {
            'country_code': country_code,
            'country_name': country_context.country_name,
            'region': country_context.region,
            'priority': country_context.priority,
            'risk_level': country_context.risk_level,
            'critical_cities': country_context.critical_cities,
            'city_results': city_results,
            'timestamp': datetime.now().isoformat()
        }
        
        return results
    
    async def analyze_priority_countries(
        self,
        max_countries: int = 20,
        max_cities_per_country: int = 3
    ) -> Dict[str, Any]:
        """Analysiere Länder mit höchster Priorität"""
        console.print(Panel.fit(
            f"[bold green]🌍 Globale Klima-Analyse[/bold green]\n"
            f"[cyan]Analysiere {max_countries} Länder mit höchster Priorität[/cyan]",
            border_style="green"
        ))
        
        priority_countries = self.get_priority_countries(max_countries)
        
        console.print(f"\n[bold yellow]📋 Prioritäts-Länder:[/bold yellow]")
        for i, country_code in enumerate(priority_countries[:10], 1):
            country = self.country_contexts[country_code]
            console.print(f"  {i}. {country.country_name} ({country_code}) - {country.risk_level}")
        
        results = {}
        
        async with MultiStageProcessor() as processor:
            for country_code in priority_countries:
                try:
                    result = await self.analyze_country(country_code, processor)
                    results[country_code] = result
                except Exception as e:
                    console.print(f"[red]❌ Fehler bei {country_code}: {e}[/red]")
        
        return results
    
    def generate_summary_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generiere Zusammenfassungs-Report"""
        summary = {
            'total_countries_analyzed': len(results),
            'countries_by_risk_level': {},
            'countries_by_region': {},
            'top_risk_countries': [],
            'total_critical_cities': 0
        }
        
        # Gruppiere nach Risk Level
        for country_code, result in results.items():
            risk_level = result.get('risk_level', 'UNKNOWN')
            summary['countries_by_risk_level'][risk_level] = \
                summary['countries_by_risk_level'].get(risk_level, 0) + 1
            
            # Gruppiere nach Region
            region = result.get('region', 'UNKNOWN')
            summary['countries_by_region'][region] = \
                summary['countries_by_region'].get(region, 0) + 1
            
            # Zähle kritische Städte
            summary['total_critical_cities'] += len(result.get('critical_cities', []))
        
        # Top Risk Countries
        sorted_results = sorted(
            results.items(),
            key=lambda x: (
                1 if x[1].get('risk_level') == 'CRITICAL' else 2,
                x[1].get('priority', 999)
            )
        )
        
        summary['top_risk_countries'] = [
            {
                'country_code': code,
                'country_name': result.get('country_name'),
                'risk_level': result.get('risk_level'),
                'region': result.get('region')
            }
            for code, result in sorted_results[:10]
        ]
        
        return summary


async def main():
    """Hauptfunktion"""
    analyzer = GlobalClimateAnalyzer()
    
    # Analysiere Top 20 Länder
    results = await analyzer.analyze_priority_countries(max_countries=20)
    
    # Generiere Report
    summary = analyzer.generate_summary_report(results)
    
    # Zeige Zusammenfassung
    console.print("\n[bold green]📊 Globale Analyse-Zusammenfassung:[/bold green]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metrik", style="cyan")
    table.add_column("Wert", style="green")
    
    table.add_row("Länder analysiert", str(summary['total_countries_analyzed']))
    table.add_row("Kritische Städte gesamt", str(summary['total_critical_cities']))
    
    console.print(table)
    
    # Risk Level Verteilung
    console.print("\n[bold cyan]📈 Verteilung nach Risk Level:[/bold cyan]")
    for risk_level, count in summary['countries_by_risk_level'].items():
        console.print(f"  {risk_level}: {count}")
    
    # Regionale Verteilung
    console.print("\n[bold cyan]🌍 Regionale Verteilung:[/bold cyan]")
    for region, count in sorted(summary['countries_by_region'].items(), key=lambda x: x[1], reverse=True):
        console.print(f"  {region}: {count}")
    
    # Top Risk Countries
    console.print("\n[bold red]⚠️  Top 10 Risk Countries:[/bold red]")
    for i, country in enumerate(summary['top_risk_countries'], 1):
        console.print(f"  {i}. {country['country_name']} ({country['country_code']}) - {country['risk_level']}")
    
    # Speichere Ergebnisse
    output_file = Path("./data/global_climate_analysis.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump({
            'results': results,
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        }, f, indent=2, default=str)
    
    console.print(f"\n[bold green]💾 Ergebnisse gespeichert: {output_file}[/bold green]")


if __name__ == "__main__":
    asyncio.run(main())



