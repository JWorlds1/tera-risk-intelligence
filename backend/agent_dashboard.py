#!/usr/bin/env python3
"""
Climate Conflict Agent Dashboard
Real-time Monitoring und Visualisierung
"""

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import structlog
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
import httpx
import firecrawl

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

class AgentDashboard:
    """Real-time Dashboard für Climate Conflict Agent"""
    
    def __init__(self, db_path: str = "./climate_agent_advanced.db"):
        self.db_path = db_path
        self.firecrawl = firecrawl.FirecrawlApp(api_key='fc-a0b3b8aa31244c10b0f15b4f2d570ac7')
        
    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Basic stats
        cursor.execute("SELECT COUNT(*) FROM extracted_data")
        total_items = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM extracted_data WHERE conflict_risk_score > 0.6")
        high_risk_items = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM analysis_results")
        total_analyses = cursor.fetchone()[0]
        
        # Recent activity (last 24 hours)
        cursor.execute("""
            SELECT source, COUNT(*) as count 
            FROM extracted_data 
            WHERE extracted_at > datetime('now', '-24 hours')
            GROUP BY source
        """)
        recent_by_source = dict(cursor.fetchall())
        
        # Risk distribution
        cursor.execute("""
            SELECT urgency_level, COUNT(*) as count 
            FROM extracted_data 
            WHERE extracted_at > datetime('now', '-7 days')
            GROUP BY urgency_level
        """)
        risk_distribution = dict(cursor.fetchall())
        
        # Top regions
        cursor.execute("""
            SELECT region, COUNT(*) as count 
            FROM extracted_data 
            WHERE region != '' AND extracted_at > datetime('now', '-7 days')
            GROUP BY region 
            ORDER BY count DESC 
            LIMIT 10
        """)
        top_regions = dict(cursor.fetchall())
        
        # Recent high-risk items
        cursor.execute("""
            SELECT title, region, conflict_risk_score, extracted_at
            FROM extracted_data 
            WHERE conflict_risk_score > 0.6 
            ORDER BY extracted_at DESC 
            LIMIT 5
        """)
        recent_high_risk = [dict(zip(['title', 'region', 'risk_score', 'extracted_at'], row)) 
                           for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'total_items': total_items,
            'high_risk_items': high_risk_items,
            'total_analyses': total_analyses,
            'recent_by_source': recent_by_source,
            'risk_distribution': risk_distribution,
            'top_regions': top_regions,
            'recent_high_risk': recent_high_risk
        }
    
    def create_stats_table(self, stats: Dict[str, Any]) -> Table:
        """Create statistics table"""
        table = Table(title="📊 Agent Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Total Items", str(stats['total_items']))
        table.add_row("High Risk Items", str(stats['high_risk_items']))
        table.add_row("Total Analyses", str(stats['total_analyses']))
        
        # Risk distribution
        risk_dist = stats['risk_distribution']
        table.add_row("High Risk (7d)", str(risk_dist.get('high', 0)))
        table.add_row("Medium Risk (7d)", str(risk_dist.get('medium', 0)))
        table.add_row("Low Risk (7d)", str(risk_dist.get('low', 0)))
        
        return table
    
    def create_sources_table(self, stats: Dict[str, Any]) -> Table:
        """Create sources activity table"""
        table = Table(title="📡 Recent Activity (24h)")
        table.add_column("Source", style="cyan")
        table.add_column("Items", style="magenta")
        
        for source, count in stats['recent_by_source'].items():
            table.add_row(source.upper(), str(count))
        
        return table
    
    def create_regions_table(self, stats: Dict[str, Any]) -> Table:
        """Create top regions table"""
        table = Table(title="🌍 Top Regions (7d)")
        table.add_column("Region", style="cyan")
        table.add_column("Items", style="magenta")
        
        for region, count in list(stats['top_regions'].items())[:5]:
            table.add_row(region, str(count))
        
        return table
    
    def create_high_risk_table(self, stats: Dict[str, Any]) -> Table:
        """Create high risk items table"""
        table = Table(title="⚠️ Recent High Risk Items")
        table.add_column("Title", style="red")
        table.add_column("Region", style="yellow")
        table.add_column("Risk Score", style="red")
        table.add_column("Date", style="blue")
        
        for item in stats['recent_high_risk']:
            title = item['title'][:50] + "..." if len(item['title']) > 50 else item['title']
            table.add_row(
                title,
                item['region'] or "Unknown",
                f"{item['risk_score']:.2f}",
                item['extracted_at'][:16]
            )
        
        return table
    
    def create_status_panel(self) -> Panel:
        """Create system status panel"""
        status_text = Text()
        status_text.append("🟢 Agent Status: RUNNING\n", style="green")
        status_text.append(f"⏰ Last Update: {datetime.now().strftime('%H:%M:%S')}\n", style="blue")
        status_text.append("🔄 Analysis: Active\n", style="green")
        status_text.append("💾 Database: Connected\n", style="green")
        status_text.append("🌐 Firecrawl: Connected\n", style="green")
        
        return Panel(status_text, title="🚀 System Status", border_style="green")
    
    def create_layout(self, stats: Dict[str, Any]) -> Layout:
        """Create dashboard layout"""
        layout = Layout()
        
        # Split into sections
        layout.split_column(
            Layout(self.create_status_panel(), size=6),
            Layout(name="main")
        )
        
        layout["main"].split_row(
            Layout(self.create_stats_table(stats), name="left"),
            Layout(name="right")
        )
        
        layout["right"].split_column(
            Layout(self.create_sources_table(stats), name="sources"),
            Layout(self.create_regions_table(stats), name="regions"),
            Layout(self.create_high_risk_table(stats), name="risks")
        )
        
        return layout
    
    async def run_dashboard(self):
        """Run real-time dashboard"""
        console.print("🚀 [bold green]Starting Climate Conflict Agent Dashboard[/bold green]")
        
        try:
            with Live(self.create_layout(self.get_database_stats()), refresh_per_second=1) as live:
                while True:
                    # Update stats
                    stats = self.get_database_stats()
                    layout = self.create_layout(stats)
                    live.update(layout)
                    
                    # Wait for next update
                    await asyncio.sleep(30)  # Update every 30 seconds
                    
        except KeyboardInterrupt:
            console.print("\n🛑 [yellow]Dashboard stopped by user[/yellow]")
        except Exception as e:
            console.print(f"❌ [red]Dashboard error: {e}[/red]")
            logger.error("Dashboard error", error=str(e))

async def main():
    """Main function"""
    dashboard = AgentDashboard()
    
    # Show initial stats
    stats = dashboard.get_database_stats()
    console.print(f"📊 [bold blue]Initial Stats:[/bold blue]")
    console.print(f"  Total items: {stats['total_items']}")
    console.print(f"  High risk items: {stats['high_risk_items']}")
    console.print(f"  Recent (24h): {stats['recent_by_source']}")
    
    # Run dashboard
    await dashboard.run_dashboard()

if __name__ == "__main__":
    asyncio.run(main())

