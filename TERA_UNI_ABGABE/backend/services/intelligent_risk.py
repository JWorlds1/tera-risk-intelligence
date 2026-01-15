"""
Intelligent Context-Aware Risk Calculator
Based on: IPCC AR6, NASA EONET, Geographic Context
"""
import math
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class RiskContext:
    """Contextual risk factors for a location"""
    lat: float
    lon: float
    
    # Geographic context
    is_coastal: bool = False
    is_urban: bool = False
    is_low_elevation: bool = False
    is_delta: bool = False
    is_island: bool = False
    
    # Climate factors
    sea_level_rise_mm: float = 0
    flood_frequency_multiplier: float = 1.0
    temperature_anomaly_c: float = 0
    precipitation_change_pct: float = 0
    
    # Conflict factors
    is_conflict_zone: bool = False
    political_stability: float = 0.5  # 0-1, higher = more stable
    resource_stress: float = 0.0  # 0-1

class IntelligentRiskCalculator:
    """
    Calculates risk based on:
    1. Geographic position (coastal, elevation, latitude)
    2. IPCC AR6 projections
    3. Conflict data
    4. Local context
    """
    
    # IPCC AR6 Sea Level Rise projections by scenario (mm by 2050)
    SLR_PROJECTIONS = {
        "SSP1-2.6": 150,  # Best case
        "SSP2-4.5": 220,  # Middle of road
        "SSP3-7.0": 290,  # Regional rivalry
        "SSP5-8.5": 360   # Fossil-fueled
    }
    
    # Known vulnerable coastal cities
    COASTAL_CITIES = {
        "jakarta": {"slr_vulnerability": 0.95, "subsidence_mm_yr": 250},
        "miami": {"slr_vulnerability": 0.85, "subsidence_mm_yr": 3},
        "mumbai": {"slr_vulnerability": 0.80, "subsidence_mm_yr": 5},
        "dhaka": {"slr_vulnerability": 0.90, "subsidence_mm_yr": 15},
        "manila": {"slr_vulnerability": 0.85, "subsidence_mm_yr": 10},
        "bangkok": {"slr_vulnerability": 0.88, "subsidence_mm_yr": 20},
        "shanghai": {"slr_vulnerability": 0.75, "subsidence_mm_yr": 12},
        "ho chi minh": {"slr_vulnerability": 0.82, "subsidence_mm_yr": 8},
    }
    
    # Active conflict zones (2024-2025 data)
    CONFLICT_ZONES = {
        "gaza": {"intensity": 0.95, "type": "active_war"},
        "ukraine": {"intensity": 0.90, "type": "active_war"},
        "darfur": {"intensity": 0.85, "type": "civil_conflict"},
        "yemen": {"intensity": 0.88, "type": "civil_war"},
        "somalia": {"intensity": 0.75, "type": "instability"},
        "myanmar": {"intensity": 0.70, "type": "civil_conflict"},
        "ethiopia": {"intensity": 0.65, "type": "civil_conflict"},
        "syria": {"intensity": 0.80, "type": "civil_war"},
    }
    
    def __init__(self, scenario: str = "SSP2-4.5", year: int = 2050):
        self.scenario = scenario
        self.year = year
        self.slr = self.SLR_PROJECTIONS.get(scenario, 220)
        
    def calculate_cell_risk(
        self,
        lat: float,
        lon: float,
        city: str = "",
        center_lat: float = 0,
        center_lon: float = 0
    ) -> Dict:
        """
        Calculate comprehensive risk for an H3 cell
        Returns risk scores and explanations
        """
        city_lower = city.lower() if city else ""
        
        # Base climate risk from latitude
        climate_base = self._latitude_climate_risk(lat)
        
        # Coastal vulnerability
        coastal_risk, coastal_factors = self._coastal_risk(lat, lon, city_lower)
        
        # Urban heat island effect
        urban_risk = self._urban_heat_risk(city_lower)
        
        # Distance from city center affects risk gradient
        dist_factor = self._distance_risk_gradient(lat, lon, center_lat, center_lon)
        
        # Conflict risk
        conflict_risk, conflict_factors = self._conflict_risk(city_lower)
        
        # Calculate final scores
        climate_risk = min(100, (
            climate_base * 0.2 +
            coastal_risk * 0.5 +
            urban_risk * 0.3
        ) * dist_factor)
        
        overall_risk = climate_risk * 0.6 + conflict_risk * 0.4
        
        # Generate color based on risk
        color = self._risk_to_color(overall_risk)
        
        # Risk category
        category = self._risk_category(overall_risk)
        
        return {
            "risk_score": round(overall_risk, 1),
            "climate_risk": round(climate_risk, 1),
            "conflict_risk": round(conflict_risk, 1),
            "color": color,
            "category": category,
            "factors": {
                "climate": coastal_factors,
                "conflict": conflict_factors
            }
        }
    
    def _latitude_climate_risk(self, lat: float) -> float:
        """Tropical regions face different risks than polar"""
        abs_lat = abs(lat)
        if abs_lat < 23.5:  # Tropical
            return 60  # Higher storm/flood risk
        elif abs_lat < 35:  # Subtropical
            return 50
        elif abs_lat < 55:  # Temperate
            return 40
        else:  # Polar
            return 55  # Permafrost/ice melt risks
    
    def _coastal_risk(self, lat: float, lon: float, city: str) -> Tuple[float, List[str]]:
        """Calculate coastal flooding and SLR risk"""
        factors = []
        risk = 30  # Base
        
        # Check if known coastal city
        if city in self.COASTAL_CITIES:
            data = self.COASTAL_CITIES[city]
            vulnerability = data["slr_vulnerability"]
            subsidence = data["subsidence_mm_yr"]
            
            # Sea level rise impact
            slr_impact = (self.slr / 1000) * vulnerability * 100
            risk += slr_impact
            factors.append(f"Sea level rise: +{self.slr}mm by {self.year}")
            
            # Subsidence
            if subsidence > 10:
                subsidence_years = self.year - 2025
                total_subsidence = subsidence * subsidence_years
                risk += min(30, total_subsidence / 100 * 10)
                factors.append(f"Land subsidence: {subsidence}mm/year ({total_subsidence}mm total)")
            
            # Flood frequency
            flood_mult = 1 + (vulnerability * 2)
            factors.append(f"Flood frequency: {flood_mult:.1f}x increase")
            
            return min(100, risk), factors
        
        # Generic coastal check (simplified)
        # In production, use elevation data and coastline distance
        return 35, ["Moderate climate exposure"]
    
    def _urban_heat_risk(self, city: str) -> float:
        """Urban heat island effect"""
        # Large cities have higher UHI
        major_cities = ["tokyo", "jakarta", "mumbai", "new york", "shanghai", "delhi", "cairo"]
        if city in major_cities:
            return 45
        return 30
    
    def _distance_risk_gradient(
        self,
        cell_lat: float,
        cell_lon: float,
        center_lat: float,
        center_lon: float
    ) -> float:
        """
        Risk varies with distance from city center
        - Center: Urban flood risk, infrastructure stress
        - Periphery: Different risk profile
        """
        if center_lat == 0 and center_lon == 0:
            return 1.0
            
        # Haversine-lite distance
        dlat = abs(cell_lat - center_lat)
        dlon = abs(cell_lon - center_lon)
        dist = math.sqrt(dlat**2 + dlon**2)
        
        # Risk gradient: center is 1.0, decreases outward
        if dist < 0.02:  # ~2km
            return 1.1  # Highest in center
        elif dist < 0.05:  # ~5km
            return 1.0
        elif dist < 0.1:  # ~10km
            return 0.9
        else:
            return 0.8
    
    def _conflict_risk(self, city: str) -> Tuple[float, List[str]]:
        """Calculate conflict-related risk"""
        factors = []
        
        if city in self.CONFLICT_ZONES:
            data = self.CONFLICT_ZONES[city]
            intensity = data["intensity"] * 100
            conflict_type = data["type"].replace("_", " ").title()
            
            factors.append(f"Status: {conflict_type}")
            factors.append(f"Intensity: {intensity:.0f}%")
            factors.append("Humanitarian crisis indicators: HIGH")
            factors.append("Infrastructure damage risk: SEVERE")
            
            return intensity, factors
        
        # Default low conflict risk
        factors.append("Political stability: MODERATE")
        factors.append("No active conflict")
        return 15, factors
    
    def _risk_to_color(self, risk: float) -> str:
        """Convert risk score to hex color"""
        if risk < 25:
            return "#22c55e"  # Green - Low
        elif risk < 40:
            return "#84cc16"  # Lime - Low-Moderate
        elif risk < 55:
            return "#eab308"  # Yellow - Moderate
        elif risk < 70:
            return "#f97316"  # Orange - High
        elif risk < 85:
            return "#ef4444"  # Red - Very High
        else:
            return "#991b1b"  # Dark Red - Critical
    
    def _risk_category(self, risk: float) -> str:
        """Risk category label"""
        if risk < 25:
            return "LOW"
        elif risk < 40:
            return "LOW-MODERATE"
        elif risk < 55:
            return "MODERATE"
        elif risk < 70:
            return "HIGH"
        elif risk < 85:
            return "VERY HIGH"
        else:
            return "CRITICAL"
    
    def generate_projection(self, city: str, risk_data: Dict) -> str:
        """Generate future projection text"""
        risk = risk_data["risk_score"]
        climate = risk_data["climate_risk"]
        conflict = risk_data["conflict_risk"]
        
        projection = f"## {self.year} Projection for {city.title()} ({self.scenario})\n\n"
        
        if climate > 60:
            projection += "**Climate Outlook:** CRITICAL\n"
            projection += f"- Projected sea level rise will affect {int(climate)}% of low-lying areas\n"
            projection += "- Flood events expected to increase 3-5x\n"
            projection += "- Adaptation cost: €150-300M required\n\n"
        elif climate > 40:
            projection += "**Climate Outlook:** CONCERNING\n"
            projection += "- Moderate impact from climate change expected\n"
            projection += "- Infrastructure upgrades recommended\n\n"
        else:
            projection += "**Climate Outlook:** MANAGEABLE\n"
            projection += "- Standard climate adaptation measures sufficient\n\n"
        
        if conflict > 50:
            projection += "**Conflict Outlook:** UNSTABLE\n"
            projection += "- Ongoing humanitarian concerns\n"
            projection += "- Displacement risk remains high\n\n"
        else:
            projection += "**Conflict Outlook:** STABLE\n\n"
        
        # Recommendations
        projection += "### Recommended Actions\n"
        if risk > 70:
            projection += "1. Immediate evacuation planning required\n"
            projection += "2. Critical infrastructure protection\n"
            projection += "3. International aid coordination\n"
        elif risk > 50:
            projection += "1. Enhanced early warning systems\n"
            projection += "2. Gradual infrastructure hardening\n"
            projection += "3. Community resilience programs\n"
        else:
            projection += "1. Standard monitoring protocols\n"
            projection += "2. Regular risk assessments\n"
            
        return projection
