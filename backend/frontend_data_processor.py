#!/usr/bin/env python3
"""
Frontend-Datenverarbeitung - Bereitet Daten für Frontend/Karten vor
- GeoJSON für Karten
- Frühwarnsystem-Daten
- Klimaanpassungs-Empfehlungen
- Kausale/Korrelative Analyse
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict
from collections import defaultdict

sys.path.append(str(Path(__file__).parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

from multi_stage_processing import MultiStageProcessor
from global_climate_analysis import GlobalClimateAnalyzer


@dataclass
class FrontendLocationData:
    """Daten für eine Location im Frontend-Format"""
    # Identifikation
    location_id: str
    location_name: str
    location_type: str  # 'city' or 'country'
    country_code: str
    
    # Geodaten
    coordinates: Tuple[float, float]  # (lat, lon)
    geojson: Dict[str, Any]  # GeoJSON Feature
    
    # Risiko-Daten
    risk_score: float
    risk_level: str  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    urgency_score: float
    
    # Klima-Daten
    climate_data: Dict[str, Any]
    
    # Frühwarnsystem
    early_warning: Dict[str, Any]
    
    # Klimaanpassungs-Empfehlungen
    adaptation_recommendations: List[Dict[str, Any]]
    
    # Kausale/Korrelative Zusammenhänge
    causal_relationships: List[Dict[str, Any]]
    
    # Zeitstempel
    last_updated: str
    next_update: str
    
    # Datenqualität
    data_quality: Dict[str, Any]


@dataclass
class CausalRelationship:
    """Kausaler Zusammenhang zwischen Regionen"""
    source_location: str
    target_location: str
    relationship_type: str  # 'causal', 'correlative', 'influence'
    strength: float  # 0.0-1.0
    description: str
    evidence: List[str]
    impact_direction: str  # 'positive', 'negative', 'mixed'


class FrontendDataProcessor:
    """Verarbeitet Daten für Frontend-Integration"""
    
    def __init__(self):
        self.processor = None
        self.analyzer = GlobalClimateAnalyzer()
    
    async def process_for_frontend(
        self,
        location: str,
        country_code: str,
        location_type: str = 'city',
        coordinates: Tuple[float, float] = None,
        use_full_pipeline: bool = False
    ) -> FrontendLocationData:
        """Verarbeite Daten für Frontend"""
        
        # Option 1: Vollständige Pipeline (langsam, benötigt Daten)
        if use_full_pipeline:
            if not self.processor:
                self.processor = MultiStageProcessor()
                await self.processor.__aenter__()
            
            from multi_stage_processing import CityContext
            
            city_context = CityContext(
                city_name=location,
                country_code=country_code,
                coordinates=coordinates or (0, 0),
                risk_factors={'general': 'high'},
                priority=1
            )
            
            # Füge Stadt zu processor.city_contexts hinzu, falls nicht vorhanden
            if location not in self.processor.city_contexts:
                self.processor.city_contexts[location] = city_context
            
            # Führe Pipeline aus
            pipeline_result = await self.processor.process_city_full_pipeline(location)
            
            # Verarbeite für Frontend
            frontend_data = self._convert_to_frontend_format(
                location,
                country_code,
                location_type,
                coordinates or (0, 0),
                pipeline_result,
                city_context
            )
            
            return frontend_data
        
        # Option 2: Schnelle Mock-Daten für Frontend-Testing
        else:
            # Generiere Mock-Daten basierend auf Location-Info
            mock_pipeline_result = {
                'stages': {
                    'meta_extraction': {
                        'numerical_data': {
                            'temperatures': [28.5, 29.2, 30.1],
                            'precipitation': [1200, 1500, 1800],
                            'affected_people': 5000000,
                            'population_numbers': [12000000, 15000000],
                            'funding_amount': 50000000,
                            'financial_amounts': [10000000, 25000000, 50000000],
                            'temperature_anomaly': 1.5,
                            'precipitation_anomaly': 15.0
                        }
                    },
                    'sensor_fusion': {
                        'fused_data': {
                            'climate_indicators': ['heat_waves', 'floods', 'sea_level_rise'],
                            'conflict_indicators': ['migration', 'resource_scarcity']
                        }
                    },
                    'early_warning': {
                        'signals': [
                            {
                                'type': 'HIGH_RISK',
                                'severity': 'HIGH',
                                'message': f'Hohes Risiko erkannt für {location}',
                                'indicators': ['heat_waves', 'floods'],
                                'timestamp': datetime.now().isoformat()
                            }
                        ]
                    }
                },
                'summary': {
                    'risk_score': 0.65,
                    'text_chunks': 10,
                    'numerical_data_points': 15,
                    'images': 3
                }
            }
            
            from multi_stage_processing import CityContext
            city_context = CityContext(
                city_name=location,
                country_code=country_code,
                coordinates=coordinates or (0, 0),
                risk_factors={'general': 'high'},
                priority=1
            )
            
            frontend_data = self._convert_to_frontend_format(
                location,
                country_code,
                location_type,
                coordinates or (0, 0),
                mock_pipeline_result,
                city_context
            )
            
            return frontend_data
    
    def _convert_to_frontend_format(
        self,
        location: str,
        country_code: str,
        location_type: str,
        coordinates: Tuple[float, float],
        pipeline_result: Dict[str, Any],
        city_context: Any
    ) -> FrontendLocationData:
        """Konvertiere Pipeline-Output zu Frontend-Format"""
        
        stages = pipeline_result.get('stages', {})
        summary = pipeline_result.get('summary', {})
        
        # GeoJSON erstellen
        geojson = self._create_geojson(location, coordinates, location_type)
        
        # Klima-Daten strukturieren
        climate_data = self._extract_climate_data(stages, summary)
        
        # Frühwarnsystem-Daten
        early_warning = self._extract_early_warning(stages)
        
        # Klimaanpassungs-Empfehlungen
        adaptation_recommendations = self._generate_adaptation_recommendations(
            location,
            country_code,
            climate_data,
            early_warning
        )
        
        # Kausale Zusammenhänge
        causal_relationships = self._analyze_causal_relationships(
            location,
            country_code,
            climate_data
        )
        
        # Datenqualität
        data_quality = self._assess_data_quality(stages, summary)
        
        return FrontendLocationData(
            location_id=f"{country_code}_{location.lower().replace(' ', '_')}",
            location_name=location,
            location_type=location_type,
            country_code=country_code,
            coordinates=coordinates,
            geojson=geojson,
            risk_score=summary.get('risk_score', 0.0),
            risk_level=self._get_risk_level(summary.get('risk_score', 0.0)),
            urgency_score=early_warning.get('urgency_score', 0.0),
            climate_data=climate_data,
            early_warning=early_warning,
            adaptation_recommendations=adaptation_recommendations,
            causal_relationships=causal_relationships,
            last_updated=datetime.now().isoformat(),
            next_update=(datetime.now() + timedelta(hours=24)).isoformat(),
            data_quality=data_quality
        )
    
    def _create_geojson(
        self,
        location: str,
        coordinates: Tuple[float, float],
        location_type: str
    ) -> Dict[str, Any]:
        """Erstelle GeoJSON Feature"""
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [coordinates[1], coordinates[0]]  # GeoJSON: [lon, lat]
            },
            "properties": {
                "name": location,
                "type": location_type
            }
        }
    
    def _extract_climate_data(
        self,
        stages: Dict[str, Any],
        summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extrahiere Klima-Daten"""
        meta_extraction = stages.get('meta_extraction', {})
        numerical_data = meta_extraction.get('numerical_data', {})
        sensor_fusion = stages.get('sensor_fusion', {})
        
        return {
            'temperatures': {
                'values': numerical_data.get('temperatures', []),
                'average': sum(numerical_data.get('temperatures', [])) / len(numerical_data.get('temperatures', [])) if numerical_data.get('temperatures') else None,
                'anomaly': numerical_data.get('temperature_anomaly'),
                'unit': 'celsius'
            },
            'precipitation': {
                'values': numerical_data.get('precipitation', []),
                'average': sum(numerical_data.get('precipitation', [])) / len(numerical_data.get('precipitation', [])) if numerical_data.get('precipitation') else None,
                'anomaly': numerical_data.get('precipitation_anomaly'),
                'unit': 'mm'
            },
            'population': {
                'affected': numerical_data.get('affected_people'),
                'total_estimates': numerical_data.get('population_numbers', [])
            },
            'financial': {
                'funding_amount': numerical_data.get('funding_amount'),
                'amounts': numerical_data.get('financial_amounts', [])
            },
            'risk_indicators': sensor_fusion.get('fused_data', {}).get('climate_indicators', []),
            'conflict_indicators': sensor_fusion.get('fused_data', {}).get('conflict_indicators', [])
        }
    
    def _extract_early_warning(self, stages: Dict[str, Any]) -> Dict[str, Any]:
        """Extrahiere Frühwarnsystem-Daten"""
        early_warning_stage = stages.get('early_warning', {})
        signals = early_warning_stage.get('signals', [])
        
        # Berechne Urgency Score
        urgency_score = 0.0
        high_severity_count = sum(1 for s in signals if s.get('severity') == 'HIGH')
        medium_severity_count = sum(1 for s in signals if s.get('severity') == 'MEDIUM')
        
        urgency_score = min(1.0, (high_severity_count * 0.4 + medium_severity_count * 0.2))
        
        return {
            'signals': signals,
            'total_signals': len(signals),
            'high_severity_count': high_severity_count,
            'medium_severity_count': medium_severity_count,
            'urgency_score': urgency_score,
            'warning_level': 'HIGH' if urgency_score > 0.6 else 'MEDIUM' if urgency_score > 0.3 else 'LOW',
            'requires_immediate_action': urgency_score > 0.7
        }
    
    def _generate_adaptation_recommendations(
        self,
        location: str,
        country_code: str,
        climate_data: Dict[str, Any],
        early_warning: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generiere kontextuelle Klimaanpassungs-Empfehlungen"""
        recommendations = []
        
        # Basierend auf Klima-Daten
        if climate_data.get('temperatures', {}).get('anomaly', 0) > 1.0:
            recommendations.append({
                'type': 'heat_adaptation',
                'priority': 'HIGH',
                'title': 'Hitzeschutz-Maßnahmen',
                'description': f'{location} erlebt erhöhte Temperaturen. Implementierung von Hitzeschutz-Maßnahmen erforderlich.',
                'actions': [
                    'Grünflächen und Schattenplätze schaffen',
                    'Kühlsysteme in öffentlichen Gebäuden installieren',
                    'Hitzewarnsysteme etablieren',
                    'Wasserversorgung sicherstellen'
                ],
                'timeframe': 'kurzfristig',
                'cost_estimate': 'mittel',
                'effectiveness': 0.8
            })
        
        if climate_data.get('precipitation', {}).get('anomaly', 0) < -20:
            recommendations.append({
                'type': 'drought_adaptation',
                'priority': 'HIGH',
                'title': 'Dürre-Anpassung',
                'description': f'{location} erlebt Dürre-Bedingungen. Wassermanagement-Maßnahmen erforderlich.',
                'actions': [
                    'Wasserspeicherung und -recycling',
                    'Dürre-resistente Landwirtschaft',
                    'Wasserverbrauch reduzieren',
                    'Alternative Wasserquellen erschließen'
                ],
                'timeframe': 'mittelfristig',
                'cost_estimate': 'hoch',
                'effectiveness': 0.75
            })
        
        # Basierend auf Frühwarnsignalen
        if early_warning.get('urgency_score', 0) > 0.6:
            recommendations.append({
                'type': 'early_warning_system',
                'priority': 'CRITICAL',
                'title': 'Frühwarnsystem verstärken',
                'description': f'Hohe Dringlichkeit erkannt. Frühwarnsystem muss verstärkt werden.',
                'actions': [
                    'Monitoring-Systeme ausbauen',
                    'Kommunikationskanäle etablieren',
                    'Evakuierungspläne aktualisieren',
                    'Notfallressourcen bereitstellen'
                ],
                'timeframe': 'sofort',
                'cost_estimate': 'mittel',
                'effectiveness': 0.9
            })
        
        # Basierend auf Konflikt-Indikatoren
        if climate_data.get('conflict_indicators'):
            recommendations.append({
                'type': 'conflict_prevention',
                'priority': 'HIGH',
                'title': 'Konfliktprävention',
                'description': f'Konflikt-Indikatoren erkannt. Präventive Maßnahmen erforderlich.',
                'actions': [
                    'Dialog zwischen Gemeinschaften fördern',
                    'Ressourcen-gerechte Verteilung sicherstellen',
                    'Friedensinitiativen unterstützen',
                    'Humanitäre Hilfe koordinieren'
                ],
                'timeframe': 'kurzfristig',
                'cost_estimate': 'hoch',
                'effectiveness': 0.7
            })
        
        # Region-spezifische Empfehlungen
        region_recommendations = self._get_region_specific_recommendations(country_code)
        recommendations.extend(region_recommendations)
        
        return recommendations
    
    def _analyze_causal_relationships(
        self,
        location: str,
        country_code: str,
        climate_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analysiere kausale/korrelative Zusammenhänge"""
        relationships = []
        
        # 1. Einfluss reicherer Länder
        rich_countries_impact = self._analyze_rich_countries_impact(
            location,
            country_code,
            climate_data
        )
        relationships.extend(rich_countries_impact)
        
        # 2. Regionale Zusammenhänge
        regional_relationships = self._analyze_regional_relationships(
            location,
            country_code,
            climate_data
        )
        relationships.extend(regional_relationships)
        
        # 3. Globale Zusammenhänge
        global_relationships = self._analyze_global_relationships(
            location,
            country_code,
            climate_data
        )
        relationships.extend(global_relationships)
        
        return relationships
    
    def _analyze_rich_countries_impact(
        self,
        location: str,
        country_code: str,
        climate_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analysiere Einfluss reicherer Länder"""
        relationships = []
        
        # Reiche Länder die negative Auswirkungen haben
        rich_countries = ['US', 'CN', 'DE', 'GB', 'FR', 'JP', 'CA', 'AU']
        
        # Schätze CO2-Emissionen-Einfluss
        # (Vereinfacht - in Produktion würde man echte Emissions-Daten nutzen)
        for rich_country in rich_countries:
            if rich_country != country_code:
                relationships.append({
                    'source_location': rich_country,
                    'target_location': country_code,
                    'relationship_type': 'causal',
                    'strength': 0.6,  # Schätzung
                    'description': f'Emissionen aus {rich_country} tragen zu Klimafolgen in {location} bei',
                    'evidence': [
                        'Globale CO2-Emissionen',
                        'IPCC AR6 Daten',
                        'Klimamodell-Projektionen'
                    ],
                    'impact_direction': 'negative',
                    'impact_type': 'emissions',
                    'mitigation_potential': 'high',
                    'recommendations': [
                        f'{rich_country} sollte Emissionsreduktion erhöhen',
                        f'Klimafinanzierung für {location} bereitstellen',
                        'Technologie-Transfer unterstützen'
                    ]
                })
        
        return relationships
    
    def _analyze_regional_relationships(
        self,
        location: str,
        country_code: str,
        climate_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analysiere regionale Zusammenhänge"""
        relationships = []
        
        # Regionale Nachbarn
        regional_neighbors = self._get_regional_neighbors(country_code)
        
        for neighbor_code, neighbor_name in regional_neighbors.items():
            relationships.append({
                'source_location': neighbor_code,
                'target_location': country_code,
                'relationship_type': 'correlative',
                'strength': 0.4,
                'description': f'Regionale Klimamuster zwischen {neighbor_name} und {location}',
                'evidence': [
                    'Gemeinsame Klimazone',
                    'Ähnliche Vulnerabilität',
                    'Regionale Klimamodelle'
                ],
                'impact_direction': 'mixed',
                'impact_type': 'regional_climate_patterns',
                'cooperation_potential': 'high',
                'recommendations': [
                    'Regionale Kooperation stärken',
                    'Gemeinsame Anpassungsstrategien entwickeln',
                    'Daten-Austausch etablieren'
                ]
            })
        
        return relationships
    
    def _analyze_global_relationships(
        self,
        location: str,
        country_code: str,
        climate_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analysiere globale Zusammenhänge"""
        relationships = []
        
        # Globale Klimamuster
        relationships.append({
            'source_location': 'GLOBAL',
            'target_location': country_code,
            'relationship_type': 'causal',
            'strength': 0.8,
            'description': f'Globale Klimaveränderungen beeinflussen {location}',
            'evidence': [
                'IPCC AR6 globale Projektionen',
                'Temperatur-Anomalien',
                'Meeresspiegel-Anstieg'
            ],
            'impact_direction': 'negative',
            'impact_type': 'global_climate_change',
            'mitigation_potential': 'global',
            'recommendations': [
                'Globale Emissionsreduktion erforderlich',
                'Internationale Klimaabkommen einhalten',
                'Klimafinanzierung mobilisieren'
            ]
        })
        
        return relationships
    
    def _get_region_specific_recommendations(self, country_code: str) -> List[Dict[str, Any]]:
        """Hole region-spezifische Empfehlungen"""
        recommendations = []
        
        # Beispiel: Südasien
        if country_code in ['IN', 'BD', 'PK', 'LK']:
            recommendations.append({
                'type': 'monsoon_adaptation',
                'priority': 'MEDIUM',
                'title': 'Monsun-Anpassung',
                'description': 'Südasien ist stark von Monsun abhängig. Anpassung an veränderte Monsunmuster erforderlich.',
                'actions': [
                    'Monsun-Vorhersage verbessern',
                    'Überschwemmungsschutz verstärken',
                    'Landwirtschaft anpassen',
                    'Wasserspeicherung optimieren'
                ],
                'timeframe': 'mittelfristig',
                'cost_estimate': 'hoch',
                'effectiveness': 0.75
            })
        
        # Beispiel: Afrika
        elif country_code in ['KE', 'ET', 'SO', 'UG', 'TZ']:
            recommendations.append({
                'type': 'agricultural_adaptation',
                'priority': 'HIGH',
                'title': 'Landwirtschaftliche Anpassung',
                'description': 'Landwirtschaft ist kritisch für Ernährungssicherheit. Anpassung an Klimawandel erforderlich.',
                'actions': [
                    'Dürre-resistente Sorten einführen',
                    'Bewässerungssysteme verbessern',
                    'Agroforstwirtschaft fördern',
                    'Frühwarnsysteme für Ernten'
                ],
                'timeframe': 'kurzfristig',
                'cost_estimate': 'mittel',
                'effectiveness': 0.8
            })
        
        return recommendations
    
    def _get_regional_neighbors(self, country_code: str) -> Dict[str, str]:
        """Hole regionale Nachbarn"""
        # Vereinfacht - in Produktion würde man echte geografische Daten nutzen
        regional_map = {
            'IN': {'PK': 'Pakistan', 'BD': 'Bangladesh', 'CN': 'China'},
            'BD': {'IN': 'India', 'MM': 'Myanmar'},
            'PK': {'IN': 'India', 'AF': 'Afghanistan', 'CN': 'China'},
            'CN': {'IN': 'India', 'PK': 'Pakistan', 'VN': 'Vietnam'},
            'VN': {'CN': 'China', 'TH': 'Thailand', 'LA': 'Laos'},
            'KE': {'ET': 'Ethiopia', 'SO': 'Somalia', 'UG': 'Uganda', 'TZ': 'Tanzania'},
            'ET': {'KE': 'Kenya', 'SO': 'Somalia', 'SD': 'Sudan'},
            'SO': {'ET': 'Ethiopia', 'KE': 'Kenya'},
            'UG': {'KE': 'Kenya', 'TZ': 'Tanzania'},
            'TZ': {'KE': 'Kenya', 'UG': 'Uganda', 'MZ': 'Mozambique'}
        }
        
        return regional_map.get(country_code, {})
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Konvertiere Risk Score zu Risk Level"""
        if risk_score >= 0.8:
            return 'CRITICAL'
        elif risk_score >= 0.6:
            return 'HIGH'
        elif risk_score >= 0.4:
            return 'MEDIUM'
        elif risk_score >= 0.2:
            return 'LOW'
        else:
            return 'MINIMAL'
    
    def _assess_data_quality(self, stages: Dict[str, Any], summary: Dict[str, Any]) -> Dict[str, Any]:
        """Bewerte Datenqualität"""
        data_sources = sum([
            summary.get('text_chunks', 0) > 0,
            summary.get('numerical_data_points', 0) > 0,
            summary.get('images', 0) > 0,
            stages.get('sensor_fusion', {}).get('fused_data') is not None
        ])
        
        return {
            'data_sources_count': data_sources,
            'completeness': data_sources / 4.0,
            'text_data_available': summary.get('text_chunks', 0) > 0,
            'numerical_data_available': summary.get('numerical_data_points', 0) > 0,
            'image_data_available': summary.get('images', 0) > 0,
            'sensor_fusion_available': stages.get('sensor_fusion', {}).get('fused_data') is not None,
            'quality_level': 'HIGH' if data_sources >= 3 else 'MEDIUM' if data_sources >= 2 else 'LOW'
        }
    
    async def generate_frontend_output(
        self,
        locations: List[Tuple[str, str, str, Tuple[float, float]]]  # (name, code, type, coords)
    ) -> Dict[str, Any]:
        """Generiere Frontend-Output für mehrere Locations"""
        frontend_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_locations': len(locations),
                'version': '1.0'
            },
            'locations': [],
            'global_statistics': {},
            'causal_network': []
        }
        
        all_locations_data = []
        all_relationships = []
        
        for location_name, country_code, location_type, coordinates in locations:
            try:
                location_data = await self.process_for_frontend(
                    location_name,
                    country_code,
                    location_type,
                    coordinates
                )
                location_dict = asdict(location_data)
                all_locations_data.append(location_dict)
                all_relationships.extend(location_dict.get('causal_relationships', []))
            except Exception as e:
                console.print(f"[red]Fehler bei {location_name}: {e}[/red]")
                continue
        
        frontend_data['locations'] = all_locations_data
        
        # Globale Statistiken
        frontend_data['global_statistics'] = self._calculate_global_statistics(all_locations_data)
        
        # Kausales Netzwerk
        frontend_data['causal_network'] = self._build_causal_network(all_relationships)
        
        return frontend_data
    
    def _calculate_global_statistics(self, locations_data: List[Dict]) -> Dict[str, Any]:
        """Berechne globale Statistiken"""
        total_locations = len(locations_data)
        
        risk_distribution = defaultdict(int)
        urgency_scores = []
        adaptation_count = 0
        
        for loc in locations_data:
            risk_distribution[loc.get('risk_level', 'UNKNOWN')] += 1
            urgency_scores.append(loc.get('urgency_score', 0))
            adaptation_count += len(loc.get('adaptation_recommendations', []))
        
        return {
            'total_locations': total_locations,
            'risk_distribution': dict(risk_distribution),
            'average_urgency': sum(urgency_scores) / len(urgency_scores) if urgency_scores else 0,
            'total_adaptation_recommendations': adaptation_count,
            'critical_locations': sum(1 for loc in locations_data if loc.get('risk_level') == 'CRITICAL'),
            'high_urgency_locations': sum(1 for loc in locations_data if loc.get('urgency_score', 0) > 0.6)
        }
    
    def _build_causal_network(self, relationships: List[Dict]) -> Dict[str, Any]:
        """Baue kausales Netzwerk"""
        nodes = set()
        edges = []
        
        for rel in relationships:
            source = rel.get('source_location')
            target = rel.get('target_location')
            
            nodes.add(source)
            nodes.add(target)
            
            edges.append({
                'source': source,
                'target': target,
                'type': rel.get('relationship_type'),
                'strength': rel.get('strength', 0),
                'impact_direction': rel.get('impact_direction'),
                'description': rel.get('description')
            })
        
        return {
            'nodes': [{'id': node, 'type': 'location'} for node in nodes],
            'edges': edges
        }
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.processor:
            await self.processor.__aexit__(exc_type, exc_val, exc_tb)


async def main():
    """Hauptfunktion - Generiere Frontend-Output"""
    console.print(Panel.fit(
        "[bold green]🌍 Frontend-Datenverarbeitung[/bold green]\n"
        "[cyan]Generiert strukturierte Daten für Karten, Frühwarnsystem und Klimaanpassungen[/cyan]",
        border_style="green"
    ))
    
    # Test-Locations
    test_locations = [
        ("Mumbai", "IN", "city", (19.0760, 72.8777)),
        ("Barcelona", "ES", "city", (41.3851, 2.1734)),
        ("Dhaka", "BD", "city", (23.8103, 90.4125)),
        ("Nairobi", "KE", "city", (-1.2921, 36.8219))
    ]
    
    async with FrontendDataProcessor() as processor:
        frontend_output = await processor.generate_frontend_output(test_locations)
        
        # Zeige Output
        console.print("\n[bold green]📊 Frontend-Output:[/bold green]\n")
        
        # Zeige für jede Location
        for location_data in frontend_output['locations']:
            console.print(Panel.fit(
                f"[bold cyan]{location_data['location_name']} ({location_data['country_code']})[/bold cyan]\n"
                f"Risk Level: {location_data['risk_level']} | "
                f"Urgency: {location_data['urgency_score']:.2f}\n"
                f"Anpassungs-Empfehlungen: {len(location_data['adaptation_recommendations'])}\n"
                f"Kausale Zusammenhänge: {len(location_data['causal_relationships'])}",
                border_style="cyan"
            ))
        
        # Speichere Output
        output_file = Path("./data/frontend_output.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(frontend_output, f, indent=2, default=str)
        
        console.print(f"\n[bold green]💾 Frontend-Output gespeichert: {output_file}[/bold green]")
        
        # Zeige Beispiel-Output
        console.print("\n[bold yellow]📋 Beispiel-Output für erste Location:[/bold yellow]\n")
        if frontend_output['locations']:
            example = frontend_output['locations'][0]
            console.print(json.dumps({
                'location_name': example['location_name'],
                'risk_level': example['risk_level'],
                'urgency_score': example['urgency_score'],
                'early_warning': example['early_warning'],
                'adaptation_recommendations': example['adaptation_recommendations'][:2],  # Erste 2
                'causal_relationships': example['causal_relationships'][:2]  # Erste 2
            }, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())

