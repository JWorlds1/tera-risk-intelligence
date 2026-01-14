"""
TERA V2 Integration Module
===========================

Dieses Modul integriert die neuen kausalen Risiko-Engines
in das bestehende TERA-System.
"""

from .climate_index_service import ClimateIndexService, climate_service
from .global_risk_engine import GlobalRiskEngine, global_risk_engine
from .enhanced_tessellation import EnhancedTessellationEngine, enhanced_tessellation

__all__ = [
    'ClimateIndexService',
    'climate_service',
    'GlobalRiskEngine', 
    'global_risk_engine',
    'EnhancedTessellationEngine',
    'enhanced_tessellation'
]












