"""
Action Recommendation Engine - Generates context-sensitive action recommendations
Uses action database with matching logic and LLM synthesis
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json


class ActionType(Enum):
    """Action type"""
    ADAPTATION = "Adaptation"
    MITIGATION = "Mitigation"


@dataclass
class ActionItem:
    """Action recommendation item"""
    id: str
    type: ActionType
    icon: str
    title: str
    measures: List[str]
    cost: int  # In euros
    timeline: str
    target_risks: List[str]  # e.g., ["flood", "drought", "heat"]
    context_conditions: Dict[str, Any]  # Conditions for effectiveness
    co_benefits: List[str]
    sources: List[str]  # URLs to sources/studies


class ActionRecommendationEngine:
    """Engine for generating action recommendations"""
    
    # Action database (would be loaded from external source in production)
    ACTION_DATABASE: List[ActionItem] = [
        ActionItem(
            id='ADAPT-001',
            type=ActionType.ADAPTATION,
            icon='🌊',
            title='Coastal Defense System',
            measures=['Mangrove restoration', 'Sea walls construction', 'Beach nourishment'],
            cost=5000000,
            timeline='2-5 Years',
            target_risks=['flood', 'sea_level_rise', 'storm_surge'],
            context_conditions={'coastal_proximity': '<10', 'elevation': '<5'},
            co_benefits=['Biodiversity', 'Tourism', 'Erosion control'],
            sources=['https://unfccc.int/adaptation']
        ),
        ActionItem(
            id='ADAPT-002',
            type=ActionType.ADAPTATION,
            icon='🚰',
            title='Drought Resilience Program',
            measures=['Community boreholes', 'Drip irrigation subsidies', 'Water storage systems'],
            cost=200000,
            timeline='6-12 Months',
            target_risks=['drought', 'water_scarcity'],
            context_conditions={'precipitation': '<100', 'land_use': 'Rural'},
            co_benefits=['Food security', 'Livelihood support'],
            sources=['https://www.worldbank.org/en/topic/climatechange']
        ),
        ActionItem(
            id='ADAPT-003',
            type=ActionType.ADAPTATION,
            icon='❄️',
            title='Heat Action Plan',
            measures=['Cool roofing retrofits', 'Public cooling centers', 'Urban greening'],
            cost=150000,
            timeline='0-6 Months',
            target_risks=['heat_wave', 'urban_heat_island'],
            context_conditions={'land_use': 'Urban', 'temp_max': '>30'},
            co_benefits=['Energy savings', 'Air quality', 'Public health'],
            sources=['https://www.who.int/health-topics/heatwaves']
        ),
        ActionItem(
            id='MITIG-001',
            type=ActionType.MITIGATION,
            icon='⚡',
            title='Grid Decentralization',
            measures=['Solar micro-grids', 'Battery storage units', 'Smart grid integration'],
            cost=1200000,
            timeline='1-3 Years',
            target_risks=['energy_insecurity', 'emissions'],
            context_conditions={'infrastructure': 'moderate'},
            co_benefits=['Energy independence', 'Job creation', 'Reduced emissions'],
            sources=['https://www.irena.org/']
        ),
        ActionItem(
            id='ADAPT-004',
            type=ActionType.ADAPTATION,
            icon='🌾',
            title='Food Security Net',
            measures=['Strategic grain reserves', 'Cash transfer program', 'Early warning systems'],
            cost=800000,
            timeline='0-3 Months',
            target_risks=['food_insecurity', 'price_volatility'],
            context_conditions={'poverty_rate': '>20'},
            co_benefits=['Social protection', 'Market stability'],
            sources=['https://www.wfp.org/']
        ),
        ActionItem(
            id='ADAPT-005',
            type=ActionType.ADAPTATION,
            icon='🏙️',
            title='Urban Flood Management',
            measures=['Permeable pavement', 'Canal dredging', 'Green infrastructure'],
            cost=3000000,
            timeline='2-4 Years',
            target_risks=['flood', 'urban_flooding'],
            context_conditions={'land_use': 'Urban', 'precipitation': '>150'},
            co_benefits=['Water quality', 'Recreation', 'Biodiversity'],
            sources=['https://www.c40.org/']
        ),
        ActionItem(
            id='ADAPT-006',
            type=ActionType.ADAPTATION,
            icon='🌳',
            title='Reforestation Buffer',
            measures=['Planting native species', 'Soil erosion control', 'Watershed protection'],
            cost=450000,
            timeline='1-5 Years',
            target_risks=['erosion', 'landslide', 'biodiversity_loss'],
            context_conditions={'land_use': 'Rural', 'slope': '>10'},
            co_benefits=['Carbon sequestration', 'Biodiversity', 'Water regulation'],
            sources=['https://www.un-redd.org/']
        ),
        ActionItem(
            id='MITIG-002',
            type=ActionType.MITIGATION,
            icon='🚤',
            title='Water Transport Upgrade',
            measures=['Electric ferries', 'Canal logistics', 'Efficient routing'],
            cost=1000000,
            timeline='1-3 Years',
            target_risks=['emissions', 'transport_congestion'],
            context_conditions={'water_body': True, 'infrastructure': 'moderate'},
            co_benefits=['Reduced emissions', 'Traffic reduction'],
            sources=['https://www.imo.org/']
        )
    ]
    
    def __init__(self, llm_manager=None):
        """
        Initialize the Action Recommendation Engine
        
        Args:
            llm_manager: LLM manager for synthesis (optional)
        """
        self.llm_manager = llm_manager
    
    def match_actions(
        self,
        risk_scores: Dict[str, float],
        tensor: 'ContextTensor',
        max_actions: int = 3
    ) -> List[ActionItem]:
        """
        Match actions to risk profile and context
        
        Args:
            risk_scores: Dictionary with hazard, exposure, vulnerability, total_risk
            tensor: ContextTensor object
            max_actions: Maximum number of actions to return
        
        Returns:
            List of matched ActionItem objects
        """
        matched_actions = []
        
        # Determine primary risk type
        primary_risk = self._identify_primary_risk(risk_scores, tensor)
        
        # Score each action
        action_scores = []
        for action in self.ACTION_DATABASE:
            score = self._score_action(action, primary_risk, risk_scores, tensor)
            action_scores.append((action, score))
        
        # Sort by score (highest first)
        action_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top actions
        return [action for action, score in action_scores[:max_actions]]
    
    def _identify_primary_risk(
        self,
        risk_scores: Dict[str, float],
        tensor: 'ContextTensor'
    ) -> str:
        """
        Identify primary risk type from risk scores and tensor
        
        Args:
            risk_scores: Risk scores dictionary
            tensor: ContextTensor object
        
        Returns:
            Primary risk type string
        """
        climate = tensor.dimensions.get('climate')
        geography = tensor.dimensions.get('geography')
        
        risks = []
        
        # Flood risk
        if climate and climate.precipitation > 150:
            risks.append(('flood', risk_scores.get('hazard', 0) * 0.5))
        if geography and geography.coastal_proximity < 10:
            risks.append(('sea_level_rise', risk_scores.get('hazard', 0) * 0.3))
        
        # Drought risk
        if climate and climate.precipitation < 50:
            risks.append(('drought', risk_scores.get('hazard', 0) * 0.5))
        
        # Heat risk
        if climate and climate.temp_max > 30:
            risks.append(('heat_wave', risk_scores.get('hazard', 0) * 0.4))
        
        # Extreme events
        if climate and climate.extreme_events_frequency > 0.2:
            risks.append(('extreme_events', risk_scores.get('hazard', 0) * 0.3))
        
        if not risks:
            return 'general'
        
        # Return risk with highest score
        return max(risks, key=lambda x: x[1])[0]
    
    def _score_action(
        self,
        action: ActionItem,
        primary_risk: str,
        risk_scores: Dict[str, float],
        tensor: 'ContextTensor'
    ) -> float:
        """
        Score an action based on relevance
        
        Args:
            action: ActionItem to score
            primary_risk: Primary risk type
            risk_scores: Risk scores
            tensor: ContextTensor
        
        Returns:
            Score (0-100)
        """
        score = 0.0
        
        # Risk matching (40% weight)
        if primary_risk in action.target_risks:
            score += 40.0
        elif any(risk in action.target_risks for risk in ['general', 'climate']):
            score += 20.0
        
        # Context condition matching (30% weight)
        context_match = self._check_context_conditions(action, tensor)
        score += context_match * 30.0
        
        # Risk level (20% weight)
        total_risk = risk_scores.get('total_risk', 50)
        if total_risk > 70:
            score += 20.0
        elif total_risk > 50:
            score += 10.0
        
        # Cost efficiency (10% weight) - lower cost = higher score
        if action.cost < 500000:
            score += 10.0
        elif action.cost < 2000000:
            score += 5.0
        
        return min(100.0, score)
    
    def _check_context_conditions(
        self,
        action: ActionItem,
        tensor: 'ContextTensor'
    ) -> float:
        """
        Check how well action matches context conditions
        
        Args:
            action: ActionItem
            tensor: ContextTensor
        
        Returns:
            Match score (0-1)
        """
        conditions = action.context_conditions
        if not conditions:
            return 0.5  # Neutral if no conditions
        
        matches = 0
        total = len(conditions)
        
        geography = tensor.dimensions.get('geography')
        climate = tensor.dimensions.get('climate')
        socio = tensor.dimensions.get('socioeconomic')
        
        # Check each condition
        for key, value in conditions.items():
            if key == 'coastal_proximity' and geography:
                threshold = float(value.replace('<', '').replace('>', ''))
                if '<' in value and geography.coastal_proximity < threshold:
                    matches += 1
                elif '>' in value and geography.coastal_proximity > threshold:
                    matches += 1
            
            elif key == 'elevation' and geography:
                threshold = float(value.replace('<', '').replace('>', ''))
                if '<' in value and geography.elevation < threshold:
                    matches += 1
            
            elif key == 'land_use' and geography:
                if geography.land_cover_class == value:
                    matches += 1
            
            elif key == 'precipitation' and climate:
                threshold = float(value.replace('<', '').replace('>', ''))
                if '<' in value and climate.precipitation < threshold:
                    matches += 1
                elif '>' in value and climate.precipitation > threshold:
                    matches += 1
            
            elif key == 'temp_max' and climate:
                threshold = float(value.replace('<', '').replace('>', ''))
                if '>' in value and climate.temp_max > threshold:
                    matches += 1
            
            elif key == 'poverty_rate' and socio:
                threshold = float(value.replace('<', '').replace('>', ''))
                if '>' in value and socio.poverty_rate > threshold:
                    matches += 1
        
        return matches / total if total > 0 else 0.5
    
    async def synthesize_recommendation(
        self,
        action: ActionItem,
        tensor: 'ContextTensor',
        risk_scores: Dict[str, float]
    ) -> str:
        """
        Synthesize natural language recommendation using LLM
        
        Args:
            action: ActionItem
            tensor: ContextTensor
            risk_scores: Risk scores
        
        Returns:
            Natural language recommendation text
        """
        if self.llm_manager:
            # Use LLM for synthesis
            prompt = f"""
            Generate a concise, actionable recommendation for implementing:
            {action.title}
            
            Context:
            - Risk Level: {risk_scores.get('total_risk', 0):.1f}/100
            - Primary Risks: {', '.join(action.target_risks)}
            - Location Type: {tensor.dimensions.get('geography', {}).get('land_cover_class', 'Unknown')}
            
            Measures: {', '.join(action.measures)}
            Cost: €{action.cost:,}
            Timeline: {action.timeline}
            Co-benefits: {', '.join(action.co_benefits)}
            
            Provide a 2-3 sentence recommendation that is specific, actionable, and emphasizes urgency if risk is high.
            """
            
            try:
                recommendation = await self.llm_manager.generate(prompt)
                return recommendation
            except Exception as e:
                # Fallback to template
                pass
        
        # Template-based fallback
        risk_level = risk_scores.get('total_risk', 50)
        urgency = "urgently" if risk_level > 70 else "promptly" if risk_level > 50 else "proactively"
        
        return f"""
        Based on the current risk assessment (Risk Score: {risk_level:.1f}/100), 
        it is recommended to {urgency} implement {action.title}. 
        This action addresses {', '.join(action.target_risks[:2])} risks through {action.measures[0]} and {action.measures[1] if len(action.measures) > 1 else 'related measures'}. 
        With an estimated cost of €{action.cost:,} and timeline of {action.timeline}, 
        this intervention will also provide co-benefits including {', '.join(action.co_benefits[:2])}.
        """
    
    def recommend_actions(
        self,
        h3_index: str,
        risk_scores: Dict[str, float],
        tensor: 'ContextTensor',
        max_actions: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get action recommendations for an H3 cell
        
        Args:
            h3_index: H3 cell index
            risk_scores: Risk scores dictionary
            tensor: ContextTensor object
            max_actions: Maximum number of actions
        
        Returns:
            List of action recommendation dictionaries
        """
        matched_actions = self.match_actions(risk_scores, tensor, max_actions)
        
        recommendations = []
        for action in matched_actions:
            recommendations.append({
                'id': action.id,
                'type': action.type.value,
                'icon': action.icon,
                'title': action.title,
                'measures': action.measures,
                'cost': action.cost,
                'timeline': action.timeline,
                'co_benefits': action.co_benefits,
                'sources': action.sources
            })
        
        return recommendations


# Example usage
if __name__ == '__main__':
    from context_tensor_engine import ContextTensor, ClimateDimension, GeographyDimension
    
    engine = ActionRecommendationEngine()
    
    # Create test tensor
    tensor = ContextTensor(
        h3_index="87194e64dffffff",
        timestamp=None
    )
    tensor.dimensions['climate'] = ClimateDimension(
        temp_max=35.0,
        precipitation=150.0
    )
    tensor.dimensions['geography'] = GeographyDimension(
        elevation=10.0,
        coastal_proximity=5.0,
        land_cover_class='Urban'
    )
    
    risk_scores = {
        'hazard': 65.0,
        'exposure': 70.0,
        'vulnerability': 60.0,
        'total_risk': 75.0
    }
    
    recommendations = engine.recommend_actions(
        "87194e64dffffff",
        risk_scores,
        tensor
    )
    
    print(f"Recommended {len(recommendations)} actions:")
    for rec in recommendations:
        print(f"  {rec['icon']} {rec['title']} - €{rec['cost']:,}")


