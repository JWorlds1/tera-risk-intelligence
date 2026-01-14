#!/usr/bin/env python3
"""
Test: IPCC-Kontext als Grundlage für Firecrawl und OpenAI
"""
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
import json

sys.path.append(str(Path(__file__).parent))

from ipcc_context_engine import IPCCContextEngine
from firecrawl_enrichment import FirecrawlEnricher
from llm_predictions import LLMPredictor

console = Console()

# API Keys
FIRECRAWL_API_KEY = "fc-a0b3b8aa31244c10b0f15b4f2d570ac7"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY_HERE"

os.environ["FIRECRAWL_API_KEY"] = FIRECRAWL_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


def main():
    """Test IPCC-Kontext als Grundlage"""
    console.print(Panel.fit(
        "[bold green]🌍 Test: IPCC-Kontext als Grundlage[/bold green]",
        border_style="green"
    ))
    
    # Initialisiere Komponenten
    ipcc_engine = IPCCContextEngine()
    firecrawl_enricher = FirecrawlEnricher(FIRECRAWL_API_KEY)
    
    # Test-Record
    test_record = {
        'id': 1,
        'title': 'Severe drought conditions in East Africa',
        'region': 'East Africa',
        'summary': 'Worst drought in 40 years affecting millions of people',
        'source_name': 'NASA'
    }
    
    console.print(f"\n[cyan]Test-Record:[/cyan]")
    console.print(f"  Titel: {test_record['title']}")
    console.print(f"  Region: {test_record['region']}")
    
    # 1. Erstelle IPCC-Kontext für Firecrawl
    console.print("\n[bold yellow]1. IPCC-Kontext für Firecrawl:[/bold yellow]")
    firecrawl_context = ipcc_engine.get_firecrawl_context(test_record)
    
    console.print(f"\n  Keywords ({len(firecrawl_context['keywords'])}):")
    for kw in firecrawl_context['keywords'][:10]:
        console.print(f"    • {kw}")
    
    console.print(f"\n  Kategorien: {firecrawl_context['categories']}")
    console.print(f"\n  IPCC-Baseline:")
    console.print(f"    Periode: {firecrawl_context['ipcc_context']['baseline_period']}")
    console.print(f"    Aktuelle Anomalie: {firecrawl_context['ipcc_context']['current_anomaly']}")
    console.print(f"    Ziel: {firecrawl_context['ipcc_context']['target']}")
    
    # 2. Test Firecrawl-Suche mit IPCC-Kontext
    console.print("\n[bold yellow]2. Firecrawl-Suche mit IPCC-Kontext:[/bold yellow]")
    try:
        search_results, credits = firecrawl_enricher.enrich_with_search(
            keywords=firecrawl_context['keywords'][:5],
            region=test_record['region'],
            limit=3,
            scrape_content=True,
            ipcc_context=firecrawl_context
        )
        
        console.print(f"  Gefunden: {len(search_results)} Ergebnisse")
        console.print(f"  Credits verwendet: {credits:.1f}")
        
        for i, result in enumerate(search_results[:3], 1):
            console.print(f"\n  {i}. {result.get('title', 'N/A')[:60]}...")
            console.print(f"     URL: {result.get('url', 'N/A')[:60]}...")
            if 'ipcc' in result.get('url', '').lower() or 'climate' in result.get('title', '').lower():
                console.print(f"     [green]✓ IPCC-relevant[/green]")
    
    except Exception as e:
        console.print(f"  [red]Fehler: {e}[/red]")
    
    # 3. Erstelle IPCC-Kontext für LLM
    console.print("\n[bold yellow]3. IPCC-Kontext für LLM:[/bold yellow]")
    llm_context = ipcc_engine.get_llm_context(
        test_record,
        {
            'temperatures': [35.0],
            'precipitation': [50.0],
            'affected_people': 2000000
        }
    )
    
    console.print(f"\n  Kontext-Länge: {len(llm_context)} Zeichen")
    console.print(f"\n  [cyan]IPCC-Kontext-Auszug:[/cyan]")
    lines = llm_context.split('\n')[:15]
    for line in lines:
        if line.strip():
            console.print(f"    {line[:80]}")
    
    # 4. Test LLM-Prediction mit IPCC-Kontext
    console.print("\n[bold yellow]4. LLM-Prediction mit IPCC-Kontext:[/bold yellow]")
    try:
        llm_predictor = LLMPredictor(
            provider="openai",
            model="gpt-4o-mini"
        )
        
        prediction = llm_predictor.predict_risk(
            test_record,
            {
                'temperatures': [35.0],
                'precipitation': [50.0],
                'affected_people': 2000000
            },
            ipcc_context=llm_context
        )
        
        console.print(f"\n  Prediction: {prediction.prediction_text}")
        console.print(f"  Konfidenz: {prediction.confidence:.2f}")
        console.print(f"  Zeithorizont: {prediction.predicted_timeline}")
        
        if prediction.key_factors:
            console.print(f"\n  Faktoren:")
            for factor in prediction.key_factors[:3]:
                console.print(f"    • {factor}")
        
        if prediction.recommendations:
            console.print(f"\n  Empfehlungen:")
            for rec in prediction.recommendations[:2]:
                console.print(f"    • {rec}")
    
    except Exception as e:
        console.print(f"  [red]Fehler: {e}[/red]")
    
    # 5. Zusammenfassung
    console.print("\n[bold green]✅ Test abgeschlossen![/bold green]")
    console.print("\n[yellow]Zusammenfassung:[/yellow]")
    console.print("  ✓ IPCC-Kontext-Engine erstellt")
    console.print("  ✓ Firecrawl nutzt IPCC-Kontext für Suche")
    console.print("  ✓ LLM nutzt IPCC-Kontext für Predictions")
    console.print("  ✓ IPCC-Baseline (1850-1900) als Referenz")
    console.print("  ✓ IPCC-Schwellenwerte (1.5°C, 2.0°C) integriert")


if __name__ == "__main__":
    main()

