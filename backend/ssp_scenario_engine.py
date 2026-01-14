"""
SSP Scenario Engine - Simulates Shared Socioeconomic Pathways (SSP1-5) scenarios
Implements projections for future timepoints (2025-2100) with RCP coupling
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import numpy as np


class SSPScenario(Enum):
    """SSP Scenario types"""
    SSP1 = "SSP1-2.6"  # Sustainability (Green Path)
    SSP2 = "SSP2-4.5"  # Middle of the Road
    SSP3 = "SSP3-7.0"  # Regional Rivalry (Rocky Road)
    SSP4 = "SSP4-6.0"  # Inequality (Divided Path)
    SSP5 = "SSP5-8.5"  # Fossil-fueled Development (Highway)


@dataclass
class SSPProjection:
    """SSP projection for a specific year"""
    scenario: SSPScenario
    year: int
    population_growth: float  # Multiplier
    gdp_growth: float  # Multiplier
    tech_progress: float  # 0-1
    policy_cooperation: float  # 0-1
    adaptation_capacity: float  # 0-1
    mitigation_effort: float  # 0-1
    temperature_increase: float  # Degrees Celsius
    precipitation_change: float  # Percentage change


class SSPScenarioEngine:
    """Engine for SSP scenario simulations"""
    
    # Base year for projections
    BASE_YEAR = 2020
    
    # Scenario parameters (simplified - would use IPCC data in production)
    SCENARIO_PARAMS = {
        SSPScenario.SSP1: {
            'population_growth_rate': 0.005,  # Low growth
            'gdp_growth_rate': 0.02,
            'tech_progress_base': 0.8,
            'policy_cooperation_base': 0.9,
            'adaptation_capacity_base': 0.8,
            'mitigation_effort_base': 0.9,
            'temp_increase_rate': 0.02,  # Low warming
            'precip_change_rate': 0.01
        },
        SSPScenario.SSP2: {
            'population_growth_rate': 0.01,
            'gdp_growth_rate': 0.025,
            'tech_progress_base': 0.6,
            'policy_cooperation_base': 0.6,
            'adaptation_capacity_base': 0.6,
            'mitigation_effort_base': 0.6,
            'temp_increase_rate': 0.03,
            'precip_change_rate': 0.02
        },
        SSPScenario.SSP3: {
            'population_growth_rate': 0.015,
            'gdp_growth_rate': 0.015,
            'tech_progress_base': 0.4,
            'policy_cooperation_base': 0.3,
            'adaptation_capacity_base': 0.4,
            'mitigation_effort_base': 0.3,
            'temp_increase_rate': 0.04,
            'precip_change_rate': 0.03
        },
        SSPScenario.SSP4: {
            'population_growth_rate': 0.012,
            'gdp_growth_rate': 0.02,
            'tech_progress_base': 0.5,
            'policy_cooperation_base': 0.4,
            'adaptation_capacity_base': 0.3,
            'mitigation_effort_base': 0.5,
            'temp_increase_rate': 0.035,
            'precip_change_rate': 0.025
        },
        SSPScenario.SSP5: {
            'population_growth_rate': 0.008,
            'gdp_growth_rate': 0.03,
            'tech_progress_base': 0.9,
            'policy_cooperation_base': 0.7,
            'adaptation_capacity_base': 0.7,
            'mitigation_effort_base': 0.2,  # Low mitigation
            'temp_increase_rate': 0.05,  # High warming
            'precip_change_rate': 0.04
        }
    }
    
    def __init__(self):
        """Initialize the SSP Scenario Engine"""
        pass
    
    def parse_scenario(self, scenario_str: str) -> Optional[SSPScenario]:
        """
        Parse scenario string to SSPScenario enum
        
        Args:
            scenario_str: Scenario string (e.g., "SSP1-2.6", "SSP2-4.5")
        
        Returns:
            SSPScenario or None
        """
        scenario_str = scenario_str.upper()
        for scenario in SSPScenario:
            if scenario.value.startswith(scenario_str.split('-')[0]):
                return scenario
        return None
    
    def project_to_year(
        self,
        scenario: SSPScenario,
        year: int,
        base_values: Optional[Dict[str, float]] = None
    ) -> SSPProjection:
        """
        Project scenario to a specific year
        
        Args:
            scenario: SSP scenario
            year: Target year (2025-2100)
            base_values: Base values for projection (optional)
        
        Returns:
            SSPProjection object
        """
        if year < self.BASE_YEAR:
            year = self.BASE_YEAR
        
        years_ahead = year - self.BASE_YEAR
        params = self.SCENARIO_PARAMS[scenario]
        
        # Project population growth (compound)
        pop_growth = (1 + params['population_growth_rate']) ** years_ahead
        
        # Project GDP growth (compound)
        gdp_growth = (1 + params['gdp_growth_rate']) ** years_ahead
        
        # Project technology progress (sigmoid curve)
        tech_progress = params['tech_progress_base'] + (
            (1 - params['tech_progress_base']) * 
            (1 / (1 + np.exp(-years_ahead / 20)))
        )
        
        # Project policy cooperation (varies by scenario)
        policy_cooperation = params['policy_cooperation_base'] + (
            (1 - params['policy_cooperation_base']) * 
            (years_ahead / 80) * 0.3  # Slow improvement
        )
        policy_cooperation = min(1.0, policy_cooperation)
        
        # Project adaptation capacity
        adaptation_capacity = params['adaptation_capacity_base'] + (
            (1 - params['adaptation_capacity_base']) * 
            (years_ahead / 80) * 0.4
        )
        adaptation_capacity = min(1.0, adaptation_capacity)
        
        # Project mitigation effort
        mitigation_effort = params['mitigation_effort_base'] + (
            (1 - params['mitigation_effort_base']) * 
            (years_ahead / 80) * 0.3
        )
        mitigation_effort = min(1.0, mitigation_effort)
        
        # Project temperature increase (cumulative)
        temp_increase = params['temp_increase_rate'] * years_ahead
        
        # Project precipitation change (cumulative percentage)
        precip_change = params['precip_change_rate'] * years_ahead * 100
        
        return SSPProjection(
            scenario=scenario,
            year=year,
            population_growth=pop_growth,
            gdp_growth=gdp_growth,
            tech_progress=tech_progress,
            policy_cooperation=policy_cooperation,
            adaptation_capacity=adaptation_capacity,
            mitigation_effort=mitigation_effort,
            temperature_increase=temp_increase,
            precipitation_change=precip_change
        )
    
    def apply_projection_to_tensor(
        self,
        tensor: 'ContextTensor',  # Forward reference
        projection: SSPProjection
    ) -> 'ContextTensor':
        """
        Apply SSP projection to a context tensor
        
        Args:
            tensor: ContextTensor object
            projection: SSPProjection object
        
        Returns:
            Modified ContextTensor
        """
        # Create a copy (simplified - would deep copy in production)
        modified_tensor = tensor
        
        # Apply climate changes
        climate = modified_tensor.dimensions.get('climate')
        if climate:
            climate.temp_mean += projection.temperature_increase
            climate.temp_max += projection.temperature_increase * 1.2
            climate.temp_min += projection.temperature_increase * 0.8
            climate.precipitation *= (1 + projection.precipitation_change / 100)
            
            # Increase extreme events based on scenario
            if projection.scenario in [SSPScenario.SSP3, SSPScenario.SSP5]:
                climate.extreme_events_frequency *= 1.5
                climate.extreme_events_intensity *= 1.3
        
        # Apply socioeconomic changes
        socio = modified_tensor.dimensions.get('socioeconomic')
        if socio:
            socio.population_density *= projection.population_growth
            socio.gdp_per_capita *= projection.gdp_growth
            socio.poverty_rate *= (1 - projection.tech_progress * 0.3)
            socio.education_level *= (1 + projection.tech_progress * 0.2)
            socio.education_level = min(100.0, socio.education_level)
        
        # Apply vulnerability changes
        vuln = modified_tensor.dimensions.get('vulnerability')
        if vuln:
            # Better adaptation capacity reduces vulnerability
            vuln.social_vulnerability_index *= (1 - projection.adaptation_capacity * 0.3)
            vuln.governance_quality *= (1 + projection.policy_cooperation * 0.2)
            vuln.governance_quality = min(1.0, vuln.governance_quality)
            vuln.financial_access *= (1 + projection.gdp_growth * 0.1)
            vuln.financial_access = min(1.0, vuln.financial_access)
        
        return modified_tensor
    
    def simulate_region(
        self,
        region_name: str,
        scenario_str: str,
        year: int,
        base_tensors: List['ContextTensor']
    ) -> List['ContextTensor']:
        """
        Simulate a region under a specific scenario
        
        Args:
            region_name: Name of the region
            scenario_str: Scenario string (e.g., "SSP2-4.5")
            year: Target year
            base_tensors: List of base ContextTensor objects
        
        Returns:
            List of projected ContextTensor objects
        """
        scenario = self.parse_scenario(scenario_str)
        if not scenario:
            scenario = SSPScenario.SSP2  # Default
        
        projection = self.project_to_year(scenario, year)
        
        projected_tensors = []
        for tensor in base_tensors:
            projected = self.apply_projection_to_tensor(tensor, projection)
            projected_tensors.append(projected)
        
        return projected_tensors


# Example usage
if __name__ == '__main__':
    engine = SSPScenarioEngine()
    
    # Project SSP2 to 2050
    projection = engine.project_to_year(SSPScenario.SSP2, 2050)
    print(f"SSP2-4.5 Projection for 2050:")
    print(f"  Population Growth: {projection.population_growth:.2f}x")
    print(f"  GDP Growth: {projection.gdp_growth:.2f}x")
    print(f"  Temperature Increase: {projection.temperature_increase:.2f}°C")
    print(f"  Precipitation Change: {projection.precipitation_change:.1f}%")


