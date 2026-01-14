#!/usr/bin/env python3
"""
Climate Conflict 24/7 Agent System
Inspiriert von Agent Zero mit Memory, Browser-Use und Firecrawl Integration
"""

import asyncio
import json
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
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

class ClimateConflictAgent:
    """24/7 Climate Conflict Monitoring Agent"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = Path("./climate_agent.db")
        self.memory_path = Path("./agent_memory")
        self.memory_path.mkdir(exist_ok=True)
        
        # Initialize Firecrawl
        self.firecrawl = firecrawl.FirecrawlApp(api_key=config.get('FIRECRAWL_API_KEY'))
        
        # Initialize database
        self.init_database()
        
        # Agent state
        self.is_running = False
        self.last_analysis = None
        self.analysis_interval = config.get('ANALYSIS_INTERVAL', 3600)  # 1 hour
        
        # Data sources
        self.sources = {
            'nasa': {
                'name': 'NASA Earth Observatory',
                'urls': [
                    'https://earthobservatory.nasa.gov/global-maps',
                    'https://earthobservatory.nasa.gov/world-of-change',
                    'https://earthobservatory.nasa.gov/features',
                ],
                'extract_schema': {
                    'title': 'string',
                    'description': 'string',
                    'date': 'string',
                    'region': 'string',
                    'climate_impact': 'string',
                    'conflict_risk': 'string'
                }
            },
            'un_press': {
                'name': 'UN Press',
                'urls': [
                    'https://press.un.org/en',
                    'https://press.un.org/en/content/meetings-coverage',
                ],
                'extract_schema': {
                    'title': 'string',
                    'content': 'string',
                    'date': 'string',
                    'region': 'string',
                    'topics': 'array',
                    'conflict_mentions': 'array'
                }
            },
            'worldbank': {
                'name': 'World Bank',
                'urls': [
                    'https://www.worldbank.org/en/news',
                    'https://www.worldbank.org/en/news/feature',
                ],
                'extract_schema': {
                    'title': 'string',
                    'content': 'string',
                    'date': 'string',
                    'country': 'string',
                    'sector': 'string',
                    'economic_impact': 'string'
                }
            }
        }
    
    def init_database(self):
        """Initialize SQLite database for agent memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
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
                keywords TEXT,
                raw_data TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                importance REAL DEFAULT 0.5,
                tags TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_type TEXT NOT NULL,
                results TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                confidence REAL DEFAULT 0.0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def extract_with_firecrawl(self, url: str, source: str) -> List[Dict]:
        """Extract data using Firecrawl API"""
        try:
            # Use Firecrawl extract with custom schema
            schema = self.sources[source]['extract_schema']
            
            result = self.firecrawl.extract(
                url=url,
                schema=schema,
                onlyMainContent=True,
                removeBase64Images=True
            )
            
            if result and 'data' in result:
                extracted_data = result['data']
                
                # Process and normalize data
                processed_data = []
                if isinstance(extracted_data, list):
                    for item in extracted_data:
                        processed_item = self.process_extracted_item(item, source, url)
                        if processed_item:
                            processed_data.append(processed_item)
                elif isinstance(extracted_data, dict):
                    processed_item = self.process_extracted_item(extracted_data, source, url)
                    if processed_item:
                        processed_data.append(processed_item)
                
                return processed_data
            
        except Exception as e:
            logger.error("Firecrawl extraction failed", url=url, error=str(e))
            return []
    
    def process_extracted_item(self, item: Dict, source: str, url: str) -> Optional[Dict]:
        """Process and normalize extracted data"""
        try:
            processed = {
                'source': source,
                'url': url,
                'title': item.get('title', ''),
                'content': item.get('content', '') or item.get('description', ''),
                'date': item.get('date', ''),
                'region': item.get('region', '') or item.get('country', ''),
                'extracted_at': datetime.now().isoformat(),
                'raw_data': json.dumps(item)
            }
            
            # Add source-specific fields
            if source == 'nasa':
                processed['climate_impact'] = item.get('climate_impact', '')
                processed['conflict_risk'] = item.get('conflict_risk', '')
            elif source == 'un_press':
                processed['topics'] = json.dumps(item.get('topics', []))
                processed['conflict_mentions'] = json.dumps(item.get('conflict_mentions', []))
            elif source == 'worldbank':
                processed['sector'] = item.get('sector', '')
                processed['economic_impact'] = item.get('economic_impact', '')
            
            return processed
            
        except Exception as e:
            logger.error("Data processing failed", error=str(e))
            return None
    
    async def store_extracted_data(self, data: List[Dict]):
        """Store extracted data in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for item in data:
            cursor.execute('''
                INSERT INTO extracted_data 
                (source, url, title, content, region, keywords, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                item['source'],
                item['url'],
                item['title'],
                item['content'],
                item['region'],
                json.dumps(item.get('topics', [])),
                item['raw_data']
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
            'confidence': 0.0
        }
        
        # Simple conflict risk analysis
        conflict_keywords = [
            'conflict', 'war', 'violence', 'crisis', 'emergency',
            'drought', 'famine', 'migration', 'displacement',
            'resource scarcity', 'water shortage', 'food security'
        ]
        
        for item in data:
            content = (item.get('title', '') + ' ' + item.get('content', '')).lower()
            
            # Check for conflict indicators
            risk_score = 0
            for keyword in conflict_keywords:
                if keyword in content:
                    risk_score += 1
            
            if risk_score > 2:
                analysis['high_risk_items'] += 1
                if item.get('region'):
                    analysis['regions_at_risk'].add(item['region'])
            
            # Extract key indicators
            if any(keyword in content for keyword in ['climate change', 'global warming']):
                analysis['key_indicators'].append('Climate change mentioned')
            
            if any(keyword in content for keyword in ['migration', 'displacement']):
                analysis['key_indicators'].append('Migration/displacement mentioned')
        
        analysis['regions_at_risk'] = list(analysis['regions_at_risk'])
        analysis['confidence'] = min(analysis['high_risk_items'] / max(analysis['total_items'], 1), 1.0)
        
        return analysis
    
    async def run_analysis_cycle(self):
        """Run one complete analysis cycle"""
        console.print(f"🔄 [bold blue]Starting analysis cycle at {datetime.now()}[/bold blue]")
        
        all_data = []
        
        # Extract data from all sources
        for source_key, source_info in self.sources.items():
            console.print(f"📡 Extracting from {source_info['name']}...")
            
            for url in source_info['urls']:
                try:
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
                INSERT INTO analysis_results (analysis_type, results, confidence)
                VALUES (?, ?, ?)
            ''', ('conflict_risk', json.dumps(analysis), analysis['confidence']))
            conn.commit()
            conn.close()
            
            # Display results
            console.print(f"\n📊 [bold green]Analysis Results:[/bold green]")
            console.print(f"  Total items: {analysis['total_items']}")
            console.print(f"  High risk items: {analysis['high_risk_items']}")
            console.print(f"  Regions at risk: {', '.join(analysis['regions_at_risk'])}")
            console.print(f"  Confidence: {analysis['confidence']:.2%}")
            
            if analysis['key_indicators']:
                console.print(f"  Key indicators: {', '.join(analysis['key_indicators'])}")
        
        self.last_analysis = datetime.now()
        console.print(f"✅ Analysis cycle completed at {self.last_analysis}")
    
    async def start_24_7_monitoring(self):
        """Start 24/7 monitoring"""
        console.print("🚀 [bold green]Starting 24/7 Climate Conflict Monitoring[/bold green]")
        
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
        """Stop 24/7 monitoring"""
        self.is_running = False
        console.print("🛑 [yellow]Stopping monitoring...[/yellow]")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get counts
        cursor.execute("SELECT COUNT(*) FROM extracted_data")
        total_items = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM extracted_data WHERE processed = 1")
        processed_items = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM analysis_results")
        total_analyses = cursor.fetchone()[0]
        
        # Get recent data
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
            'processed_items': processed_items,
            'total_analyses': total_analyses,
            'recent_by_source': recent_by_source
        }

async def main():
    """Main function"""
    config = {
        'FIRECRAWL_API_KEY': 'fc-a0b3b8aa31244c10b0f15b4f2d570ac7',
        'ANALYSIS_INTERVAL': 3600,  # 1 hour
        'MAX_CONCURRENT_REQUESTS': 5
    }
    
    agent = ClimateConflictAgent(config)
    
    # Show database stats
    stats = agent.get_database_stats()
    console.print(f"📊 [bold blue]Database Stats:[/bold blue]")
    console.print(f"  Total items: {stats['total_items']}")
    console.print(f"  Processed: {stats['processed_items']}")
    console.print(f"  Recent (24h): {stats['recent_by_source']}")
    
    # Start monitoring
    try:
        await agent.start_24_7_monitoring()
    except KeyboardInterrupt:
        agent.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(main())

