# 🔮 Prediction System - Dokumentation

## Übersicht

Das Prediction System kombiniert **LLM-basierte semantische Analysen** mit **numerischen Zeitreihenvorhersagen** um aus gecrawlten Daten Vorhersagen zu erstellen.

## Architektur

```
┌─────────────────────────────────────────────────────────┐
│              Gecrawlte Daten (Database)                 │
│  - NASA, UN Press, World Bank Records                  │
│  - Text: title, summary, full_text                     │
│  - Metadaten: region, date, source                      │
└──────────────────┬────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐   ┌───────▼────────┐
│ Data Extraction│   │ Risk Scoring   │
│                 │   │                │
│ Extrahiert:     │   │ Berechnet:     │
│ - Temperaturen  │   │ - Climate Risk │
│ - Niederschlag  │   │ - Conflict Risk│
│ - Bevölkerung   │   │ - Urgency      │
│ - Finanzbeträge │   │ - Gesamt-Score │
└───────┬────────┘   └───────┬────────┘
        │                     │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │  Prediction Pipeline │
        └──────────┬──────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐   ┌───────▼────────┐
│ LLM Predictions│   │ Time Series     │
│                 │   │ Predictions     │
│ - Risk Analysis │   │                 │
│ - Trend Analysis│   │ - Risk Trends   │
│ - Impact Assess │   │ - Temp Trends   │
│ - Recommendations│  │ - Population    │
└───────┬────────┘   └───────┬────────┘
        │                     │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │ Combined Predictions│
        │ - Gesamt-Risiko     │
        │ - Konfidenz         │
        │ - Zeithorizont      │
        │ - Empfehlungen      │
        └─────────────────────┘
```

## Module

### 1. Data Extraction (`data_extraction.py`)

Extrahiert strukturierte numerische Daten aus Text:

**Extrahiert:**
- 🌡️ **Temperaturen** (Celsius/Fahrenheit)
- 🌧️ **Niederschlag** (mm/inches)
- 👥 **Bevölkerungszahlen** (mit Millionen/Milliarden)
- 💰 **Finanzbeträge** (USD, mit Multiplikatoren)
- 📊 **Prozentsätze**
- 📅 **Datumsangaben**
- 📍 **Orte/Regionen**

**Beispiel:**
```python
from data_extraction import NumberExtractor

extractor = NumberExtractor()
text = "Temperature reached 35°C. 2 million people affected. $500M funding."
extracted = extractor.extract_all(text)

print(extracted.temperatures)  # [35.0]
print(extracted.population_numbers)  # [2000000]
print(extracted.financial_amounts)  # [500000000.0]
```

### 2. LLM Predictions (`llm_predictions.py`)

Nutzt LLMs (OpenAI/Anthropic) für semantische Analysen:

**Funktionen:**
- **Risk Prediction**: Bewertet Risiko-Level, Konfidenz, Zeithorizont
- **Trend Analysis**: Identifiziert Trends über mehrere Records
- **Impact Assessment**: Bewertet humanitäre, wirtschaftliche, geopolitische Auswirkungen

**Konfiguration:**
```python
# Setze Environment Variable
export OPENAI_API_KEY="your-key-here"

# Oder für Anthropic
export ANTHROPIC_API_KEY="your-key-here"
```

**Beispiel:**
```python
from llm_predictions import LLMPredictor

predictor = LLMPredictor(provider="openai", model="gpt-4o-mini")
prediction = predictor.predict_risk(record, extracted_numbers)

print(prediction.prediction_text)  # "Risk Level: HIGH"
print(prediction.confidence)  # 0.85
print(prediction.key_factors)  # ["drought", "population displacement"]
```

### 3. Time Series Predictions (`time_series_predictions.py`)

Erstellt numerische Zeitreihenvorhersagen:

**Methoden:**
- **Linear Regression**: Für Trends mit genug Datenpunkten
- **Moving Average**: Fallback für kleine Datensätze
- **Polynomial Regression**: Für komplexere Trends (mit scikit-learn)

**Vorhersagen:**
- Risk Score Trends
- Temperatur-Trends
- Bevölkerungsauswirkungen
- Niederschlags-Trends

**Beispiel:**
```python
from time_series_predictions import TimeSeriesPredictor

predictor = TimeSeriesPredictor()
prediction = predictor.predict_risk_score_trend(records, days_back=90)

print(prediction.current_value)  # 0.45
print(prediction.predictions)  # {"30_days": 0.48, "90_days": 0.52, "180_days": 0.55}
print(prediction.trend)  # "increasing"
```

### 4. Prediction Pipeline (`prediction_pipeline.py`)

Kombiniert alle Module:

**Funktionen:**
- `process_record(record_id)`: Verarbeitet einen einzelnen Record
- `process_all_records()`: Verarbeitet alle Records
- `create_trend_predictions()`: Erstellt Trend-Vorhersagen
- `get_combined_prediction()`: Kombiniert alle Prediction-Typen

**Beispiel:**
```python
from prediction_pipeline import PredictionPipeline

pipeline = PredictionPipeline()

# Verarbeite einen Record
result = pipeline.process_record(record_id=1)
print(result['extracted_numbers'])
print(result['risk_score'])
print(result['llm_prediction'])

# Erstelle Trend-Predictions
trends = pipeline.create_trend_predictions(days_back=90)
print(trends['predictions'])

# Kombinierte Prediction
combined = pipeline.get_combined_prediction(record_id=1)
print(combined['combined_prediction'])
```

## Datenbank-Schema

Das System erweitert die Datenbank um folgende Tabellen:

### `extracted_numbers`
Speichert extrahierte numerische Daten:
- `record_id`, `temperatures`, `precipitation`, `population_numbers`
- `financial_amounts`, `affected_people`, `funding_amount`

### `risk_scores`
Speichert berechnete Risk Scores:
- `record_id`, `total_score`, `climate_risk`, `conflict_risk`
- `urgency`, `risk_level`, `indicators`

### `llm_predictions`
Speichert LLM-basierte Vorhersagen:
- `record_id`, `prediction_type`, `prediction_text`
- `confidence`, `reasoning`, `predicted_timeline`
- `key_factors`, `recommendations`

### `trend_predictions`
Speichert Zeitreihenvorhersagen:
- `region`, `metric_name`, `current_value`
- `predictions` (JSON), `trend`, `confidence`, `model_type`

## Verwendung

### 1. Installation

```bash
# Basis-Abhängigkeiten
pip install numpy pandas

# Für LLM-Predictions (optional)
pip install openai  # oder anthropic

# Für bessere Zeitreihenvorhersagen (optional)
pip install scikit-learn
```

### 2. Environment Variables

```bash
# Für OpenAI
export OPENAI_API_KEY="your-key-here"

# Für Anthropic (Alternative)
export ANTHROPIC_API_KEY="your-key-here"
```

### 3. Demo ausführen

```bash
cd backend
python3 run_predictions.py
```

### 4. In Code verwenden

```python
from prediction_pipeline import PredictionPipeline

# Initialisiere Pipeline
pipeline = PredictionPipeline(
    llm_provider="openai",  # oder "anthropic"
    llm_model="gpt-4o-mini"  # oder "claude-3-haiku"
)

# Verarbeite alle Records
results = pipeline.process_all_records(limit=100)

# Erstelle Trend-Predictions
trends = pipeline.create_trend_predictions(
    region="East Africa",  # Optional
    days_back=90
)

# Hole kombinierte Prediction
combined = pipeline.get_combined_prediction(record_id=1)
```

## Output-Format

### Einzelner Record

```json
{
  "record_id": 1,
  "extracted_numbers": {
    "temperatures": [35.0],
    "precipitation": [50.0],
    "affected_people": 2000000,
    "funding_amount": 500000000.0
  },
  "risk_score": {
    "total": 0.65,
    "climate_risk": 0.7,
    "conflict_risk": 0.6,
    "urgency": 0.65,
    "level": "HIGH",
    "indicators": ["drought", "displacement"]
  },
  "llm_prediction": {
    "prediction_text": "Risk Level: HIGH",
    "confidence": 0.85,
    "reasoning": "...",
    "predicted_timeline": "medium_term",
    "key_factors": ["drought", "water scarcity"],
    "recommendations": ["Monitor situation", "Prepare response"]
  }
}
```

### Trend-Predictions

```json
{
  "region": "East Africa",
  "time_window_days": 90,
  "predictions": {
    "risk_score": {
      "current_value": 0.45,
      "predictions": {
        "30_days": 0.48,
        "90_days": 0.52,
        "180_days": 0.55
      },
      "trend": "increasing",
      "confidence": 0.75,
      "model_type": "linear"
    },
    "temperature": {
      "current_value": 32.5,
      "predictions": {
        "30_days": 33.0,
        "90_days": 33.5,
        "180_days": 34.0
      },
      "trend": "increasing",
      "confidence": 0.65
    }
  }
}
```

## Best Practices

### 1. Datenqualität
- Stelle sicher, dass Records vollständige Textdaten haben
- Validiere Datumsangaben vor der Verarbeitung
- Filtere Duplikate vor Trend-Analysen

### 2. LLM-Konfiguration
- Verwende günstigere Modelle (gpt-4o-mini) für große Datenmengen
- Setze `temperature=0.3` für konsistentere Ergebnisse
- Nutze `response_format={"type": "json_object"}` für strukturierte Outputs

### 3. Zeitreihenvorhersagen
- Mindestens 5-10 Datenpunkte für zuverlässige Vorhersagen
- Verwende `days_back=90` für kurzfristige Trends
- Kombiniere mehrere Metriken für robustere Vorhersagen

### 4. Performance
- Verarbeite Records in Batches
- Cache LLM-Responses für ähnliche Records
- Nutze Indizes in der Datenbank für schnelle Queries

## Erweiterungen

### Zukünftige Features

1. **Multi-Model Ensemble**: Kombiniere mehrere LLMs für robustere Vorhersagen
2. **Geospatial Predictions**: Nutze Koordinaten für regionale Vorhersagen
3. **Real-time Updates**: Automatische Updates bei neuen Records
4. **Confidence Intervals**: Statistische Konfidenzintervalle für Vorhersagen
5. **Anomaly Detection**: Erkennung von ungewöhnlichen Mustern

### Custom Extractions

Erweitere `NumberExtractor` für spezifische Metriken:

```python
class CustomExtractor(NumberExtractor):
    def extract_custom_metric(self, text: str) -> List[float]:
        # Custom extraction logic
        pass
```

## Troubleshooting

### LLM-Fehler
- Prüfe API-Key: `echo $OPENAI_API_KEY`
- Prüfe Rate Limits
- Nutze Mock-Mode für Tests ohne API-Key

### Zeitreihen-Fehler
- Stelle sicher, dass genug Datenpunkte vorhanden sind
- Prüfe Datumsformat
- Installiere scikit-learn für bessere Vorhersagen

### Datenbank-Fehler
- Prüfe Datenbankpfad
- Stelle sicher, dass Tabellen existieren
- Nutze `init_database()` wenn nötig

## Support

Bei Fragen oder Problemen:
1. Prüfe Logs in `backend/data/climate_conflict.db`
2. Teste einzelne Module isoliert
3. Nutze Demo-Script für Debugging

