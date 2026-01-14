"""
Risk Modeling Engine - IPCC Framework Risk Calculation
Formula: Risk = Hazard × Exposure × Vulnerability
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from context_tensor_engine import ContextTensor
import numpy as np


@dataclass
class RiskScores:
    """Risk scores for an H3 cell"""
    hazard: float  # 0-100
    exposure: float  # 0-100
    vulnerability: float  # 0-100
    total_risk: float  # 0-100 (Hazard × Exposure × Vulnerability / 10000)


class RiskModelingEngine:
    """Engine for calculating climate risk using IPCC framework"""
    
    def __init__(self):
        """Initialize the Risk Modeling Engine"""
        pass
    
    def calculate_hazard(
        self,
        tensor: ContextTensor
    ) -> float:
        """
        Calculate hazard component (0-100)
        
        Args:
            tensor: ContextTensor object
        
        Returns:
            Hazard score (0-100)
        """
        climate = tensor.dimensions.get('climate')
        geography = tensor.dimensions.get('geography')
        
        if not climate or not geography:
            return 30.0  # Default moderate hazard
        
        # Base hazard from climate
        hazard = 0.0
        
        # Temperature extremes
        if climate.temp_max > 35:
            hazard += 20
        elif climate.temp_max > 30:
            hazard += 10
        
        # Precipitation extremes
        if climate.precipitation > 200:
            hazard += 15  # Flood risk
        elif climate.precipitation < 50:
            hazard += 15  # Drought risk
        
        # Extreme events
        hazard += climate.extreme_events_frequency * 30
        hazard += climate.extreme_events_intensity * 20
        
        # Geographic factors
        if geography.coastal_proximity < 10:  # Within 10km of coast
            hazard += 15  # Sea level rise, storm surge
        
        if geography.elevation < 5:  # Low elevation
            hazard += 10  # Flood risk
        
        # Air quality
        if climate.air_quality_pm25 > 25:
            hazard += 5
        
        return min(100.0, hazard)
    
    def calculate_exposure(
        self,
        tensor: ContextTensor
    ) -> float:
        """
        Calculate exposure component (0-100)
        
        Args:
            tensor: ContextTensor object
        
        Returns:
            Exposure score (0-100)
        """
        socio = tensor.dimensions.get('socioeconomic')
        infra = tensor.dimensions.get('infrastructure')
        
        if not socio or not infra:
            return 50.0  # Default moderate exposure
        
        exposure = 0.0
        
        # Population density (higher = more exposure)
        exposure += min(50.0, socio.population_density / 20)
        
        # Infrastructure density (higher = more exposure)
        exposure += min(30.0, infra.road_density * 5)
        
        # Critical infrastructure proximity
        if infra.hospital_proximity < 5:  # Within 5km
            exposure += 10  # Critical infrastructure nearby
        
        # Economic activity (GDP per capita as proxy)
        if socio.gdp_per_capita > 50000:
            exposure += 10  # High economic value at risk
        
        return min(100.0, exposure)
    
    def calculate_vulnerability(
        self,
        tensor: ContextTensor
    ) -> float:
        """
        Calculate vulnerability component (0-100)
        
        Args:
            tensor: ContextTensor object
        
        Returns:
            Vulnerability score (0-100)
        """
        vuln = tensor.dimensions.get('vulnerability')
        socio = tensor.dimensions.get('socioeconomic')
        infra = tensor.dimensions.get('infrastructure')
        
        if not vuln:
            return 50.0  # Default moderate vulnerability
        
        vulnerability = 0.0
        
        # Social vulnerability
        vulnerability += vuln.social_vulnerability_index * 30
        
        # Governance quality (inverse - poor governance = higher vulnerability)
        vulnerability += (1 - vuln.governance_quality) * 25
        
        # Financial access (inverse)
        vulnerability += (1 - vuln.financial_access) * 20
        
        # Health system quality (inverse)
        vulnerability += (1 - vuln.health_system_quality) * 15
        
        # Socioeconomic factors
        if socio:
            # Poverty increases vulnerability
            vulnerability += socio.poverty_rate * 0.5
            
            # Low education increases vulnerability
            vulnerability += (100 - socio.education_level) * 0.2
        
        # Infrastructure gaps
        if infra:
            # Poor infrastructure increases vulnerability
            vulnerability += (100 - infra.water_infrastructure * 100) * 0.1
        
        return min(100.0, vulnerability)
    
    def calculate_total_risk(
        self,
        tensor: ContextTensor
    ) -> RiskScores:
        """
        Calculate total risk using IPCC formula: Risk = Hazard × Exposure × Vulnerability
        
        Args:
            tensor: ContextTensor object
        
        Returns:
            RiskScores object
        """
        hazard = self.calculate_hazard(tensor)
        exposure = self.calculate_exposure(tensor)
        vulnerability = self.calculate_vulnerability(tensor)
        
        # IPCC formula: Risk = Hazard × Exposure × Vulnerability
        # Normalize to 0-100 scale
        raw_risk = (hazard * exposure * vulnerability) / 10000
        
        # Apply power scaling for better distribution
        total_risk = min(100.0, np.power(raw_risk, 0.7) * 100)
        
        return RiskScores(
            hazard=hazard,
            exposure=exposure,
            vulnerability=vulnerability,
            total_risk=total_risk
        )
    
    def calculate_risk_for_cell(
        self,
        tensor: ContextTensor
    ) -> Dict[str, float]:
        """
        Calculate risk for a single cell and return as dictionary
        
        Args:
            tensor: ContextTensor object
        
        Returns:
            Dictionary with risk scores
        """
        scores = self.calculate_total_risk(tensor)
        
        return {
            'hazard': scores.hazard,
            'exposure': scores.exposure,
            'vulnerability': scores.vulnerability,
            'total_risk': scores.total_risk
        }
    
    def calculate_risk_for_grid(
        self,
        tensors: List[ContextTensor]
    ) -> List[Dict[str, float]]:
        """
        Calculate risk for multiple cells
        
        Args:
            tensors: List of ContextTensor objects
        
        Returns:
            List of risk score dictionaries
        """
        return [
            self.calculate_risk_for_cell(tensor)
            for tensor in tensors
        ]
    
    def normalize_scores(
        self,
        scores: List[Dict[str, float]]
    ) -> List[Dict[str, float]]:
        """
        Normalize risk scores across a grid (0-100)
        
        Args:
            scores: List of risk score dictionaries
        
        Returns:
            Normalized scores
        """
        if not scores:
            return []
        
        # Find min/max for each component
        hazards = [s['hazard'] for s in scores]
        exposures = [s['exposure'] for s in scores]
        vulnerabilities = [s['vulnerability'] for s in scores]
        total_risks = [s['total_risk'] for s in scores]
        
        def normalize_value(value, min_val, max_val):
            if max_val == min_val:
                return 50.0
            return ((value - min_val) / (max_val - min_val)) * 100
        
        normalized = []
        for score in scores:
            normalized.append({
                'hazard': normalize_value(score['hazard'], min(hazards), max(hazards)),
                'exposure': normalize_value(score['exposure'], min(exposures), max(exposures)),
                'vulnerability': normalize_value(score['vulnerability'], min(vulnerabilities), max(vulnerabilities)),
                'total_risk': normalize_value(score['total_risk'], min(total_risks), max(total_risks))
            })
        
        return normalized


# Example usage
if __name__ == '__main__':
    from context_tensor_engine import ContextTensor, ClimateDimension, GeographyDimension, SocioeconomicDimension, InfrastructureDimension, VulnerabilityDimension
    
    engine = RiskModelingEngine()
    
    # Create test tensor
    tensor = ContextTensor(
        h3_index="87194e64dffffff",
        timestamp=None
    )
    tensor.dimensions['climate'] = ClimateDimension(
        temp_max=35.0,
        precipitation=150.0,
        extreme_events_frequency=0.3
    )
    tensor.dimensions['geography'] = GeographyDimension(
        elevation=10.0,
        coastal_proximity=5.0
    )
    tensor.dimensions['socioeconomic'] = SocioeconomicDimension(
        population_density=2000.0,
        gdp_per_capita=30000.0
    )
    tensor.dimensions['infrastructure'] = InfrastructureDimension(
        road_density=8.0,
        hospital_proximity=3.0
    )
    tensor.dimensions['vulnerability'] = VulnerabilityDimension(
        social_vulnerability_index=0.6,
        governance_quality=0.5
    )
    
    # Calculate risk
    risk_scores = engine.calculate_total_risk(tensor)
    print(f"Hazard: {risk_scores.hazard:.1f}")
    print(f"Exposure: {risk_scores.exposure:.1f}")
    print(f"Vulnerability: {risk_scores.vulnerability:.1f}")
    print(f"Total Risk: {risk_scores.total_risk:.1f}")


