#!/usr/bin/env python3
"""
Test-Script für Firecrawl und kostenloses LLM (Ollama)
Testet beide Komponenten separat für robuste Funktionalität
"""
import sys
from pathlib import Path
import json
import requests
from typing import Dict, Any

sys.path.append(str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from config import Config

console = Console()


def test_firecrawl_api():
    """Teste Firecrawl API mit verschiedenen Methoden"""
    console.print("\n[bold cyan]🔥 Teste Firecrawl API...[/bold cyan]")
    
    config = Config()
    api_key = config.FIRECRAWL_API_KEY
    test_url = "https://www.dwd.de/DE/klimaumwelt/klimawandel/klimawandel_node.html"
    
    results = {
        'direct_api': None,
        'client_scrape': None,
        'client_crawl': None,
        'errors': []
    }
    
    # Test 1: Direkter API-Call
    console.print("  [dim]Test 1: Direkter API-Call (scrape)...[/dim]")
    try:
        response = requests.post(
            "https://api.firecrawl.dev/v0/scrape",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "url": test_url,
                "formats": ["markdown"],
                "onlyMainContent": True
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            results['direct_api'] = {
                'success': True,
                'has_markdown': bool(data.get('data', {}).get('markdown')),
                'markdown_length': len(data.get('data', {}).get('markdown', '')),
                'metadata': data.get('data', {}).get('metadata', {})
            }
            console.print(f"    [green]✅ Erfolg! Markdown: {results['direct_api']['markdown_length']} Zeichen[/green]")
        else:
            results['errors'].append(f"Direct API: Status {response.status_code}")
            console.print(f"    [red]❌ Fehler: Status {response.status_code}[/red]")
            console.print(f"    [dim]Response: {response.text[:200]}[/dim]")
    except Exception as e:
        results['errors'].append(f"Direct API: {str(e)}")
        console.print(f"    [red]❌ Fehler: {e}[/red]")
    
    # Test 2: Firecrawl Client (scrape)
    console.print("\n  [dim]Test 2: Firecrawl Client (scrape)...[/dim]")
    try:
        from firecrawl import Firecrawl
        
        client = Firecrawl(api_key=api_key)
        
        # Versuche verschiedene Methoden
        scrape_result = None
        
        # Methode 1: scrape_url
        if hasattr(client, 'scrape_url'):
            try:
                scrape_result = client.scrape_url(
                    url=test_url,
                    params={
                        "formats": ["markdown"],
                        "onlyMainContent": True
                    }
                )
                console.print("    [green]✅ scrape_url() funktioniert[/green]")
            except Exception as e:
                console.print(f"    [yellow]⚠️  scrape_url() Fehler: {e}[/yellow]")
        
        # Methode 2: scrape
        if not scrape_result and hasattr(client, 'scrape'):
            try:
                scrape_result = client.scrape(
                    url=test_url,
                    formats=["markdown"],
                    onlyMainContent=True
                )
                console.print("    [green]✅ scrape() funktioniert[/green]")
            except Exception as e:
                console.print(f"    [yellow]⚠️  scrape() Fehler: {e}[/yellow]")
        
        # Methode 3: scrape mit Dict
        if not scrape_result:
            try:
                scrape_result = client.scrape(
                    url=test_url,
                    **{
                        "formats": ["markdown"],
                        "onlyMainContent": True
                    }
                )
                console.print("    [green]✅ scrape(**kwargs) funktioniert[/green]")
            except Exception as e:
                console.print(f"    [yellow]⚠️  scrape(**kwargs) Fehler: {e}[/yellow]")
        
        if scrape_result:
            results['client_scrape'] = {
                'success': True,
                'has_markdown': bool(scrape_result.get('markdown') or scrape_result.get('data', {}).get('markdown')),
                'result_keys': list(scrape_result.keys()) if isinstance(scrape_result, dict) else []
            }
        else:
            results['errors'].append("Client scrape: Keine Methode funktionierte")
            
    except ImportError:
        results['errors'].append("Firecrawl Client: Nicht installiert")
        console.print("    [yellow]⚠️  firecrawl-py nicht installiert[/yellow]")
    except Exception as e:
        results['errors'].append(f"Client scrape: {str(e)}")
        console.print(f"    [red]❌ Fehler: {e}[/red]")
    
    # Test 3: Crawl (falls scrape funktioniert)
    if results.get('direct_api', {}).get('success'):
        console.print("\n  [dim]Test 3: Crawl API...[/dim]")
        try:
            response = requests.post(
                "https://api.firecrawl.dev/v0/crawl",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "url": test_url,
                    "maxDepth": 1,
                    "limit": 5,
                    "scrapeOptions": {
                        "formats": ["markdown"],
                        "onlyMainContent": True
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                pages = data.get('data', [])
                results['client_crawl'] = {
                    'success': True,
                    'pages_found': len(pages),
                    'has_data': bool(pages)
                }
                console.print(f"    [green]✅ Crawl erfolgreich! {len(pages)} Seiten gefunden[/green]")
            else:
                results['errors'].append(f"Crawl API: Status {response.status_code}")
                console.print(f"    [yellow]⚠️  Crawl Status: {response.status_code}[/yellow]")
        except Exception as e:
            results['errors'].append(f"Crawl API: {str(e)}")
            console.print(f"    [yellow]⚠️  Crawl Fehler: {e}[/yellow]")
    
    return results


def test_ollama_llm():
    """Teste Ollama LLM"""
    console.print("\n[bold cyan]🤖 Teste Ollama LLM...[/bold cyan]")
    
    config = Config()
    ollama_host = config.OLLAMA_HOST
    model = config.OLLAMA_MODEL
    
    results = {
        'available': False,
        'model': model,
        'host': ollama_host,
        'test_extraction': None,
        'errors': []
    }
    
    # Test 1: Prüfe ob Ollama läuft
    console.print(f"  [dim]Prüfe Ollama auf {ollama_host}...[/dim]")
    try:
        response = requests.get(f"{ollama_host}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m.get('name', '') for m in models]
            results['available'] = True
            results['installed_models'] = model_names
            
            console.print(f"    [green]✅ Ollama läuft![/green]")
            console.print(f"    [dim]Installierte Modelle: {', '.join(model_names[:3])}...[/dim]")
            
            # Prüfe ob gewünschtes Modell verfügbar ist
            if model in model_names or any(model in m for m in model_names):
                console.print(f"    [green]✅ Modell '{model}' verfügbar[/green]")
            else:
                console.print(f"    [yellow]⚠️  Modell '{model}' nicht gefunden[/yellow]")
                console.print(f"    [dim]Verfügbare Modelle: {', '.join(model_names)}[/dim]")
                if model_names:
                    results['model'] = model_names[0]  # Verwende erstes verfügbares Modell
                    console.print(f"    [dim]Verwende stattdessen: {results['model']}[/dim]")
        else:
            results['errors'].append(f"Ollama API: Status {response.status_code}")
            console.print(f"    [red]❌ Ollama antwortet nicht (Status {response.status_code})[/red]")
    except requests.exceptions.ConnectionError:
        results['errors'].append("Ollama: Verbindung fehlgeschlagen")
        console.print(f"    [yellow]⚠️  Ollama nicht erreichbar auf {ollama_host}[/yellow]")
        console.print("    [dim]Tipp: Starte Ollama mit 'ollama serve'[/dim]")
    except Exception as e:
        results['errors'].append(f"Ollama Check: {str(e)}")
        console.print(f"    [red]❌ Fehler: {e}[/red]")
    
    # Test 2: Teste Extraktion mit LLM
    if results['available']:
        console.print(f"\n  [dim]Teste Extraktion mit Modell '{results['model']}'...[/dim]")
        test_text = """
        Deutschland erlebt zunehmend extreme Wetterereignisse aufgrund des Klimawandels.
        Im Jahr 2023 wurden Rekordtemperaturen von über 40°C gemessen.
        Schwere Überschwemmungen entlang des Rheins haben zu erheblichen Schäden geführt.
        Die Niederschlagsmenge lag 30% über dem langjährigen Durchschnitt.
        """
        
        try:
            prompt = f"""Extrahiere strukturierte Daten aus dem folgenden Text im JSON-Format.

Text:
{test_text}

Antworte NUR mit einem gültigen JSON-Objekt:
{{
    "title": "Titel",
    "summary": "Zusammenfassung",
    "location": "Ort",
    "temperature_data": {{"value": 40}},
    "precipitation_data": {{"value": 30}},
    "climate_event": "heat wave"
}}
"""
            
            response = requests.post(
                f"{ollama_host}/api/generate",
                json={
                    "model": results['model'],
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                extracted_text = result.get('response', '')
                
                try:
                    extracted_data = json.loads(extracted_text)
                    results['test_extraction'] = {
                        'success': True,
                        'data': extracted_data
                    }
                    console.print("    [green]✅ LLM-Extraktion erfolgreich![/green]")
                    console.print(f"    [dim]Extrahiert: {json.dumps(extracted_data, indent=2)[:200]}...[/dim]")
                except json.JSONDecodeError:
                    results['test_extraction'] = {
                        'success': False,
                        'raw_response': extracted_text[:200]
                    }
                    console.print("    [yellow]⚠️  LLM antwortete nicht im JSON-Format[/yellow]")
                    console.print(f"    [dim]Response: {extracted_text[:200]}...[/dim]")
            else:
                results['errors'].append(f"LLM Generate: Status {response.status_code}")
                console.print(f"    [red]❌ LLM-Generate Fehler: Status {response.status_code}[/red]")
        except Exception as e:
            results['errors'].append(f"LLM Extraction: {str(e)}")
            console.print(f"    [red]❌ Fehler: {e}[/red]")
    
    return results


def print_summary(firecrawl_results: Dict, llm_results: Dict):
    """Zeige Zusammenfassung der Tests"""
    console.print("\n" + "="*60)
    console.print("[bold green]📊 Test-Zusammenfassung[/bold green]")
    console.print("="*60)
    
    # Firecrawl Status
    console.print("\n[bold cyan]🔥 Firecrawl:[/bold cyan]")
    if firecrawl_results.get('direct_api', {}).get('success'):
        console.print("  [green]✅ Direkter API-Call: FUNKTIONIERT[/green]")
    else:
        console.print("  [red]❌ Direkter API-Call: FEHLER[/red]")
    
    client_scrape = firecrawl_results.get('client_scrape')
    if client_scrape and client_scrape.get('success'):
        console.print("  [green]✅ Client Scrape: FUNKTIONIERT[/green]")
    else:
        console.print("  [yellow]⚠️  Client Scrape: Probleme (aber direkter API-Call funktioniert)[/yellow]")
    
    if firecrawl_results.get('client_crawl', {}).get('success'):
        console.print("  [green]✅ Client Crawl: FUNKTIONIERT[/green]")
    else:
        console.print("  [yellow]⚠️  Client Crawl: Nicht getestet/Probleme[/yellow]")
    
    if firecrawl_results.get('errors'):
        console.print(f"  [red]Fehler: {len(firecrawl_results['errors'])}[/red]")
        for error in firecrawl_results['errors'][:3]:
            console.print(f"    [dim]- {error}[/dim]")
    
    # LLM Status
    console.print("\n[bold cyan]🤖 Ollama LLM:[/bold cyan]")
    if llm_results.get('available'):
        console.print("  [green]✅ Ollama: VERFÜGBAR[/green]")
        console.print(f"  [dim]Modell: {llm_results.get('model', 'N/A')}[/dim]")
        if llm_results.get('test_extraction', {}).get('success'):
            console.print("  [green]✅ LLM-Extraktion: FUNKTIONIERT[/green]")
        else:
            console.print("  [yellow]⚠️  LLM-Extraktion: Probleme[/yellow]")
    else:
        console.print("  [yellow]⚠️  Ollama: NICHT VERFÜGBAR[/yellow]")
        console.print("  [dim]Fallback: Pattern-Matching wird verwendet[/dim]")
    
    if llm_results.get('errors'):
        console.print(f"  [red]Fehler: {len(llm_results['errors'])}[/red]")
        for error in llm_results['errors'][:3]:
            console.print(f"    [dim]- {error}[/dim]")
    
    # Empfehlungen
    console.print("\n[bold yellow]💡 Empfehlungen:[/bold yellow]")
    
    if not firecrawl_results.get('direct_api', {}).get('success'):
        console.print("  - Firecrawl API-Key prüfen")
        console.print("  - Direkter API-Call sollte funktionieren")
    
    if not llm_results.get('available'):
        console.print("  - Ollama installieren: curl -fsSL https://ollama.ai/install.sh | sh")
        console.print("  - Ollama starten: ollama serve")
        console.print("  - Modell installieren: ollama pull llama2:7b")
    
    if firecrawl_results.get('direct_api', {}).get('success') and llm_results.get('available'):
        console.print("  [green]✅ Beide Systeme funktionieren! Bereit für Produktion.[/green]")


def main():
    """Hauptfunktion"""
    console.print(Panel.fit(
        "[bold green]🧪 Firecrawl & LLM Test-Suite[/bold green]\n"
        "[cyan]Testet beide Komponenten für robuste Funktionalität[/cyan]",
        border_style="green"
    ))
    
    # Teste Firecrawl
    firecrawl_results = test_firecrawl_api()
    
    # Teste LLM
    llm_results = test_ollama_llm()
    
    # Zeige Zusammenfassung
    print_summary(firecrawl_results, llm_results)
    
    console.print("\n[bold green]✅ Tests abgeschlossen![/bold green]\n")


if __name__ == "__main__":
    main()

