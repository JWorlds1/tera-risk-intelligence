#!/usr/bin/env python3
"""
Risk Raster Generator - Iso-Risk Contours basierend auf Jones & Furnas (1987)
Erstellt ein geografisches Raster mit Risiko-Scores und Contour-Linien
"""
import numpy as np
from scipy.interpolate import griddata, RBFInterpolator
from scipy.spatial.distance import cdist
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import asyncio

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()


@dataclass
class RasterPoint:
    """Ein Punkt im Raster"""
    lat: float
    lon: float
    risk_score: float
    risk_level: str
    distance_to_nearest: float  # Distanz zum nächsten bekannten Punkt


class RiskRasterGenerator:
    """
    Generiert ein Risiko-Raster über die Weltkarte
    Basierend auf geometrischer Interpretation von Ähnlichkeitsmaßen (Jones & Furnas, 1987)
    """
    
    def __init__(
        self,
        resolution: float = 0.5,  # Grad (0.5° ≈ 55km)
        interpolation_method: str = 'rbf',  # 'rbf', 'linear', 'cubic'
        max_interpolation_distance: float = 5.0  # Max. Distanz für Interpolation (Grad)
    ):
        self.resolution = resolution
        self.interpolation_method = interpolation_method
        self.max_interpolation_distance = max_interpolation_distance
        
        # Risiko-Level Thresholds
        self.risk_thresholds = {
            'CRITICAL': 0.8,
            'HIGH': 0.6,
            'MEDIUM': 0.4,
            'LOW': 0.2,
            'MINIMAL': 0.0
        }
    
    def load_location_data(self, data_file: Optional[Path] = None) -> List[Dict]:
        """Lade Location-Daten aus Frontend-Daten"""
        if data_file is None:
            data_file = Path("./data/frontend/complete_data.json")
        
        if not data_file.exists():
            raise FileNotFoundError(f"Frontend-Daten nicht gefunden: {data_file}")
        
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        locations = []
        for loc in data.get('locations', []):
            coords = loc.get('coordinates', [0, 0])
            # Überspringe Platzhalter-Koordinaten
            if coords[0] == 0 and coords[1] == 0:
                continue
            
            locations.append({
                'lat': coords[0],
                'lon': coords[1],
                'risk_score': loc.get('risk_score', 0.0),
                'risk_level': loc.get('risk_level', 'MINIMAL'),
                'location_id': loc.get('location_id'),
                'location_name': loc.get('location_name'),
                'country_code': loc.get('country_code')
            })
        
        return locations
    
    def create_raster_grid(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Erstelle ein geografisches Raster über die Weltkarte
        Returns: (lats, lons) - 2D Arrays mit Koordinaten
        """
        # Weltweite Bounds
        lat_min, lat_max = -90, 90
        lon_min, lon_max = -180, 180
        
        # Erstelle Grid
        lats = np.arange(lat_min, lat_max + self.resolution, self.resolution)
        lons = np.arange(lon_min, lon_max + self.resolution, self.resolution)
        
        # Meshgrid für alle Kombinationen
        lon_grid, lat_grid = np.meshgrid(lons, lats)
        
        return lat_grid, lon_grid
    
    def calculate_distance_weights(
        self,
        point_lat: float,
        point_lon: float,
        known_points: List[Dict],
        power: float = 2.0
    ) -> np.ndarray:
        """
        Berechne Distanz-Gewichte für Interpolation
        Verwendet inverse Distanz-Gewichtung (IDW)
        """
        distances = []
        for known in known_points:
            # Haversine-Distanz (ungefähr)
            lat_diff = point_lat - known['lat']
            lon_diff = point_lon - known['lon']
            # Vereinfachte Distanz (in Grad)
            dist = np.sqrt(lat_diff**2 + lon_diff**2)
            distances.append(max(dist, 0.01))  # Vermeide Division durch 0
        
        distances = np.array(distances)
        
        # Inverse Distanz-Gewichtung
        weights = 1.0 / (distances ** power)
        weights = weights / weights.sum()  # Normalisiere
        
        return weights
    
    def interpolate_risk_score(
        self,
        point_lat: float,
        point_lon: float,
        known_points: List[Dict]
    ) -> Tuple[float, float]:
        """
        Interpoliere Risiko-Score für einen Punkt
        Returns: (risk_score, distance_to_nearest)
        """
        if not known_points:
            return 0.0, float('inf')
        
        # Finde nächsten bekannten Punkt
        distances = []
        for known in known_points:
            lat_diff = point_lat - known['lat']
            lon_diff = point_lon - known['lon']
            dist = np.sqrt(lat_diff**2 + lon_diff**2)
            distances.append(dist)
        
        min_distance = min(distances)
        
        # Wenn zu weit entfernt, verwende niedriges Risiko
        if min_distance > self.max_interpolation_distance:
            return 0.1, min_distance
        
        # Interpolation basierend auf Methode
        if self.interpolation_method == 'rbf':
            # Radial Basis Function Interpolation
            known_lats = np.array([p['lat'] for p in known_points])
            known_lons = np.array([p['lon'] for p in known_points])
            known_scores = np.array([p['risk_score'] for p in known_points])
            
            try:
                # Verwende RBF Interpolator
                rbf = RBFInterpolator(
                    np.column_stack([known_lats, known_lons]),
                    known_scores,
                    kernel='gaussian',
                    epsilon=2.0  # Smoothing parameter
                )
                interpolated_score = rbf([[point_lat, point_lon]])[0]
                interpolated_score = np.clip(interpolated_score, 0.0, 1.0)
                return float(interpolated_score), min_distance
            except:
                # Fallback zu IDW
                weights = self.calculate_distance_weights(point_lat, point_lon, known_points)
                risk_score = np.sum([p['risk_score'] * w for p, w in zip(known_points, weights)])
                return float(risk_score), min_distance
        
        elif self.interpolation_method == 'idw':
            # Inverse Distance Weighting
            weights = self.calculate_distance_weights(point_lat, point_lon, known_points)
            risk_score = np.sum([p['risk_score'] * w for p, w in zip(known_points, weights)])
            return float(risk_score), min_distance
        
        else:
            # Linear/Cubic Interpolation (scipy)
            known_lats = np.array([p['lat'] for p in known_points])
            known_lons = np.array([p['lon'] for p in known_points])
            known_scores = np.array([p['risk_score'] for p in known_points])
            
            interpolated = griddata(
                (known_lats, known_lons),
                known_scores,
                (point_lat, point_lon),
                method=self.interpolation_method if self.interpolation_method in ['linear', 'cubic'] else 'linear',
                fill_value=0.1  # Default für Punkte außerhalb
            )
            
            if np.isnan(interpolated):
                return 0.1, min_distance
            
            return float(interpolated), min_distance
    
    def get_risk_level(self, risk_score: float) -> str:
        """Konvertiere Risk Score zu Risk Level"""
        if risk_score >= self.risk_thresholds['CRITICAL']:
            return 'CRITICAL'
        elif risk_score >= self.risk_thresholds['HIGH']:
            return 'HIGH'
        elif risk_score >= self.risk_thresholds['MEDIUM']:
            return 'MEDIUM'
        elif risk_score >= self.risk_thresholds['LOW']:
            return 'LOW'
        else:
            return 'MINIMAL'
    
    def generate_raster(
        self,
        locations: Optional[List[Dict]] = None,
        bounds: Optional[Dict] = None
    ) -> Dict:
        """
        Generiere Risiko-Raster für die Weltkarte
        
        Args:
            locations: Liste von Locations mit lat, lon, risk_score
            bounds: Optional {'lat_min', 'lat_max', 'lon_min', 'lon_max'}
        
        Returns:
            Dictionary mit Raster-Daten
        """
        console.print("[bold green]🌍 Generiere Risiko-Raster...[/bold green]")
        
        # Lade Daten falls nicht bereitgestellt
        if locations is None:
            locations = self.load_location_data()
        
        console.print(f"[cyan]📊 {len(locations)} bekannte Locations gefunden[/cyan]")
        
        # Setze Bounds
        if bounds is None:
            bounds = {
                'lat_min': -90,
                'lat_max': 90,
                'lon_min': -180,
                'lon_max': 180
            }
        
        # Erstelle Grid
        lat_grid, lon_grid = self.create_raster_grid()
        
        # Filtere Grid nach Bounds
        mask = (
            (lat_grid >= bounds['lat_min']) &
            (lat_grid <= bounds['lat_max']) &
            (lon_grid >= bounds['lon_min']) &
            (lon_grid <= bounds['lon_max'])
        )
        
        # Berechne Risiko-Scores für jeden Grid-Punkt
        risk_grid = np.zeros_like(lat_grid)
        distance_grid = np.full_like(lat_grid, np.inf)
        
        grid_points = []
        total_points = np.sum(mask)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%")
        ) as progress:
            task = progress.add_task("Berechne Risiko-Scores...", total=total_points)
            
            for i in range(lat_grid.shape[0]):
                for j in range(lon_grid.shape[1]):
                    if not mask[i, j]:
                        continue
                    
                    lat = lat_grid[i, j]
                    lon = lon_grid[i, j]
                    
                    # Interpoliere Risiko-Score
                    risk_score, distance = self.interpolate_risk_score(lat, lon, locations)
                    
                    risk_grid[i, j] = risk_score
                    distance_grid[i, j] = distance
                    
                    grid_points.append({
                        'lat': float(lat),
                        'lon': float(lon),
                        'risk_score': float(risk_score),
                        'risk_level': self.get_risk_level(risk_score),
                        'distance_to_nearest': float(distance)
                    })
                    
                    progress.update(task, advance=1)
        
        console.print(f"[green]✅ Raster generiert: {len(grid_points)} Punkte[/green]")
        
        # Berechne Contour-Linien für verschiedene Risiko-Level
        contours = self.calculate_contours(lat_grid, lon_grid, risk_grid, mask)
        
        return {
            'raster': {
                'lats': lat_grid.tolist(),
                'lons': lon_grid.tolist(),
                'risk_scores': risk_grid.tolist(),
                'distances': distance_grid.tolist()
            },
            'points': grid_points,
            'contours': contours,
            'metadata': {
                'resolution': self.resolution,
                'interpolation_method': self.interpolation_method,
                'total_points': len(grid_points),
                'known_locations': len(locations),
                'bounds': bounds
            }
        }
    
    def calculate_contours(
        self,
        lat_grid: np.ndarray,
        lon_grid: np.ndarray,
        risk_grid: np.ndarray,
        mask: np.ndarray
    ) -> List[Dict]:
        """
        Berechne Iso-Risk Contour-Linien
        Analog zu Höhenlinien in der Geographie
        """
        from matplotlib import contour
        
        console.print("[cyan]📐 Berechne Contour-Linien...[/cyan]")
        
        # Filtere Grid mit Mask
        masked_risk = np.ma.masked_array(risk_grid, mask=~mask)
        
        # Definiere Contour-Levels für jedes Risiko-Level
        contour_levels = {
            'CRITICAL': [0.8, 0.85, 0.9, 0.95],
            'HIGH': [0.6, 0.65, 0.7, 0.75],
            'MEDIUM': [0.4, 0.45, 0.5, 0.55],
            'LOW': [0.2, 0.25, 0.3, 0.35],
            'MINIMAL': [0.0, 0.05, 0.1, 0.15]
        }
        
        contours_data = []
        
        # Berechne Contours für jedes Level
        for level_name, levels in contour_levels.items():
            try:
                cs = contour.contour(
                    lon_grid,
                    lat_grid,
                    masked_risk,
                    levels=levels
                )
                
                for i, level in enumerate(levels):
                    paths = cs.collections[i].get_paths()
                    
                    for path in paths:
                        vertices = path.vertices
                        if len(vertices) > 0:
                            contours_data.append({
                                'level': level_name,
                                'risk_value': float(level),
                                'coordinates': [
                                    {'lat': float(v[1]), 'lon': float(v[0])}
                                    for v in vertices
                                ]
                            })
            except Exception as e:
                console.print(f"[yellow]⚠️  Contour für {level_name} fehlgeschlagen: {e}[/yellow]")
                continue
        
        console.print(f"[green]✅ {len(contours_data)} Contour-Linien berechnet[/green]")
        
        return contours_data
    
    def _calculate_simple_contours(
        self,
        lat_grid: np.ndarray,
        lon_grid: np.ndarray,
        risk_grid: np.ndarray,
        mask: np.ndarray
    ) -> List[Dict]:
        """
        Vereinfachte Contour-Berechnung ohne Matplotlib
        Erstellt Iso-Risk-Linien durch Thresholding
        """
        contours_data = []
        
        # Definiere Threshold-Levels
        threshold_levels = {
            'CRITICAL': 0.8,
            'HIGH': 0.6,
            'MEDIUM': 0.4,
            'LOW': 0.2
        }
        
        for level_name, threshold in threshold_levels.items():
            # Finde Punkte nahe dem Threshold (±0.05)
            threshold_mask = (risk_grid >= threshold - 0.05) & (risk_grid <= threshold + 0.05) & mask
            
            # Extrahiere Koordinaten
            contour_points = []
            for i in range(lat_grid.shape[0]):
                for j in range(lon_grid.shape[1]):
                    if threshold_mask[i, j]:
                        contour_points.append({
                            'lat': float(lat_grid[i, j]),
                            'lon': float(lon_grid[i, j])
                        })
            
            if contour_points:
                # Gruppiere Punkte in Linien (vereinfacht)
                contours_data.append({
                    'level': level_name,
                    'risk_value': float(threshold),
                    'coordinates': contour_points[:100]  # Limit für Performance
                })
        
        return contours_data
    
    def export_geojson(
        self,
        raster_data: Dict,
        output_file: Path
    ):
        """Exportiere Raster als GeoJSON"""
        console.print(f"[cyan]💾 Exportiere GeoJSON: {output_file}[/cyan]")
        
        # Erstelle GeoJSON Features für Raster-Punkte
        features = []
        
        for point in raster_data['points']:
            # Überspringe Punkte mit sehr niedrigem Risiko und großer Distanz
            if point['risk_score'] < 0.1 and point['distance_to_nearest'] > 10:
                continue
            
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [point['lon'], point['lat']]
                },
                'properties': {
                    'risk_score': point['risk_score'],
                    'risk_level': point['risk_level'],
                    'distance_to_nearest': point['distance_to_nearest']
                }
            }
            features.append(feature)
        
        # Füge Contour-Linien hinzu
        for contour in raster_data['contours']:
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'LineString',
                    'coordinates': [
                        [c['lon'], c['lat']] for c in contour['coordinates']
                    ]
                },
                'properties': {
                    'level': contour['level'],
                    'risk_value': contour['risk_value'],
                    'type': 'iso_risk_contour'
                }
            }
            features.append(feature)
        
        geojson = {
            'type': 'FeatureCollection',
            'features': features,
            'metadata': raster_data['metadata']
        }
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(geojson, f, indent=2)
        
        console.print(f"[green]✅ GeoJSON exportiert: {len(features)} Features[/green]")


async def main():
    """Hauptfunktion"""
    console.print("[bold green]🌍 Risk Raster Generator[/bold green]")
    console.print("[cyan]Basierend auf Jones & Furnas (1987) - Iso-Similarity Contours[/cyan]\n")
    
    # Erstelle Generator
    generator = RiskRasterGenerator(
        resolution=1.0,  # 1 Grad ≈ 111km
        interpolation_method='rbf',  # Radial Basis Function
        max_interpolation_distance=10.0  # Max 10 Grad für Interpolation
    )
    
    # Generiere Raster
    raster_data = generator.generate_raster()
    
    # Exportiere GeoJSON
    output_file = Path("./data/frontend/risk_raster.geojson")
    generator.export_geojson(raster_data, output_file)
    
    # Zeige Statistiken
    console.print("\n[bold cyan]📊 Statistiken:[/bold cyan]")
    console.print(f"  Raster-Punkte: {len(raster_data['points'])}")
    console.print(f"  Contour-Linien: {len(raster_data['contours'])}")
    console.print(f"  Resolution: {raster_data['metadata']['resolution']}°")
    
    # Risiko-Verteilung
    risk_distribution = {}
    for point in raster_data['points']:
        level = point['risk_level']
        risk_distribution[level] = risk_distribution.get(level, 0) + 1
    
    console.print("\n[bold cyan]📈 Risiko-Verteilung:[/bold cyan]")
    for level, count in sorted(risk_distribution.items(), key=lambda x: x[1], reverse=True):
        console.print(f"  {level}: {count} Punkte")


if __name__ == "__main__":
    asyncio.run(main())

