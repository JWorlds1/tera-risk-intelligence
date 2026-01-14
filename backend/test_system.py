"""
System Test - Testet das gesamte System End-to-End
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from h3_grid_engine import H3GridEngine
from context_tensor_engine import ContextTensorEngine
from ssp_scenario_engine import SSPScenarioEngine, SSPScenario
from risk_modeling_engine import RiskModelingEngine
from action_recommendation_engine import ActionRecommendationEngine
from color_computation_engine import ColorComputationEngine
from config import Config


async def test_system():
    """Test the complete system"""
    print("=" * 60)
    print("CLIMATE CONTEXT SPACE SYSTEM TEST")
    print("=" * 60)
    
    config = Config()
    
    # 1. Test H3 Grid Engine
    print("\n1. Testing H3 Grid Engine...")
    h3_engine = H3GridEngine()
    grid = h3_engine.generate_grid(
        center_lat=-6.2088,
        center_lng=106.8456,
        scale='city',
        region_name='Jakarta'
    )
    print(f"   ✓ Generated {len(grid.cells)} H3 cells")
    print(f"   ✓ Resolution: {grid.resolution}")
    
    # 2. Test Context Tensor Engine
    print("\n2. Testing Context Tensor Engine...")
    tensor_engine = ContextTensorEngine(config)
    tensor = await tensor_engine.generate_tensor_for_cell(grid.cells[0])
    print(f"   ✓ Generated tensor for cell {tensor.h3_index}")
    print(f"   ✓ Climate temp: {tensor.dimensions.get('climate', {}).temp_mean if hasattr(tensor.dimensions.get('climate', {}), 'temp_mean') else 'N/A'}")
    
    # 3. Test SSP Scenario Engine
    print("\n3. Testing SSP Scenario Engine...")
    ssp_engine = SSPScenarioEngine()
    projection = ssp_engine.project_to_year(SSPScenario.SSP2, 2050)
    print(f"   ✓ SSP2-4.5 projection for 2050")
    print(f"   ✓ Temperature increase: {projection.temperature_increase:.2f}°C")
    print(f"   ✓ Population growth: {projection.population_growth:.2f}x")
    
    # 4. Test Risk Modeling Engine
    print("\n4. Testing Risk Modeling Engine...")
    risk_engine = RiskModelingEngine()
    risk_scores = risk_engine.calculate_total_risk(tensor)
    print(f"   ✓ Hazard: {risk_scores.hazard:.1f}")
    print(f"   ✓ Exposure: {risk_scores.exposure:.1f}")
    print(f"   ✓ Vulnerability: {risk_scores.vulnerability:.1f}")
    print(f"   ✓ Total Risk: {risk_scores.total_risk:.1f}")
    
    # 5. Test Action Recommendation Engine
    print("\n5. Testing Action Recommendation Engine...")
    action_engine = ActionRecommendationEngine()
    recommendations = action_engine.recommend_actions(
        tensor.h3_index,
        {
            'hazard': risk_scores.hazard,
            'exposure': risk_scores.exposure,
            'vulnerability': risk_scores.vulnerability,
            'total_risk': risk_scores.total_risk
        },
        tensor
    )
    print(f"   ✓ Generated {len(recommendations)} recommendations")
    for rec in recommendations[:2]:
        print(f"     - {rec['icon']} {rec['title']}")
    
    # 6. Test Color Computation Engine
    print("\n6. Testing Color Computation Engine...")
    color_engine = ColorComputationEngine()
    color, alpha = color_engine.compute_final_color(tensor, 'composite')
    print(f"   ✓ Computed color: {color.to_hex()}")
    print(f"   ✓ Alpha: {alpha:.2f}")
    
    # 7. Test SSP Projection Application
    print("\n7. Testing SSP Projection Application...")
    projected_tensor = ssp_engine.apply_projection_to_tensor(tensor, projection)
    projected_risk = risk_engine.calculate_total_risk(projected_tensor)
    print(f"   ✓ Projected risk for 2050: {projected_risk.total_risk:.1f}")
    
    await tensor_engine.close()
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(test_system())
