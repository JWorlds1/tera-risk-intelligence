#!/usr/bin/env python3
"""
Advanced Climate Conflict Agent System
Mit Memory, Browser-Use und erweiterten Analyse-Features
Inspiriert von Agent Zero Architecture
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
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
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

class AgentMemory:
    """Persistent Memory System für den Agent"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_memory_db()
    
    def init_memory_db(self):
        """Initialize memory database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                importance REAL DEFAULT 0.5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                tags TEXT,
                embedding TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learned_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_data TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success_count INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_memory(self, memory_type: str, content: str, importance: float = 0.5, tags: List[str] = None):
        """Store a memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO agent_memories (memory_type, content, importance, tags)
            VALUES (?, ?, ?, ?)
        ''', (memory_type, content, importance, json.dumps(tags or [])))
        
        conn.commit()
        conn.close()
    
    def retrieve_memories(self, memory_type: str = None, limit: int = 10) -> List[Dict]:
        """Retrieve memories"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if memory_type:
            cursor.execute('''
                SELECT * FROM agent_memories 
                WHERE memory_type = ? 
                ORDER BY importance DESC, last_accessed DESC 
                LIMIT ?
            ''', (memory_type, limit))
        else:
            cursor.execute('''
                SELECT * FROM agent_memories 
                ORDER BY importance DESC, last_accessed DESC 
                LIMIT ?
            ''', (limit,))
        
        columns = [description[0] for description in cursor.description]
        memories = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return memories
    
    def update_memory_access(self, memory_id: int):
        """Update memory access statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE agent_memories 
            SET last_accessed = CURRENT_TIMESTAMP, access_count = access_count + 1
            WHERE id = ?
        ''', (memory_id,))
        
        conn.commit()
        conn.close()

class ClimateConflictAgent:
    """Advanced 24/7 Climate Conflict Monitoring Agent"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = Path("./climate_agent_advanced.db")
        self.memory = AgentMemory(str(self.db_path))
        
        # Initialize Firecrawl
        self.firecrawl = firecrawl.FirecrawlApp(api_key=config.get('FIRECRAWL_API_KEY'))
        
        # Initialize database
        self.init_database()
        
        # Agent state
        self.is_running = False
        self.last_analysis = None
        self.analysis_interval = config.get('ANALYSIS_INTERVAL', 1800)  # 30 minutes
        
        # Data sources with enhanced schemas
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
                    'conflict_risk': 'string',
                    'temperature_data': 'string',
                    'precipitation_data': 'string'
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
                    'conflict_mentions': 'array',
                    'resolution_status': 'string',
                    'stakeholders': 'array'
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
                    'economic_impact': 'string',
                    'funding_amount': 'string',
                    'project_status': 'string'
                }
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
        
        # Enhanced tables
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
                embedding TEXT,
                sentiment_score REAL DEFAULT 0.0,
                urgency_level TEXT DEFAULT 'low'
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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conflict_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                region TEXT NOT NULL,
                description TEXT,
                severity TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                source_urls TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def extract_with_firecrawl(self, url: str, source: str) -> List[Dict]:
        """Enhanced extraction with Firecrawl"""
        try:
            schema = self.sources[source]['extract_schema']
            
            # Use Firecrawl search for better results
            search_result = self.firecrawl.search(
                query=f"climate conflict {source}",
                num_results=5,
                page_options={
                    'onlyMainContent': True,
                    'removeBase64Images': True
                }
            )
            
            # Also extract from specific URL
            extract_result = self.firecrawl.extract(
                url=url,
                schema=schema,
                onlyMainContent=True,
                removeBase64Images=True
            )
            
            all_data = []
            
            # Process search results
            if search_result and 'data' in search_result:
                for item in search_result['data']:
                    processed = self.process_extracted_item(item, source, item.get('url', url))
                    if processed:
                        all_data.append(processed)
            
            # Process extract results
            if extract_result and 'data' in extract_result:
                extracted_data = extract_result['data']
                if isinstance(extracted_data, list):
                    for item in extracted_data:
                        processed = self.process_extracted_item(item, source, url)
                        if processed:
                            all_data.append(processed)
                elif isinstance(extracted_data, dict):
                    processed = self.process_extracted_item(extracted_data, source, url)
                    if processed:
                        all_data.append(processed)
            
            return all_data
            
        except Exception as e:
            logger.error("Firecrawl extraction failed", url=url, error=str(e))
            return []
    
    def process_extracted_item(self, item: Dict, source: str, url: str) -> Optional[Dict]:
        """Enhanced data processing with conflict risk assessment"""
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
            
            # Calculate conflict risk score
            content_text = (processed['title'] + ' ' + processed['content']).lower()
            risk_score = self.calculate_conflict_risk(content_text)
            processed['conflict_risk_score'] = risk_score
            
            # Determine urgency level
            if risk_score > 0.7:
                processed['urgency_level'] = 'high'
            elif risk_score > 0.4:
                processed['urgency_level'] = 'medium'
            else:
                processed['urgency_level'] = 'low'
            
            # Add source-specific fields
            if source == 'nasa':
                processed['climate_impact'] = item.get('climate_impact', '')
                processed['temperature_data'] = item.get('temperature_data', '')
                processed['precipitation_data'] = item.get('precipitation_data', '')
            elif source == 'un_press':
                processed['topics'] = json.dumps(item.get('topics', []))
                processed['conflict_mentions'] = json.dumps(item.get('conflict_mentions', []))
                processed['resolution_status'] = item.get('resolution_status', '')
                processed['stakeholders'] = json.dumps(item.get('stakeholders', []))
            elif source == 'worldbank':
                processed['sector'] = item.get('sector', '')
                processed['economic_impact'] = item.get('economic_impact', '')
                processed['funding_amount'] = item.get('funding_amount', '')
                processed['project_status'] = item.get('project_status', '')
            
            return processed
            
        except Exception as e:
            logger.error("Data processing failed", error=str(e))
            return None
    
    def calculate_conflict_risk(self, text: str) -> float:
        """Calculate conflict risk score based on text content"""
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
        """Store extracted data with enhanced processing"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for item in data:
            cursor.execute('''
                INSERT INTO extracted_data 
                (source, url, title, content, region, country, keywords, raw_data, 
                 conflict_risk_score, urgency_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item['source'],
                item['url'],
                item['title'],
                item['content'],
                item['region'],
                item.get('country', ''),
                json.dumps(item.get('topics', [])),
                item['raw_data'],
                item['conflict_risk_score'],
                item['urgency_level']
            ))
        
        conn.commit()
        conn.close()
    
    async def analyze_conflict_patterns(self, data: List[Dict]) -> Dict[str, Any]:
        """Advanced conflict pattern analysis"""
        analysis = {
            'total_items': len(data),
            'high_risk_items': 0,
            'regions_at_risk': set(),
            'conflict_patterns': [],
            'trending_topics': [],
            'confidence': 0.0,
            'recommendations': []
        }
        
        # Analyze risk levels
        for item in data:
            if item['conflict_risk_score'] > 0.6:
                analysis['high_risk_items'] += 1
                if item['region']:
                    analysis['regions_at_risk'].add(item['region'])
        
        # Extract trending topics using TF-IDF
        if len(data) > 5:
            texts = [item['title'] + ' ' + item['content'] for item in data]
            vectorizer = TfidfVectorizer(max_features=50, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()
            
            # Get top terms
            mean_scores = np.mean(tfidf_matrix.toarray(), axis=0)
            top_indices = np.argsort(mean_scores)[-10:]
            analysis['trending_topics'] = [feature_names[i] for i in top_indices]
        
        # Generate recommendations
        if analysis['high_risk_items'] > 0:
            analysis['recommendations'].append(
                f"Monitor {len(analysis['regions_at_risk'])} regions for potential conflicts"
            )
        
        if 'drought' in str(analysis['trending_topics']).lower():
            analysis['recommendations'].append(
                "Drought conditions detected - monitor food security"
            )
        
        analysis['regions_at_risk'] = list(analysis['regions_at_risk'])
        analysis['confidence'] = min(analysis['high_risk_items'] / max(analysis['total_items'], 1), 1.0)
        
        return analysis
    
    async def run_analysis_cycle(self):
        """Run enhanced analysis cycle"""
        console.print(f"🔄 [bold blue]Starting enhanced analysis cycle at {datetime.now()}[/bold blue]")
        
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
            
            # Store in agent memory
            self.memory.store_memory(
                'extraction_cycle',
                f"Extracted {len(all_data)} items from {len(self.sources)} sources",
                importance=0.7,
                tags=['extraction', 'data_collection']
            )
        
        # Analyze conflict patterns
        if all_data:
            analysis = await self.analyze_conflict_patterns(all_data)
            
            # Store analysis results
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO analysis_results (analysis_type, results, confidence, risk_level)
                VALUES (?, ?, ?, ?)
            ''', (
                'conflict_patterns',
                json.dumps(analysis),
                analysis['confidence'],
                'high' if analysis['high_risk_items'] > 5 else 'medium' if analysis['high_risk_items'] > 0 else 'low'
            ))
            conn.commit()
            conn.close()
            
            # Store analysis in memory
            self.memory.store_memory(
                'conflict_analysis',
                f"Analysis: {analysis['high_risk_items']} high-risk items, {len(analysis['regions_at_risk'])} regions at risk",
                importance=0.9,
                tags=['analysis', 'conflict_risk']
            )
            
            # Display results
            console.print(f"\n📊 [bold green]Enhanced Analysis Results:[/bold green]")
            console.print(f"  Total items: {analysis['total_items']}")
            console.print(f"  High risk items: {analysis['high_risk_items']}")
            console.print(f"  Regions at risk: {', '.join(analysis['regions_at_risk'])}")
            console.print(f"  Confidence: {analysis['confidence']:.2%}")
            
            if analysis['trending_topics']:
                console.print(f"  Trending topics: {', '.join(analysis['trending_topics'][:5])}")
            
            if analysis['recommendations']:
                console.print(f"  Recommendations: {', '.join(analysis['recommendations'])}")
        
        self.last_analysis = datetime.now()
        console.print(f"✅ Enhanced analysis cycle completed at {self.last_analysis}")
    
    async def start_24_7_monitoring(self):
        """Start 24/7 monitoring with enhanced features"""
        console.print("🚀 [bold green]Starting Advanced 24/7 Climate Conflict Monitoring[/bold green]")
        
        # Store startup in memory
        self.memory.store_memory(
            'system_startup',
            f"Advanced Climate Conflict Agent started at {datetime.now()}",
            importance=1.0,
            tags=['system', 'startup']
        )
        
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
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Database stats
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
        
        # Memory stats
        memories = self.memory.retrieve_memories(limit=5)
        
        return {
            'total_items': total_items,
            'high_risk_items': high_risk_items,
            'total_analyses': total_analyses,
            'recent_by_source': recent_by_source,
            'last_analysis': self.last_analysis.isoformat() if self.last_analysis else None,
            'recent_memories': len(memories),
            'is_running': self.is_running
        }

async def main():
    """Main function"""
    config = {
        'FIRECRAWL_API_KEY': 'fc-a0b3b8aa31244c10b0f15b4f2d570ac7',
        'ANALYSIS_INTERVAL': 1800,  # 30 minutes
        'MAX_CONCURRENT_REQUESTS': 5
    }
    
    agent = ClimateConflictAgent(config)
    
    # Show agent status
    status = agent.get_agent_status()
    console.print(f"📊 [bold blue]Agent Status:[/bold blue]")
    console.print(f"  Total items: {status['total_items']}")
    console.print(f"  High risk items: {status['high_risk_items']}")
    console.print(f"  Recent (24h): {status['recent_by_source']}")
    console.print(f"  Recent memories: {status['recent_memories']}")
    
    # Start monitoring
    try:
        await agent.start_24_7_monitoring()
    except KeyboardInterrupt:
        agent.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(main())

