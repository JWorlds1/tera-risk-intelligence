"""
Tests for mining/risk_scoring.py - RiskScorer class
"""
import pytest
import sys
from pathlib import Path

# Add mining directory to path
mining_path = Path(__file__).parent.parent / "mining"
sys.path.insert(0, str(mining_path))

from risk_scoring import RiskScorer, RiskScore


class TestRiskScorer:
    """Test suite for RiskScorer class"""
    
    def test_scorer_initialization(self):
        """Test that RiskScorer initializes correctly"""
        scorer = RiskScorer()
        assert scorer is not None
        assert hasattr(scorer, 'climate_indicators')
        assert hasattr(scorer, 'conflict_indicators')
        assert hasattr(scorer, 'urgency_indicators')
        assert len(scorer.climate_indicators) > 0
        assert len(scorer.conflict_indicators) > 0
        assert len(scorer.urgency_indicators) > 0
    
    def test_calculate_climate_risk(self, sample_record_climate):
        """Test climate risk calculation"""
        scorer = RiskScorer()
        risk = scorer.calculate_risk(sample_record_climate)
        
        assert isinstance(risk, RiskScore)
        assert risk.record_id == 1
        assert 0.0 <= risk.climate_risk <= 1.0
        # Should have high climate risk due to drought, crop failure, water scarcity keywords
        assert risk.climate_risk > 0.5
    
    def test_calculate_conflict_risk(self, sample_record_conflict):
        """Test conflict risk calculation"""
        scorer = RiskScorer()
        risk = scorer.calculate_risk(sample_record_conflict)
        
        assert isinstance(risk, RiskScore)
        assert risk.record_id == 2
        assert 0.0 <= risk.conflict_risk <= 1.0
        # Should have high conflict risk due to war, violence, displacement keywords
        assert risk.conflict_risk > 0.5
    
    def test_calculate_urgency(self, sample_record_urgency):
        """Test urgency calculation"""
        scorer = RiskScorer()
        risk = scorer.calculate_risk(sample_record_urgency)
        
        assert isinstance(risk, RiskScore)
        assert risk.record_id == 3
        assert 0.0 <= risk.urgency <= 1.0
        # Should have high urgency due to critical, emergency keywords
        assert risk.urgency > 0.5
    
    def test_calculate_mixed_risk(self, sample_record_mixed):
        """Test risk calculation with mixed indicators"""
        scorer = RiskScorer()
        risk = scorer.calculate_risk(sample_record_mixed)
        
        assert isinstance(risk, RiskScore)
        assert 0.0 <= risk.climate_risk <= 1.0
        assert 0.0 <= risk.conflict_risk <= 1.0
        assert 0.0 <= risk.urgency <= 1.0
        assert 0.0 <= risk.score <= 1.0
    
    def test_total_score_weighting(self, sample_record_mixed):
        """Test that total score uses correct weighting (40% climate, 40% conflict, 20% urgency)"""
        scorer = RiskScorer()
        risk = scorer.calculate_risk(sample_record_mixed)
        
        # Calculate expected weighted score
        expected_score = (
            risk.climate_risk * 0.4 +
            risk.conflict_risk * 0.4 +
            risk.urgency * 0.2
        )
        
        # Allow small floating point differences
        assert abs(risk.score - expected_score) < 0.01
    
    def test_risk_level_critical(self):
        """Test risk level classification for CRITICAL"""
        scorer = RiskScorer()
        assert scorer.get_risk_level(0.85) == "CRITICAL"
        assert scorer.get_risk_level(0.95) == "CRITICAL"
        assert scorer.get_risk_level(1.0) == "CRITICAL"
    
    def test_risk_level_high(self):
        """Test risk level classification for HIGH"""
        scorer = RiskScorer()
        assert scorer.get_risk_level(0.65) == "HIGH"
        assert scorer.get_risk_level(0.75) == "HIGH"
        assert scorer.get_risk_level(0.79) == "HIGH"
    
    def test_risk_level_medium(self):
        """Test risk level classification for MEDIUM"""
        scorer = RiskScorer()
        assert scorer.get_risk_level(0.45) == "MEDIUM"
        assert scorer.get_risk_level(0.55) == "MEDIUM"
        assert scorer.get_risk_level(0.59) == "MEDIUM"
    
    def test_risk_level_low(self):
        """Test risk level classification for LOW"""
        scorer = RiskScorer()
        assert scorer.get_risk_level(0.25) == "LOW"
        assert scorer.get_risk_level(0.35) == "LOW"
        assert scorer.get_risk_level(0.39) == "LOW"
    
    def test_risk_level_minimal(self):
        """Test risk level classification for MINIMAL"""
        scorer = RiskScorer()
        assert scorer.get_risk_level(0.0) == "MINIMAL"
        assert scorer.get_risk_level(0.15) == "MINIMAL"
        assert scorer.get_risk_level(0.19) == "MINIMAL"
    
    def test_empty_record(self, sample_record_empty):
        """Test risk calculation with empty record"""
        scorer = RiskScorer()
        risk = scorer.calculate_risk(sample_record_empty)
        
        assert isinstance(risk, RiskScore)
        assert risk.climate_risk == 0.0
        assert risk.conflict_risk == 0.0
        assert risk.urgency == 0.0
        assert risk.score == 0.0
        assert risk.indicators == []
    
    def test_indicators_collection(self, sample_record_climate):
        """Test that indicators are collected correctly"""
        scorer = RiskScorer()
        risk = scorer.calculate_risk(sample_record_climate)
        
        assert isinstance(risk.indicators, list)
        # Should contain climate-related indicators
        assert any(ind in risk.indicators for ind in ['drought', 'crop_failure', 'water_scarcity', 'famine'])
    
    def test_multiple_indicator_matches(self):
        """Test that multiple indicator matches increase score"""
        scorer = RiskScorer()
        record = {
            'id': 10,
            'title': 'Severe drought and flood crisis',
            'summary': 'Multiple disasters including drought, flood, and famine',
            'full_text': 'The region faces drought conditions, flooding, and famine risk',
            'region': 'East Africa'
        }
        risk = scorer.calculate_risk(record)
        
        # Multiple climate indicators should result in higher climate risk
        assert risk.climate_risk > 0.0
        assert len(risk.indicators) >= 2
    
    def test_score_bounds(self, sample_record_mixed):
        """Test that all scores are within valid bounds [0.0, 1.0]"""
        scorer = RiskScorer()
        risk = scorer.calculate_risk(sample_record_mixed)
        
        assert 0.0 <= risk.climate_risk <= 1.0
        assert 0.0 <= risk.conflict_risk <= 1.0
        assert 0.0 <= risk.urgency <= 1.0
        assert 0.0 <= risk.score <= 1.0
    
    def test_famine_high_weight(self):
        """Test that famine indicator has high weight (0.95)"""
        scorer = RiskScorer()
        assert scorer.climate_indicators.get('famine') == 0.95
    
    def test_war_high_weight(self):
        """Test that war indicator has high weight (0.95)"""
        scorer = RiskScorer()
        assert scorer.conflict_indicators.get('war') == 0.95
    
    def test_critical_high_weight(self):
        """Test that critical indicator has high weight (0.95)"""
        scorer = RiskScorer()
        assert scorer.urgency_indicators.get('critical') == 0.95
