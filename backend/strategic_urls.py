# strategic_urls.py - Strategische URL-Sammlung für Klima-Konflikt-Analyse
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum

class Priority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

@dataclass
class StrategicURL:
    url: str
    priority: Priority
    region: str
    category: str
    description: str
    climate_indicators: List[str]
    conflict_indicators: List[str]

class StrategicURLManager:
    """Strategische URL-Sammlung für Klima-Konflikt-Frühwarnsystem"""
    
    def __init__(self):
        self.urls = self._initialize_strategic_urls()
    
    def _initialize_strategic_urls(self) -> Dict[str, List[StrategicURL]]:
        """Initialisiere strategische URLs basierend auf geopolitischen Hotspots"""
        
        return {
            "CRITICAL_SUPPLY_CHAINS": [
                # Maritime Chokepoints
                StrategicURL(
                    url="https://www.worldbank.org/en/topic/transport",
                    priority=Priority.CRITICAL,
                    region="Global Maritime",
                    category="Supply Chain",
                    description="Maritime Transport & Chokepoints",
                    climate_indicators=["sea_level_rise", "storm_intensity", "port_flooding"],
                    conflict_indicators=["trade_disruption", "shipping_delays", "economic_impact"]
                ),
                StrategicURL(
                    url="https://earthobservatory.nasa.gov/topic/water",
                    priority=Priority.CRITICAL,
                    region="Global Waterways",
                    category="Water Infrastructure",
                    description="Critical Water Systems",
                    climate_indicators=["drought", "flooding", "water_scarcity"],
                    conflict_indicators=["water_conflicts", "migration", "food_security"]
                ),
            ],
            
            "GEOPOLITICAL_HOTSPOTS": [
                # Horn of Africa
                StrategicURL(
                    url="https://www.wfp.org/countries/ethiopia",
                    priority=Priority.CRITICAL,
                    region="Horn of Africa",
                    category="Food Security",
                    description="Ethiopia - Tigray Conflict + Climate",
                    climate_indicators=["drought", "desertification", "crop_failure"],
                    conflict_indicators=["civil_war", "displacement", "famine"]
                ),
                StrategicURL(
                    url="https://www.wfp.org/countries/somalia",
                    priority=Priority.CRITICAL,
                    region="Horn of Africa",
                    category="Crisis Response",
                    description="Somalia - Al-Shabaab + Climate",
                    climate_indicators=["drought", "flooding", "desert_locusts"],
                    conflict_indicators=["terrorism", "displacement", "food_insecurity"]
                ),
                
                # Sahel Region
                StrategicURL(
                    url="https://www.wfp.org/countries/mali",
                    priority=Priority.HIGH,
                    region="Sahel",
                    category="Security",
                    description="Mali - Jihadist Insurgency + Desertification",
                    climate_indicators=["desertification", "drought", "land_degradation"],
                    conflict_indicators=["jihadist_insurgency", "ethnic_conflicts", "migration"]
                ),
                StrategicURL(
                    url="https://www.wfp.org/countries/niger",
                    priority=Priority.HIGH,
                    region="Sahel",
                    category="Development",
                    description="Niger - Uranium + Climate Vulnerability",
                    climate_indicators=["drought", "temperature_rise", "water_scarcity"],
                    conflict_indicators=["resource_conflicts", "terrorism", "migration"]
                ),
                
                # Middle East
                StrategicURL(
                    url="https://press.un.org/en/content/middle-east",
                    priority=Priority.HIGH,
                    region="Middle East",
                    category="Security",
                    description="Middle East - Water Wars + Climate",
                    climate_indicators=["drought", "water_scarcity", "heat_waves"],
                    conflict_indicators=["water_conflicts", "refugee_crisis", "resource_wars"]
                ),
                
                # South Asia
                StrategicURL(
                    url="https://www.worldbank.org/en/country/india",
                    priority=Priority.HIGH,
                    region="South Asia",
                    category="Infrastructure",
                    description="India - Monsoon Disruption + Urban Heat",
                    climate_indicators=["monsoon_failure", "urban_heat_islands", "glacier_melt"],
                    conflict_indicators=["water_disputes", "migration", "economic_instability"]
                ),
                StrategicURL(
                    url="https://www.worldbank.org/en/country/pakistan",
                    priority=Priority.HIGH,
                    region="South Asia",
                    category="Crisis",
                    description="Pakistan - Floods + Political Instability",
                    climate_indicators=["extreme_flooding", "glacier_melt", "monsoon_intensification"],
                    conflict_indicators=["political_instability", "displacement", "economic_crisis"]
                ),
                
                # Southeast Asia
                StrategicURL(
                    url="https://www.worldbank.org/en/country/vietnam",
                    priority=Priority.MEDIUM,
                    region="Southeast Asia",
                    category="Manufacturing",
                    description="Vietnam - Manufacturing Hub + Sea Level Rise",
                    climate_indicators=["sea_level_rise", "typhoon_intensity", "saltwater_intrusion"],
                    conflict_indicators=["supply_chain_disruption", "migration", "economic_impact"]
                ),
            ],
            
            "CLIMATE_VULNERABILITY_ZONES": [
                # Small Island States
                StrategicURL(
                    url="https://press.un.org/en/content/small-island-developing-states",
                    priority=Priority.CRITICAL,
                    region="SIDS",
                    category="Existential Threat",
                    description="Small Island States - Existential Climate Threat",
                    climate_indicators=["sea_level_rise", "storm_intensity", "saltwater_intrusion"],
                    conflict_indicators=["climate_migration", "territorial_loss", "economic_collapse"]
                ),
                
                # Arctic
                StrategicURL(
                    url="https://earthobservatory.nasa.gov/topic/arctic",
                    priority=Priority.HIGH,
                    region="Arctic",
                    category="Geopolitics",
                    description="Arctic - Resource Competition + Melting",
                    climate_indicators=["ice_melt", "permafrost_thaw", "temperature_rise"],
                    conflict_indicators=["resource_competition", "territorial_disputes", "military_buildup"]
                ),
                
                # Amazon
                StrategicURL(
                    url="https://www.worldbank.org/en/country/brazil",
                    priority=Priority.HIGH,
                    region="Amazon",
                    category="Ecosystem",
                    description="Brazil - Amazon Deforestation + Climate",
                    climate_indicators=["deforestation", "drought", "fire_intensity"],
                    conflict_indicators=["land_conflicts", "indigenous_rights", "environmental_activism"]
                ),
            ],
            
            "SUPPLY_CHAIN_CRITICAL_POINTS": [
                # Suez Canal
                StrategicURL(
                    url="https://www.worldbank.org/en/topic/trade",
                    priority=Priority.CRITICAL,
                    region="Suez Canal",
                    category="Trade Route",
                    description="Suez Canal - Global Trade Chokepoint",
                    climate_indicators=["sea_level_rise", "storm_intensity", "port_flooding"],
                    conflict_indicators=["trade_disruption", "economic_impact", "geopolitical_tension"]
                ),
                
                # Strait of Hormuz
                StrategicURL(
                    url="https://press.un.org/en/content/security-council",
                    priority=Priority.CRITICAL,
                    region="Persian Gulf",
                    category="Energy Security",
                    description="Strait of Hormuz - Oil Chokepoint",
                    climate_indicators=["sea_level_rise", "storm_intensity", "heat_waves"],
                    conflict_indicators=["energy_conflicts", "military_tension", "economic_warfare"]
                ),
                
                # Panama Canal
                StrategicURL(
                    url="https://www.worldbank.org/en/country/panama",
                    priority=Priority.HIGH,
                    region="Central America",
                    category="Trade Route",
                    description="Panama Canal - Climate Vulnerability",
                    climate_indicators=["drought", "water_scarcity", "storm_intensity"],
                    conflict_indicators=["trade_disruption", "economic_impact", "migration"]
                ),
            ],
            
            "URBAN_VULNERABILITY_HOTSPOTS": [
                # Mega Cities
                StrategicURL(
                    url="https://www.worldbank.org/en/topic/urbandevelopment",
                    priority=Priority.HIGH,
                    region="Global Cities",
                    category="Urban Resilience",
                    description="Mega Cities - Climate Vulnerability",
                    climate_indicators=["urban_heat_islands", "flooding", "air_pollution"],
                    conflict_indicators=["social_unrest", "migration", "infrastructure_failure"]
                ),
                
                # Delta Cities
                StrategicURL(
                    url="https://earthobservatory.nasa.gov/topic/deltas",
                    priority=Priority.HIGH,
                    region="River Deltas",
                    category="Coastal Vulnerability",
                    description="Delta Cities - Sea Level Rise",
                    climate_indicators=["sea_level_rise", "saltwater_intrusion", "storm_surge"],
                    conflict_indicators=["climate_migration", "economic_displacement", "social_instability"]
                ),
            ]
        }
    
    def get_critical_urls(self) -> List[StrategicURL]:
        """Hole kritische URLs für sofortige Analyse"""
        critical = []
        for category, urls in self.urls.items():
            critical.extend([url for url in urls if url.priority == Priority.CRITICAL])
        return critical
    
    def get_urls_by_region(self, region: str) -> List[StrategicURL]:
        """Hole URLs für spezifische Region"""
        region_urls = []
        for category, urls in self.urls.items():
            region_urls.extend([url for url in urls if region.lower() in url.region.lower()])
        return region_urls
    
    def get_urls_by_category(self, category: str) -> List[StrategicURL]:
        """Hole URLs für spezifische Kategorie"""
        category_urls = []
        for cat, urls in self.urls.items():
            category_urls.extend([url for url in urls if category.lower() in url.category.lower()])
        return category_urls
    
    def get_priority_matrix(self) -> Dict[str, List[str]]:
        """Erstelle Prioritäts-Matrix für strategische Planung"""
        return {
            "IMMEDIATE_ACTION": [
                "Horn of Africa - Food Security Crisis",
                "Small Island States - Existential Threat", 
                "Suez Canal - Trade Disruption Risk",
                "Strait of Hormuz - Energy Security"
            ],
            "HIGH_PRIORITY": [
                "Sahel Region - Desertification + Conflict",
                "Middle East - Water Wars",
                "South Asia - Monsoon Disruption",
                "Arctic - Resource Competition"
            ],
            "MONITORING": [
                "Southeast Asia - Manufacturing Disruption",
                "Amazon - Deforestation + Climate",
                "Urban Centers - Heat Islands",
                "Delta Cities - Sea Level Rise"
            ]
        }
    
    def get_cascade_effects_map(self) -> Dict[str, List[str]]:
        """Erstelle Kaskadeneffekt-Map"""
        return {
            "Horn of Africa Drought": [
                "→ Food Price Inflation",
                "→ Migration to Europe", 
                "→ Political Instability",
                "→ Terrorism Recruitment",
                "→ Regional Conflict"
            ],
            "Suez Canal Disruption": [
                "→ Global Supply Chain Shock",
                "→ Inflation Spike",
                "→ Economic Recession",
                "→ Social Unrest",
                "→ Political Instability"
            ],
            "Arctic Ice Melt": [
                "→ New Trade Routes",
                "→ Resource Competition",
                "→ Military Buildup",
                "→ Territorial Disputes",
                "→ Geopolitical Tension"
            ],
            "Small Island Displacement": [
                "→ Climate Refugees",
                "→ Territorial Loss",
                "→ Economic Collapse",
                "→ Regional Instability",
                "→ International Law Challenges"
            ]
        }
