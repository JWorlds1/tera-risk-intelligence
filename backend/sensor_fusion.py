#!/usr/bin/env python3
"""
Sensorpunktfusion - Fusioniert Daten aus verschiedenen Quellen
für eine umfassende Klima-Konflikt-Analyse
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import json
from collections import defaultdict

from database import DatabaseManager
from risk_scoring import RiskScorer
from geocoding import GeocodingService


@dataclass
class FusedDataPoint:
    """Fusionierter Datenpunkt aus mehreren Quellen"""
    location: str
    latitude: float
    longitude: float
    country_code: str
    
    # Klima-Daten (NASA)
    climate_indicators: List[str]
    satellite_data: Dict[str, Any]
    temperature_anomaly: Optional[float]
    precipitation_anomaly: Optional[float]
    
    # Konflikt-Daten (UN Press)
    conflict_indicators: List[str]
    security_council_mentions: int
    meeting_frequency: int
    
    # Wirtschaftliche Daten (World Bank)
    economic_indicators: Dict[str, Any]
    project_count: int
    sectors: List[str]
    
    # Humanitäre Daten (WFP)
    crisis_type: Optional[str]
    affected_population: Optional[int]
    
    # Fusionierte Metriken
    risk_score: float
    risk_level: str
    confidence: float
    data_sources_count: int
    last_updated: datetime
    
    # Zeitreihen
    trend: str  # 'increasing', 'decreasing', 'stable'
    urgency: float


class SensorFusionEngine:
    """Fusioniert Daten aus verschiedenen Sensoren/Quellen"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.risk_scorer = RiskScorer()
        self.geocoder = GeocodingService()
    
    def fuse_by_location(self, location: str) -> Optional[FusedDataPoint]:
        """Fusioniere alle Daten für einen Standort"""
        # Hole alle Records für diesen Standort
        all_records = self.db.get_records(limit=1000)
        
        location_records = []
        for record in all_records:
            if not record:
                continue
            region = (record.get('region') or '').lower() if record.get('region') else ''
            country_code = record.get('primary_country_code', '') or ''
            title = (record.get('title') or '').lower() if record.get('title') else ''
            location_lower = location.lower() if location else ''
            
            if (location_lower and (
                (region and location_lower in region) or 
                (country_code and country_code == location.upper()) or
                (title and location_lower in title)
            )):
                location_records.append(record)
        
        if not location_records:
            return None
        
        # Gruppiere nach Quelle
        nasa_records = [r for r in location_records if r.get('source_name') == 'NASA']
        un_records = [r for r in location_records if r.get('source_name') == 'UN Press']
        wb_records = [r for r in location_records if r.get('source_name') == 'World Bank']
        wfp_records = [r for r in location_records if r.get('source_name') == 'WFP']
        
        # Extrahiere Klima-Daten (NASA)
        climate_indicators = []
        satellite_data = {}
        temp_anomaly = None
        precip_anomaly = None
        
        for record in nasa_records:
            try:
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT environmental_indicators, satellite_source FROM nasa_records WHERE record_id = ?", (record.get('id'),))
                    nasa_data = cursor.fetchone()
                    if nasa_data:
                        indicators_str = nasa_data[0] if nasa_data[0] else '[]'
                        try:
                            indicators = json.loads(indicators_str) if isinstance(indicators_str, str) else indicators_str
                            if isinstance(indicators, list):
                                climate_indicators.extend(indicators)
                        except:
                            # Fallback: wenn JSON-Parsing fehlschlägt
                            if isinstance(indicators_str, str) and indicators_str:
                                climate_indicators.append(indicators_str)
                        
                        if nasa_data[1]:
                            satellite_data['source'] = nasa_data[1]
                
                # Extrahiere auch aus Record-Metadaten
                title = (record.get('title') or '').lower()
                summary = (record.get('summary') or '').lower()
                combined_text = f"{title} {summary}"
                
                # Suche nach Klima-Indikatoren im Text
                climate_keywords = ['temperature', 'precipitation', 'drought', 'flood', 'fire', 'vegetation', 'soil moisture', 'ndvi']
                for keyword in climate_keywords:
                    if keyword in combined_text and keyword not in [i.lower() for i in climate_indicators]:
                        climate_indicators.append(keyword)
            except Exception as e:
                print(f"Fehler beim Extrahieren von NASA-Daten für Record {record.get('id')}: {e}")
                continue
        
        # Extrahiere Konflikt-Daten (UN Press)
        conflict_indicators = []
        security_council_count = 0
        meeting_count = len(un_records)
        
        for record in un_records:
            try:
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT security_council, speakers FROM un_press_records WHERE record_id = ?", (record.get('id'),))
                    un_data = cursor.fetchone()
                    if un_data and un_data[0]:
                        security_council_count += 1
                
                # Extrahiere Konflikt-Keywords
                title = (record.get('title') or '').lower()
                summary = (record.get('summary') or '').lower()
                combined_text = f"{title} {summary}"
                
                conflict_keywords = ['conflict', 'violence', 'crisis', 'war', 'displacement', 'refugee', 'unrest', 'instability', 'tension']
                for keyword in conflict_keywords:
                    if keyword in combined_text and keyword not in conflict_indicators:
                        conflict_indicators.append(keyword)
            except Exception as e:
                print(f"Fehler beim Extrahieren von UN-Daten für Record {record.get('id')}: {e}")
                continue
        
        # Extrahiere Wirtschaftliche Daten (World Bank)
        economic_indicators = {}
        project_count = len(wb_records)
        sectors = []
        
        for record in wb_records:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT sector, project_id FROM worldbank_records WHERE record_id = ?", (record['id'],))
                wb_data = cursor.fetchone()
                if wb_data:
                    if wb_data[0] and wb_data[0] not in sectors:
                        sectors.append(wb_data[0])
                    if wb_data[1]:
                        economic_indicators['has_project'] = True
        
        # Extrahiere Humanitäre Daten (WFP)
        crisis_type = None
        affected_population = None
        
        for record in wfp_records:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT crisis_type, affected_population FROM wfp_records WHERE record_id = ?", (record['id'],))
                wfp_data = cursor.fetchone()
                if wfp_data:
                    if wfp_data[0]:
                        crisis_type = wfp_data[0]
                    if wfp_data[1]:
                        # Parse population number
                        try:
                            affected_population = int(wfp_data[1].replace(',', ''))
                        except:
                            pass
        
        # Berechne fusionierte Metriken
        total_records = len(location_records)
        risk_scores = [self.risk_scorer.calculate_risk(r).score for r in location_records]
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
        risk_level = self.risk_scorer.get_risk_level(avg_risk)
        
        # Confidence basierend auf Datenquellen-Anzahl
        data_sources = sum([
            len(nasa_records) > 0,
            len(un_records) > 0,
            len(wb_records) > 0,
            len(wfp_records) > 0
        ])
        confidence = min(1.0, data_sources / 4.0 + (total_records / 20.0))
        
        # Geocoding - NUR echte Koordinaten verwenden
        lat, lon, country_code = None, None, None
        
        # Versuche zuerst aus Records (NUR echte Koordinaten)
        for record in location_records:
            if record.get('primary_latitude') and record.get('primary_longitude'):
                # Prüfe ob Koordinaten gültig sind (nicht 0.0, 0.0)
                if record['primary_latitude'] != 0.0 and record['primary_longitude'] != 0.0:
                    lat = record['primary_latitude']
                    lon = record['primary_longitude']
                    country_code = record.get('primary_country_code') or None
                    break
        
        # KEIN Fallback-Geocoding - nur echte Koordinaten verwenden
        # Wenn keine Koordinaten vorhanden, bleiben lat/lon None
        
        # Trend-Analyse (vereinfacht)
        trend = 'stable'
        if len(location_records) > 1:
            recent_count = sum(1 for r in location_records if r.get('fetched_at'))
            if recent_count > len(location_records) * 0.7:
                trend = 'increasing'
        
        # Urgency basierend auf verschiedenen Faktoren
        urgency = 0.0
        if crisis_type:
            urgency += 0.3
        if security_council_count > 0:
            urgency += 0.2
        if affected_population and affected_population > 100000:
            urgency += 0.3
        if avg_risk > 0.5:
            urgency += 0.2
        
        # Prüfe ob wir gültige Koordinaten haben - wenn nicht, return None
        if lat is None or lon is None:
            return None
        
        return FusedDataPoint(
            location=location,
            latitude=lat,
            longitude=lon,
            country_code=country_code or '',
            climate_indicators=list(set(climate_indicators)),
            satellite_data=satellite_data,
            temperature_anomaly=temp_anomaly,
            precipitation_anomaly=precip_anomaly,
            conflict_indicators=list(set(conflict_indicators)),
            security_council_mentions=security_council_count,
            meeting_frequency=meeting_count,
            economic_indicators=economic_indicators,
            project_count=project_count,
            sectors=sectors,
            crisis_type=crisis_type,
            affected_population=affected_population,
            risk_score=avg_risk,
            risk_level=risk_level,
            confidence=confidence,
            data_sources_count=data_sources,
            last_updated=datetime.now(),
            trend=trend,
            urgency=min(1.0, urgency)
        )
    
    def fuse_all_locations(self) -> List[FusedDataPoint]:
        """Fusioniere Daten für alle Standorte"""
        all_records = self.db.get_records(limit=1000)
        
        # Gruppiere nach Standort
        locations = defaultdict(list)
        for record in all_records:
            if not record:
                continue
            # NUR echte Locations verwenden - keine Fallback-Locations
            location = None
            if record.get('region'):
                location = record.get('region')
            elif record.get('primary_country_code'):
                location = record.get('primary_country_code')
            
            # KEIN Fallback auf Title - nur echte geografische Daten
            if location:
                locations[location].append(record)
        
        fused_points = []
        for location, records in locations.items():
            if location != 'Unknown' and len(records) > 0:
                try:
                    fused = self.fuse_by_location(location)
                    if fused:
                        fused_points.append(fused)
                except Exception as e:
                    print(f"Fehler beim Fusionieren von {location}: {e}")
                    continue
        
        return fused_points
    
    def get_fusion_summary(self) -> Dict[str, Any]:
        """Hole Zusammenfassung der fusionierten Daten"""
        fused_points = self.fuse_all_locations()
        
        return {
            'total_locations': len(fused_points),
            'locations_by_risk': {
                'CRITICAL': sum(1 for p in fused_points if p.risk_level == 'CRITICAL'),
                'HIGH': sum(1 for p in fused_points if p.risk_level == 'HIGH'),
                'MEDIUM': sum(1 for p in fused_points if p.risk_level == 'MEDIUM'),
                'LOW': sum(1 for p in fused_points if p.risk_level == 'LOW'),
                'MINIMAL': sum(1 for p in fused_points if p.risk_level == 'MINIMAL'),
            },
            'data_coverage': {
                'with_climate_data': sum(1 for p in fused_points if p.climate_indicators),
                'with_conflict_data': sum(1 for p in fused_points if p.conflict_indicators),
                'with_economic_data': sum(1 for p in fused_points if p.project_count > 0),
                'with_humanitarian_data': sum(1 for p in fused_points if p.crisis_type),
            },
            'average_confidence': sum(p.confidence for p in fused_points) / len(fused_points) if fused_points else 0.0,
            'high_urgency_locations': [p.location for p in fused_points if p.urgency > 0.5]
        }

