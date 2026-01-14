#!/usr/bin/env python3
"""
Direkter Test des Climate Conflict Scraping Systems
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
from rich.console import Console

console = Console()

async def test_direct_scraping():
    """Test direkte HTTP-Anfrage"""
    console.print("🚀 [bold green]Testing Direct HTTP Scraping[/bold green]")
    
    # Test URLs
    test_urls = [
        "https://earthobservatory.nasa.gov/global-maps",
        "https://press.un.org/en",
        "https://www.wfp.org/news",
        "https://www.worldbank.org/en/news"
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for url in test_urls:
            try:
                console.print(f"📡 Testing: {url}")
                
                response = await client.get(url, follow_redirects=True)
                
                if response.status_code == 200:
                    console.print(f"✅ Status: {response.status_code} - {len(response.text)} chars")
                    
                    # Parse with BeautifulSoup
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Count elements
                    titles = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    links = soup.find_all('a', href=True)
                    images = soup.find_all('img')
                    
                    console.print(f"  📊 Found: {len(titles)} headings, {len(links)} links, {len(images)} images")
                    
                    # Show first few titles
                    for i, title in enumerate(titles[:3]):
                        if title.get_text().strip():
                            console.print(f"    {i+1}. {title.get_text().strip()[:60]}...")
                            
                else:
                    console.print(f"❌ Status: {response.status_code}")
                    
            except Exception as e:
                console.print(f"❌ Error with {url}: {e}")
            
            console.print()  # Empty line

if __name__ == "__main__":
    asyncio.run(test_direct_scraping())
