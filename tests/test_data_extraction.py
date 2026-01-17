"""
Tests for mining/data_extraction.py - NumberExtractor class
"""
import pytest
import sys
from pathlib import Path

# Add mining directory to path
mining_path = Path(__file__).parent.parent / "mining"
sys.path.insert(0, str(mining_path))

from data_extraction import NumberExtractor, ExtractedNumbers


class TestNumberExtractor:
    """Test suite for NumberExtractor class"""
    
    def test_extractor_initialization(self):
        """Test that NumberExtractor initializes correctly"""
        extractor = NumberExtractor()
        assert extractor is not None
        assert hasattr(extractor, 'temperature_patterns')
        assert hasattr(extractor, 'population_patterns')
        assert hasattr(extractor, 'financial_patterns')
    
    def test_extract_temperatures_celsius(self, sample_text_with_temperatures):
        """Test temperature extraction in Celsius"""
        extractor = NumberExtractor()
        temps = extractor._extract_temperatures(sample_text_with_temperatures)
        assert len(temps) > 0
        assert 35.0 in temps or any(abs(t - 35.0) < 0.1 for t in temps)
    
    def test_extract_temperatures_fahrenheit_conversion(self):
        """Test Fahrenheit to Celsius conversion"""
        extractor = NumberExtractor()
        text = "Temperature reached 77F today"
        temps = extractor._extract_temperatures(text)
        # 77F = 25C
        assert any(abs(t - 25.0) < 1.0 for t in temps)
    
    def test_extract_population_million(self, sample_text_with_population):
        """Test population extraction with million multiplier"""
        extractor = NumberExtractor()
        population = extractor._extract_population(sample_text_with_population)
        assert len(population) > 0
        # Should extract 2 million = 2,000,000
        assert any(p == 2000000 or abs(p - 2000000) < 1000 for p in population)
    
    def test_extract_population_billion(self):
        """Test population extraction with billion multiplier"""
        extractor = NumberExtractor()
        text = "Approximately 3.5 billion people live in vulnerable areas"
        population = extractor._extract_population(text)
        assert len(population) > 0
        # Should extract 3.5 billion = 3,500,000,000
        assert any(p == 3500000000 or abs(p - 3500000000) < 1000000 for p in population)
    
    def test_extract_financial_million(self, sample_text_with_financial):
        """Test financial amount extraction with million multiplier"""
        extractor = NumberExtractor()
        amounts = extractor._extract_financial(sample_text_with_financial)
        assert len(amounts) > 0
        # Should extract $500 million = 500,000,000
        assert any(abs(a - 500000000) < 1000 for a in amounts)
    
    def test_extract_financial_billion(self):
        """Test financial amount extraction with billion multiplier"""
        extractor = NumberExtractor()
        text = "Total aid amounts to 1.5 billion dollars"
        amounts = extractor._extract_financial(text)
        assert len(amounts) > 0
        # Should extract 1.5 billion = 1,500,000,000
        assert any(abs(a - 1500000000) < 1000 for a in amounts)
    
    def test_extract_percentages(self, sample_text_with_percentages):
        """Test percentage extraction"""
        extractor = NumberExtractor()
        percentages = extractor._extract_percentages(sample_text_with_percentages)
        assert len(percentages) > 0
        assert 25.0 in percentages or any(abs(p - 25.0) < 0.1 for p in percentages)
        # All percentages should be between 0 and 100
        assert all(0 <= p <= 100 for p in percentages)
    
    def test_extract_percentages_invalid_range(self):
        """Test that percentages outside 0-100 are filtered"""
        extractor = NumberExtractor()
        text = "The value is 150% which is invalid"
        percentages = extractor._extract_percentages(text)
        # Should not include 150% as it's outside valid range
        assert 150.0 not in percentages
    
    def test_extract_dates(self, sample_text_with_dates):
        """Test date extraction"""
        extractor = NumberExtractor()
        dates = extractor._extract_dates(sample_text_with_dates)
        assert len(dates) > 0
        # Should extract various date formats
        assert any('2025' in d for d in dates)
    
    def test_extract_all_comprehensive(self, sample_text_comprehensive):
        """Test comprehensive extraction with all data types"""
        extractor = NumberExtractor()
        result = extractor.extract_all(sample_text_comprehensive)
        
        assert isinstance(result, ExtractedNumbers)
        assert len(result.temperatures) > 0
        assert len(result.population_numbers) > 0
        assert len(result.financial_amounts) > 0
        assert len(result.percentages) > 0
        assert len(result.dates) > 0
    
    def test_extract_all_empty_text(self):
        """Test extraction with empty text"""
        extractor = NumberExtractor()
        result = extractor.extract_all("")
        
        assert isinstance(result, ExtractedNumbers)
        assert result.temperatures == []
        assert result.population_numbers == []
        assert result.financial_amounts == []
        assert result.percentages == []
        assert result.dates == []
    
    def test_extract_all_none(self):
        """Test extraction with None input"""
        extractor = NumberExtractor()
        result = extractor.extract_all(None)
        
        assert isinstance(result, ExtractedNumbers)
        assert result.temperatures == []
    
    def test_extract_affected_people(self):
        """Test affected people extraction"""
        extractor = NumberExtractor()
        text = "Over 2 million people are affected by the crisis"
        affected = extractor._extract_affected_people(text)
        assert affected is not None
        assert affected == 2000000
    
    def test_extract_funding_amount(self):
        """Test funding amount extraction"""
        extractor = NumberExtractor()
        text = "The UN has allocated $500 million USD in funding"
        funding = extractor._extract_funding_amount(text)
        assert funding is not None
        assert abs(funding - 500000000) < 1000
    
    def test_extract_locations(self):
        """Test location extraction"""
        extractor = NumberExtractor()
        text = "The crisis in East Africa region has worsened"
        locations = extractor._extract_locations(text)
        # Should extract "East Africa" from "East Africa region"
        assert len(locations) > 0
    
    def test_extract_precipitation_mm(self):
        """Test precipitation extraction in mm"""
        extractor = NumberExtractor()
        text = "Precipitation of 50mm was recorded"
        precipitation = extractor._extract_precipitation(text)
        assert len(precipitation) > 0
        assert any(abs(p - 50.0) < 0.1 for p in precipitation)
    
    def test_extract_precipitation_inches_conversion(self):
        """Test precipitation extraction with inches to mm conversion"""
        extractor = NumberExtractor()
        text = "Rainfall of 2 inches was recorded"
        precipitation = extractor._extract_precipitation(text)
        assert len(precipitation) > 0
        # 2 inches = 50.8 mm
        assert any(abs(p - 50.8) < 1.0 for p in precipitation)
    
    def test_duplicate_removal(self):
        """Test that duplicate values are removed"""
        extractor = NumberExtractor()
        text = "Temperature is 25°C. The temperature was 25C yesterday."
        temps = extractor._extract_temperatures(text)
        # Should only have one instance of 25.0
        assert temps.count(25.0) <= 1 or len(set(temps)) == len(temps)
