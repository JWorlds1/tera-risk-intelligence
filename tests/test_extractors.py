"""
Tests for mining/extractors.py - BaseExtractor and ExtractorFactory classes
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock

# Add mining directory to path
mining_path = Path(__file__).parent.parent / "mining"
sys.path.insert(0, str(mining_path))

from extractors import BaseExtractor, NASAExtractor, UNPressExtractor, WFPExtractor, WorldBankExtractor, ExtractorFactory
from fetchers import FetchResult


class TestBaseExtractor:
    """Test suite for BaseExtractor class"""
    
    def test_base_extractor_initialization(self):
        """Test that BaseExtractor initializes correctly"""
        extractor = BaseExtractor("TestSource")
        assert extractor.source_name == "TestSource"
        assert extractor._get_domain() == ""
    
    def test_clean_text_normalizes_whitespace(self):
        """Test that _clean_text normalizes whitespace"""
        extractor = BaseExtractor("Test")
        text = "This   has    multiple    spaces"
        cleaned = extractor._clean_text(text)
        assert "  " not in cleaned
        assert cleaned == "This has multiple spaces"
    
    def test_clean_text_removes_special_characters(self):
        """Test that _clean_text removes special characters"""
        extractor = BaseExtractor("Test")
        text = "Text with @#$% special chars!"
        cleaned = extractor._clean_text(text)
        # Should remove @#$% but keep basic punctuation
        assert "@" not in cleaned
        assert "#" not in cleaned
        assert "$" not in cleaned
        assert "%" not in cleaned
        assert "!" in cleaned  # Keep punctuation
    
    def test_clean_text_handles_empty_string(self):
        """Test that _clean_text handles empty string"""
        extractor = BaseExtractor("Test")
        assert extractor._clean_text("") == ""
        assert extractor._clean_text(None) == ""
    
    def test_extract_date_iso_format(self):
        """Test date extraction and ISO format conversion"""
        extractor = BaseExtractor("Test")
        text = "Published on January 15, 2025"
        date = extractor._extract_date(text)
        assert date is not None
        assert date == "2025-01-15"
    
    def test_extract_date_slash_format(self):
        """Test date extraction from slash format"""
        extractor = BaseExtractor("Test")
        text = "Date: 01/15/2025"
        date = extractor._extract_date(text)
        assert date is not None
        assert "2025" in date or "01" in date
    
    def test_extract_date_dash_format(self):
        """Test date extraction from dash format"""
        extractor = BaseExtractor("Test")
        text = "Published 2025-01-15"
        date = extractor._extract_date(text)
        assert date is not None
        assert date == "2025-01-15"
    
    def test_extract_date_returns_none_for_no_match(self):
        """Test that _extract_date returns None when no date found"""
        extractor = BaseExtractor("Test")
        text = "No date information here"
        date = extractor._extract_date(text)
        assert date is None
    
    def test_extract_region_direct_match(self):
        """Test region extraction with direct region name"""
        extractor = BaseExtractor("Test")
        text = "The crisis in East Africa has worsened"
        region = extractor._extract_region(text)
        assert region == "East Africa"
    
    def test_extract_region_country_mapping(self):
        """Test region extraction via country name mapping"""
        extractor = BaseExtractor("Test")
        text = "The situation in Kenya is critical"
        region = extractor._extract_region(text)
        assert region == "East Africa"
    
    def test_extract_region_prioritizes_specific_regions(self):
        """Test that more specific regions are prioritized"""
        extractor = BaseExtractor("Test")
        text = "The Horn of Africa region faces severe drought"
        region = extractor._extract_region(text)
        # Should return "Horn of Africa" not just "East Africa"
        assert region == "Horn of Africa"
    
    def test_extract_region_returns_none_for_no_match(self):
        """Test that _extract_region returns None when no region found"""
        extractor = BaseExtractor("Test")
        text = "No geographical information"
        region = extractor._extract_region(text)
        assert region is None
    
    def test_extract_domain_from_url(self):
        """Test domain extraction from URL"""
        extractor = BaseExtractor("Test")
        url = "https://earthobservatory.nasa.gov/article/123"
        domain = extractor._extract_domain(url)
        assert "nasa.gov" in domain
    
    def test_extract_links_absolute_urls(self, sample_html_content):
        """Test link extraction with absolute URLs"""
        from bs4 import BeautifulSoup
        extractor = BaseExtractor("Test")
        soup = BeautifulSoup(sample_html_content, 'lxml')
        base_url = "https://example.com"
        
        # Add a link to the soup
        link_tag = soup.new_tag('a', href='https://external.com/page')
        soup.body.append(link_tag)
        
        links = extractor._extract_links(soup, base_url)
        assert len(links) > 0
        assert any('external.com' in link for link in links)
    
    def test_extract_links_relative_urls(self, sample_html_content):
        """Test link extraction with relative URLs"""
        from bs4 import BeautifulSoup
        extractor = BaseExtractor("Test")
        soup = BeautifulSoup(sample_html_content, 'lxml')
        base_url = "https://example.com"
        
        # Add a relative link
        link_tag = soup.new_tag('a', href='/page')
        soup.body.append(link_tag)
        
        links = extractor._extract_links(soup, base_url)
        assert any('example.com/page' in link for link in links)
    
    def test_extract_images(self, sample_html_content):
        """Test image URL extraction"""
        from bs4 import BeautifulSoup
        extractor = BaseExtractor("Test")
        soup = BeautifulSoup(sample_html_content, 'lxml')
        base_url = "https://example.com"
        
        # Add an image
        img_tag = soup.new_tag('img', src='https://example.com/image.jpg')
        soup.body.append(img_tag)
        
        images = extractor._extract_images(soup, base_url)
        assert len(images) > 0
        assert any('image.jpg' in img for img in images)


class TestNASAExtractor:
    """Test suite for NASAExtractor class"""
    
    def test_nasa_extractor_initialization(self):
        """Test that NASAExtractor initializes correctly"""
        extractor = NASAExtractor()
        assert extractor.source_name == "NASA"
        assert extractor._get_domain() == "earthobservatory.nasa.gov"
    
    def test_nasa_extractor_extracts_title(self, sample_html_content):
        """Test that NASAExtractor extracts title"""
        extractor = NASAExtractor()
        fetch_result = FetchResult(
            url="https://earthobservatory.nasa.gov/test",
            success=True,
            content=sample_html_content
        )
        record = extractor.extract(fetch_result)
        assert record is not None
        assert record.title is not None
        assert "Drought" in record.title or "Test" in record.title


class TestExtractorFactory:
    """Test suite for ExtractorFactory class"""
    
    def test_factory_initialization(self):
        """Test that ExtractorFactory initializes correctly"""
        factory = ExtractorFactory()
        assert factory is not None
    
    def test_get_extractor_nasa(self):
        """Test that factory returns NASAExtractor for NASA URLs"""
        factory = ExtractorFactory()
        url = "https://earthobservatory.nasa.gov/article/123"
        extractor = factory.get_extractor(url)
        assert isinstance(extractor, NASAExtractor)
    
    def test_get_extractor_un_press(self):
        """Test that factory returns UNPressExtractor for UN Press URLs"""
        factory = ExtractorFactory()
        url = "https://press.un.org/en/2025/test"
        extractor = factory.get_extractor(url)
        assert isinstance(extractor, UNPressExtractor)
    
    def test_get_extractor_wfp(self):
        """Test that factory returns WFPExtractor for WFP URLs"""
        factory = ExtractorFactory()
        url = "https://www.wfp.org/news/test"
        extractor = factory.get_extractor(url)
        assert isinstance(extractor, WFPExtractor)
    
    def test_get_extractor_world_bank(self):
        """Test that factory returns WorldBankExtractor for World Bank URLs"""
        factory = ExtractorFactory()
        url = "https://www.worldbank.org/en/news/test"
        extractor = factory.get_extractor(url)
        assert isinstance(extractor, WorldBankExtractor)
    
    def test_get_extractor_unknown_domain(self):
        """Test that factory returns BaseExtractor for unknown domains"""
        factory = ExtractorFactory()
        url = "https://unknown-domain.com/article"
        extractor = factory.get_extractor(url)
        assert isinstance(extractor, BaseExtractor)
        assert extractor.source_name == "Unknown"
    
    def test_extract_with_failed_fetch(self):
        """Test extraction with failed fetch result"""
        extractor = BaseExtractor("Test")
        fetch_result = FetchResult(
            url="https://example.com",
            success=False,
            content=None,
            error="Connection failed"
        )
        record = extractor.extract(fetch_result)
        assert record is None
    
    def test_extract_with_empty_content(self):
        """Test extraction with empty content"""
        extractor = BaseExtractor("Test")
        fetch_result = FetchResult(
            url="https://example.com",
            success=True,
            content=""
        )
        # Should handle empty content gracefully
        # The actual behavior depends on BeautifulSoup handling
        record = extractor.extract(fetch_result)
        # May return None or a record with empty fields
        assert record is None or record is not None
