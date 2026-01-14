#!/usr/bin/env python3
"""
Test-Script: Prüft ob Backend und Frontend zusammenarbeiten
"""
import requests
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

BASE_URL = "http://localhost:5000"


def test_api_endpoints():
    """Teste alle API-Endpunkte"""
    console.print(Panel.fit(
        "[bold green]🧪 Teste Backend-Frontend Integration[/bold green]",
        border_style="green"
    ))
    
    results = []
    
    # 1. Test Stats API
    try:
        response = requests.get(f"{BASE_URL}/api/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            results.append(("✅", "/api/stats", "OK", f"{data.get('total_records', 0)} Records"))
        else:
            results.append(("❌", "/api/stats", f"Status {response.status_code}", ""))
    except Exception as e:
        results.append(("❌", "/api/stats", "Fehler", str(e)[:50]))
    
    # 2. Test Records API
    try:
        response = requests.get(f"{BASE_URL}/api/records?limit=5", timeout=5)
        if response.status_code == 200:
            data = response.json()
            results.append(("✅", "/api/records", "OK", f"{len(data.get('records', []))} Records"))
        else:
            results.append(("❌", "/api/records", f"Status {response.status_code}", ""))
    except Exception as e:
        results.append(("❌", "/api/records", "Fehler", str(e)[:50]))
    
    # 3. Test Map Data API
    try:
        response = requests.get(f"{BASE_URL}/api/map-data", timeout=5)
        if response.status_code == 200:
            data = response.json()
            results.append(("✅", "/api/map-data", "OK", f"{len(data.get('points', []))} Punkte"))
        else:
            results.append(("❌", "/api/map-data", f"Status {response.status_code}", ""))
    except Exception as e:
        results.append(("❌", "/api/map-data", "Fehler", str(e)[:50]))
    
    # 4. Test Predictions API
    try:
        response = requests.get(f"{BASE_URL}/api/predictions", timeout=5)
        if response.status_code == 200:
            data = response.json()
            results.append(("✅", "/api/predictions", "OK", f"{len(data.get('predictions', []))} Predictions"))
        else:
            results.append(("❌", "/api/predictions", f"Status {response.status_code}", ""))
    except Exception as e:
        results.append(("❌", "/api/predictions", "Fehler", str(e)[:50]))
    
    # 5. Test Batch Enrichment API
    try:
        response = requests.get(f"{BASE_URL}/api/batch-enrichment", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('table_exists'):
                results.append(("✅", "/api/batch-enrichment", "OK", f"{data.get('total_enriched', 0)} angereichert"))
            else:
                results.append(("⚠️", "/api/batch-enrichment", "Tabelle existiert nicht", "Führe batch_enrichment_50.py aus"))
        else:
            results.append(("❌", "/api/batch-enrichment", f"Status {response.status_code}", ""))
    except Exception as e:
        results.append(("❌", "/api/batch-enrichment", "Fehler", str(e)[:50]))
    
    # 6. Test Data Sources API
    try:
        response = requests.get(f"{BASE_URL}/api/data-sources", timeout=5)
        if response.status_code == 200:
            data = response.json()
            results.append(("✅", "/api/data-sources", "OK", f"{len(data)} Quellen"))
        else:
            results.append(("❌", "/api/data-sources", f"Status {response.status_code}", ""))
    except Exception as e:
        results.append(("❌", "/api/data-sources", "Fehler", str(e)[:50]))
    
    # 7. Test Records mit Enrichment
    try:
        response = requests.get(f"{BASE_URL}/api/records?limit=5&include_enrichment=true", timeout=5)
        if response.status_code == 200:
            data = response.json()
            enriched_count = sum(1 for r in data.get('records', []) if r.get('enrichment'))
            results.append(("✅", "/api/records?include_enrichment=true", "OK", f"{enriched_count} mit Enrichment"))
        else:
            results.append(("❌", "/api/records?include_enrichment=true", f"Status {response.status_code}", ""))
    except Exception as e:
        results.append(("❌", "/api/records?include_enrichment=true", "Fehler", str(e)[:50]))
    
    # Zeige Ergebnisse
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Status", style="cyan")
    table.add_column("Endpoint", style="green")
    table.add_column("Ergebnis", style="yellow")
    table.add_column("Details", style="white")
    
    for status, endpoint, result, details in results:
        table.add_row(status, endpoint, result, details)
    
    console.print("\n")
    console.print(table)
    
    # Zusammenfassung
    success_count = sum(1 for r in results if r[0] == "✅")
    total_count = len(results)
    
    console.print(f"\n[bold cyan]Zusammenfassung:[/bold cyan] {success_count}/{total_count} Tests erfolgreich")
    
    if success_count == total_count:
        console.print("[bold green]✅ Alle Tests erfolgreich! System funktioniert.[/bold green]")
    elif success_count > 0:
        console.print("[bold yellow]⚠️  Einige Tests fehlgeschlagen. Prüfe die Details oben.[/bold yellow]")
    else:
        console.print("[bold red]❌ Keine Tests erfolgreich. Backend läuft möglicherweise nicht.[/bold red]")
        console.print("[cyan]Starte Backend mit: python web_app.py[/cyan]")


if __name__ == "__main__":
    test_api_endpoints()

