# 🔥 Firecrawl Integration - Dokumentation

## Übersicht

Das System nutzt **Firecrawl** zur Datenanreicherung und kombiniert es mit **LLM-Predictions** und **numerischen Zeitreihenvorhersagen** für bessere Ergebnisse.

## Features

### 1. Firecrawl Search
- Web-Suche basierend auf Keywords/Buzzwords
- Unterstützt Kategorien: `github`, `research`, `pdf`
- Optional: Content-Scraping der Ergebnisse
- Location-basierte Suche

### 2. Firecrawl Map
- Mappt alle URLs einer Website
- Sehr schnell (prioritized for speed)
- Location & Language Support

### 3. Firecrawl Crawl
- Crawlt komplette Websites
- Konfigurierbare Tiefe und Limits
- Content-Scraping in verschiedenen Formaten

### 4. Firecrawl Extract (Agent-basiert)
- Strukturierte Datenextraktion mit Schema
- Extrahiert spezifische Felder (Temperaturen, Bevölkerungszahlen, etc.)
- Nutzt AI-Agenten für intelligente Extraktion

## Kosten-Tracking

### Firecrawl Credits
- **Start**: 20.000 Credits
- **Search** (ohne Scraping): 2 Credits pro 10 Ergebnisse
- **Search** (mit Scraping): ~1 Credit pro Ergebnis
- **Map**: ~1 Credit pro Operation
- **Crawl**: ~1 Credit pro gecrawlte Seite
- **Extract**: ~2-5 Credits pro Extraktion

### OpenAI Kosten
- **gpt-4o-mini**: 
  - Input: $0.15 per 1M tokens
  - Output: $0.60 per 1M tokens
- **Tracking**: Automatisch über CostTracker

## Verwendung

### Basis-Setup

```python
from enriched_predictions import EnrichedPredictionPipeline

# API Keys
firecrawl_key = "fc-a0b3b8aa31244c10b0f15b4f2d570ac7"
openai_key = "sk-proj-..."

# Initialisiere Pipeline
pipeline = EnrichedPredictionPipeline(
    firecrawl_api_key=firecrawl_key,
    openai_api_key=openai_key
)
```

### Einzelner Record

```python
# Reichere Record an und erstelle Predictions
result = pipeline.enrich_and_predict(
    record_id=1,
    use_search=True,    # Web-Suche aktivieren
    use_extract=True,   # Agent-Extraktion aktivieren
    use_llm=True       # LLM-Predictions aktivieren
)

# Ergebnisse
print(result['enrichment'])      # Firecrawl-Daten
print(result['predictions'])      # Predictions
print(result['costs'])           # Kosten-Tracking
```

### Batch-Verarbeitung

```python
# Verarbeite mehrere Records
results = pipeline.batch_enrich_and_predict(
    record_ids=[1, 2, 3],  # Oder None für alle
    limit=10,
    use_search=True,
    use_extract=True,
    use_llm=True
)

# Kosten-Zusammenfassung
print(results['total_costs'])
```

### Direkte Firecrawl-Nutzung

```python
from firecrawl_enrichment import FirecrawlEnricher

enricher = FirecrawlEnricher(api_key="fc-...")

# Search
results, credits = enricher.enrich_with_search(
    keywords=["drought", "East Africa", "climate"],
    region="East Africa",
    limit=10,
    scrape_content=True,
    categories=["research"]  # Optional
)

# Map
urls, credits = enricher.enrich_with_map(
    base_url="https://earthobservatory.nasa.gov"
)

# Crawl
crawled_data, credits = enricher.enrich_with_crawl(
    start_url="https://example.com",
    max_depth=2,
    limit=50
)

# Extract (Agent-basiert)
schema = {
    "type": "object",
    "properties": {
        "temperatures": {"type": "array", "items": {"type": "number"}},
        "affected_population": {"type": "number"}
    }
}
extracted, credits = enricher.enrich_with_extract(
    url="https://example.com/article",
    extraction_schema=schema
)
```

## Demo ausführen

```bash
cd backend
python3 run_enriched_predictions.py
```

## Output-Format

### Enrichment Results

```json
{
  "enrichment": {
    "enriched_at": "2025-11-09T12:00:00",
    "methods_used": ["search", "extract"],
    "search_results": [
      {
        "url": "https://...",
        "title": "...",
        "description": "...",
        "markdown": "...",
        "category": "research"
      }
    ],
    "extracted_data": {
      "temperatures": [35.0],
      "affected_population": 2000000,
      "funding_amount": 500000000
    },
    "search_credits": 5.0,
    "extract_credits": 3.0
  }
}
```

### Predictions

```json
{
  "predictions": {
    "extracted_numbers": {
      "temperatures": [35.0],
      "affected_people": 2000000,
      "funding_amount": 500000000
    },
    "risk_score": {
      "total": 0.65,
      "level": "HIGH",
      "climate_risk": 0.7,
      "conflict_risk": 0.6
    },
    "llm_prediction": {
      "prediction_text": "Risk Level: HIGH",
      "confidence": 0.85,
      "key_factors": ["drought", "water scarcity"],
      "recommendations": ["Monitor situation"]
    }
  }
}
```

### Costs

```json
{
  "costs": {
    "firecrawl_credits_used": 8.0,
    "firecrawl_credits_remaining": 19992.0,
    "openai_tokens_used": 1250,
    "openai_cost_usd": 0.0002,
    "requests_made": 3,
    "runtime_seconds": 12.5
  }
}
```

## Best Practices

### 1. Kosten-Management

```python
# Überwache Kosten regelmäßig
costs = pipeline.cost_tracker.get_summary()

if costs['firecrawl_credits_remaining'] < 1000:
    print("⚠️  Wenig Firecrawl Credits!")
    
if costs['openai_cost_usd'] > 1.0:
    print("⚠️  Hohe OpenAI-Kosten!")
```

### 2. Rate Limits

```python
# Pause zwischen Requests
import time

for record_id in record_ids:
    result = pipeline.enrich_and_predict(record_id)
    time.sleep(2)  # 2 Sekunden Pause
```

### 3. Selektive Anreicherung

```python
# Nur Search für schnelle Anreicherung
result = pipeline.enrich_and_predict(
    record_id=1,
    use_search=True,
    use_extract=False,  # Spart Credits
    use_llm=False       # Spart OpenAI-Kosten
)
```

### 4. Keyword-Extraktion

Das System extrahiert automatisch Keywords aus Records:
- Titel-Wörter (>4 Zeichen)
- Summary-Wörter
- Region
- Topics

Diese werden für Firecrawl Search verwendet.

## Erweiterte Features

### Custom Extraction Schema

```python
custom_schema = {
    "type": "object",
    "properties": {
        "risk_indicators": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Risiko-Indikatoren aus dem Text"
        },
        "key_events": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Wichtige Ereignisse"
        },
        "geographic_locations": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Erwähnte geografische Orte"
        }
    }
}

extracted, credits = enricher.enrich_with_extract(
    url="https://example.com",
    extraction_schema=custom_schema
)
```

### Research Category Search

```python
# Suche in akademischen Quellen
results, credits = enricher.enrich_with_search(
    keywords=["climate change", "conflict"],
    categories=["research"],  # arXiv, Nature, IEEE, PubMed
    limit=10
)
```

### Location-basierte Suche

```python
# Suche mit Location-Settings
results, credits = enricher.enrich_with_search(
    keywords=["drought"],
    region="Germany",  # Location für Suche
    limit=10
)
```

## Troubleshooting

### Firecrawl-Fehler
- Prüfe API-Key: `echo $FIRECRAWL_API_KEY`
- Prüfe Rate Limits
- Reduziere `limit` Parameter

### OpenAI-Fehler
- Prüfe API-Key: `echo $OPENAI_API_KEY`
- Prüfe Token-Limits
- Nutze günstigere Modelle (gpt-4o-mini)

### Kosten zu hoch
- Reduziere `use_search`, `use_extract`, `use_llm`
- Nutze `limit` Parameter
- Pausiere zwischen Requests

## Monitoring

### Kosten-Dashboard

```python
# Regelmäßige Kosten-Prüfung
import json

costs = pipeline.cost_tracker.get_summary()
print(json.dumps(costs, indent=2))

# Speichere Kosten-Log
with open('costs_log.json', 'a') as f:
    json.dump({
        'timestamp': datetime.now().isoformat(),
        'costs': costs
    }, f)
    f.write('\n')
```

## Nächste Schritte

1. ✅ Firecrawl Integration implementiert
2. ✅ Kosten-Tracking implementiert
3. ✅ Enriched Predictions Pipeline erstellt
4. 🔄 Testen mit echten Daten
5. 🔄 Optimieren für Kosten-Effizienz
6. 🔄 Erweitern um weitere Firecrawl-Features

