#!/usr/bin/env python3
"""
Interaktive Risiko-Karte mit Zonen und Farben
Erstellt eine interaktive Weltkarte mit Risiko-Zonen basierend auf Kontexträumen
"""
import sys
from pathlib import Path
from typing import List, Dict, Optional
import json

sys.path.append(str(Path(__file__).parent))

try:
    import folium
    from folium import plugins
    import folium.plugins as folium_plugins
except ImportError:
    print("Folium nicht installiert. Installiere...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "folium"])
    import folium
    from folium import plugins
    import folium.plugins as folium_plugins

from database import DatabaseManager
from rich.console import Console

console = Console()


class InteractiveRiskMap:
    """Erstellt interaktive Risiko-Karte mit Zonen und Farben"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.risk_colors = {
            'CRITICAL': '#8B0000',  # Dunkelrot
            'HIGH': '#FF4500',      # Orange-Rot
            'MEDIUM': '#FFD700',    # Gold
            'LOW': '#90EE90',        # Hellgrün
            'MINIMAL': '#E0E0E0'     # Grau
        }
    
    def get_risk_color(self, risk_level: str) -> str:
        """Hole Farbe für Risiko-Level"""
        return self.risk_colors.get(risk_level, '#808080')
    
    def create_map(self, output_path: str = "backend/data/interactive_risk_map.html") -> str:
        """Erstelle interaktive Risiko-Karte"""
        console.print("\n[bold cyan]🗺️  Erstelle interaktive Risiko-Karte...[/bold cyan]")
        
        # Hole Kontexträume aus Datenbank
        context_spaces = self._load_context_spaces()
        
        if not context_spaces:
            console.print("[yellow]⚠️  Keine Kontexträume gefunden. Führe zuerst geospatial_context_pipeline.py aus.[/yellow]")
            # Fallback: Verwende Records
            context_spaces = self._load_records_as_context()
        
        console.print(f"✅ {len(context_spaces)} Kontexträume geladen")
        
        # Erstelle Karte
        world_map = folium.Map(
            location=[20, 0],
            zoom_start=2,
            tiles='OpenStreetMap',
            min_zoom=2,
            max_zoom=18
        )
        
        # Füge verschiedene Tile-Layer hinzu
        folium.TileLayer(
            tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            attr='OpenStreetMap',
            name='OpenStreetMap',
            overlay=False,
            control=True
        ).add_to(world_map)
        
        folium.TileLayer(
            tiles='CartoDB positron',
            name='Light Map',
            overlay=False,
            control=True
        ).add_to(world_map)
        
        folium.TileLayer(
            tiles='CartoDB dark_matter',
            name='Dark Map',
            overlay=False,
            control=True
        ).add_to(world_map)
        
        # Erstelle Marker-Gruppen nach Risiko-Level
        marker_groups = {}
        for level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'MINIMAL']:
            marker_groups[level] = folium.FeatureGroup(name=f'Risiko: {level}')
        
        # Erstelle Heatmap-Daten
        heatmap_data = []
        
        # Füge Marker für jeden Kontextraum hinzu
        for context in context_spaces:
            if not context.get('latitude') or not context.get('longitude'):
                continue
            
            lat = context['latitude']
            lon = context['longitude']
            risk_level = context.get('risk_level', 'MINIMAL')
            risk_score = context.get('risk_score', 0.0)
            
            # Marker-Größe basierend auf Risiko-Score
            marker_size = max(8, min(30, int(risk_score * 30)))
            
            # Marker-Farbe
            color = self.get_risk_color(risk_level)
            
            # Popup-Content
            popup_html = self._create_popup_html(context)
            
            # Erstelle Marker
            marker = folium.CircleMarker(
                location=[lat, lon],
                radius=marker_size,
                popup=folium.Popup(popup_html, max_width=400),
                tooltip=f"{context.get('country_name', 'Unknown')} - {risk_level}",
                color='white',
                weight=2,
                fillColor=color,
                fillOpacity=0.7
            )
            
            # Füge zu entsprechender Gruppe hinzu
            if risk_level in marker_groups:
                marker.add_to(marker_groups[risk_level])
            
            # Heatmap-Daten
            heatmap_data.append([lat, lon, risk_score])
        
        # Füge Marker-Gruppen zur Karte hinzu
        for group in marker_groups.values():
            group.add_to(world_map)
        
        # Erstelle Heatmap-Layer
        if heatmap_data:
            heatmap_layer = folium_plugins.HeatMap(
                heatmap_data,
                name='Risiko-Heatmap',
                min_opacity=0.2,
                max_zoom=18,
                radius=25,
                blur=15,
                gradient={
                    0.0: 'blue',
                    0.3: 'cyan',
                    0.5: 'lime',
                    0.7: 'yellow',
                    1.0: 'red'
                }
            )
            heatmap_layer.add_to(world_map)
        
        # Erstelle Risiko-Zonen (Choropleth)
        self._add_risk_zones(world_map, context_spaces)
        
        # Füge Layer-Control hinzu
        folium.LayerControl(collapsed=False).add_to(world_map)
        
        # Füge Legende hinzu
        self._add_legend(world_map)
        
        # Füge Fullscreen-Button hinzu
        folium_plugins.Fullscreen(
            position='topright',
            title='Vollbild',
            title_cancel='Vollbild beenden',
            force_separate_button=True
        ).add_to(world_map)
        
        # Speichere Karte
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        world_map.save(str(output_file))
        
        console.print(f"[green]✅ Karte gespeichert: {output_file.absolute()}[/green]")
        return str(output_file.absolute())
    
    def _load_context_spaces(self) -> List[Dict]:
        """Lade Kontexträume aus Datenbank"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    country_code,
                    country_name,
                    latitude,
                    longitude,
                    risk_score,
                    risk_level,
                    climate_indicators,
                    conflict_indicators,
                    future_risks,
                    context_summary,
                    data_sources,
                    last_updated
                FROM country_context_spaces
                WHERE latitude IS NOT NULL
                AND longitude IS NOT NULL
                ORDER BY risk_score DESC
            """)
            
            results = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                # Parse JSON-Felder
                for field in ['climate_indicators', 'conflict_indicators', 'future_risks', 'data_sources']:
                    if row_dict.get(field):
                        try:
                            row_dict[field] = json.loads(row_dict[field])
                        except:
                            row_dict[field] = []
                    else:
                        row_dict[field] = []
                
                results.append(row_dict)
            
            return results
    
    def _load_records_as_context(self) -> List[Dict]:
        """Lade Records als Fallback-Kontext"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    primary_country_code as country_code,
                    region as country_name,
                    primary_latitude as latitude,
                    primary_longitude as longitude,
                    COUNT(*) as record_count
                FROM records
                WHERE primary_latitude IS NOT NULL
                AND primary_longitude IS NOT NULL
                GROUP BY primary_country_code, region, primary_latitude, primary_longitude
                LIMIT 100
            """)
            
            results = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                # Schätze Risiko-Score basierend auf Anzahl Records
                record_count = row_dict.get('record_count', 0)
                risk_score = min(1.0, record_count / 10.0)
                
                results.append({
                    'country_code': row_dict.get('country_code', ''),
                    'country_name': row_dict.get('country_name', 'Unknown'),
                    'latitude': row_dict.get('latitude', 0.0),
                    'longitude': row_dict.get('longitude', 0.0),
                    'risk_score': risk_score,
                    'risk_level': self._score_to_level(risk_score),
                    'climate_indicators': [],
                    'conflict_indicators': [],
                    'future_risks': [],
                    'context_summary': f"{record_count} Records gefunden",
                    'data_sources': []
                })
            
            return results
    
    def _score_to_level(self, score: float) -> str:
        """Konvertiere Score zu Risiko-Level"""
        if score >= 0.8:
            return 'CRITICAL'
        elif score >= 0.6:
            return 'HIGH'
        elif score >= 0.4:
            return 'MEDIUM'
        elif score >= 0.2:
            return 'LOW'
        else:
            return 'MINIMAL'
    
    def _create_popup_html(self, context: Dict) -> str:
        """Erstelle HTML für Popup"""
        country_name = context.get('country_name', 'Unknown')
        risk_level = context.get('risk_level', 'MINIMAL')
        risk_score = context.get('risk_score', 0.0)
        climate_indicators = context.get('climate_indicators', [])
        conflict_indicators = context.get('conflict_indicators', [])
        future_risks = context.get('future_risks', [])
        context_summary = context.get('context_summary', '')
        
        html = f"""
        <div style="width: 350px;">
            <h3 style="margin-top: 0; color: {self.get_risk_color(risk_level)};">
                {country_name}
            </h3>
            <p><strong>Risiko-Level:</strong> <span style="color: {self.get_risk_color(risk_level)};">{risk_level}</span></p>
            <p><strong>Risiko-Score:</strong> {risk_score:.2f}</p>
            
            <h4>Klima-Indikatoren:</h4>
            <ul>
        """
        
        for indicator in climate_indicators[:5]:
            html += f"<li>{indicator}</li>"
        
        html += """
            </ul>
            
            <h4>Konflikt-Indikatoren:</h4>
            <ul>
        """
        
        for indicator in conflict_indicators[:5]:
            html += f"<li>{indicator}</li>"
        
        html += """
            </ul>
        """
        
        if future_risks:
            html += "<h4>Zukünftige Risiken:</h4><ul>"
            for risk in future_risks[:3]:
                risk_type = risk.get('type', 'Unknown')
                probability = risk.get('probability', 0.0)
                timeframe = risk.get('timeframe', 'Unknown')
                html += f"<li>{risk_type} ({probability:.0%}) - {timeframe}</li>"
            html += "</ul>"
        
        if context_summary:
            html += f"<p><strong>Zusammenfassung:</strong> {context_summary[:200]}...</p>"
        
        html += "</div>"
        
        return html
    
    def _add_risk_zones(self, map_obj, context_spaces: List[Dict]):
        """Füge Risiko-Zonen als Choropleth hinzu"""
        # Erstelle GeoJSON für Länder mit Risiko-Daten
        # Für jetzt verwenden wir Marker, aber später können wir echte GeoJSON-Polygone hinzufügen
        
        # Erstelle Feature-Gruppe für Zonen
        zones_group = folium.FeatureGroup(name='Risiko-Zonen')
        
        # Für jedes Land: Erstelle Zone basierend auf Risiko
        for context in context_spaces:
            if not context.get('latitude') or not context.get('longitude'):
                continue
            
            lat = context['latitude']
            lon = context['longitude']
            risk_score = context.get('risk_score', 0.0)
            risk_level = context.get('risk_level', 'MINIMAL')
            
            # Erstelle Kreis-Zone basierend auf Risiko
            # Größere Risiken = größere Zonen
            zone_radius = max(50000, min(500000, int(risk_score * 500000)))  # 50km bis 500km
            
            color = self.get_risk_color(risk_level)
            
            folium.Circle(
                location=[lat, lon],
                radius=zone_radius,
                popup=f"{context.get('country_name', 'Unknown')} - Zone",
                color=color,
                weight=2,
                fillColor=color,
                fillOpacity=0.1,
                tooltip=f"Risiko-Zone: {risk_level}"
            ).add_to(zones_group)
        
        zones_group.add_to(map_obj)
    
    def _add_legend(self, map_obj):
        """Füge Legende hinzu"""
        legend_html = """
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 200px; height: 200px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4 style="margin-top: 0;">Risiko-Legende</h4>
        <p><i class="fa fa-circle" style="color:#8B0000"></i> CRITICAL</p>
        <p><i class="fa fa-circle" style="color:#FF4500"></i> HIGH</p>
        <p><i class="fa fa-circle" style="color:#FFD700"></i> MEDIUM</p>
        <p><i class="fa fa-circle" style="color:#90EE90"></i> LOW</p>
        <p><i class="fa fa-circle" style="color:#E0E0E0"></i> MINIMAL</p>
        </div>
        """
        map_obj.get_root().html.add_child(folium.Element(legend_html))


def main():
    """Hauptfunktion"""
    map_creator = InteractiveRiskMap()
    output_path = map_creator.create_map()
    
    console.print(f"\n[bold green]✅ Interaktive Karte erstellt: {output_path}[/bold green]")
    console.print(f"[dim]Öffne die Datei in einem Browser, um die Karte anzuzeigen.[/dim]")


if __name__ == "__main__":
    main()

