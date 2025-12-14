"""
Risk Calculation Engine
Computes context tensors and risk scores for H3 cells
"""
import random
from typing import Dict, Any, List
import h3

from models.schemas import ContextTensor, RiskScores, Scenario, EventType
from loguru import logger


class RiskEngine:
    """
    Risk calculation using the formula:
    Risk = Hazard × Exposure × Vulnerability
    
    Each dimension is calculated from the context tensor.
    """
    
    # Scenario multipliers (IPCC-based)
    SCENARIO_FACTORS = {
        Scenario.SSP1_26: {"climate": 1.1, "hazard": 0.9},
        Scenario.SSP2_45: {"climate": 1.5, "hazard": 1.2},
        Scenario.SSP3_70: {"climate": 2.0, "hazard": 1.6},
        Scenario.SSP5_85: {"climate": 2.5, "hazard": 2.0},
        Scenario.BASELINE: {"climate": 1.0, "hazard": 1.0}
    }
    
    # Land use risk modifiers
    LAND_USE_RISK = {
        "Urban": 1.5,
        "Suburban": 1.2,
        "Industrial": 1.4,
        "Agricultural": 1.1,
        "Forest": 0.8,
        "Water": 0.3,
        "Desert": 0.9,
        "Unknown": 1.0
    }
    
    async def calculate_tensor(
        self,
        h3_index: str,
        lat: float,
        lon: float,
        scenario: Scenario,
        year: int
    ) -> ContextTensor:
        """
        Calculate full context tensor for an H3 cell.
        In production, this would query real data sources.
        """
        # Get scenario factors
        factors = self.SCENARIO_FACTORS.get(scenario, self.SCENARIO_FACTORS[Scenario.BASELINE])
        year_factor = 1 + (year - 2025) * 0.02  # 2% increase per year
        
        # Simulate data (replace with real data queries in production)
        tensor = ContextTensor()
        
        # Climate dimension
        tensor.climate.temperature_anomaly = random.uniform(0.5, 3.0) * factors["climate"] * year_factor
        tensor.climate.precipitation_change = random.uniform(-30, 30) * factors["climate"]
        tensor.climate.sea_level_rise = random.uniform(0, 50) * factors["climate"] * year_factor
        tensor.climate.extreme_events_frequency = random.uniform(1, 5) * factors["hazard"]
        
        # Geography dimension (based on coordinates)
        tensor.geography.elevation = self._estimate_elevation(lat, lon)
        tensor.geography.land_use = self._estimate_land_use(lat, lon)
        tensor.geography.water_body = tensor.geography.elevation < 5 and random.random() < 0.3
        tensor.geography.coastal = abs(lat) < 60 and random.random() < 0.2
        
        # Socio-economic dimension
        tensor.socio.population_density = random.uniform(100, 10000)
        tensor.socio.gdp_per_capita = random.uniform(1000, 50000)
        tensor.socio.poverty_rate = random.uniform(5, 50)
        
        # Infrastructure dimension
        tensor.infrastructure.road_density = random.uniform(10, 100)
        tensor.infrastructure.hospital_access = random.uniform(20, 95)
        tensor.infrastructure.shelter_capacity = random.uniform(10, 80)
        
        # Vulnerability dimension
        tensor.vulnerability.governance_index = random.uniform(20, 90)
        tensor.vulnerability.adaptation_capacity = random.uniform(20, 80)
        tensor.vulnerability.historical_events = random.randint(0, 10)
        
        # Calculate risk scores
        tensor.scores = self._calculate_scores(tensor, factors)
        
        return tensor
    
    def _calculate_scores(self, tensor: ContextTensor, factors: Dict[str, float]) -> RiskScores:
        """Calculate risk scores from tensor dimensions"""
        
        # Hazard score (from climate and geography)
        hazard = (
            tensor.climate.temperature_anomaly * 10 +
            abs(tensor.climate.precipitation_change) * 0.5 +
            tensor.climate.extreme_events_frequency * 10 +
            (50 if tensor.geography.coastal else 0)
        ) * factors["hazard"]
        hazard = min(100, max(0, hazard))
        
        # Exposure score (from socio-economic and infrastructure)
        land_use_factor = self.LAND_USE_RISK.get(tensor.geography.land_use, 1.0)
        exposure = (
            min(tensor.socio.population_density / 100, 50) +
            (100 - tensor.infrastructure.hospital_access) * 0.3 +
            (100 - tensor.infrastructure.shelter_capacity) * 0.2
        ) * land_use_factor
        exposure = min(100, max(0, exposure))
        
        # Vulnerability score (from governance and adaptation)
        vulnerability = (
            (100 - tensor.vulnerability.governance_index) * 0.4 +
            (100 - tensor.vulnerability.adaptation_capacity) * 0.4 +
            tensor.vulnerability.historical_events * 2
        )
        vulnerability = min(100, max(0, vulnerability))
        
        # Total risk (multiplicative model normalized)
        total_risk = (hazard * exposure * vulnerability) ** (1/3)  # Geometric mean
        total_risk = min(100, max(0, total_risk))
        
        return RiskScores(
            total_risk=round(total_risk, 1),
            hazard=round(hazard, 1),
            exposure=round(exposure, 1),
            vulnerability=round(vulnerability, 1)
        )
    
    def _estimate_elevation(self, lat: float, lon: float) -> float:
        """Estimate elevation (simplified)"""
        # In production: query DEM data
        return max(0, random.gauss(100, 50))
    
    def _estimate_land_use(self, lat: float, lon: float) -> str:
        """Estimate land use (simplified)"""
        # In production: query land use data
        options = ["Urban", "Suburban", "Agricultural", "Forest", "Desert"]
        weights = [0.2, 0.2, 0.3, 0.2, 0.1]
        return random.choices(options, weights=weights)[0]
    
    def generate_actions(self, tensor: ContextTensor) -> List[Dict[str, Any]]:
        """Generate recommended actions based on risk profile"""
        actions = []
        scores = tensor.scores
        
        # High hazard actions
        if scores.hazard > 60:
            actions.append({
                "icon": "🌊",
                "title": "Early Warning System",
                "type": "INFRASTRUCTURE",
                "cost": random.randint(50000, 200000),
                "timeline": "6-12 months",
                "impact": "Reduces casualties by 40%"
            })
        
        # High exposure actions
        if scores.exposure > 60:
            actions.append({
                "icon": "🏥",
                "title": "Emergency Shelter Network",
                "type": "HUMANITARIAN",
                "cost": random.randint(100000, 500000),
                "timeline": "12-24 months",
                "impact": "Protects 10,000+ people"
            })
        
        # High vulnerability actions
        if scores.vulnerability > 60:
            actions.append({
                "icon": "📚",
                "title": "Community Resilience Training",
                "type": "CAPACITY",
                "cost": random.randint(20000, 80000),
                "timeline": "3-6 months",
                "impact": "Builds local response capability"
            })
        
        # Critical risk actions
        if scores.total_risk > 70:
            actions.append({
                "icon": "🚨",
                "title": "Emergency Evacuation Plan",
                "type": "EMERGENCY",
                "cost": random.randint(30000, 100000),
                "timeline": "1-3 months",
                "impact": "Critical life-saving measure"
            })
            actions.append({
                "icon": "🌱",
                "title": "Nature-Based Solutions",
                "type": "ADAPTATION",
                "cost": random.randint(200000, 1000000),
                "timeline": "24-48 months",
                "impact": "Long-term risk reduction 30%"
            })
        
        # Always include baseline action
        if not actions:
            actions.append({
                "icon": "📊",
                "title": "Continuous Monitoring",
                "type": "MONITORING",
                "cost": random.randint(5000, 20000),
                "timeline": "Ongoing",
                "impact": "Maintains situational awareness"
            })
        
        return actions

