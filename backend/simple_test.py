#!/usr/bin/env python3
"""
Einfacher Test des Climate Conflict Scraping Systems
Nur HTTP-basiert, ohne Playwright
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from config import Config
from fetchers import HTTPFetcher
from extractors import NASAExtractor
from schemas import PageRecord
from compliance import ComplianceAgent
from rich.console import Console

console = Console()

async def test_http_scraping():
    """Test HTTP-only scraping"""
    console.print("🚀 [bold green]Testing HTTP Scraping System[/bold green]")
    
    # Test URL
    test_url = "https://earthobservatory.nasa.gov/global-maps"
    
    try:
        # Initialize components
        config = Config()
        compliance_agent = ComplianceAgent(config)
        fetcher = HTTPFetcher(config, compliance_agent)
        extractor = NASAExtractor()
        
        console.print(f"📡 Fetching: {test_url}")
        
        # Fetch content
        result = await fetcher.fetch(test_url)
        
        if result and result.content:
            console.print(f"✅ Successfully fetched {len(result.content)} characters")
            
            # Extract data
            extracted_data = extractor.extract(result.content, test_url)
            
            if extracted_data:
                console.print(f"📊 Extracted {len(extracted_data)} records")
                for i, record in enumerate(extracted_data[:3]):  # Show first 3
                    console.print(f"  {i+1}. {record.title[:50]}...")
            else:
                console.print("⚠️  No data extracted")
        else:
            console.print("❌ Failed to fetch content")
            
    except Exception as e:
        console.print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_http_scraping())
