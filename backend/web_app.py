#!/usr/bin/env python3
"""
Web-Frontend für Climate Conflict Intelligence
Zeigt extrahierte Daten, Karte und Predictions
"""
from flask import Flask, render_template_string, jsonify, request
from pathlib import Path
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Import our modules
from database import DatabaseManager
from risk_scoring import RiskScorer

app = Flask(__name__)

DB_PATH = Path("./data/climate_conflict.db")
db = DatabaseManager()
scorer = RiskScorer()


def get_db_connection():
    """Datenbankverbindung"""
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    """Hauptseite"""
    return render_template_string(MAIN_TEMPLATE)


@app.route('/api/stats')
def get_stats():
    """API: Statistiken - mit Sensorfusion"""
    from sensor_fusion import SensorFusionEngine
    
    stats = db.get_statistics()
    
    # Berechne Risiko-Verteilung
    records = db.get_records(limit=1000)
    risk_distribution = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'MINIMAL': 0}
    
    for record in records:
        risk = scorer.calculate_risk(record)
        level = scorer.get_risk_level(risk.score)
        risk_distribution[level] += 1
    
    stats['risk_distribution'] = risk_distribution
    
    # Füge Sensorfusion-Statistiken hinzu
    try:
        fusion_engine = SensorFusionEngine()
        fusion_summary = fusion_engine.get_fusion_summary()
        stats['sensor_fusion'] = fusion_summary
    except Exception as e:
        print(f"Fusion-Statistiken Fehler: {e}")
        stats['sensor_fusion'] = {'error': str(e)}
    
    return jsonify(stats)


@app.route('/api/records')
def get_records():
    """API: Records mit Risiko-Scores und Batch-Enrichment-Daten"""
    source = request.args.get('source', None)
    risk_level = request.args.get('risk_level', None)
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    include_enrichment = request.args.get('include_enrichment', 'false').lower() == 'true'
    
    records = db.get_records(source_name=source, limit=limit * 2, offset=offset)
    
    # Berechne Risiko-Scores
    enriched_records = []
    for record in records:
        risk = scorer.calculate_risk(record)
        level = scorer.get_risk_level(risk.score)
        
        # Filter nach Risiko-Level
        if risk_level and level != risk_level:
            continue
        
        record_dict = dict(record)
        record_dict['risk'] = {
            'climate_risk': risk.climate_risk,
            'conflict_risk': risk.conflict_risk,
            'urgency': risk.urgency,
            'total_score': risk.score,
            'level': level,
            'indicators': risk.indicators
        }
        
        # Füge Batch-Enrichment-Daten hinzu falls vorhanden
        if include_enrichment:
            enrichment_data = get_batch_enrichment(record['id'])
            if enrichment_data:
                record_dict['enrichment'] = enrichment_data
        
        enriched_records.append(record_dict)
        
        if len(enriched_records) >= limit:
            break
    
    return jsonify({'records': enriched_records})


def get_batch_enrichment(record_id: int) -> Dict[str, Any]:
    """Hole Batch-Enrichment-Daten für einen Record"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT datapoints, ipcc_metrics, extracted_numbers, firecrawl_data, enrichment_timestamp
            FROM batch_enrichment
            WHERE record_id = ?
        """, (record_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            'datapoints': json.loads(row[0]) if row[0] else {},
            'ipcc_metrics': json.loads(row[1]) if row[1] else {},
            'extracted_numbers': json.loads(row[2]) if row[2] else {},
            'firecrawl_data': json.loads(row[3]) if row[3] else {},
            'enrichment_timestamp': row[4]
        }
    except Exception as e:
        print(f"Error fetching enrichment: {e}")
        return None
    finally:
        conn.close()


@app.route('/api/map-data')
def get_map_data():
    """API: Daten für Karte - mit Sensorfusion"""
    from sensor_fusion import SensorFusionEngine
    
    fusion_engine = SensorFusionEngine()
    
    # Option 1: Verwende fusionierte Datenpunkte
    try:
        fused_points = fusion_engine.fuse_all_locations()
        if fused_points:
            map_points = []
            for point in fused_points:
                if point.latitude and point.longitude:
                    map_points.append({
                        'id': f'fused_{point.location}',
                        'title': f'{point.location} - Fusionierte Daten',
                        'source': 'FUSED',
                        'region': point.location,
                        'country': point.country_code,
                        'lat': point.latitude,
                        'lon': point.longitude,
                        'risk_level': point.risk_level,
                        'risk_score': point.risk_score,
                        'climate_risk': len(point.climate_indicators) / 10.0,  # Normalisiert
                        'conflict_risk': len(point.conflict_indicators) / 10.0,
                        'indicators': (point.climate_indicators[:3] + point.conflict_indicators[:2]),
                        'data_sources': point.data_sources_count,
                        'confidence': point.confidence,
                        'urgency': point.urgency,
                        'trend': point.trend
                    })
            
            if map_points:
                return jsonify({'points': map_points, 'fusion': True})
    except Exception as e:
        print(f"Fusion-Fehler, verwende normale Daten: {e}")
    
    # Option 2: Fallback zu normalen Records
    records = db.get_records(limit=1000)
    
    map_points = []
    for record in records:
        if record.get('primary_latitude') and record.get('primary_longitude'):
            risk = scorer.calculate_risk(record)
            level = scorer.get_risk_level(risk.score)
            
            map_points.append({
                'id': record['id'],
                'title': record.get('title', 'N/A'),
                'source': record.get('source_name', 'N/A'),
                'region': record.get('region', 'N/A'),
                'country': record.get('primary_country_code', 'N/A'),
                'lat': record['primary_latitude'],
                'lon': record['primary_longitude'],
                'risk_level': level,
                'risk_score': risk.score,
                'climate_risk': risk.climate_risk,
                'conflict_risk': risk.conflict_risk,
                'indicators': risk.indicators[:5]
            })
    
    return jsonify({'points': map_points, 'fusion': False})


@app.route('/api/predictions')
def get_predictions():
    """API: Predictions für gefährdete Regionen"""
    records = db.get_records(limit=1000)
    
    # Gruppiere nach Region/Land
    region_risks = {}
    
    for record in records:
        region = record.get('region') or record.get('primary_country_code', 'Unknown')
        risk = scorer.calculate_risk(record)
        
        if region not in region_risks:
            region_risks[region] = {
                'region': region,
                'records': [],
                'total_score': 0,
                'count': 0,
                'indicators': set()
            }
        
        region_risks[region]['records'].append({
            'title': record.get('title'),
            'score': risk.score,
            'level': scorer.get_risk_level(risk.score)
        })
        region_risks[region]['total_score'] += risk.score
        region_risks[region]['count'] += 1
        region_risks[region]['indicators'].update(risk.indicators)
    
    # Berechne durchschnittliche Risiko-Scores
    predictions = []
    for region, data in region_risks.items():
        avg_score = data['total_score'] / data['count'] if data['count'] > 0 else 0
        level = scorer.get_risk_level(avg_score)
        
        # Nur HIGH und CRITICAL für Predictions
        if level in ['HIGH', 'CRITICAL']:
            predictions.append({
                'region': region,
                'risk_level': level,
                'risk_score': avg_score,
                'record_count': data['count'],
                'indicators': list(data['indicators'])[:10],
                'recent_records': data['records'][:3]
            })
    
    # Sortiere nach Risiko-Score
    predictions.sort(key=lambda x: x['risk_score'], reverse=True)
    
    return jsonify({'predictions': predictions[:20]})


@app.route('/api/batch-enrichment')
def get_batch_enrichment_stats():
    """API: Statistiken zu Batch-Enrichment"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Prüfe ob Tabelle existiert
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='batch_enrichment'
        """)
        
        if not cursor.fetchone():
            return jsonify({
                'table_exists': False,
                'total_enriched': 0,
                'average_datapoints': 0
            })
        
        # Hole Statistiken
        cursor.execute("SELECT COUNT(*) FROM batch_enrichment")
        total_enriched = cursor.fetchone()[0]
        
        cursor.execute("SELECT datapoints FROM batch_enrichment")
        rows = cursor.fetchall()
        
        total_datapoints = 0
        for row in rows:
            if row[0]:
                try:
                    datapoints = json.loads(row[0])
                    total_datapoints += len(datapoints)
                except:
                    pass
        
        avg_datapoints = total_datapoints / total_enriched if total_enriched > 0 else 0
        
        return jsonify({
            'table_exists': True,
            'total_enriched': total_enriched,
            'total_datapoints': total_datapoints,
            'average_datapoints': round(avg_datapoints, 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/regional-data')
def get_regional_data():
    """API: Regionale Daten für Deutschland und Europa"""
    critical_regions = {
        'Germany': {
            'countries': ['DE'],
            'keywords': ['Germany', 'Deutschland', 'German']
        },
        'Europe': {
            'countries': ['DE', 'FR', 'IT', 'ES', 'PL', 'NL', 'BE', 'AT', 'CH', 'CZ', 'SE', 'NO', 'DK', 'FI'],
            'keywords': ['Europe', 'Europa', 'European', 'EU']
        }
    }
    
    regional_data = {}
    
    for region_name, config in critical_regions.items():
        keywords = config['keywords']
        countries = config['countries']
        
        # Hole alle Records
        all_records = db.get_records(limit=1000)
        region_records = []
        
        for record in all_records:
            region = (record.get('region') or '').lower()
            country_code = record.get('primary_country_code', '')
            
            if any(kw.lower() in region for kw in keywords) or country_code in countries:
                region_records.append(record)
        
        # Berechne Statistiken
        risk_distribution = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'MINIMAL': 0}
        sources = {}
        total_risk_score = 0
        records_with_coords = 0
        enriched_count = 0
        
        for record in region_records:
            risk = scorer.calculate_risk(record)
            level = scorer.get_risk_level(risk.score)
            risk_distribution[level] += 1
            total_risk_score += risk.score
            
            source = record.get('source_name', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
            
            if record.get('primary_latitude'):
                records_with_coords += 1
            
            # Prüfe ob angereichert
            enrichment = get_batch_enrichment(record['id'])
            if enrichment:
                enriched_count += 1
        
        avg_risk = total_risk_score / len(region_records) if region_records else 0
        
        regional_data[region_name] = {
            'total_records': len(region_records),
            'risk_distribution': risk_distribution,
            'average_risk_score': round(avg_risk, 2),
            'sources': sources,
            'records_with_coordinates': records_with_coords,
            'enriched_records': enriched_count,
            'enrichment_rate': round(enriched_count / len(region_records) * 100, 1) if region_records else 0
        }
    
    return jsonify(regional_data)


@app.route('/api/regional-records')
def get_regional_records():
    """API: Records für eine spezifische Region"""
    region_name = request.args.get('region', 'Germany')
    limit = int(request.args.get('limit', 50))
    
    critical_regions = {
        'Germany': {
            'countries': ['DE'],
            'keywords': ['Germany', 'Deutschland', 'German']
        },
        'Europe': {
            'countries': ['DE', 'FR', 'IT', 'ES', 'PL', 'NL', 'BE', 'AT', 'CH', 'CZ', 'SE', 'NO', 'DK', 'FI'],
            'keywords': ['Europe', 'Europa', 'European', 'EU']
        }
    }
    
    config = critical_regions.get(region_name, critical_regions['Germany'])
    keywords = config['keywords']
    countries = config['countries']
    
    all_records = db.get_records(limit=1000)
    region_records = []
    
    for record in all_records:
        region = (record.get('region') or '').lower()
        country_code = record.get('primary_country_code', '')
        
        if any(kw.lower() in region for kw in keywords) or country_code in countries:
            risk = scorer.calculate_risk(record)
            record_dict = dict(record)
            record_dict['risk'] = {
                'level': scorer.get_risk_level(risk.score),
                'score': risk.score,
                'indicators': risk.indicators[:5]
            }
            region_records.append(record_dict)
            
            if len(region_records) >= limit:
                break
    
    return jsonify({'records': region_records, 'region': region_name})


@app.route('/api/data-sources')
def get_data_sources():
    """API: Welche Daten werden von welchen Quellen extrahiert"""
    return jsonify({
        'nasa': {
            'name': 'NASA Earth Observatory',
            'url': 'https://earthobservatory.nasa.gov',
            'fields': [
                'title', 'summary', 'publish_date', 'region',
                'topics', 'environmental_indicators', 'satellite_source'
            ],
            'description': 'Umweltstress & Klimaveränderungen',
            'useful_for': [
                'Klima-Indikatoren (Drought, Flood, Temperature)',
                'Satelliten-Daten',
                'Regionale Umweltveränderungen'
            ]
        },
        'un_press': {
            'name': 'UN Press',
            'url': 'https://press.un.org',
            'fields': [
                'title', 'summary', 'publish_date', 'region',
                'topics', 'meeting_coverage', 'security_council', 'speakers'
            ],
            'description': 'Politische & sicherheitspolitische Reaktionen',
            'useful_for': [
                'Konflikt-Indikatoren',
                'Security Council Aktivitäten',
                'Politische Reaktionen auf Klima-Events'
            ]
        },
        'world_bank': {
            'name': 'World Bank',
            'url': 'https://www.worldbank.org/en/news',
            'fields': [
                'title', 'summary', 'publish_date', 'country',
                'sector', 'project_id'
            ],
            'description': 'Wirtschaftliche & strukturelle Verwundbarkeit',
            'useful_for': [
                'Wirtschaftliche Auswirkungen',
                'Projekt-Finanzierung',
                'Strukturelle Verwundbarkeit'
            ]
        }
    })


@app.route('/api/frontend/map-data')
def get_frontend_map_data():
    """API: GeoJSON-Daten für Frontend-Karte"""
    frontend_file = Path("./data/frontend/map_data.geojson")
    if not frontend_file.exists():
        return jsonify({'error': 'Frontend-Daten nicht gefunden. Führe generate_frontend_data.py aus.'}), 404
    
    try:
        with open(frontend_file, 'r') as f:
            geojson_data = json.load(f)
        return jsonify(geojson_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/frontend/complete-data')
def get_frontend_complete_data():
    """API: Vollständige Frontend-Daten"""
    frontend_file = Path("./data/frontend/complete_data.json")
    if not frontend_file.exists():
        return jsonify({'error': 'Frontend-Daten nicht gefunden'}), 404
    
    try:
        with open(frontend_file, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/frontend/early-warnings')
def get_frontend_early_warnings():
    """API: Frühwarnsystem-Daten"""
    warnings_file = Path("./data/frontend/early_warning.json")
    if not warnings_file.exists():
        return jsonify({'error': 'Warnungs-Daten nicht gefunden'}), 404
    
    try:
        with open(warnings_file, 'r') as f:
            warnings = json.load(f)
        
        # Filtere nur Locations mit Warnungen
        locations_with_warnings = [
            loc for loc in warnings.get('locations', [])
            if loc.get('early_warning', {}).get('total_signals', 0) > 0
        ]
        
        # Sortiere nach Urgency Score
        locations_with_warnings.sort(key=lambda x: x.get('urgency_score', 0), reverse=True)
        
        return jsonify({
            'locations': locations_with_warnings,
            'total': len(locations_with_warnings),
            'generated_at': warnings.get('generated_at')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/frontend/adaptation-recommendations')
def get_frontend_adaptation_recommendations():
    """API: Klimaanpassungs-Empfehlungen"""
    rec_file = Path("./data/frontend/adaptation_recommendations.json")
    if not rec_file.exists():
        return jsonify({'error': 'Empfehlungs-Daten nicht gefunden'}), 404
    
    try:
        with open(rec_file, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/frontend/location/<location_id>')
def get_frontend_location(location_id):
    """API: Details für eine spezifische Location"""
    complete_file = Path("./data/frontend/complete_data.json")
    if not complete_file.exists():
        return jsonify({'error': 'Frontend-Daten nicht gefunden'}), 404
    
    try:
        with open(complete_file, 'r') as f:
            data = json.load(f)
        
        # Finde Location
        location = None
        for loc in data.get('locations', []):
            if loc.get('location_id') == location_id:
                location = loc
                break
        
        if not location:
            return jsonify({'error': 'Location nicht gefunden'}), 404
        
        return jsonify(location)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/frontend/risk-raster')
def get_frontend_risk_raster():
    """API: Risiko-Raster mit Iso-Risk Contours"""
    raster_file = Path("./data/frontend/risk_raster.geojson")
    if not raster_file.exists():
        return jsonify({
            'error': 'Raster-Daten nicht gefunden. Führe risk_raster_generator.py aus.',
            'available': False
        }), 404
    
    try:
        with open(raster_file, 'r') as f:
            raster_data = json.load(f)
        return jsonify({
            'available': True,
            'raster': raster_data
        })
    except Exception as e:
        return jsonify({'error': str(e), 'available': False}), 500


@app.route('/api/frontend/regions')
def get_frontend_regions():
    """API: Regionale Gruppierung der Locations"""
    complete_file = Path("./data/frontend/complete_data.json")
    if not complete_file.exists():
        return jsonify({'error': 'Frontend-Daten nicht gefunden'}), 404
    
    try:
        with open(complete_file, 'r') as f:
            data = json.load(f)
        
        # Gruppiere nach Ländern
        regions = {}
        for loc in data.get('locations', []):
            country_code = loc.get('country_code', 'UNKNOWN')
            if country_code not in regions:
                regions[country_code] = {
                    'country_code': country_code,
                    'locations': [],
                    'total_locations': 0,
                    'risk_distribution': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'MINIMAL': 0},
                    'average_urgency': 0,
                    'total_warnings': 0
                }
            
            regions[country_code]['locations'].append(loc)
            regions[country_code]['total_locations'] += 1
            risk_level = loc.get('risk_level', 'MINIMAL')
            regions[country_code]['risk_distribution'][risk_level] = \
                regions[country_code]['risk_distribution'].get(risk_level, 0) + 1
            
            # Zähle Warnungen
            if loc.get('early_warning', {}).get('total_signals', 0) > 0:
                regions[country_code]['total_warnings'] += 1
        
        # Berechne durchschnittliche Urgency pro Region
        for country_code, region_data in regions.items():
            urgency_scores = [loc.get('urgency_score', 0) for loc in region_data['locations']]
            region_data['average_urgency'] = sum(urgency_scores) / len(urgency_scores) if urgency_scores else 0
        
        return jsonify({
            'regions': list(regions.values()),
            'total_regions': len(regions)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


MAIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Climate Conflict Intelligence Dashboard</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
          crossorigin=""/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
            integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
            crossorigin=""></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header h1 { margin-bottom: 10px; }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-card h3 {
            font-size: 12px;
            color: #666;
            margin-bottom: 10px;
        }
        .stat-card .value {
            font-size: 28px;
            font-weight: bold;
            color: #667eea;
        }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .tab {
            padding: 10px 20px;
            background: white;
            border: none;
            border-radius: 8px 8px 0 0;
            cursor: pointer;
            font-weight: 500;
        }
        .tab.active {
            background: #667eea;
            color: white;
        }
        .tab-content {
            display: none;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .tab-content.active {
            display: block;
        }
        #map {
            height: 600px;
            width: 100%;
            border-radius: 8px;
            z-index: 1;
            background-color: #e5e5e5;
        }
        /* Leaflet Container Fix */
        .leaflet-container {
            background-color: #e5e5e5 !important;
        }
        /* Seitenleiste für Warnungen */
        .sidebar {
            position: fixed;
            right: -400px;
            top: 0;
            width: 400px;
            height: 100vh;
            background: white;
            box-shadow: -2px 0 10px rgba(0,0,0,0.1);
            transition: right 0.3s ease;
            z-index: 1000;
            overflow-y: auto;
            padding: 20px;
        }
        .sidebar.open {
            right: 0;
        }
        .sidebar-toggle {
            position: fixed;
            right: 20px;
            top: 100px;
            z-index: 1001;
            background: #667eea;
            color: white;
            border: none;
            padding: 15px 20px;
            border-radius: 8px 0 0 8px;
            cursor: pointer;
            box-shadow: -2px 0 5px rgba(0,0,0,0.2);
        }
        .warning-item {
            padding: 15px;
            margin-bottom: 10px;
            border-left: 4px solid #f97316;
            background: #fff5f0;
            border-radius: 4px;
        }
        .warning-item.critical {
            border-left-color: #ef4444;
            background: #fee2e2;
        }
        .warning-item.high {
            border-left-color: #f97316;
            background: #fff5f0;
        }
        .recommendation-item {
            padding: 15px;
            margin-bottom: 10px;
            border-left: 4px solid #3b82f6;
            background: #eff6ff;
            border-radius: 4px;
        }
        .recommendation-item.priority-high {
            border-left-color: #f97316;
            background: #fff5f0;
        }
        .recommendation-item.priority-critical {
            border-left-color: #ef4444;
            background: #fee2e2;
        }
        .location-detail {
            padding: 15px;
            margin-bottom: 15px;
            background: #f9fafb;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
        }
        .filter-panel {
            background: white;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .filter-group {
            margin-bottom: 15px;
        }
        .filter-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
            color: #374151;
        }
        .filter-group select, .filter-group input {
            width: 100%;
            padding: 8px;
            border: 1px solid #d1d5db;
            border-radius: 4px;
        }
        .info.legend {
            background: transparent;
            line-height: 18px;
            color: #333;
        }
        .info.legend h4 {
            margin: 0 0 5px;
            color: #333;
        }
        .record-item {
            padding: 15px;
            border-bottom: 1px solid #eee;
        }
        .record-item:last-child {
            border-bottom: none;
        }
        .risk-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            margin-right: 10px;
        }
        .risk-CRITICAL { background: #ef4444; color: white; }
        .risk-HIGH { background: #f97316; color: white; }
        .risk-MEDIUM { background: #eab308; color: white; }
        .risk-LOW { background: #3b82f6; color: white; }
        .risk-MINIMAL { background: #94a3b8; color: white; }
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>🌍 Climate Conflict Intelligence Dashboard</h1>
            <p>Frühwarnsystem für klimabedingte Konflikte</p>
        </div>
    </div>
    
    <div class="container">
        <div class="stats-grid" id="stats">
            <div class="stat-card">
                <h3>Gesamt Records</h3>
                <div class="value" id="total-records">-</div>
            </div>
            <div class="stat-card">
                <h3>Mit Koordinaten</h3>
                <div class="value" id="with-coords">-</div>
            </div>
            <div class="stat-card">
                <h3>CRITICAL Risk</h3>
                <div class="value" id="critical-risk">-</div>
            </div>
            <div class="stat-card">
                <h3>HIGH Risk</h3>
                <div class="value" id="high-risk">-</div>
            </div>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="showTab('map')">🗺️ Karte</button>
            <button class="tab" onclick="showTab('records')">📊 Records</button>
            <button class="tab" onclick="showTab('regions')">🌍 Regionen</button>
            <button class="tab" onclick="showTab('frontend-data')">🌐 Frontend-Daten</button>
            <button class="tab" onclick="showTab('enrichment')">📈 Enrichment</button>
            <button class="tab" onclick="showTab('predictions')">🔮 Predictions</button>
            <button class="tab" onclick="showTab('sources')">📡 Datenquellen</button>
        </div>
        
        <div id="map-tab" class="tab-content active">
            <div class="filter-panel">
                <div class="filter-group">
                    <label>Datenquelle:</label>
                    <select id="map-data-source" onchange="loadMapData()">
                        <option value="api">API Records (Datenbank)</option>
                        <option value="frontend">Frontend GeoJSON (Generierte Daten)</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label>Risiko-Level Filter:</label>
                    <select id="risk-filter" onchange="filterMapMarkers()">
                        <option value="all">Alle</option>
                        <option value="CRITICAL">CRITICAL</option>
                        <option value="HIGH">HIGH</option>
                        <option value="MEDIUM">MEDIUM</option>
                        <option value="LOW">LOW</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label>Region Filter:</label>
                    <select id="region-filter" onchange="filterMapMarkers()">
                        <option value="all">Alle Regionen</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label>Visualisierung:</label>
                    <select id="visualization-type" onchange="updateVisualization()">
                        <option value="markers">Marker</option>
                        <option value="heatmap">Heatmap</option>
                        <option value="raster">Risiko-Raster</option>
                        <option value="contours">Iso-Risk Contours</option>
                    </select>
                </div>
            </div>
            <div id="map"></div>
        </div>
        
        <!-- Seitenleiste für Warnungen und Empfehlungen -->
        <button class="sidebar-toggle" onclick="toggleSidebar()">⚠️ Warnungen</button>
        <div class="sidebar" id="sidebar">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2>⚠️ Warnungen & Empfehlungen</h2>
                <button onclick="toggleSidebar()" style="background: none; border: none; font-size: 24px; cursor: pointer;">×</button>
            </div>
            <div id="sidebar-content">
                <div class="loading">Lade Warnungen...</div>
            </div>
        </div>
        
        <div id="records-tab" class="tab-content">
            <div id="records-list" class="loading">Lade Records...</div>
        </div>
        
        <div id="regions-tab" class="tab-content">
            <div id="regional-overview" class="loading">Lade regionale Übersicht...</div>
            <div id="regional-details" style="margin-top: 20px;">
                <div id="germany-section" style="display: none;">
                    <h2>🇩🇪 Deutschland</h2>
                    <div id="germany-stats"></div>
                    <div id="germany-records" class="loading">Lade Records...</div>
                </div>
                <div id="europe-section" style="display: none;">
                    <h2>🇪🇺 Europa</h2>
                    <div id="europe-stats"></div>
                    <div id="europe-records" class="loading">Lade Records...</div>
                </div>
            </div>
        </div>
        
        <div id="enrichment-tab" class="tab-content">
            <div id="enrichment-stats" class="loading">Lade Enrichment-Statistiken...</div>
            <div id="enrichment-list" class="loading">Lade angereicherte Records...</div>
        </div>
        
        <div id="predictions-tab" class="tab-content">
            <div id="predictions-list" class="loading">Lade Predictions...</div>
        </div>
        
        <div id="frontend-data-tab" class="tab-content">
            <div class="loading">Lade Frontend-Daten...</div>
        </div>
        
        <div id="sources-tab" class="tab-content">
            <div id="sources-list" class="loading">Lade Datenquellen...</div>
        </div>
    </div>
    
    <script>
        let map;
        let markers = [];
        let geojsonLayer = null;
        let heatmapLayer = null;
        let rasterLayer = null;
        let contourLayers = [];
        let allLocations = [];
        let currentDataSource = 'api';
        
        function showTab(tabName) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById(tabName + '-tab').classList.add('active');
            
            if (tabName === 'map') {
                // Initialisiere Karte wenn noch nicht geschehen
                if (!map) {
                    setTimeout(() => initMap(), 100);
                } else {
                    // Lade Daten neu wenn Karte bereits existiert
                    loadMapData();
                }
            } else if (tabName === 'records') {
                loadRecords();
            } else if (tabName === 'regions') {
                loadRegionalData();
            } else if (tabName === 'frontend-data') {
                loadFrontendData();
            } else if (tabName === 'enrichment') {
                loadEnrichment();
            } else if (tabName === 'predictions') {
                loadPredictions();
            } else if (tabName === 'sources') {
                loadSources();
            }
        }
        
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            sidebar.classList.toggle('open');
        }
        
        async function loadSidebarContent() {
            const sidebarContent = document.getElementById('sidebar-content');
            
            try {
                // Lade Warnungen
                const warningsRes = await fetch('/api/frontend/early-warnings');
                const warningsData = await warningsRes.json();
                
                // Lade Empfehlungen
                const recRes = await fetch('/api/frontend/adaptation-recommendations');
                const recData = await recRes.json();
                
                let html = '<div style="margin-bottom: 30px;"><h3>⚠️ Aktive Warnungen</h3>';
                
                if (warningsData.locations && warningsData.locations.length > 0) {
                    warningsData.locations.forEach(loc => {
                        const warning = loc.early_warning;
                        const severityClass = warning.warning_level === 'HIGH' ? 'critical' : 'high';
                        html += `
                            <div class="warning-item ${severityClass}" onclick="showLocationDetails('${loc.id}')" style="cursor: pointer;">
                                <strong>${loc.name} (${loc.country_code})</strong><br>
                                <small>Urgency: ${(loc.urgency_score * 100).toFixed(0)}%</small><br>
                                ${warning.signals.map(s => `
                                    <div style="margin-top: 5px;">
                                        <strong>${s.type}:</strong> ${s.message}<br>
                                        <small>Indikatoren: ${s.indicators.join(', ')}</small>
                                    </div>
                                `).join('')}
                            </div>
                        `;
                    });
                } else {
                    html += '<p>Keine aktiven Warnungen</p>';
                }
                
                html += '</div><div><h3>💡 Anpassungs-Empfehlungen</h3>';
                
                if (recData.recommendations_by_location) {
                    Object.entries(recData.recommendations_by_location).slice(0, 5).forEach(([locationId, data]) => {
                        data.recommendations.forEach(rec => {
                            const priorityClass = rec.priority.toLowerCase();
                            html += `
                                <div class="recommendation-item priority-${priorityClass}">
                                    <strong>${rec.title}</strong><br>
                                    <small>${data.location_name} (${data.country_code})</small><br>
                                    <p style="margin-top: 5px;">${rec.description}</p>
                                    <small>Zeitraum: ${rec.timeframe} | Kosten: ${rec.cost_estimate}</small>
                                </div>
                            `;
                        });
                    });
                } else {
                    html += '<p>Keine Empfehlungen verfügbar</p>';
                }
                
                html += '</div>';
                sidebarContent.innerHTML = html;
            } catch (error) {
                sidebarContent.innerHTML = '<div class="loading">Fehler beim Laden der Daten</div>';
                console.error('Error loading sidebar:', error);
            }
        }
        
        async function showLocationDetails(locationId) {
            try {
                const res = await fetch(`/api/frontend/location/${locationId}`);
                const location = await res.json();
                
                // Zeige Details in einem Modal oder Popup
                const detailHtml = `
                    <div class="location-detail">
                        <h3>${location.location_name} (${location.country_code})</h3>
                        <p><strong>Risiko-Level:</strong> ${location.risk_level} | Score: ${location.risk_score.toFixed(2)}</p>
                        <p><strong>Urgency Score:</strong> ${(location.urgency_score * 100).toFixed(0)}%</p>
                        <h4>Klima-Daten:</h4>
                        <p>Temperatur: ${location.climate_data?.temperatures?.average?.toFixed(1)}°C (Anomalie: ${location.climate_data?.temperatures?.anomaly}°C)</p>
                        <p>Niederschlag: ${location.climate_data?.precipitation?.average?.toFixed(0)}mm</p>
                        <h4>Warnungen:</h4>
                        <p>${location.early_warning?.total_signals || 0} Signale</p>
                        <h4>Empfehlungen:</h4>
                        <p>${location.adaptation_recommendations?.length || 0} Anpassungs-Empfehlungen</p>
                    </div>
                `;
                
                // Öffne Sidebar und zeige Details
                document.getElementById('sidebar-content').innerHTML = detailHtml;
                toggleSidebar();
            } catch (error) {
                console.error('Error loading location details:', error);
            }
        }
        
        function filterMapMarkers() {
            const riskFilter = document.getElementById('risk-filter').value;
            const regionFilter = document.getElementById('region-filter').value;
            
            // Filtere Marker basierend auf Auswahl
            markers.forEach(marker => {
                const data = marker.options.data;
                if (!data) return;
                
                let show = true;
                
                if (riskFilter !== 'all' && data.risk_level !== riskFilter) {
                    show = false;
                }
                
                if (regionFilter !== 'all' && data.country_code !== regionFilter) {
                    show = false;
                }
                
                if (show) {
                    marker.addTo(map);
                } else {
                    map.removeLayer(marker);
                }
            });
        }
        
        function initMap() {
            // Prüfe ob Karte bereits existiert
            if (map) {
                map.remove();
            }
            
            // Warte bis DOM bereit ist
            const mapElement = document.getElementById('map');
            if (!mapElement) {
                console.error('Map element nicht gefunden!');
                return;
            }
            
            // Initialisiere Karte
            map = L.map('map', {
                center: [20, 0],
                zoom: 2,
                zoomControl: true
            });
            
            // Füge Tile Layer hinzu - verwende mehrere Quellen als Fallback
            const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{s}/{z}/{x}/{y}.png', {
                attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
                maxZoom: 19,
                subdomains: ['a', 'b', 'c']
            });
            
            // Alternative Tile-Layer als Fallback
            const cartoLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
                attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> © <a href="https://carto.com/attributions">CARTO</a>',
                subdomains: 'abcd',
                maxZoom: 19
            });
            
            // Versuche zuerst OSM, dann Carto als Fallback
            osmLayer.addTo(map);
            
            // Prüfe ob Tiles geladen werden
            osmLayer.on('tileerror', function(error, tile) {
                console.warn('OSM Tile-Fehler, wechsle zu Carto:', error);
                map.removeLayer(osmLayer);
                cartoLayer.addTo(map);
            });
            
            // Warte bis Karte vollständig geladen ist
            map.whenReady(function() {
                console.log('Karte bereit, lade Daten...');
                // Wichtig: invalidateSize() nach kurzer Verzögerung
                setTimeout(() => {
                    map.invalidateSize();
                    // Lade Daten nachdem Karte bereit ist
                    loadMapData();
                }, 300);
            });
            
            // Fallback: Lade Daten auch nach 1 Sekunde
            setTimeout(() => {
                if (map && !markers || markers.length === 0) {
                    console.log('Fallback: Lade Daten...');
            loadMapData();
                }
            }, 1000);
        }
        
        async function loadStats() {
            const res = await fetch('/api/stats');
            const data = await res.json();
            
            document.getElementById('total-records').textContent = data.total_records || 0;
            document.getElementById('with-coords').textContent = data.records_with_coordinates || 0;
            document.getElementById('critical-risk').textContent = data.risk_distribution?.CRITICAL || 0;
            document.getElementById('high-risk').textContent = data.risk_distribution?.HIGH || 0;
        }
        
        async function loadMapData() {
            try {
                console.log('Lade Karten-Daten...');
                
                if (!map) {
                    console.error('Karte nicht initialisiert!');
                    return;
                }
                
                // Prüfe welche Datenquelle ausgewählt ist
                currentDataSource = document.getElementById('map-data-source')?.value || 'api';
                
                if (currentDataSource === 'frontend') {
                    await loadFrontendGeoJSON();
                } else {
                    await loadAPIMapData();
                }
            } catch (error) {
                console.error('Fehler beim Laden der Karten-Daten:', error);
            }
        }
        
        async function loadAPIMapData() {
            const res = await fetch('/api/map-data');
            if (!res.ok) {
                console.error('API-Fehler:', res.status, res.statusText);
                return;
            }
            
            const data = await res.json();
            console.log('Daten erhalten:', data.points ? data.points.length : 0, 'Points');
            
            // Entferne alte Marker
            if (markers && markers.length > 0) {
                markers.forEach(m => {
                    try {
                        map.removeLayer(m);
                    } catch(e) {
                        console.warn('Fehler beim Entfernen von Marker:', e);
                    }
                });
            }
            if (geojsonLayer) {
                map.removeLayer(geojsonLayer);
                geojsonLayer = null;
            }
            markers = [];
            
            if (!data.points || data.points.length === 0) {
                console.log('Keine Datenpunkte für Karte gefunden');
                const infoMarker = L.marker([20, 0]).addTo(map);
                infoMarker.bindPopup('Keine Daten mit Koordinaten verfügbar. Führe Geocoding durch!').openPopup();
                markers.push(infoMarker);
                return;
            }
        
            const colors = {
                'CRITICAL': '#ef4444',
                'HIGH': '#f97316',
                'MEDIUM': '#eab308',
                'LOW': '#3b82f6',
                'MINIMAL': '#94a3b8'
            };
            
            const markerGroup = L.layerGroup();
            
            data.points.forEach((point, index) => {
                if (!point.lat || !point.lon) {
                    console.warn(`Point ${index} ohne Koordinaten:`, point);
                    return;
                }
                
                try {
                    const radius = Math.max(10, Math.min(30, 10 + (point.risk_score || 0) * 50));
                    const marker = L.circleMarker([point.lat, point.lon], {
                        radius: radius,
                        fillColor: colors[point.risk_level] || '#94a3b8',
                        color: '#fff',
                        weight: 2,
                        opacity: 1,
                        fillOpacity: 0.8
                    });
                    
                    marker.options.data = point;
                    
                    const popupContent = `
                        <div style="min-width: 200px;">
                            <strong>${(point.title || 'N/A').substring(0, 50)}</strong><br>
                            <hr style="margin: 5px 0;">
                            <strong>Quelle:</strong> ${point.source || 'N/A'}<br>
                            <strong>Region:</strong> ${point.region || 'N/A'}<br>
                            <strong>Land:</strong> ${point.country || 'N/A'}<br>
                            <strong>Risiko:</strong> <span style="background: ${colors[point.risk_level] || '#94a3b8'}; color: white; padding: 2px 6px; border-radius: 3px;">${point.risk_level || 'MINIMAL'}</span><br>
                            <strong>Score:</strong> ${point.risk_score ? point.risk_score.toFixed(2) : '0.00'}<br>
                            ${point.indicators && point.indicators.length > 0 ? `<strong>Indikatoren:</strong> ${point.indicators.join(', ')}<br>` : ''}
                        </div>
                    `;
                    
                    marker.bindPopup(popupContent);
                    markerGroup.addLayer(marker);
                    markers.push(marker);
                } catch (error) {
                    console.error(`Fehler beim Erstellen von Marker ${index}:`, error, point);
                }
            });
            
            markerGroup.addTo(map);
            
            if (markers.length > 0) {
                const group = new L.featureGroup(markers);
                map.fitBounds(group.getBounds().pad(0.1));
            }
            
            addRegionalZones();
            updateRegionFilter();
            console.log(`Karte geladen: ${markers.length} Marker angezeigt`);
        }
        
        async function loadFrontendGeoJSON() {
            try {
                const res = await fetch('/api/frontend/map-data');
                if (!res.ok) {
                    throw new Error('GeoJSON nicht gefunden');
                }
                
                const geojsonData = await res.json();
                
                // Entferne alte Layer
                if (geojsonLayer) {
                    map.removeLayer(geojsonLayer);
                }
                if (markers && markers.length > 0) {
                    markers.forEach(m => map.removeLayer(m));
                    markers = [];
                }
                
                const colors = {
                    'CRITICAL': '#ef4444',
                    'HIGH': '#f97316',
                    'MEDIUM': '#eab308',
                    'LOW': '#3b82f6',
                    'MINIMAL': '#94a3b8'
                };
                
                // Lade vollständige Daten für Popups
                const completeRes = await fetch('/api/frontend/complete-data');
                const completeData = await completeRes.json();
                allLocations = completeData.locations || [];
                
                // Erstelle GeoJSON Layer
                geojsonLayer = L.geoJSON(geojsonData, {
                    pointToLayer: function(feature, latlng) {
                        const props = feature.properties;
                        const riskLevel = props.risk_level || 'MINIMAL';
                        const riskScore = props.risk_score || 0;
                        
                        const radius = Math.max(8, Math.min(25, 8 + riskScore * 30));
                        
                        return L.circleMarker(latlng, {
                            radius: radius,
                            fillColor: colors[riskLevel] || '#94a3b8',
                            color: '#fff',
                            weight: 2,
                            opacity: 1,
                            fillOpacity: 0.8
                        });
                    },
                    onEachFeature: function(feature, layer) {
                        const props = feature.properties;
                        const locationId = `${props.country_code}_${props.name.toLowerCase().replace(' ', '_')}`;
                        const location = allLocations.find(l => l.location_id === locationId);
                        
                        let popupContent = `
                            <div style="min-width: 250px;">
                                <strong>${props.name}</strong> (${props.country_code})<br>
                                <hr style="margin: 5px 0;">
                                <strong>Risiko:</strong> <span style="background: ${colors[props.risk_level] || '#94a3b8'}; color: white; padding: 2px 6px; border-radius: 3px;">${props.risk_level}</span><br>
                                <strong>Score:</strong> ${props.risk_score?.toFixed(2) || '0.00'}<br>
                                <strong>Urgency:</strong> ${((props.urgency_score || 0) * 100).toFixed(0)}%<br>
                        `;
                        
                        if (location) {
                            const warning = location.early_warning;
                            if (warning && warning.total_signals > 0) {
                                popupContent += `<br><strong>⚠️ Warnungen:</strong> ${warning.total_signals}<br>`;
                            }
                            if (location.adaptation_recommendations && location.adaptation_recommendations.length > 0) {
                                popupContent += `<strong>💡 Empfehlungen:</strong> ${location.adaptation_recommendations.length}<br>`;
                            }
                        }
                        
                        popupContent += `<br><button onclick="showLocationDetails('${locationId}')" style="background: #667eea; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">Details anzeigen</button>`;
                        popupContent += `</div>`;
                        
                        layer.bindPopup(popupContent);
                        
                        // Speichere Daten für Filter
                        layer.options.data = {
                            risk_level: props.risk_level,
                            country_code: props.country_code,
                            location_id: locationId
                        };
                    }
                });
                
                geojsonLayer.addTo(map);
                
                // Auto-Zoom
                if (geojsonLayer.getBounds().isValid()) {
                    map.fitBounds(geojsonLayer.getBounds().pad(0.1));
                }
                
                updateRegionFilter();
                addRegionalZones();
                console.log('GeoJSON geladen:', geojsonData.features.length, 'Features');
            } catch (error) {
                console.error('Fehler beim Laden von GeoJSON:', error);
                alert('Frontend-Daten nicht gefunden. Führe generate_frontend_data.py aus.');
            }
        }
        
        function updateRegionFilter() {
            const regionSelect = document.getElementById('region-filter');
            if (!regionSelect) return;
            
            // Sammle alle Länder-Codes
            const countries = new Set();
            
            if (currentDataSource === 'frontend' && allLocations.length > 0) {
                allLocations.forEach(loc => {
                    if (loc.country_code) countries.add(loc.country_code);
                });
            } else {
                markers.forEach(m => {
                    if (m.options.data && m.options.data.country_code) {
                        countries.add(m.options.data.country_code);
                    }
                });
            }
            
            // Aktualisiere Dropdown
            regionSelect.innerHTML = '<option value="all">Alle Regionen</option>';
            Array.from(countries).sort().forEach(code => {
                const option = document.createElement('option');
                option.value = code;
                option.textContent = code;
                regionSelect.appendChild(option);
            });
        }
        
        async function loadFrontendData() {
            const tab = document.getElementById('frontend-data-tab');
            if (!tab) return;
            
            tab.innerHTML = '<div class="loading">Lade Frontend-Daten...</div>';
            
            try {
                const [completeRes, warningsRes, recRes, regionsRes] = await Promise.all([
                    fetch('/api/frontend/complete-data'),
                    fetch('/api/frontend/early-warnings'),
                    fetch('/api/frontend/adaptation-recommendations'),
                    fetch('/api/frontend/regions')
                ]);
                
                const completeData = await completeRes.json();
                const warningsData = await warningsRes.json();
                const recData = await recRes.json();
                const regionsData = await regionsRes.json();
                
                let html = `
                    <div class="stats-grid" style="margin-bottom: 20px;">
                        <div class="stat-card">
                            <h3>Total Locations</h3>
                            <div class="value">${completeData.metadata?.total_locations || 0}</div>
                        </div>
                        <div class="stat-card">
                            <h3>Aktive Warnungen</h3>
                            <div class="value">${warningsData.total || 0}</div>
                        </div>
                        <div class="stat-card">
                            <h3>Regionen</h3>
                            <div class="value">${regionsData.total_regions || 0}</div>
                        </div>
                    </div>
                    
                    <h2>🌍 Regionen</h2>
                    <div id="regions-list"></div>
                    
                    <h2 style="margin-top: 30px;">📍 Locations</h2>
                    <div id="locations-list"></div>
                `;
                
                tab.innerHTML = html;
                
                // Zeige Regionen
                const regionsList = document.getElementById('regions-list');
                if (regionsData.regions && regionsData.regions.length > 0) {
                    regionsList.innerHTML = regionsData.regions.map(region => `
                        <div class="location-detail" onclick="filterByRegion('${region.country_code}')" style="cursor: pointer;">
                            <strong>${region.country_code}</strong><br>
                            <small>Locations: ${region.total_locations} | Warnungen: ${region.total_warnings}</small><br>
                            <small>Avg Urgency: ${(region.average_urgency * 100).toFixed(0)}%</small>
                        </div>
                    `).join('');
                }
                
                // Zeige Locations
                const locationsList = document.getElementById('locations-list');
                if (completeData.locations && completeData.locations.length > 0) {
                    locationsList.innerHTML = completeData.locations.map(loc => `
                        <div class="location-detail" onclick="showLocationDetails('${loc.location_id}')" style="cursor: pointer;">
                            <strong>${loc.location_name}</strong> (${loc.country_code})<br>
                            <span class="risk-badge risk-${loc.risk_level}">${loc.risk_level}</span>
                            <small>Urgency: ${(loc.urgency_score * 100).toFixed(0)}% | Warnungen: ${loc.early_warning?.total_signals || 0}</small>
                        </div>
                    `).join('');
                }
            } catch (error) {
                tab.innerHTML = `<div class="loading">Fehler: ${error.message}</div>`;
            }
        }
        
        function filterByRegion(countryCode) {
            document.getElementById('map-data-source').value = 'frontend';
            document.getElementById('region-filter').value = countryCode;
            loadMapData();
            showTab('map');
        }
        
        function updateVisualization() {
            const vizType = document.getElementById('visualization-type')?.value || 'markers';
            
            // Entferne alle Visualisierungs-Layer
            if (heatmapLayer) {
                map.removeLayer(heatmapLayer);
                heatmapLayer = null;
            }
            if (rasterLayer) {
                map.removeLayer(rasterLayer);
                rasterLayer = null;
            }
            contourLayers.forEach(layer => map.removeLayer(layer));
            contourLayers = [];
            
            if (vizType === 'heatmap') {
                loadHeatmap();
            } else if (vizType === 'raster' || vizType === 'contours') {
                loadRiskRaster(vizType === 'contours');
            }
            // 'markers' ist Standard und wird bereits angezeigt
        }
        
        async function loadHeatmap() {
            try {
                const res = await fetch('/api/frontend/complete-data');
                const data = await res.json();
                
                if (!data.locations || data.locations.length === 0) {
                    return;
                }
                
                // Erstelle Heatmap-Daten
                const heatmapData = data.locations
                    .filter(loc => loc.coordinates[0] !== 0 && loc.coordinates[1] !== 0)
                    .map(loc => [
                        loc.coordinates[0],  // lat
                        loc.coordinates[1],  // lon
                        loc.risk_score * 10  // intensity
                    ]);
                
                // Verwende Leaflet.heat Plugin (falls verfügbar)
                if (typeof L.heatLayer !== 'undefined') {
                    heatmapLayer = L.heatLayer(heatmapData, {
                        radius: 25,
                        blur: 15,
                        maxZoom: 17,
                        gradient: {
                            0.0: 'blue',
                            0.5: 'yellow',
            1.0: 'red'
                        }
                    }).addTo(map);
                } else {
                    console.warn('Leaflet.heat nicht verfügbar - installiere: npm install leaflet.heat');
                }
            } catch (error) {
                console.error('Fehler beim Laden der Heatmap:', error);
            }
        }
        
        async function loadRiskRaster(showContours = false) {
            try {
                const res = await fetch('/api/frontend/risk-raster');
                const data = await res.json();
                
                if (!data.available || !data.raster) {
                    console.log('Raster-Daten nicht verfügbar');
                    return;
                }
                
                const rasterData = data.raster;
                
                // Zeige Contour-Linien
                if (showContours && rasterData.contours) {
                    const colors = {
                        'CRITICAL': '#ef4444',
                        'HIGH': '#f97316',
                        'MEDIUM': '#eab308',
                        'LOW': '#3b82f6',
                        'MINIMAL': '#94a3b8'
                    };
                    
                    rasterData.contours.forEach(contour => {
                        if (contour.coordinates && contour.coordinates.length > 0) {
                            const coordinates = contour.coordinates.map(c => [c.lat, c.lon]);
                            
                            const polyline = L.polyline(coordinates, {
                                color: colors[contour.level] || '#94a3b8',
                                weight: 2,
                                opacity: 0.7,
                                dashArray: contour.level === 'CRITICAL' ? '10, 5' : '5, 5'
                            }).addTo(map);
                            
                            polyline.bindPopup(`
                                <strong>${contour.level} Risk</strong><br>
                                Risk Value: ${contour.risk_value.toFixed(2)}
                            `);
                            
                            contourLayers.push(polyline);
                        }
                    });
                    
                    console.log(`✅ ${contourLayers.length} Contour-Linien geladen`);
                }
                
                // Zeige Raster-Punkte als Heatmap
                if (rasterData.points && rasterData.points.length > 0) {
                    const heatmapData = rasterData.points
                        .filter(p => p.risk_score > 0.1)
                        .map(p => [
                            p.lat,
                            p.lon,
                            p.risk_score * 10
                        ]);
                    
                    if (typeof L.heatLayer !== 'undefined') {
                        rasterLayer = L.heatLayer(heatmapData, {
                            radius: 20,
                            blur: 10,
                            maxZoom: 17,
                            gradient: {
                                0.0: 'blue',
                                0.3: 'cyan',
                                0.5: 'yellow',
                                0.7: 'orange',
                                1.0: 'red'
                            }
                        }).addTo(map);
                    }
                }
            } catch (error) {
                console.error('Fehler beim Laden des Rasters:', error);
            }
        }
        
        function addRegionalZones() {
            // Deutschland Zone (vereinfachtes Polygon)
            const germanyBounds = [[47.27, 5.87], [55.06, 15.04]];
            const germanyZone = L.rectangle(germanyBounds, {
                color: '#3b82f6',
                fillColor: '#3b82f6',
                fillOpacity: 0.1,
                weight: 2
            }).addTo(map);
            
            germanyZone.bindPopup('<strong>🇩🇪 Deutschland</strong><br>Fokus-Region für Klima-Konflikt-Analyse');
            
            // Europa Zone (vereinfachtes Polygon)
            const europeBounds = [[35.0, -10.0], [71.0, 40.0]];
            const europeZone = L.rectangle(europeBounds, {
                color: '#667eea',
                fillColor: '#667eea',
                fillOpacity: 0.05,
                weight: 2,
                dashArray: '5, 5'
            }).addTo(map);
            
            europeZone.bindPopup('<strong>🇪🇺 Europa</strong><br>Regionale Analyse-Zone');
            
            // Legende hinzufügen
            const legend = L.control({position: 'bottomright'});
            legend.onAdd = function(map) {
                const div = L.DomUtil.create('div', 'info legend');
                div.innerHTML = `
                    <h4 style="margin: 5px 0;">Risiko-Level</h4>
                    <div style="background: white; padding: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                        <div><span style="background: #ef4444; width: 12px; height: 12px; display: inline-block; border-radius: 50%; margin-right: 5px;"></span> CRITICAL</div>
                        <div><span style="background: #f97316; width: 12px; height: 12px; display: inline-block; border-radius: 50%; margin-right: 5px;"></span> HIGH</div>
                        <div><span style="background: #eab308; width: 12px; height: 12px; display: inline-block; border-radius: 50%; margin-right: 5px;"></span> MEDIUM</div>
                        <div><span style="background: #3b82f6; width: 12px; height: 12px; display: inline-block; border-radius: 50%; margin-right: 5px;"></span> LOW</div>
                        <div><span style="background: #94a3b8; width: 12px; height: 12px; display: inline-block; border-radius: 50%; margin-right: 5px;"></span> MINIMAL</div>
                        <hr style="margin: 8px 0;">
                        <div><span style="border: 2px solid #3b82f6; width: 12px; height: 12px; display: inline-block; margin-right: 5px; background: rgba(59,130,246,0.1);"></span> 🇩🇪 Deutschland</div>
                        <div><span style="border: 2px dashed #667eea; width: 12px; height: 12px; display: inline-block; margin-right: 5px; background: rgba(102,126,234,0.05);"></span> 🇪🇺 Europa</div>
                    </div>
                `;
                return div;
            };
            legend.addTo(map);
        }
        
        async function loadRecords() {
            const res = await fetch('/api/records?limit=50');
            const data = await res.json();
            
            const list = document.getElementById('records-list');
            if (!data.records || data.records.length === 0) {
                list.innerHTML = '<div class="loading">Keine Records gefunden</div>';
                return;
            }
            
            list.innerHTML = data.records.map(record => `
                <div class="record-item">
                    <span class="risk-badge risk-${record.risk.level}">${record.risk.level}</span>
                    <strong>${record.title || 'N/A'}</strong><br>
                    <small>${record.source_name} | ${record.region || 'N/A'} | Score: ${record.risk.total_score.toFixed(2)}</small>
                </div>
            `).join('');
        }
        
        async function loadEnrichment() {
            // Lade Statistiken
            const statsRes = await fetch('/api/batch-enrichment');
            const statsData = await statsRes.json();
            
            const statsDiv = document.getElementById('enrichment-stats');
            if (statsData.table_exists) {
                statsDiv.innerHTML = `
                    <div class="stat-card" style="margin-bottom: 20px;">
                        <h3>Batch-Enrichment Statistiken</h3>
                        <div class="value">${statsData.total_enriched} angereicherte Records</div>
                        <p>Durchschnitt: ${statsData.average_datapoints} Datenpunkte pro Record</p>
                    </div>
                `;
            } else {
                statsDiv.innerHTML = '<div class="loading">Keine Enrichment-Daten vorhanden. Führe batch_enrichment_50.py aus.</div>';
            }
            
            // Lade Records mit Enrichment
            const res = await fetch('/api/records?limit=50&include_enrichment=true');
            const data = await res.json();
            
            const list = document.getElementById('enrichment-list');
            if (!data.records || data.records.length === 0) {
                list.innerHTML = '<div class="loading">Keine Records gefunden</div>';
                return;
            }
            
            // Filtere nur Records mit Enrichment
            const enrichedRecords = data.records.filter(r => r.enrichment);
            
            if (enrichedRecords.length === 0) {
                list.innerHTML = '<div class="loading">Keine angereicherten Records gefunden</div>';
                return;
            }
            
            list.innerHTML = enrichedRecords.map(record => {
                const enrichment = record.enrichment;
                const datapoints = enrichment.datapoints || {};
                const datapointCount = Object.keys(datapoints).length;
                
                // Zeige Top 5 Datenpunkte
                const topDatapoints = Object.entries(datapoints)
                    .slice(0, 5)
                    .map(([key, value]) => `<strong>${key}:</strong> ${value}`)
                    .join(', ');
                
                return `
                    <div class="record-item">
                        <span class="risk-badge risk-${record.risk.level}">${record.risk.level}</span>
                        <strong>${record.title || 'N/A'}</strong><br>
                        <small>${record.source_name} | ${record.region || 'N/A'}</small><br>
                        <div style="margin-top: 10px; padding: 10px; background: #f5f5f5; border-radius: 4px;">
                            <strong>📊 ${datapointCount} Datenpunkte:</strong><br>
                            <small>${topDatapoints || 'Keine Datenpunkte'}</small>
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        async function loadPredictions() {
            const res = await fetch('/api/predictions');
            const data = await res.json();
            
            const list = document.getElementById('predictions-list');
            if (!data.predictions || data.predictions.length === 0) {
                list.innerHTML = '<div class="loading">Keine Predictions verfügbar</div>';
                return;
            }
            
            list.innerHTML = data.predictions.map(pred => `
                <div class="record-item">
                    <span class="risk-badge risk-${pred.risk_level}">${pred.risk_level}</span>
                    <strong>${pred.region}</strong><br>
                    <small>Risiko-Score: ${pred.risk_score.toFixed(2)} | Records: ${pred.record_count}</small><br>
                    <small>Indikatoren: ${pred.indicators.join(', ')}</small>
                </div>
            `).join('');
        }
        
        async function loadRegionalData() {
            try {
                const res = await fetch('/api/regional-data');
                const data = await res.json();
                
                const overview = document.getElementById('regional-overview');
                
                if (!data || Object.keys(data).length === 0) {
                    overview.innerHTML = '<div class="loading">Keine regionalen Daten verfügbar</div>';
                    return;
                }
                
                // Übersicht
                overview.innerHTML = `
                    <div class="stats-grid">
                        ${Object.entries(data).map(([region, stats]) => `
                            <div class="stat-card" onclick="showRegionDetails('${region}')" style="cursor: pointer;">
                                <h3>${region}</h3>
                                <div class="value">${stats.total_records}</div>
                                <p>Records | Avg Risk: ${stats.average_risk_score}</p>
                                <p>Enriched: ${stats.enriched_records} (${stats.enrichment_rate}%)</p>
                            </div>
                        `).join('')}
                    </div>
                `;
                
                // Details für jede Region
                for (const [region, stats] of Object.entries(data)) {
                    await loadRegionDetails(region, stats);
                }
            } catch (error) {
                console.error('Error loading regional data:', error);
                document.getElementById('regional-overview').innerHTML = '<div class="loading">Fehler beim Laden</div>';
            }
        }
        
        async function loadRegionDetails(region, stats) {
            try {
                const res = await fetch(`/api/regional-records?region=${region}&limit=20`);
                const data = await res.json();
                
                const sectionId = region.toLowerCase() + '-section';
                const statsId = region.toLowerCase() + '-stats';
                const recordsId = region.toLowerCase() + '-records';
                
                document.getElementById(sectionId).style.display = 'block';
                
                // Statistiken
                document.getElementById(statsId).innerHTML = `
                    <div class="stats-grid" style="margin-bottom: 20px;">
                        <div class="stat-card">
                            <h3>Risiko-Verteilung</h3>
                            <div>
                                CRITICAL: ${stats.risk_distribution.CRITICAL || 0}<br>
                                HIGH: ${stats.risk_distribution.HIGH || 0}<br>
                                MEDIUM: ${stats.risk_distribution.MEDIUM || 0}<br>
                                LOW: ${stats.risk_distribution.LOW || 0}
                            </div>
                        </div>
                        <div class="stat-card">
                            <h3>Datenquellen</h3>
                            <div>
                                ${Object.entries(stats.sources).map(([source, count]) => 
                                    `${source}: ${count}`
                                ).join('<br>')}
                            </div>
                        </div>
                        <div class="stat-card">
                            <h3>Geocoding</h3>
                            <div class="value">${stats.records_with_coordinates}</div>
                            <p>Records mit Koordinaten</p>
                        </div>
                    </div>
                `;
                
                // Records
                if (data.records && data.records.length > 0) {
                    document.getElementById(recordsId).innerHTML = data.records.map(record => `
                        <div class="record-item">
                            <span class="risk-badge risk-${record.risk.level}">${record.risk.level}</span>
                            <strong>${record.title || 'N/A'}</strong><br>
                            <small>${record.source_name} | ${record.region || 'N/A'} | Score: ${record.risk.score.toFixed(2)}</small>
                            ${record.risk.indicators && record.risk.indicators.length > 0 ? 
                                `<br><small>Indikatoren: ${record.risk.indicators.join(', ')}</small>` : ''}
                        </div>
                    `).join('');
                } else {
                    document.getElementById(recordsId).innerHTML = '<div class="loading">Keine Records gefunden</div>';
                }
            } catch (error) {
                console.error(`Error loading ${region} details:`, error);
            }
        }
        
        function showRegionDetails(region) {
            const sectionId = region.toLowerCase() + '-section';
            const section = document.getElementById(sectionId);
            if (section) {
                section.scrollIntoView({ behavior: 'smooth' });
            }
        }
        
        async function loadSources() {
            const res = await fetch('/api/data-sources');
            const data = await res.json();
            
            const list = document.getElementById('sources-list');
            list.innerHTML = Object.values(data).map(source => `
                <div class="record-item">
                    <h3>${source.name}</h3>
                    <p>${source.description}</p>
                    <p><strong>Extrahiert:</strong> ${source.fields.join(', ')}</p>
                    <p><strong>Nützlich für:</strong></p>
                    <ul>
                        ${source.useful_for.map(item => `<li>${item}</li>`).join('')}
                    </ul>
                </div>
            `).join('');
        }
        
        // Initial load
        loadStats();
        loadSidebarContent();
        
        // Initialisiere Karte sofort wenn Tab aktiv ist
        document.addEventListener('DOMContentLoaded', function() {
            // Warte bis alles geladen ist
            setTimeout(() => {
                const mapTab = document.getElementById('map-tab');
                if (mapTab && mapTab.classList.contains('active')) {
                    initMap();
                }
            }, 500);
        });
        
        // Fallback: Initialisiere wenn Seite bereits geladen ist
        if (document.readyState === 'complete' || document.readyState === 'interactive') {
            setTimeout(() => {
                const mapTab = document.getElementById('map-tab');
                if (mapTab && mapTab.classList.contains('active')) {
                    initMap();
                }
            }, 500);
        }
        
        // Auto-refresh Stats
        setInterval(loadStats, 30000);
        
        // Refresh Sidebar alle 60 Sekunden
        setInterval(loadSidebarContent, 60000);
        
        // Refresh Karte alle 60 Sekunden wenn aktiv
        setInterval(() => {
            if (map && document.getElementById('map-tab').classList.contains('active')) {
                loadMapData();
            }
        }, 60000);
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    import socket
    
    # Finde freien Port
    def find_free_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]
    
    port = find_free_port()
    
    print("🌍 Climate Conflict Intelligence Dashboard")
    print(f"📊 Verfügbar unter: http://localhost:{port}")
    print(f"🔗 API-Endpoints: http://localhost:{port}/api/stats")
    print("\nDrücke Ctrl+C zum Beenden\n")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except KeyboardInterrupt:
        print("\n\nServer gestoppt.")

