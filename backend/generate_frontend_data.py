#!/usr/bin/env python3
"""
Generiere Frontend-Daten für alle kritischen Länder
Output: GeoJSON + strukturierte Daten für Karten und Frühwarnsystem
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import json

sys.path.append(str(Path(__file__).parent))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel

console = Console()

from frontend_data_processor import FrontendDataProcessor
from global_climate_analysis import GLOBAL_COUNTRIES, CRITICAL_CITIES_BY_COUNTRY


async def generate_all_frontend_data(max_countries: int = 20) -> Dict[str, Any]:
    """Generiere Frontend-Daten für alle kritischen Länder"""
    console.print(Panel.fit(
        "[bold green]🌍 Generiere Frontend-Daten[/bold green]\n"
        f"[cyan]Für {max_countries} kritische Länder mit Städten[/cyan]",
        border_style="green"
    ))
    
    processor = FrontendDataProcessor()
    await processor.__aenter__()
    
    # Sammle alle Locations
    all_locations = []
    
    # Prioritäts-Länder
    priority_countries = sorted(
        GLOBAL_COUNTRIES.items(),
        key=lambda x: (x[1]['priority'], x[1]['risk_level'] == 'CRITICAL')
    )[:max_countries]
    
    for country_code, country_data in priority_countries:
        country_name = country_data['name']
        
        # Kritische Städte für dieses Land
        critical_cities = CRITICAL_CITIES_BY_COUNTRY.get(country_code, [])
        
        # Füge Hauptstadt hinzu (vereinfacht - Koordinaten würden geocodiert)
        if critical_cities:
            for city_name in critical_cities[:2]:  # Max 2 Städte pro Land
                # Vereinfachte Koordinaten (würde normalerweise geocodiert)
                coords = (0, 0)  # Placeholder
                all_locations.append((city_name, country_code, 'city', coords))
        else:
            # Wenn keine Städte, füge Land hinzu
            all_locations.append((country_name, country_code, 'country', (0, 0)))
    
    console.print(f"\n[cyan]📋 Verarbeite {len(all_locations)} Locations...[/cyan]\n")
    
    # Generiere Frontend-Daten
    frontend_output = await processor.generate_frontend_output(all_locations)
    
    await processor.__aexit__(None, None, None)
    
    return frontend_output


async def main():
    """Hauptfunktion"""
    # Generiere Daten
    frontend_output = await generate_all_frontend_data(max_countries=10)
    
    # Speichere verschiedene Formate
    output_dir = Path("./data/frontend")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Vollständiger JSON-Output
    with open(output_dir / "complete_data.json", 'w') as f:
        json.dump(frontend_output, f, indent=2, default=str)
    
    # 2. GeoJSON für Karten
    geojson_features = []
    for location in frontend_output['locations']:
        feature = location['geojson'].copy()
        feature['properties'].update({
            'name': location['location_name'],
            'country_code': location['country_code'],
            'risk_level': location['risk_level'],
            'risk_score': location['risk_score'],
            'urgency_score': location['urgency_score']
        })
        geojson_features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": geojson_features
    }
    
    with open(output_dir / "map_data.geojson", 'w') as f:
        json.dump(geojson, f, indent=2)
    
    # 3. Frühwarnsystem-Daten
    early_warning_data = {
        'locations': [
            {
                'id': loc['location_id'],
                'name': loc['location_name'],
                'country_code': loc['country_code'],
                'coordinates': loc['coordinates'],
                'early_warning': loc['early_warning'],
                'risk_level': loc['risk_level'],
                'urgency_score': loc['urgency_score']
            }
            for loc in frontend_output['locations']
            if loc['early_warning']['total_signals'] > 0 or loc['urgency_score'] > 0.3
        ],
        'generated_at': datetime.now().isoformat()
    }
    
    with open(output_dir / "early_warning.json", 'w') as f:
        json.dump(early_warning_data, f, indent=2, default=str)
    
    # 4. Klimaanpassungs-Empfehlungen
    adaptation_data = {
        'recommendations_by_location': {
            loc['location_id']: {
                'location_name': loc['location_name'],
                'country_code': loc['country_code'],
                'recommendations': loc['adaptation_recommendations']
            }
            for loc in frontend_output['locations']
        },
        'generated_at': datetime.now().isoformat()
    }
    
    with open(output_dir / "adaptation_recommendations.json", 'w') as f:
        json.dump(adaptation_data, f, indent=2, default=str)
    
    # 5. Kausale Zusammenhänge
    causal_data = {
        'network': frontend_output['causal_network'],
        'relationships_by_location': {
            loc['location_id']: loc['causal_relationships']
            for loc in frontend_output['locations']
        },
        'generated_at': datetime.now().isoformat()
    }
    
    with open(output_dir / "causal_relationships.json", 'w') as f:
        json.dump(causal_data, f, indent=2, default=str)
    
    # Zeige Zusammenfassung
    console.print("\n[bold green]✅ Frontend-Daten generiert![/bold green]\n")
    console.print(f"[cyan]Gespeichert in: {output_dir}[/cyan]\n")
    
    console.print("[bold yellow]📁 Generierte Dateien:[/bold yellow]")
    console.print("  1. complete_data.json - Vollständige Daten")
    console.print("  2. map_data.geojson - GeoJSON für Karten")
    console.print("  3. early_warning.json - Frühwarnsystem-Daten")
    console.print("  4. adaptation_recommendations.json - Klimaanpassungs-Empfehlungen")
    console.print("  5. causal_relationships.json - Kausale Zusammenhänge\n")
    
    # Zeige Statistiken
    stats = frontend_output['global_statistics']
    console.print("[bold cyan]📊 Globale Statistiken:[/bold cyan]")
    console.print(f"  Locations: {stats['total_locations']}")
    console.print(f"  Kritische Locations: {stats['critical_locations']}")
    console.print(f"  Hohe Dringlichkeit: {stats['high_urgency_locations']}")
    console.print(f"  Durchschnittliche Dringlichkeit: {stats['average_urgency']:.2f}")
    console.print(f"  Anpassungs-Empfehlungen: {stats['total_adaptation_recommendations']}")


if __name__ == "__main__":
    asyncio.run(main())



