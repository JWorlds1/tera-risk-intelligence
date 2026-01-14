#!/usr/bin/env python3
"""
Debug Firecrawl Search - Finde heraus warum die Suche keine Ergebnisse liefert
"""
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from firecrawl import Firecrawl
from rich.console import Console
import json

console = Console()

FIRECRAWL_API_KEY = "fc-a0b3b8aa31244c10b0f15b4f2d570ac7"

def test_firecrawl_search():
    """Teste verschiedene Firecrawl Search-Varianten"""
    console.print("[bold cyan]🔍 Teste Firecrawl Search...[/bold cyan]\n")
    
    client = Firecrawl(api_key=FIRECRAWL_API_KEY)
    
    # Test 1: Einfache Suche ohne Kategorien
    console.print("[yellow]Test 1: Einfache Suche ohne Kategorien[/yellow]")
    try:
        result = client.search(
            query="climate change drought",
            limit=3
        )
        console.print(f"  Ergebnis-Typ: {type(result)}")
        console.print(f"  Ergebnis-Keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
        if isinstance(result, dict):
            console.print(f"  Data-Keys: {result.get('data', {}).keys() if isinstance(result.get('data'), dict) else 'N/A'}")
            if 'data' in result:
                data = result['data']
                if isinstance(data, dict):
                    web_results = data.get('web', [])
                    console.print(f"  ✅ {len(web_results)} Web-Ergebnisse gefunden")
                    if web_results:
                        console.print(f"  Erstes Ergebnis: {web_results[0].get('title', 'N/A')[:60]}")
                else:
                    console.print(f"  Data-Typ: {type(data)}")
                    console.print(f"  Data: {str(data)[:200]}")
        else:
            console.print(f"  Ergebnis: {str(result)[:200]}")
    except Exception as e:
        console.print(f"  ❌ Fehler: {e}")
    
    # Test 2: Suche mit Kategorien
    console.print("\n[yellow]Test 2: Suche mit Research-Kategorie[/yellow]")
    try:
        result = client.search(
            query="climate change drought",
            limit=3,
            categories=["research"]
        )
        if isinstance(result, dict) and 'data' in result:
            data = result['data']
            if isinstance(data, dict):
                web_results = data.get('web', [])
                console.print(f"  ✅ {len(web_results)} Ergebnisse gefunden")
            else:
                console.print(f"  Data-Typ: {type(data)}")
    except Exception as e:
        console.print(f"  ❌ Fehler: {e}")
    
    # Test 3: Suche ohne scrape_options
    console.print("\n[yellow]Test 3: Suche ohne scrape_options[/yellow]")
    try:
        result = client.search(
            query="drought East Africa",
            limit=2
        )
        if isinstance(result, dict) and 'data' in result:
            data = result['data']
            if isinstance(data, dict):
                web_results = data.get('web', [])
                console.print(f"  ✅ {len(web_results)} Ergebnisse gefunden")
                if web_results:
                    for i, r in enumerate(web_results[:2], 1):
                        console.print(f"    {i}. {r.get('title', 'N/A')[:60]}")
    except Exception as e:
        console.print(f"  ❌ Fehler: {e}")
    
    # Test 4: Prüfe API-Response-Struktur
    console.print("\n[yellow]Test 4: Vollständige API-Response-Struktur[/yellow]")
    try:
        result = client.search(
            query="climate",
            limit=1
        )
        console.print(f"  Vollständige Response:")
        console.print(json.dumps(result, indent=2, default=str)[:500])
    except Exception as e:
        console.print(f"  ❌ Fehler: {e}")

if __name__ == "__main__":
    test_firecrawl_search()

