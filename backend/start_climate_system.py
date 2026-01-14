#!/usr/bin/env python3
"""
Climate Conflict Early Warning System - Starter Script
Vereinfachte Version für sofortigen Start
"""

import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from working_system import ClimateConflictScraper

console = Console()

def print_banner():
    """Print system banner"""
    banner = Text("""
🌍 Climate Conflict Early Warning System 🌍
    Multi-Agent Web Scraping & Analysis
    
    Sources: NASA, UN Press, World Bank
    AI-Powered: Firecrawl + LangChain
    Real-time: FastAPI + WebSockets
    """, style="bold green")
    
    console.print(Panel(banner, title="🚀 System Ready", border_style="green"))

async def main():
    """Main function"""
    print_banner()
    
    console.print("\n[bold blue]Starting Climate Conflict Data Collection...[/bold blue]")
    
    # Initialize scraper
    scraper = ClimateConflictScraper()
    
    # Run scraping session
    try:
        results = await scraper.run_scraping_session(['nasa', 'un', 'worldbank'])
        
        # Print detailed results
        console.print("\n[bold green]📊 Detailed Results:[/bold green]")
        for source, records in results.items():
            console.print(f"  {source.upper()}: {len(records)} records")
        
        # Show data files
        console.print(f"\n[bold blue]📁 Data Files Created:[/bold blue]")
        data_dir = Path("./data")
        for file in data_dir.glob("*.json"):
            console.print(f"  📄 {file.name}")
        
        console.print(f"\n[bold green]✅ System Successfully Started![/bold green]")
        console.print(f"[bold blue]Next Steps:[/bold blue]")
        console.print("  1. Review extracted data in ./data/")
        console.print("  2. Start AI analysis with: python ai_analysis.py")
        console.print("  3. Launch real-time dashboard: python dashboard.py")
        console.print("  4. Run geopolitical analysis: python geopolitical_analysis.py")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error: {e}[/bold red]")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
