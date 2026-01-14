# geopolitical_analysis.py - Geopolitische Analyse für Klima-Konflikt-Frühwarnsystem
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)

class RiskLevel(Enum):
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    MINIMAL = 1

class ConflictType(Enum):
    CIVIL_WAR = "civil_war"
    TERRORISM = "terrorism"
    RESOURCE_CONFLICT = "resource_conflict"
    ETHNIC_CONFLICT = "ethnic_conflict"
    BORDER_DISPUTE = "border_dispute"
    WATER_WAR = "water_war"
    CLIMATE_MIGRATION = "climate_migration"

@dataclass
class GeopoliticalHotspot:
    name: str
    region: str
    coordinates: Tuple[float, float]
    risk_level: RiskLevel
    conflict_types: List[ConflictType]
    climate_indicators: List[str]
    supply_chain_impact: float  # 0-1
    population_affected: int
    last_updated: datetime
    description: str

class GeopoliticalAnalyzer:
    """Analyseur für geopolitische Hotspots und Kaskadeneffekte"""
    
    def __init__(self):
        self.hotspots = self._initialize_hotspots()
        self.supply_chains = self._initialize_supply_chains()
        self.cascade_effects = self._initialize_cascade_effects()
    
    def _initialize_hotspots(self) -> List[GeopoliticalHotspot]:
        """Initialisiere geopolitische Hotspots"""
        return [
            # HORN OF AFRICA - KRITISCH
            GeopoliticalHotspot(
                name="Horn of Africa Crisis",
                region="Horn of Africa",
                coordinates=(9.1450, 40.4897),  # Ethiopia
                risk_level=RiskLevel.CRITICAL,
                conflict_types=[ConflictType.CIVIL_WAR, ConflictType.ETHNIC_CONFLICT, ConflictType.CLIMATE_MIGRATION],
                climate_indicators=["drought", "desertification", "crop_failure", "water_scarcity"],
                supply_chain_impact=0.3,  # Red Sea shipping
                population_affected=120_000_000,
                last_updated=datetime.now(),
                description="Tigray Conflict + Worst Drought in 40 Years + Food Crisis"
            ),
            
            # SAHEL ZONE - HOCH
            GeopoliticalHotspot(
                name="Sahel Jihadist Insurgency",
                region="Sahel",
                coordinates=(17.6078, 8.0817),  # Niger
                risk_level=RiskLevel.HIGH,
                conflict_types=[ConflictType.TERRORISM, ConflictType.RESOURCE_CONFLICT, ConflictType.ETHNIC_CONFLICT],
                climate_indicators=["desertification", "drought", "land_degradation", "temperature_rise"],
                supply_chain_impact=0.1,  # Uranium supply
                population_affected=80_000_000,
                last_updated=datetime.now(),
                description="Jihadist Groups + Desertification + Uranium Mining Conflicts"
            ),
            
            # MIDDLE EAST - HOCH
            GeopoliticalHotspot(
                name="Middle East Water Wars",
                region="Middle East",
                coordinates=(31.7683, 35.2137),  # Israel/Palestine
                risk_level=RiskLevel.HIGH,
                conflict_types=[ConflictType.WATER_WAR, ConflictType.BORDER_DISPUTE, ConflictType.RESOURCE_CONFLICT],
                climate_indicators=["drought", "water_scarcity", "heat_waves", "desertification"],
                supply_chain_impact=0.4,  # Strait of Hormuz
                population_affected=50_000_000,
                last_updated=datetime.now(),
                description="Water Scarcity + Oil Conflicts + Refugee Crisis"
            ),
            
            # SOUTH ASIA - HOCH
            GeopoliticalHotspot(
                name="South Asia Monsoon Crisis",
                region="South Asia",
                coordinates=(28.7041, 77.1025),  # Delhi
                risk_level=RiskLevel.HIGH,
                conflict_types=[ConflictType.WATER_WAR, ConflictType.BORDER_DISPUTE, ConflictType.CLIMATE_MIGRATION],
                climate_indicators=["monsoon_failure", "glacier_melt", "urban_heat_islands", "flooding"],
                supply_chain_impact=0.2,  # Manufacturing disruption
                population_affected=1_800_000_000,
                last_updated=datetime.now(),
                description="Monsoon Disruption + India-Pakistan Water Disputes + Urban Heat"
            ),
            
            # ARCTIC - MITTEL
            GeopoliticalHotspot(
                name="Arctic Resource Competition",
                region="Arctic",
                coordinates=(78.2208, 15.6400),  # Svalbard
                risk_level=RiskLevel.MEDIUM,
                conflict_types=[ConflictType.RESOURCE_CONFLICT, ConflictType.BORDER_DISPUTE],
                climate_indicators=["ice_melt", "permafrost_thaw", "temperature_rise", "ecosystem_collapse"],
                supply_chain_impact=0.1,  # New trade routes
                population_affected=4_000_000,
                last_updated=datetime.now(),
                description="Melting Ice + New Trade Routes + Resource Competition"
            ),
            
            # SMALL ISLAND STATES - KRITISCH
            GeopoliticalHotspot(
                name="Small Island States Displacement",
                region="Pacific/Caribbean",
                coordinates=(-8.3405, 115.0920),  # Bali (representative)
                risk_level=RiskLevel.CRITICAL,
                conflict_types=[ConflictType.CLIMATE_MIGRATION, ConflictType.RESOURCE_CONFLICT],
                climate_indicators=["sea_level_rise", "storm_intensity", "saltwater_intrusion", "coral_bleaching"],
                supply_chain_impact=0.05,  # Limited but symbolic
                population_affected=65_000_000,
                last_updated=datetime.now(),
                description="Existential Threat + Climate Refugees + Territorial Loss"
            ),
        ]
    
    def _initialize_supply_chains(self) -> Dict[str, Dict]:
        """Initialisiere kritische Supply Chain Routen"""
        return {
            "MARITIME_CHOKEPOINTS": {
                "suez_canal": {
                    "importance": 0.9,  # 12% of global trade
                    "climate_risks": ["sea_level_rise", "storm_intensity", "port_flooding"],
                    "conflict_risks": ["egypt_instability", "israel_palestine", "red_sea_piracy"],
                    "alternative_routes": ["cape_of_good_hope", "northern_sea_route"],
                    "economic_impact": "12% of global trade, $1 trillion annually"
                },
                "strait_of_hormuz": {
                    "importance": 0.95,  # 20% of global oil
                    "climate_risks": ["sea_level_rise", "storm_intensity", "heat_waves"],
                    "conflict_risks": ["iran_tension", "gulf_conflicts", "energy_warfare"],
                    "alternative_routes": ["pipelines", "alternative_ports"],
                    "economic_impact": "20% of global oil, $2 trillion annually"
                },
                "panama_canal": {
                    "importance": 0.7,  # 5% of global trade
                    "climate_risks": ["drought", "water_scarcity", "storm_intensity"],
                    "conflict_risks": ["central_america_instability", "migration_crisis"],
                    "alternative_routes": ["suez_canal", "northern_sea_route"],
                    "economic_impact": "5% of global trade, $500 billion annually"
                },
                "malacca_strait": {
                    "importance": 0.8,  # 40% of global trade
                    "climate_risks": ["sea_level_rise", "storm_intensity", "tsunami_risk"],
                    "conflict_risks": ["china_sea_disputes", "piracy", "territorial_conflicts"],
                    "alternative_routes": ["sunda_strait", "lombok_strait"],
                    "economic_impact": "40% of global trade, $4 trillion annually"
                }
            },
            "CRITICAL_INFRASTRUCTURE": {
                "arctic_shipping": {
                    "importance": 0.3,  # Growing importance
                    "climate_risks": ["ice_melt", "unpredictable_weather", "infrastructure_damage"],
                    "conflict_risks": ["territorial_disputes", "military_buildup", "resource_competition"],
                    "economic_impact": "New trade routes, $100 billion potential"
                },
                "trans_siberian_railway": {
                    "importance": 0.6,  # Land bridge
                    "climate_risks": ["permafrost_thaw", "extreme_weather", "infrastructure_damage"],
                    "conflict_risks": ["russia_ukraine", "china_russia_tension", "sanctions"],
                    "economic_impact": "Eurasian connectivity, $200 billion annually"
                }
            }
        }
    
    def _initialize_cascade_effects(self) -> Dict[str, List[Dict]]:
        """Initialisiere Kaskadeneffekt-Modelle"""
        return {
            "HORN_OF_AFRICA_DROUGHT": [
                {
                    "trigger": "Worst drought in 40 years",
                    "immediate_effects": ["crop_failure", "livestock_death", "water_scarcity"],
                    "secondary_effects": ["food_price_inflation", "malnutrition", "disease_outbreak"],
                    "tertiary_effects": ["mass_migration", "social_unrest", "political_instability"],
                    "quaternary_effects": ["terrorism_recruitment", "regional_conflict", "european_migration_crisis"],
                    "economic_impact": "$50 billion in humanitarian aid needed",
                    "timeline": "6-18 months"
                }
            ],
            "SUEZ_CANAL_DISRUPTION": [
                {
                    "trigger": "Climate event or conflict blocks canal",
                    "immediate_effects": ["shipping_delays", "port_congestion", "fuel_shortages"],
                    "secondary_effects": ["supply_chain_disruption", "price_inflation", "manufacturing_delays"],
                    "tertiary_effects": ["economic_recession", "social_unrest", "political_instability"],
                    "quaternary_effects": ["global_economic_crisis", "trade_wars", "geopolitical_tension"],
                    "economic_impact": "$1 trillion in global trade disruption",
                    "timeline": "2-6 months"
                }
            ],
            "ARCTIC_ICE_MELT": [
                {
                    "trigger": "Accelerated ice melt opens new routes",
                    "immediate_effects": ["new_shipping_routes", "resource_access", "territorial_claims"],
                    "secondary_effects": ["military_buildup", "infrastructure_development", "environmental_damage"],
                    "tertiary_effects": ["geopolitical_tension", "resource_conflicts", "indigenous_rights_issues"],
                    "quaternary_effects": ["new_cold_war", "environmental_catastrophe", "global_power_shift"],
                    "economic_impact": "$500 billion in new economic opportunities",
                    "timeline": "5-15 years"
                }
            ],
            "SMALL_ISLAND_DISPLACEMENT": [
                {
                    "trigger": "Sea level rise makes islands uninhabitable",
                    "immediate_effects": ["coastal_flooding", "freshwater_contamination", "infrastructure_damage"],
                    "secondary_effects": ["climate_migration", "economic_collapse", "cultural_loss"],
                    "tertiary_effects": ["refugee_crisis", "territorial_disputes", "international_law_challenges"],
                    "quaternary_effects": ["global_migration_crisis", "sovereignty_crisis", "climate_justice_movement"],
                    "economic_impact": "$100 billion in relocation costs",
                    "timeline": "10-30 years"
                }
            ]
        }
    
    def analyze_cascade_effects(self, trigger_event: str) -> Dict[str, any]:
        """Analysiere Kaskadeneffekte für ein Trigger-Event"""
        if trigger_event not in self.cascade_effects:
            return {"error": "Unknown trigger event"}
        
        effects = self.cascade_effects[trigger_event][0]
        
        # Berechne Risiko-Score
        risk_score = self._calculate_risk_score(effects)
        
        # Identifiziere kritische Zeitpunkte
        critical_timeline = self._identify_critical_timeline(effects)
        
        # Empfehle Gegenmaßnahmen
        mitigation_strategies = self._recommend_mitigation(effects)
        
        return {
            "trigger_event": trigger_event,
            "effects": effects,
            "risk_score": risk_score,
            "critical_timeline": critical_timeline,
            "mitigation_strategies": mitigation_strategies,
            "analysis_date": datetime.now()
        }
    
    def _calculate_risk_score(self, effects: Dict) -> float:
        """Berechne Risiko-Score basierend auf Effekten"""
        # Gewichtete Bewertung der Effekte
        weights = {
            "immediate_effects": 0.3,
            "secondary_effects": 0.25,
            "tertiary_effects": 0.25,
            "quaternary_effects": 0.2
        }
        
        total_score = 0
        for effect_type, weight in weights.items():
            if effect_type in effects:
                effect_count = len(effects[effect_type])
                total_score += effect_count * weight
        
        return min(total_score / 10, 1.0)  # Normalisiert auf 0-1
    
    def _identify_critical_timeline(self, effects: Dict) -> List[Dict]:
        """Identifiziere kritische Zeitpunkte für Intervention"""
        timeline = []
        
        # Sofortige Maßnahmen (0-6 Monate)
        if "immediate_effects" in effects:
            timeline.append({
                "phase": "immediate",
                "timeframe": "0-6 months",
                "actions": ["emergency_response", "humanitarian_aid", "infrastructure_repair"],
                "priority": "critical"
            })
        
        # Kurzfristige Maßnahmen (6-18 Monate)
        if "secondary_effects" in effects:
            timeline.append({
                "phase": "short_term",
                "timeframe": "6-18 months",
                "actions": ["economic_stabilization", "social_programs", "conflict_prevention"],
                "priority": "high"
            })
        
        # Mittelfristige Maßnahmen (1-5 Jahre)
        if "tertiary_effects" in effects:
            timeline.append({
                "phase": "medium_term",
                "timeframe": "1-5 years",
                "actions": ["structural_reforms", "international_cooperation", "resilience_building"],
                "priority": "medium"
            })
        
        # Langfristige Maßnahmen (5+ Jahre)
        if "quaternary_effects" in effects:
            timeline.append({
                "phase": "long_term",
                "timeframe": "5+ years",
                "actions": ["systemic_change", "global_governance", "climate_adaptation"],
                "priority": "low"
            })
        
        return timeline
    
    def _recommend_mitigation(self, effects: Dict) -> List[Dict]:
        """Empfehle Gegenmaßnahmen basierend auf Effekten"""
        strategies = []
        
        # Präventive Maßnahmen
        strategies.append({
            "type": "preventive",
            "description": "Early warning systems and monitoring",
            "implementation": "immediate",
            "cost": "low",
            "effectiveness": "high"
        })
        
        # Adaptive Maßnahmen
        strategies.append({
            "type": "adaptive",
            "description": "Infrastructure resilience and social safety nets",
            "implementation": "short_term",
            "cost": "medium",
            "effectiveness": "high"
        })
        
        # Transformative Maßnahmen
        strategies.append({
            "type": "transformative",
            "description": "Systemic changes and international cooperation",
            "implementation": "long_term",
            "cost": "high",
            "effectiveness": "very_high"
        })
        
        return strategies
    
    def get_priority_regions(self) -> List[Dict]:
        """Hole priorisierte Regionen für Monitoring"""
        return [
            {
                "region": "Horn of Africa",
                "priority": "CRITICAL",
                "reasons": ["food_crisis", "civil_war", "climate_drought"],
                "monitoring_focus": ["food_security", "migration", "conflict_escalation"]
            },
            {
                "region": "Sahel Zone",
                "priority": "HIGH",
                "reasons": ["jihadist_insurgency", "desertification", "uranium_mining"],
                "monitoring_focus": ["terrorism", "resource_conflicts", "migration"]
            },
            {
                "region": "Middle East",
                "priority": "HIGH",
                "reasons": ["water_scarcity", "oil_conflicts", "refugee_crisis"],
                "monitoring_focus": ["water_wars", "energy_security", "geopolitical_tension"]
            },
            {
                "region": "South Asia",
                "priority": "HIGH",
                "reasons": ["monsoon_disruption", "water_disputes", "urban_heat"],
                "monitoring_focus": ["water_conflicts", "migration", "economic_instability"]
            },
            {
                "region": "Small Island States",
                "priority": "CRITICAL",
                "reasons": ["existential_threat", "sea_level_rise", "climate_refugees"],
                "monitoring_focus": ["displacement", "territorial_loss", "international_law"]
            }
        ]
    
    def get_supply_chain_vulnerabilities(self) -> List[Dict]:
        """Hole Supply Chain Vulnerabilitäten"""
        vulnerabilities = []
        
        for chokepoint, data in self.supply_chains["MARITIME_CHOKEPOINTS"].items():
            vulnerabilities.append({
                "chokepoint": chokepoint,
                "importance": data["importance"],
                "climate_risks": data["climate_risks"],
                "conflict_risks": data["conflict_risks"],
                "economic_impact": data["economic_impact"],
                "mitigation_priority": "high" if data["importance"] > 0.8 else "medium"
            })
        
        return vulnerabilities
