#!/usr/bin/env python3
"""
Weltkarten-Visualisierung für gefährdete Regionen
Erstellt interaktive Karte mit Folium/Leaflet
"""
import sys
from pathlib import Path
from typing import List, Dict
import json

sys.path.append(str(Path(__file__).parent))

try:
    import folium
    from folium import plugins
except ImportError:
    print("Folium nicht installiert. Installiere...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "folium"])
    import folium
    from folium import plugins

from database import DatabaseManager
from risk_scoring import RiskScorer

def create_world_map():
    """Erstelle interaktive Weltkarte mit gefährdeten Regionen"""
    print("🌍 Erstelle Weltkarten-Visualisierung...")
    
    db = DatabaseManager()
    scorer = RiskScorer()
    
    # Hole alle Records mit Koordinaten
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                r.id,
                r.title,
                r.summary,
                r.region,
                r.source_name,
                r.publish_date,
                r.primary_latitude,
                r.primary_longitude,
                r.primary_country_code,
                r.geo_confidence
            FROM records r
            WHERE r.primary_latitude IS NOT NULL 
            AND r.primary_longitude IS NOT NULL
            ORDER BY r.fetched_at DESC
        """)
        records = [dict(row) for row in cursor.fetchall()]
    
    if not records:
        print("❌ Keine Records mit Koordinaten gefunden!")
        print("💡 Führe zuerst aus: python geocode_existing_records.py")
        return None
    
    print(f"✅ Gefunden: {len(records)} Records mit Koordinaten")
    
    # Erstelle Karte (zentriert auf Welt)
    world_map = folium.Map(
        location=[20, 0],
        zoom_start=2,
        tiles='OpenStreetMap'
    )
    
    # Füge verschiedene Tile-Layer hinzu
    folium.TileLayer('CartoDB positron', name='Light Map').add_to(world_map)
    folium.TileLayer('CartoDB dark_matter', name='Dark Map').add_to(world_map)
    
    # Gruppiere nach Risiko-Level
    risk_groups = {
        'CRITICAL': [],
        'HIGH': [],
        'MEDIUM': [],
        'LOW': [],
        'MINIMAL': []
    }
    
    # Berechne Risiko-Scores und gruppiere
    for record in records:
        risk = scorer.calculate_risk(record)
        risk_level = scorer.get_risk_level(risk.score)
        risk_groups[risk_level].append({
            'record': record,
            'risk': risk
        })
    
    # Farben für Risiko-Level
    colors = {
        'CRITICAL': 'red',
        'HIGH': 'orange',
        'MEDIUM': 'yellow',
        'LOW': 'lightblue',
        'MINIMAL': 'lightgray'
    }
    
    # Icons für Risiko-Level
    icons = {
        'CRITICAL': 'exclamation-triangle',
        'HIGH': 'exclamation-circle',
        'MEDIUM': 'info-circle',
        'LOW': 'info',
        'MINIMAL': 'circle'
    }
    
    # Erstelle Feature Groups für jedes Risiko-Level
    for risk_level, items in risk_groups.items():
        if not items:
            continue
        
        fg = folium.FeatureGroup(name=f'{risk_level} Risk ({len(items)})')
        
        for item in items:
            record = item['record']
            risk = item['risk']
            
            lat = record['primary_latitude']
            lon = record['primary_longitude']
            
            # Popup-Text
            popup_html = f"""
            <div style="width: 300px;">
                <h4>{record.get('title', 'N/A')[:50]}...</h4>
                <p><strong>Quelle:</strong> {record.get('source_name', 'N/A')}</p>
                <p><strong>Region:</strong> {record.get('region', 'N/A')}</p>
                <p><strong>Land:</strong> {record.get('primary_country_code', 'N/A')}</p>
                <p><strong>Datum:</strong> {record.get('publish_date', 'N/A')}</p>
                <hr>
                <p><strong>Climate Risk:</strong> {risk.climate_risk:.2f}</p>
                <p><strong>Conflict Risk:</strong> {risk.conflict_risk:.2f}</p>
                <p><strong>Urgency:</strong> {risk.urgency:.2f}</p>
                <p><strong>Gesamt-Score:</strong> {risk.score:.2f}</p>
                <p><strong>Indikatoren:</strong> {', '.join(risk.indicators[:5])}</p>
                {f'<p><small>{record.get("summary", "")[:200]}...</small></p>' if record.get("summary") else ''}
            </div>
            """
            
            # Marker-Größe basierend auf Score
            marker_size = max(8, min(risk.score * 20, 25))
            
            # Marker hinzufügen
            folium.CircleMarker(
                location=[lat, lon],
                radius=marker_size,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{risk_level}: {record.get('title', 'N/A')[:30]}...",
                color=colors[risk_level],
                fillColor=colors[risk_level],
                fillOpacity=0.7,
                weight=2
            ).add_to(fg)
        
        fg.add_to(world_map)
    
    # Heatmap für alle Records
    heat_data = [
        [record['primary_latitude'], record['primary_longitude']]
        for record in records
    ]
    
    if heat_data:
        plugins.HeatMap(
            heat_data,
            name='Heatmap',
            min_opacity=0.2,
            max_zoom=18,
            radius=15,
            blur=15,
            gradient={
                0.2: 'blue',
                0.4: 'cyan',
                0.6: 'lime',
                0.8: 'yellow',
                1.0: 'red'
            }
        ).add_to(world_map)
    
    # Layer Control hinzufügen
    folium.LayerControl(collapsed=False).add_to(world_map)
    
    # Legende hinzufügen
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: 200px; 
                background-color: white; z-index:9999; font-size:14px;
                border:2px solid grey; border-radius:5px; padding: 10px">
    <h4>Risiko-Level</h4>
    <p><i class="fa fa-circle" style="color:red"></i> CRITICAL</p>
    <p><i class="fa fa-circle" style="color:orange"></i> HIGH</p>
    <p><i class="fa fa-circle" style="color:yellow"></i> MEDIUM</p>
    <p><i class="fa fa-circle" style="color:lightblue"></i> LOW</p>
    <p><i class="fa fa-circle" style="color:lightgray"></i> MINIMAL</p>
    </div>
    '''
    world_map.get_root().html.add_child(folium.Element(legend_html))
    
    # Speichere Karte
    output_file = Path("./data/world_map.html")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    world_map.save(str(output_file))
    
    print(f"✅ Karte gespeichert: {output_file}")
    print(f"📊 Statistiken:")
    print(f"   - CRITICAL: {len(risk_groups['CRITICAL'])}")
    print(f"   - HIGH: {len(risk_groups['HIGH'])}")
    print(f"   - MEDIUM: {len(risk_groups['MEDIUM'])}")
    print(f"   - LOW: {len(risk_groups['LOW'])}")
    print(f"   - MINIMAL: {len(risk_groups['MINIMAL'])}")
    
    return world_map


if __name__ == "__main__":
    map_obj = create_world_map()
    if map_obj:
        print("\n🌐 Öffne Karte im Browser...")
        import webbrowser
        webbrowser.open(f"file://{Path('./data/world_map.html').absolute()}")

