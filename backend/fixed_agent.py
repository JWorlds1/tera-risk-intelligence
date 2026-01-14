#!/usr/bin/env python3
"""
Fixed Climate Conflict Agent System
Reparierte Extraktion mit Fallback-Methoden
"""

import asyncio
import json
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import structlog
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import httpx
import firecrawl
from bs4 import BeautifulSoup
import schedule

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

class FixedClimateAgent:
    """Reparierter Climate Conflict Agent mit robusten Extraktionsmethoden"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = Path("./climate_agent_fixed.db")
        self.memory_path = Path("./agent_memory")
        self.memory_path.mkdir(exist_ok=True)
        
        # Initialize Firecrawl with error handling
        try:
            self.firecrawl = firecrawl.FirecrawlApp(api_key=config.get('FIRECRAWL_API_KEY'))
            self.firecrawl_available = True
        except Exception as e:
            console.print(f"⚠️ [yellow]Firecrawl not available: {e}[/yellow]")
            self.firecrawl_available = False
        
        # Initialize database
        self.init_database()
        
        # Agent state
        self.is_running = False
        self.last_analysis = None
        self.analysis_interval = config.get('ANALYSIS_INTERVAL', 1800)  # 30 minutes
        
        # Data sources
        self.sources = {
            'nasa': {
                'name': 'NASA Earth Observatory',
                'urls': [
                    'https://earthobservatory.nasa.gov/global-maps',
                    'https://earthobservatory.nasa.gov/world-of-change',
                    'https://earthobservatory.nasa.gov/features',
                ]
            },
            'un_press': {
                'name': 'UN Press',
                'urls': [
                    'https://press.un.org/en',
                    'https://press.un.org/en/content/meetings-coverage',
                ]
            },
            'worldbank': {
                'name': 'World Bank',
                'urls': [
                    'https://www.worldbank.org/en/news',
                    'https://www.worldbank.org/en/news/feature',
                ]
            }
        }
        
        # Conflict risk indicators
        self.conflict_indicators = {
            'high_risk': [
                'war', 'conflict', 'violence', 'crisis', 'emergency',
                'military', 'armed', 'attack', 'bombing', 'terrorism'
            ],
            'climate_risk': [
                'drought', 'famine', 'flooding', 'hurricane', 'typhoon',
                'heat wave', 'water shortage', 'crop failure', 'desertification'
            ],
            'social_risk': [
                'migration', 'displacement', 'refugee', 'protest', 'riot',
                'unrest', 'strike', 'demonstration', 'evacuation'
            ],
            'economic_risk': [
                'recession', 'inflation', 'unemployment', 'poverty',
                'food security', 'resource scarcity', 'trade war'
            ]
        }
    
    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS extracted_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                url TEXT NOT NULL,
                title TEXT,
                content TEXT,
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT FALSE,
                conflict_risk_score REAL DEFAULT 0.0,
                region TEXT,
                country TEXT,
                keywords TEXT,
                raw_data TEXT,
                extraction_method TEXT DEFAULT 'http'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_type TEXT NOT NULL,
                results TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                confidence REAL DEFAULT 0.0,
                region TEXT,
                risk_level TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def extract_with_http(self, url: str, source: str) -> List[Dict]:
        """Robuste HTTP-basierte Extraktion als Fallback"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, follow_redirects=True)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    return self.parse_html_content(soup, source, url)
                else:
                    logger.warning("HTTP error", url=url, status=response.status_code)
                    return []
                    
        except Exception as e:
            logger.error("HTTP extraction failed", url=url, error=str(e))
            return []
    
    def parse_html_content(self, soup: BeautifulSoup, source: str, url: str) -> List[Dict]:
        """Parse HTML content and extract relevant data"""
        records = []
        
        # Find articles/items based on source
        if source == 'nasa':
            articles = soup.find_all(['article', 'div'], class_=lambda x: x and (
                'article' in x.lower() or 'feature' in x.lower() or 'story' in x.lower() or
                'post' in x.lower() or 'content' in x.lower()
            ))
        elif source == 'un_press':
            articles = soup.find_all(['div', 'article'], class_=lambda x: x and (
                'news' in x.lower() or 'press' in x.lower() or 'release' in x.lower() or
                'meeting' in x.lower() or 'coverage' in x.lower()
            ))
        elif source == 'worldbank':
            articles = soup.find_all(['div', 'article'], class_=lambda x: x and (
                'news' in x.lower() or 'press' in x.lower() or 'release' in x.lower() or
                'feature' in x.lower() or 'story' in x.lower()
            ))
        else:
            articles = soup.find_all(['article', 'div'], class_=lambda x: x and (
                'article' in x.lower() or 'news' in x.lower() or 'content' in x.lower()
            ))
        
        # If no specific articles found, try to find any content containers
        if not articles:
            articles = soup.find_all(['div', 'section'], class_=lambda x: x and (
                'content' in x.lower() or 'main' in x.lower() or 'body' in x.lower()
            ))
        
        # If still no articles, use the whole page
        if not articles:
            articles = [soup]
        
        for article in articles:
            try:
                # Extract title
                title_elem = article.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                title = title_elem.get_text().strip() if title_elem else ""
                
                # Skip if no title or very short
                if not title or len(title) < 10:
                    continue
                
                # Extract description/content
                desc_elem = article.find(['p', 'div'], class_=lambda x: x and (
                    'description' in x.lower() or 'summary' in x.lower() or 
                    'excerpt' in x.lower() or 'content' in x.lower()
                ))
                
                if not desc_elem:
                    # Try to find any paragraph
                    desc_elem = article.find('p')
                
                description = desc_elem.get_text().strip() if desc_elem else ""
                
                # Extract date
                date_elem = article.find(['time', 'span', 'div'], class_=lambda x: x and (
                    'date' in x.lower() or 'time' in x.lower() or 'published' in x.lower()
                ))
                date = date_elem.get_text().strip() if date_elem else ""
                
                # Extract region/country
                region_elem = article.find(['span', 'div'], class_=lambda x: x and (
                    'region' in x.lower() or 'location' in x.lower() or 
                    'area' in x.lower() or 'country' in x.lower()
                ))
                region = region_elem.get_text().strip() if region_elem else ""
                
                # Calculate conflict risk score
                content_text = (title + ' ' + description).lower()
                risk_score = self.calculate_conflict_risk(content_text)
                
                # Create record
                record = {
                    'source': source,
                    'url': url,
                    'title': title,
                    'content': description,
                    'date': date,
                    'region': region,
                    'extracted_at': datetime.now().isoformat(),
                    'conflict_risk_score': risk_score,
                    'extraction_method': 'http',
                    'raw_data': json.dumps({
                        'title': title,
                        'content': description,
                        'date': date,
                        'region': region
                    })
                }
                
                records.append(record)
                
            except Exception as e:
                logger.warning("Error parsing article", error=str(e))
                continue
        
        return records
    
    async def extract_with_firecrawl(self, url: str, source: str) -> List[Dict]:
        """Firecrawl extraction with fallback"""
        if not self.firecrawl_available:
            return await self.extract_with_http(url, source)
        
        try:
            # Try multiple Firecrawl signatures for compatibility across versions
            result = None
            try:
                # Newer signature variants (dict payload)
                result = self.firecrawl.extract({
                    'url': url,
                    'onlyMainContent': True,
                    'removeBase64Images': True
                })
            except TypeError:
                try:
                    # Legacy signature with kwargs
                    result = self.firecrawl.extract(
                        url=url,
                        onlyMainContent=True,
                        removeBase64Images=True
                    )
                except TypeError:
                    try:
                        # Minimal signature
                        result = self.firecrawl.extract(url)
                    except Exception:
                        result = None
            
            # Normalize result
            data_block = None
            if isinstance(result, dict):
                data_block = result.get('data') or result.get('results') or result.get('page') or result
            else:
                data_block = result
            
            if data_block:
                extracted_data = data_block
                
                # Process extracted data
                processed_data = []
                if isinstance(extracted_data, dict):  # single object
                    processed = self.process_firecrawl_data(extracted_data, source, url)
                    if processed:
                        processed_data.append(processed)
                elif isinstance(extracted_data, list):  # list of objects
                    for item in extracted_data:
                        processed = self.process_firecrawl_data(item, source, url)
                        if processed:
                            processed_data.append(processed)
                
                return processed_data
            else:
                # Fallback to HTTP if Firecrawl fails
                return await self.extract_with_http(url, source)
                
        except Exception as e:
            logger.error("Firecrawl extraction failed", url=url, error=str(e))
            # Fallback to HTTP
            return await self.extract_with_http(url, source)
    
    def process_firecrawl_data(self, item: Dict, source: str, url: str) -> Optional[Dict]:
        """Process Firecrawl extracted data"""
        try:
            title = item.get('title', '') or item.get('headline', '')
            content = item.get('content', '') or item.get('description', '') or item.get('text', '')
            
            if not title or len(title) < 10:
                return None
            
            # Calculate conflict risk
            content_text = (title + ' ' + content).lower()
            risk_score = self.calculate_conflict_risk(content_text)
            
            processed = {
                'source': source,
                'url': url,
                'title': title,
                'content': content,
                'date': item.get('date', '') or item.get('published', ''),
                'region': item.get('region', '') or item.get('country', '') or item.get('location', ''),
                'extracted_at': datetime.now().isoformat(),
                'conflict_risk_score': risk_score,
                'extraction_method': 'firecrawl',
                'raw_data': json.dumps(item)
            }
            
            return processed
            
        except Exception as e:
            logger.error("Firecrawl data processing failed", error=str(e))
            return None
    
    def calculate_conflict_risk(self, text: str) -> float:
        """Calculate conflict risk score"""
        risk_score = 0.0
        total_indicators = 0
        
        for category, indicators in self.conflict_indicators.items():
            category_score = 0
            for indicator in indicators:
                if indicator in text:
                    category_score += 1
            
            if category_score > 0:
                risk_score += category_score / len(indicators)
                total_indicators += 1
        
        if total_indicators > 0:
            return min(risk_score / total_indicators, 1.0)
        
        return 0.0
    
    async def store_extracted_data(self, data: List[Dict]):
        """Store extracted data in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for item in data:
            cursor.execute('''
                INSERT INTO extracted_data 
                (source, url, title, content, region, country, keywords, raw_data, 
                 conflict_risk_score, extraction_method)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item['source'],
                item['url'],
                item['title'],
                item['content'],
                item['region'],
                item.get('country', ''),
                json.dumps(item.get('keywords', [])),
                item['raw_data'],
                item['conflict_risk_score'],
                item['extraction_method']
            ))
        
        conn.commit()
        conn.close()
    
    async def analyze_conflict_risk(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze conflict risk from extracted data"""
        analysis = {
            'total_items': len(data),
            'high_risk_items': 0,
            'regions_at_risk': set(),
            'key_indicators': [],
            'confidence': 0.0,
            'recommendations': []
        }
        
        for item in data:
            if item['conflict_risk_score'] > 0.6:
                analysis['high_risk_items'] += 1
                if item['region']:
                    analysis['regions_at_risk'].add(item['region'])
        
        # Generate recommendations
        if analysis['high_risk_items'] > 0:
            analysis['recommendations'].append(
                f"Monitor {len(analysis['regions_at_risk'])} regions for potential conflicts"
            )
        
        analysis['regions_at_risk'] = list(analysis['regions_at_risk'])
        analysis['confidence'] = min(analysis['high_risk_items'] / max(analysis['total_items'], 1), 1.0)
        
        return analysis
    
    async def run_analysis_cycle(self):
        """Run analysis cycle with robust extraction"""
        console.print(f"🔄 [bold blue]Starting analysis cycle at {datetime.now()}[/bold blue]")
        
        all_data = []
        
        # Extract data from all sources
        for source_key, source_info in self.sources.items():
            console.print(f"📡 Extracting from {source_info['name']}...")
            
            for url in source_info['urls']:
                try:
                    # Try Firecrawl first, fallback to HTTP
                    extracted_data = await self.extract_with_firecrawl(url, source_key)
                    all_data.extend(extracted_data)
                    
                    if extracted_data:
                        console.print(f"  ✅ {url}: {len(extracted_data)} items")
                    else:
                        console.print(f"  ⚠️  {url}: No data extracted")
                    
                    # Rate limiting
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    console.print(f"  ❌ {url}: Error - {e}")
                    logger.error("Extraction failed", url=url, error=str(e))
        
        # Store data
        if all_data:
            await self.store_extracted_data(all_data)
            console.print(f"💾 Stored {len(all_data)} items in database")
        
        # Analyze conflict risk
        if all_data:
            analysis = await self.analyze_conflict_risk(all_data)
            
            # Store analysis results
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO analysis_results (analysis_type, results, confidence, risk_level)
                VALUES (?, ?, ?, ?)
            ''', (
                'conflict_risk',
                json.dumps(analysis),
                analysis['confidence'],
                'high' if analysis['high_risk_items'] > 5 else 'medium' if analysis['high_risk_items'] > 0 else 'low'
            ))
            conn.commit()
            conn.close()
            
            # Display results
            console.print(f"\n📊 [bold green]Analysis Results:[/bold green]")
            console.print(f"  Total items: {analysis['total_items']}")
            console.print(f"  High risk items: {analysis['high_risk_items']}")
            console.print(f"  Regions at risk: {', '.join(analysis['regions_at_risk'])}")
            console.print(f"  Confidence: {analysis['confidence']:.2%}")
            
            if analysis['recommendations']:
                console.print(f"  Recommendations: {', '.join(analysis['recommendations'])}")
        
        self.last_analysis = datetime.now()
        console.print(f"✅ Analysis cycle completed at {self.last_analysis}")
    
    async def start_24_7_monitoring(self):
        """Start 24/7 monitoring"""
        console.print("🚀 [bold green]Starting Fixed Climate Conflict Monitoring[/bold green]")
        
        self.is_running = True
        
        # Run initial analysis
        await self.run_analysis_cycle()
        
        # Schedule regular analysis
        while self.is_running:
            try:
                await asyncio.sleep(self.analysis_interval)
                if self.is_running:
                    await self.run_analysis_cycle()
            except KeyboardInterrupt:
                console.print("\n🛑 [yellow]Monitoring stopped by user[/yellow]")
                break
            except Exception as e:
                console.print(f"❌ [red]Error in monitoring loop: {e}[/red]")
                logger.error("Monitoring error", error=str(e))
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_running = False
        console.print("🛑 [yellow]Stopping monitoring...[/yellow]")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM extracted_data")
        total_items = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM extracted_data WHERE conflict_risk_score > 0.6")
        high_risk_items = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM analysis_results")
        total_analyses = cursor.fetchone()[0]
        
        # Recent activity
        cursor.execute("""
            SELECT source, COUNT(*) as count 
            FROM extracted_data 
            WHERE extracted_at > datetime('now', '-24 hours')
            GROUP BY source
        """)
        recent_by_source = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_items': total_items,
            'high_risk_items': high_risk_items,
            'total_analyses': total_analyses,
            'recent_by_source': recent_by_source
        }

async def main():
    """Main function"""
    config = {
        'FIRECRAWL_API_KEY': 'fc-a0b3b8aa31244c10b0f15b4f2d570ac7',
        'ANALYSIS_INTERVAL': 1800,  # 30 minutes
        'MAX_CONCURRENT_REQUESTS': 5
    }
    
    agent = FixedClimateAgent(config)
    
    # Show database stats
    stats = agent.get_database_stats()
    console.print(f"📊 [bold blue]Database Stats:[/bold blue]")
    console.print(f"  Total items: {stats['total_items']}")
    console.print(f"  High risk items: {stats['high_risk_items']}")
    console.print(f"  Recent (24h): {stats['recent_by_source']}")
    
    # Start monitoring
    try:
        await agent.start_24_7_monitoring()
    except KeyboardInterrupt:
        agent.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(main())
