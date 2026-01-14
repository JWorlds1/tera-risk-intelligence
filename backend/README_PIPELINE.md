# 🌍 Haupt-Pipeline - Komplette Übersicht

## ✅ Status: FUNKTIONSFÄHIG

Alle Komponenten sind integriert und funktionieren zusammen!

## Komponenten

### 1. IPCC Context Engine
- **Datei**: `ipcc_context_engine.py`
- **Funktion**: Erstellt IPCC-basierten Kontext für Firecrawl und LLM
- **Baseline**: 1850-1900 (vorindustriell)
- **Schwellenwerte**: 1.5°C, 2.0°C

### 2. Firecrawl Enrichment
- **Datei**: `firecrawl_enrichment.py`
- **Funktion**: Datenanreicherung mit Firecrawl (IPCC-basiert)
- **Features**: Search, Map, Crawl, Extract

### 3. LLM Predictions
- **Datei**: `llm_predictions.py`
- **Funktion**: LLM-basierte Predictions mit IPCC-Kontext
- **Model**: gpt-4o-mini

### 4. Data Extraction
- **Datei**: `data_extraction.py`
- **Funktion**: Extrahiert Zahlen aus Text
- **Features**: Temperaturen, Niederschlag, Bevölkerung, Finanzbeträge

### 5. Risk Scoring
- **Datei**: `risk_scoring.py`
- **Funktion**: Berechnet Risk Scores
- **Metriken**: Climate Risk, Conflict Risk, Urgency

### 6. Time Series Predictions
- **Datei**: `time_series_predictions.py`
- **Funktion**: Zeitreihenvorhersagen
- **Features**: Trends für 30/90/180 Tage

### 7. Enriched Predictions Pipeline
- **Datei**: `enriched_predictions.py`
- **Funktion**: Kombiniert Firecrawl + LLM + Predictions
- **IPCC-basiert**: Ja

### 8. Main Pipeline
- **Datei**: `main_pipeline.py`
- **Funktion**: Führt alle Komponenten zusammen
- **Status**: ✅ FUNKTIONSFÄHIG

## Verwendung

### Haupt-Pipeline ausführen

```bash
cd backend
python3 main_pipeline.py
```

### Einzelne Komponenten testen

```bash
# IPCC-Kontext testen
python3 test_ipcc_context.py

# Enriched Predictions
python3 run_enriched_predictions.py

# Standard Predictions
python3 run_predictions.py
```

## Workflow

```
1. Record aus DB laden
   ↓
2. IPCC-Kontext erstellen
   ↓
3. Firecrawl-Anreicherung (IPCC-basiert)
   ├─ Search mit IPCC-Keywords
   ├─ Extract mit IPCC-Schema
   └─ Anreicherung mit wissenschaftlichen Quellen
   ↓
4. Data Extraction
   ├─ Zahlen extrahieren
   ├─ Temperaturen, Niederschlag, etc.
   └─ IPCC-Anomalien berechnen
   ↓
5. Risk Scoring
   ├─ Climate Risk
   ├─ Conflict Risk
   └─ Urgency
   ↓
6. LLM-Predictions (IPCC-basiert)
   ├─ Bewertung gegen IPCC-Baseline
   ├─ Schwellenwert-Analyse
   └─ IPCC-basierte Empfehlungen
   ↓
7. Time Series Predictions
   ├─ Trend-Analyse
   └─ Vorhersagen für 30/90/180 Tage
   ↓
8. Kombinierte Analyse
   └─ Alle Ergebnisse zusammenführen
```

## Output-Beispiel

```json
{
  "record_id": 1,
  "ipcc_context": {
    "focus_areas": ["temperature", "precipitation"],
    "baseline": "1850-1900",
    "current_anomaly": "1.1°C"
  },
  "enrichment": {
    "methods_used": ["search", "extract"],
    "search_results": [...],
    "extracted_data": {...}
  },
  "predictions": {
    "extracted_numbers": {
      "temperatures": [35.0],
      "affected_people": 2000000
    },
    "risk_score": {
      "total": 0.65,
      "level": "HIGH"
    },
    "llm_prediction": {
      "prediction_text": "Risk Level: HIGH",
      "ipcc_relevance": "high",
      "baseline_comparison": "1.2°C über vorindustriell"
    }
  },
  "time_series": {
    "trend": "increasing",
    "predictions": {
      "30_days": 0.68,
      "90_days": 0.72
    }
  },
  "combined_analysis": {
    "overall_risk": "HIGH",
    "key_insights": [...],
    "recommendations": [...]
  },
  "costs": {
    "firecrawl_credits_used": 5.0,
    "openai_cost_usd": 0.0001
  }
}
```

## API Keys

```python
FIRECRAWL_API_KEY = "fc-a0b3b8aa31244c10b0f15b4f2d570ac7"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY_HERE"
```

## Kosten-Tracking

- **Firecrawl**: 20.000 Credits verfügbar
- **OpenAI**: Automatisches Tracking
- **Monitoring**: Echtzeit in Pipeline

## Nächste Schritte

1. ✅ Alle Komponenten integriert
2. ✅ IPCC-Kontext als Grundlage
3. ✅ Pipeline funktionsfähig
4. 🔄 Weitere Tests mit mehr Daten
5. 🔄 Optimierungen
6. 🔄 Erweiterte Features

## Dokumentation

- `IPCC_CONTEXT_FOUNDATION.md` - IPCC-Kontext als Grundlage
- `FIRECRAWL_INTEGRATION.md` - Firecrawl-Integration
- `PREDICTION_SYSTEM.md` - Prediction-System
- `IPCC_ENRICHMENT_STRATEGY.md` - Anreicherungsstrategie



