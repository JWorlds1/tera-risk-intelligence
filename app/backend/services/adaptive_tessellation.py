"""
Adaptive Tessellation with 2026 Projections
============================================
Generates meaningful H3 hexagon grids with risk-based coloring
"""

import h3
import math
import random
from typing import List, Dict, Tuple
from dataclasses import dataclass


# Risk zone definitions with 2026 projections
RISK_ZONES_2026 = {
    'coastal': {
        'CRITICAL_COASTAL': {
            'risk_range': (0.80, 0.95),
            'color': '#ff0000',
            'description': 'Kritische Küstenzone - Sofortige Maßnahmen 2025',
            'elevation_max': 2,  # meters above sea level
            'weight': 0.15,
        },
        'HIGH_FLOOD': {
            'risk_range': (0.60, 0.79),
            'color': '#ff6600',
            'description': 'Hohes Überschwemmungsrisiko - Anpassung bis 2026',
            'elevation_max': 5,
            'weight': 0.25,
        },
        'MODERATE_RISK': {
            'risk_range': (0.40, 0.59),
            'color': '#ffcc00',
            'description': 'Moderates Risiko - Monitoring erforderlich',
            'elevation_max': 10,
            'weight': 0.35,
        },
        'INLAND_SAFE': {
            'risk_range': (0.15, 0.39),
            'color': '#00ff88',
            'description': 'Inland-Zone - Niedriges Risiko, Klimarefugium',
            'elevation_max': 50,
            'weight': 0.25,
        },
    },
    'arid': {
        'EXTREME_HEAT': {
            'risk_range': (0.80, 0.95),
            'color': '#ff0000',
            'description': 'Extreme Hitze - Lebensbedrohlich ab 2026',
            'weight': 0.20,
        },
        'WATER_STRESS': {
            'risk_range': (0.60, 0.79),
            'color': '#ff8800',
            'description': 'Wasserstress - Rationierung wahrscheinlich',
            'weight': 0.30,
        },
        'DROUGHT_RISK': {
            'risk_range': (0.40, 0.59),
            'color': '#ffcc00',
            'description': 'Dürrerisiko - Landwirtschaft gefährdet',
            'weight': 0.30,
        },
        'OASIS': {
            'risk_range': (0.20, 0.39),
            'color': '#00cc66',
            'description': 'Bewässerte Zone - Stabiler',
            'weight': 0.20,
        },
    },
    'tropical': {
        'CYCLONE_PATH': {
            'risk_range': (0.75, 0.95),
            'color': '#ff0044',
            'description': 'Zyklon-Korridor - Evakuierungsplanung',
            'weight': 0.15,
        },
        'FLOOD_PLAIN': {
            'risk_range': (0.55, 0.74),
            'color': '#ff8800',
            'description': 'Überschwemmungsgebiet - Drainage kritisch',
            'weight': 0.30,
        },
        'MONSOON_ZONE': {
            'risk_range': (0.35, 0.54),
            'color': '#00aaff',
            'description': 'Monsunzone - Saisonale Risiken',
            'weight': 0.35,
        },
        'ELEVATED': {
            'risk_range': (0.15, 0.34),
            'color': '#00ff88',
            'description': 'Höhenlage - Geringeres Risiko',
            'weight': 0.20,
        },
    },
    'temperate': {
        'URBAN_HEAT': {
            'risk_range': (0.50, 0.70),
            'color': '#ff6600',
            'description': 'Urban Heat Island - Hitzewellen 2026',
            'weight': 0.25,
        },
        'FLOOD_RISK': {
            'risk_range': (0.35, 0.49),
            'color': '#00aaff',
            'description': 'Überschwemmungsrisiko - Starkregen',
            'weight': 0.30,
        },
        'MODERATE': {
            'risk_range': (0.20, 0.34),
            'color': '#88cc00',
            'description': 'Moderates Klima - Anpassungsfähig',
            'weight': 0.30,
        },
        'LOW_RISK': {
            'risk_range': (0.10, 0.19),
            'color': '#00ff88',
            'description': 'Niedriges Risiko - Gute Resilienz',
            'weight': 0.15,
        },
    },
    'conflict': {
        'ACTIVE_CONFLICT': {
            'risk_range': (0.85, 0.98),
            'color': '#ff0000',
            'description': 'Aktiver Konflikt - Keine Klimaanpassung möglich',
            'weight': 0.30,
        },
        'HIGH_TENSION': {
            'risk_range': (0.65, 0.84),
            'color': '#cc0066',
            'description': 'Hohe Spannung - Humanitäre Krise',
            'weight': 0.35,
        },
        'UNSTABLE': {
            'risk_range': (0.45, 0.64),
            'color': '#ff8800',
            'description': 'Instabil - Fragiler Frieden',
            'weight': 0.25,
        },
        'BUFFER': {
            'risk_range': (0.25, 0.44),
            'color': '#ffcc00',
            'description': 'Pufferzone - Flüchtlingsströme',
            'weight': 0.10,
        },
    },
    'seismic': {
        'FAULT_LINE': {
            'risk_range': (0.70, 0.90),
            'color': '#9900ff',
            'description': 'Verwerfungslinie - Höchstes Erdbebenrisiko',
            'weight': 0.15,
        },
        'LIQUEFACTION': {
            'risk_range': (0.50, 0.69),
            'color': '#cc66ff',
            'description': 'Verflüssigungszone - Weicher Boden',
            'weight': 0.25,
        },
        'MODERATE_SEISMIC': {
            'risk_range': (0.30, 0.49),
            'color': '#ffcc00',
            'description': 'Moderate seismische Aktivität',
            'weight': 0.35,
        },
        'STABLE_GROUND': {
            'risk_range': (0.10, 0.29),
            'color': '#00cc66',
            'description': 'Stabiler Untergrund',
            'weight': 0.25,
        },
    },
}


class AdaptiveTessellation:
    """Generate adaptive H3 tessellation with 2026 risk projections"""
    
    def __init__(self):
        self.cache = {}
    
    def generate_risk_map(
        self,
        lat: float,
        lon: float,
        risk_type: str,
        resolution: int = 10,
        year: int = 2026,
        radius_km: float = 15.0,
    ) -> List[dict]:
        """Generate risk-colored hexagons for a city"""
        
        # Get zone definitions
        zones = RISK_ZONES_2026.get(risk_type, RISK_ZONES_2026['temperate'])
        
        # Calculate bounding box
        lat_delta = radius_km / 111.0
        lon_delta = radius_km / (111.0 * math.cos(math.radians(lat)))
        
        min_lat = lat - lat_delta
        max_lat = lat + lat_delta
        min_lon = lon - lon_delta
        max_lon = lon + lon_delta
        
        # Generate hexagons
        hexagons = self._fill_bbox(min_lat, min_lon, max_lat, max_lon, resolution)
        
        # Assign zones and create features
        features = []
        zone_counts = {zone: 0 for zone in zones}
        
        for h3_index in hexagons:
            # Get center
            center_lat, center_lon = h3.h3_to_geo(h3_index)
            
            # Calculate distance from city center (for zone assignment)
            dist = math.sqrt((center_lat - lat)**2 + (center_lon - lon)**2)
            normalized_dist = min(1.0, dist / (lat_delta * 1.5))
            
            # Assign zone based on distance and weights
            zone_name, zone_info = self._assign_zone(zones, normalized_dist, center_lat, center_lon)
            zone_counts[zone_name] += 1
            
            # Calculate cell-specific risk (with variation)
            base_risk = (zone_info['risk_range'][0] + zone_info['risk_range'][1]) / 2
            variation = random.uniform(-0.08, 0.08)
            cell_risk = max(0.05, min(0.98, base_risk + variation))
            
            # 2026 adjustment (slight increase for most zones)
            if year >= 2026:
                cell_risk = min(0.98, cell_risk * 1.05)
            
            # Get boundary
            boundary = h3.h3_to_geo_boundary(h3_index, geo_json=True)
            
            # Height based on risk (3D effect)
            height = 50 + cell_risk * 400
            
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [boundary]
                },
                'properties': {
                    'h3': h3_index,
                    'zone': zone_name,
                    'zone_reason': zone_info['description'],
                    'color': zone_info['color'],
                    'intensity': cell_risk,
                    'height': height,
                    'primary_risk': risk_type,
                    'year': year,
                }
            }
            features.append(feature)
        
        return features
    
    def _fill_bbox(
        self, 
        min_lat: float, 
        min_lon: float, 
        max_lat: float, 
        max_lon: float, 
        resolution: int
    ) -> List[str]:
        """Fill bounding box with H3 hexagons"""
        # Create polygon for bbox
        geojson = {
            'type': 'Polygon',
            'coordinates': [[
                [min_lon, min_lat],
                [max_lon, min_lat],
                [max_lon, max_lat],
                [min_lon, max_lat],
                [min_lon, min_lat],
            ]]
        }
        
        try:
            hexagons = list(h3.polyfill_geojson(geojson, resolution))
        except Exception:
            # Fallback: grid approach
            hexagons = []
            lat_step = (max_lat - min_lat) / 50
            lon_step = (max_lon - min_lon) / 50
            for i in range(50):
                for j in range(50):
                    cell_lat = min_lat + i * lat_step
                    cell_lon = min_lon + j * lon_step
                    h3_index = h3.geo_to_h3(cell_lat, cell_lon, resolution)
                    if h3_index not in hexagons:
                        hexagons.append(h3_index)
        
        return hexagons
    
    def _assign_zone(
        self, 
        zones: Dict, 
        normalized_dist: float,
        lat: float,
        lon: float
    ) -> Tuple[str, dict]:
        """Assign zone based on distance and location characteristics"""
        
        # Create weighted random selection based on distance
        zone_list = list(zones.items())
        
        # Sort by risk (high risk near center for coastal, opposite for others)
        zone_list.sort(key=lambda x: x[1]['risk_range'][0], reverse=True)
        
        # Probability based on distance
        if normalized_dist < 0.3:
            # Near center - higher risk zones
            weights = [0.4, 0.3, 0.2, 0.1][:len(zone_list)]
        elif normalized_dist < 0.6:
            # Middle - moderate risk
            weights = [0.2, 0.4, 0.3, 0.1][:len(zone_list)]
        else:
            # Far from center - lower risk
            weights = [0.1, 0.2, 0.3, 0.4][:len(zone_list)]
        
        # Normalize weights
        total = sum(weights)
        weights = [w/total for w in weights]
        
        # Random selection
        r = random.random()
        cumsum = 0
        for i, (name, info) in enumerate(zone_list):
            cumsum += weights[i] if i < len(weights) else 0.1
            if r < cumsum:
                return name, info
        
        return zone_list[-1]

# Global instance
tessellation_service = AdaptiveTessellation()
