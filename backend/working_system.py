#!/usr/bin/env python3
"""
Funktionierendes Climate Conflict Scraping System
Vereinfachte Version ohne komplexe Dependencies
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import Progress, TaskID
from datetime import datetime
import json
import csv
from pathlib import Path
import structlog

# Setup logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
console = Console()

class ClimateConflictScraper:
    """Vereinfachter Climate Conflict Scraper"""
    
    def __init__(self):
        self.data_dir = Path("./data")
        self.data_dir.mkdir(exist_ok=True)
        
        self.sources = {
            "nasa": {
                "name": "NASA Earth Observatory",
                "urls": [
                    "https://earthobservatory.nasa.gov/global-maps",
                    "https://earthobservatory.nasa.gov/world-of-change",
                    "https://earthobservatory.nasa.gov/features",
                    "https://earthobservatory.nasa.gov/images",
                ]
            },
            "un": {
                "name": "UN Press",
                "urls": [
                    "https://press.un.org/en",
                    "https://press.un.org/en/content/press-releases",
                    "https://press.un.org/en/content/meetings-coverage",
                ]
            },
            "worldbank": {
                "name": "World Bank",
                "urls": [
                    "https://www.worldbank.org/en/news",
                    "https://www.worldbank.org/en/news/press-release",
                    "https://www.worldbank.org/en/news/feature",
                ]
            }
        }
        
        self.stats = {
            'total_urls': 0,
            'successful': 0,
            'failed': 0,
            'extracted_records': 0,
            'start_time': None,
            'end_time': None
        }
    
    def extract_nasa_data(self, soup, url):
        """Extract data from NASA pages"""
        records = []
        
        # Find articles/features
        articles = soup.find_all(['article', 'div'], class_=lambda x: x and ('article' in x.lower() or 'feature' in x.lower() or 'story' in x.lower()))
        
        for article in articles:
            try:
                title_elem = article.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                title = title_elem.get_text().strip() if title_elem else "No title"
                
                # Find description
                desc_elem = article.find(['p', 'div'], class_=lambda x: x and ('description' in x.lower() or 'summary' in x.lower() or 'excerpt' in x.lower()))
                description = desc_elem.get_text().strip() if desc_elem else ""
                
                # Find date
                date_elem = article.find(['time', 'span', 'div'], class_=lambda x: x and ('date' in x.lower() or 'time' in x.lower()))
                date = date_elem.get_text().strip() if date_elem else ""
                
                # Find region/topic
                region_elem = article.find(['span', 'div'], class_=lambda x: x and ('region' in x.lower() or 'location' in x.lower() or 'area' in x.lower()))
                region = region_elem.get_text().strip() if region_elem else ""
                
                if title and title != "No title":
                    records.append({
                        'title': title,
                        'description': description,
                        'date': date,
                        'region': region,
                        'url': url,
                        'source': 'nasa',
                        'extracted_at': datetime.now().isoformat()
                    })
            except Exception as e:
                logger.warning("Error extracting NASA article", error=str(e))
                continue
        
        return records
    
    def extract_un_data(self, soup, url):
        """Extract data from UN Press pages"""
        records = []
        
        # Find news items
        news_items = soup.find_all(['div', 'article'], class_=lambda x: x and ('news' in x.lower() or 'press' in x.lower() or 'release' in x.lower()))
        
        for item in news_items:
            try:
                title_elem = item.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                title = title_elem.get_text().strip() if title_elem else "No title"
                
                # Find description
                desc_elem = item.find(['p', 'div'], class_=lambda x: x and ('description' in x.lower() or 'summary' in x.lower() or 'excerpt' in x.lower()))
                description = desc_elem.get_text().strip() if desc_elem else ""
                
                # Find date
                date_elem = item.find(['time', 'span', 'div'], class_=lambda x: x and ('date' in x.lower() or 'time' in x.lower()))
                date = date_elem.get_text().strip() if date_elem else ""
                
                # Find topics
                topics_elem = item.find(['div', 'span'], class_=lambda x: x and ('topic' in x.lower() or 'tag' in x.lower() or 'category' in x.lower()))
                topics = topics_elem.get_text().strip() if topics_elem else ""
                
                if title and title != "No title":
                    records.append({
                        'title': title,
                        'description': description,
                        'date': date,
                        'topics': topics,
                        'url': url,
                        'source': 'un',
                        'extracted_at': datetime.now().isoformat()
                    })
            except Exception as e:
                logger.warning("Error extracting UN article", error=str(e))
                continue
        
        return records
    
    def extract_worldbank_data(self, soup, url):
        """Extract data from World Bank pages"""
        records = []
        
        # Find news items
        news_items = soup.find_all(['div', 'article'], class_=lambda x: x and ('news' in x.lower() or 'press' in x.lower() or 'release' in x.lower() or 'story' in x.lower()))
        
        for item in news_items:
            try:
                title_elem = item.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                title = title_elem.get_text().strip() if title_elem else "No title"
                
                # Find description
                desc_elem = item.find(['p', 'div'], class_=lambda x: x and ('description' in x.lower() or 'summary' in x.lower() or 'excerpt' in x.lower()))
                description = desc_elem.get_text().strip() if desc_elem else ""
                
                # Find date
                date_elem = item.find(['time', 'span', 'div'], class_=lambda x: x and ('date' in x.lower() or 'time' in x.lower()))
                date = date_elem.get_text().strip() if date_elem else ""
                
                # Find country/sector
                country_elem = item.find(['span', 'div'], class_=lambda x: x and ('country' in x.lower() or 'region' in x.lower() or 'location' in x.lower()))
                country = country_elem.get_text().strip() if country_elem else ""
                
                sector_elem = item.find(['span', 'div'], class_=lambda x: x and ('sector' in x.lower() or 'topic' in x.lower() or 'category' in x.lower()))
                sector = sector_elem.get_text().strip() if sector_elem else ""
                
                if title and title != "No title":
                    records.append({
                        'title': title,
                        'description': description,
                        'date': date,
                        'country': country,
                        'sector': sector,
                        'url': url,
                        'source': 'worldbank',
                        'extracted_at': datetime.now().isoformat()
                    })
            except Exception as e:
                logger.warning("Error extracting World Bank article", error=str(e))
                continue
        
        return records
    
    async def scrape_url(self, url, source):
        """Scrape a single URL"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, follow_redirects=True)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract data based on source
                    if source == 'nasa':
                        records = self.extract_nasa_data(soup, url)
                    elif source == 'un':
                        records = self.extract_un_data(soup, url)
                    elif source == 'worldbank':
                        records = self.extract_worldbank_data(soup, url)
                    else:
                        records = []
                    
                    return records
                else:
                    logger.warning("HTTP error", url=url, status=response.status_code)
                    return []
                    
        except Exception as e:
            logger.error("Scraping error", url=url, error=str(e))
            return []
    
    async def scrape_source(self, source_key):
        """Scrape all URLs for a source"""
        source_data = self.sources[source_key]
        console.print(f"🌍 [bold blue]Scraping {source_data['name']}[/bold blue]")
        
        urls = source_data['urls']
        console.print(f"📊 Found {len(urls)} URLs to scrape")
        
        all_records = []
        
        with Progress() as progress:
            task = progress.add_task(f"Scraping {source_data['name']}...", total=len(urls))
            
            for url in urls:
                records = await self.scrape_url(url, source_key)
                all_records.extend(records)
                
                if records:
                    console.print(f"✅ {url}: {len(records)} records")
                    self.stats['extracted_records'] += len(records)
                else:
                    console.print(f"⚠️  {url}: No records extracted")
                
                self.stats['successful'] += 1
                progress.update(task, advance=1)
                
                # Rate limiting
                await asyncio.sleep(1.0)
        
        return all_records
    
    def save_data(self, records, source):
        """Save data to files"""
        if not records:
            return
        
        # Save as JSON
        json_file = self.data_dir / f"{source}_data.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        
        # Save as CSV
        csv_file = self.data_dir / f"{source}_data.csv"
        if records:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=records[0].keys())
                writer.writeheader()
                writer.writerows(records)
        
        console.print(f"💾 Saved {len(records)} records to {json_file} and {csv_file}")
    
    async def run_scraping_session(self, sources=None):
        """Run complete scraping session"""
        if sources is None:
            sources = ['nasa', 'un', 'worldbank']
        
        self.stats['start_time'] = datetime.now()
        
        console.print("🚀 [bold green]Starting Climate Conflict Scraping Session[/bold green]")
        console.print(f"📊 Sources: {', '.join(sources)}")
        
        all_results = {}
        
        for source in sources:
            if source in self.sources:
                try:
                    records = await self.scrape_source(source)
                    all_results[source] = records
                    self.save_data(records, source)
                except Exception as e:
                    console.print(f"❌ Error scraping {source}: {e}")
                    logger.error("Source scraping error", source=source, error=str(e))
            else:
                console.print(f"❌ Unknown source: {source}")
        
        self.stats['end_time'] = datetime.now()
        self.stats['total_urls'] = sum(len(self.sources[s]['urls']) for s in sources if s in self.sources)
        
        # Print summary
        console.print("\n📊 [bold green]Scraping Summary[/bold green]")
        console.print(f"⏱️  Duration: {self.stats['end_time'] - self.stats['start_time']}")
        console.print(f"🌐 Total URLs: {self.stats['total_urls']}")
        console.print(f"✅ Successful: {self.stats['successful']}")
        console.print(f"❌ Failed: {self.stats['failed']}")
        console.print(f"📊 Records Extracted: {self.stats['extracted_records']}")
        
        return all_results

async def main():
    """Main function"""
    scraper = ClimateConflictScraper()
    
    # Test with all sources
    results = await scraper.run_scraping_session(['nasa', 'un', 'worldbank'])
    
    console.print("\n🎉 [bold green]Scraping completed![/bold green]")
    console.print(f"📁 Data saved to: {scraper.data_dir}")

if __name__ == "__main__":
    asyncio.run(main())
