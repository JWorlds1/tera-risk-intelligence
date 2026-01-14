# 🌍 IPCC-Kontext als Grundlage

## Übersicht

Der **IPCC-Kontext** ist jetzt die Grundlage für:
- ✅ **Firecrawl-Suchen**: IPCC-basierte Keywords und Kategorien
- ✅ **OpenAI/LLM-Predictions**: IPCC-Baseline und Schwellenwerte als Referenz
- ✅ **Agent-basierte Extraktion**: IPCC-spezifische Schemas

## Architektur

```
┌─────────────────────────────────────────┐
│     IPCC Context Engine                 │
│     (Zentrale Kontext-Quelle)           │
│                                          │
│  - IPCC-Baseline (1850-1900)            │
│  - Schwellenwerte (1.5°C, 2.0°C)        │
│  - CO2-Konzentrationen                  │
│  - Hauptrisiken                         │
│  - Vulnerable Regionen                  │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼────────┐   ┌────────▼────┐
│ Firecrawl  │   │ OpenAI/LLM  │
│             │   │              │
│ Nutzt IPCC │   │ Nutzt IPCC  │
│ Keywords    │   │ Baseline    │
│ Kategorien  │   │ Schwellen-  │
│             │   │ werte       │
└─────────────┘   └─────────────┘
```

## IPCC-Kontext-Engine

### Kernfunktionen

```python
from ipcc_context_engine import IPCCContextEngine

engine = IPCCContextEngine()

# 1. Firecrawl-Kontext
firecrawl_context = engine.get_firecrawl_context(record)
# → Keywords, Kategorien, IPCC-Baseline-Info

# 2. LLM-Kontext
llm_context = engine.get_llm_context(record, extracted_numbers)
# → IPCC-Baseline, Schwellenwerte, regionale Kontext
```

### IPCC-Kernaussagen (AR6)

**Temperatur-Baseline:**
- Vorindustriell (1850-1900): Referenzperiode
- Aktuelle Anomalie: 1.1°C über vorindustriell
- Ziel: <1.5°C (idealerweise) oder <2.0°C

**CO2-Konzentration:**
- Vorindustriell: 280 ppm
- Aktuell (2021): 410 ppm
- Ziel: Netto-Null bis 2050

**Meeresspiegel-Anstieg:**
- Seit 1901: +20 cm
- Projektion 2100: +28-101 cm (je nach Szenario)

**Hauptrisiken:**
- Extreme heat events
- Heavy precipitation
- Drought
- Sea level rise
- Biodiversity loss
- Food insecurity
- Water scarcity
- Humanitarian crises
- Displacement and migration

## Integration

### 1. Firecrawl mit IPCC-Kontext

```python
from firecrawl_enrichment import FirecrawlEnricher
from ipcc_context_engine import IPCCContextEngine

engine = IPCCContextEngine()
enricher = FirecrawlEnricher(api_key)

# Erstelle IPCC-Kontext
ipcc_context = engine.get_firecrawl_context(record)

# Suche mit IPCC-Kontext
results, credits = enricher.enrich_with_search(
    keywords=["drought", "East Africa"],
    region="East Africa",
    limit=10,
    ipcc_context=ipcc_context  # IPCC-Kontext übergeben
)
```

**Was passiert:**
- IPCC-Keywords werden automatisch hinzugefügt
- Suche in Research-Kategorie (IPCC-Reports)
- Query wird mit "IPCC AR6 climate change" erweitert
- Fokus auf wissenschaftliche Quellen

### 2. LLM-Predictions mit IPCC-Kontext

```python
from llm_predictions import LLMPredictor
from ipcc_context_engine import IPCCContextEngine

engine = IPCCContextEngine()
predictor = LLMPredictor(provider="openai")

# Erstelle IPCC-Kontext
ipcc_context = engine.get_llm_context(record, extracted_numbers)

# Prediction mit IPCC-Kontext
prediction = predictor.predict_risk(
    record,
    extracted_numbers,
    ipcc_context=ipcc_context  # IPCC-Kontext übergeben
)
```

**Was passiert:**
- IPCC-Baseline (1850-1900) wird als Referenz verwendet
- Schwellenwerte (1.5°C, 2.0°C) werden berücksichtigt
- Bewertung basiert auf IPCC-Kriterien
- Empfehlungen orientieren sich an IPCC-Findings

### 3. Enriched Predictions Pipeline

```python
from enriched_predictions import EnrichedPredictionPipeline

pipeline = EnrichedPredictionPipeline(
    firecrawl_api_key="fc-...",
    openai_api_key="sk-..."
)

# Automatisch mit IPCC-Kontext
result = pipeline.enrich_and_predict(
    record_id=1,
    use_search=True,
    use_extract=True,
    use_llm=True
)
```

**Was passiert automatisch:**
1. IPCC-Kontext wird für Firecrawl erstellt
2. Firecrawl-Suche nutzt IPCC-Keywords
3. IPCC-Kontext wird für LLM erstellt
4. LLM-Predictions nutzen IPCC-Baseline
5. Alle Ergebnisse sind IPCC-basiert

## Beispiel-Output

### Firecrawl-Kontext

```json
{
  "keywords": [
    "East Africa",
    "temperature anomaly",
    "global warming",
    "drought",
    "IPCC",
    "climate change"
  ],
  "categories": ["research"],
  "ipcc_context": {
    "baseline_period": "1850-1900",
    "current_anomaly": "1.1°C",
    "target": "1.5°C"
  },
  "focus_areas": ["temperature", "precipitation"]
}
```

### LLM-Kontext

```
## IPCC-Kontext (AR6 - Sechster Sachstandsbericht):

**Temperatur-Baseline:**
- Vorindustriell (1850-1900): Referenzperiode
- Aktuelle Anomalie: 1.1°C über vorindustriellem Niveau
- Paris-Ziel: Begrenzung auf 1.5°C (idealerweise) oder 2.0°C

**CO2-Konzentration:**
- Vorindustriell: 280 ppm
- Aktuell (2021): 410 ppm
- Ziel: Netto-Null bis 2050

**Hauptrisiken (laut IPCC):**
- Extreme heat events
- Heavy precipitation
- Drought
- Sea level rise
- Biodiversity loss
```

### LLM-Prediction mit IPCC-Kontext

```json
{
  "risk_level": "HIGH",
  "confidence": 0.85,
  "reasoning": "Temperatur-Anomalie von 1.2°C liegt nahe am 1.5°C-Schwellenwert laut IPCC...",
  "ipcc_relevance": "high",
  "baseline_comparison": "1.2°C über vorindustriellem Niveau (IPCC-Baseline: 1850-1900)",
  "threshold_proximity": "Nahe am 1.5°C-Schwellenwert",
  "key_factors": [
    "IPCC-identifiziertes Risiko: Extreme heat events",
    "IPCC-identifiziertes Risiko: Drought"
  ],
  "recommendations": [
    "IPCC-basierte Anpassungsmaßnahmen",
    "Monitoring gemäß IPCC-Empfehlungen"
  ]
}
```

## Verwendung

### Test ausführen

```bash
cd backend
python3 test_ipcc_context.py
```

### In Code verwenden

```python
from ipcc_context_engine import IPCCContextEngine
from enriched_predictions import EnrichedPredictionPipeline

# Pipeline nutzt automatisch IPCC-Kontext
pipeline = EnrichedPredictionPipeline(
    firecrawl_api_key="fc-...",
    openai_api_key="sk-..."
)

result = pipeline.enrich_and_predict(record_id=1)
# → Alle Suchen und Predictions sind IPCC-basiert
```

## Vorteile

### 1. Wissenschaftliche Fundierung
- Alle Bewertungen basieren auf IPCC-AR6
- Konsistente Referenzpunkte
- Nachvollziehbare Kriterien

### 2. Bessere Suchergebnisse
- Fokus auf wissenschaftliche Quellen
- IPCC-relevante Keywords
- Research-Kategorie für akademische Papers

### 3. Präzisere Predictions
- Baseline-Vergleiche (vorindustriell)
- Schwellenwert-Bewertungen (1.5°C, 2.0°C)
- IPCC-basierte Risikoklassifikation

### 4. Konsistenz
- Einheitliche Bewertungskriterien
- Vergleichbare Ergebnisse
- Nachvollziehbare Begründungen

## IPCC-Baseline als Referenz

### Temperatur-Anomalie-Berechnung

```python
# IPCC-Baseline: ~13.5°C (vorindustriell 1850-1900)
baseline_temp = 13.5  # °C

# Aktuelle Temperatur
current_temp = 35.0  # °C

# Anomalie berechnen
anomaly = current_temp - baseline_temp  # 21.5°C

# Aber: Regionale Temperaturen sind höher als globale Durchschnitt
# Für globale Anomalie: ~1.1°C (IPCC AR6)
```

### Bewertung gegen Schwellenwerte

```python
# IPCC-Schwellenwerte
threshold_1_5 = 1.5  # °C
threshold_2_0 = 2.0  # °C

# Aktuelle globale Anomalie
current_anomaly = 1.1  # °C

if current_anomaly >= threshold_1_5:
    risk_level = "CRITICAL"
elif current_anomaly >= threshold_2_0:
    risk_level = "HIGH"
else:
    risk_level = "MEDIUM"
```

## Nächste Schritte

1. ✅ IPCC-Kontext-Engine implementiert
2. ✅ Firecrawl nutzt IPCC-Kontext
3. ✅ LLM nutzt IPCC-Kontext
4. ✅ Enriched Pipeline integriert
5. 🔄 Testen mit echten Daten
6. 🔄 Erweitern um weitere IPCC-Metriken

## Zusammenfassung

Der **IPCC-Kontext** ist jetzt die zentrale Grundlage für:
- **Firecrawl**: Sucht mit IPCC-Keywords in Research-Kategorie
- **OpenAI/LLM**: Bewertet gegen IPCC-Baseline und Schwellenwerte
- **Agenten**: Extrahieren IPCC-relevante Daten

Alle Komponenten nutzen jetzt konsistent die IPCC-AR6-Bewertungen als Referenz!

