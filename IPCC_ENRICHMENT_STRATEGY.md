# 🌍 IPCC-basierte Anreicherungsstrategie

## Übersicht

Agentenbasiertes System zur dynamischen Anreicherung von Daten mit:
- **IPCC-Daten**: Temperatur-Anomalien, Niederschlags-Veränderungen, CO2-Konzentrationen
- **Satellitenbilder**: NDVI-Karten, Vegetations-Indizes, NASA Earth Observatory
- **Echtzeit-Zustände**: Aktuelle Wetterdaten, Krisen-Updates, Live-Informationen
- **Fakten & Realitäten**: Wissenschaftliche Erkenntnisse, IPCC-Findings
- **Dynamische Trends**: Zeitreihen-Analysen, Vorhersagen

## Architektur

```
┌─────────────────────────────────────────────────────────┐
│         Dynamic Enrichment Orchestrator                 │
│         (Koordiniert alle Agenten)                      │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐   ┌───────▼────────┐
│ IPCC Agent     │   │ Satellite Agent│
│                 │   │                 │
│ - IPCC-Daten   │   │ - NDVI-Maps    │
│ - Anomalien    │   │ - Satelliten-  │
│ - Findings     │   │   bilder       │
└───────┬────────┘   └───────┬────────┘
        │                     │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │ Real-Time Agent     │
        │                      │
        │ - Aktuelle Daten    │
        │ - Live-Updates      │
        │ - Echtzeit-Zustände │
        └─────────────────────┘
```

## Datenquellen

### 1. IPCC-basierte Metriken

**Temperatur-Anomalie**
- Baseline: 1850-1900 (vorindustriell)
- Aktuell: ~1.1°C über Baseline
- Ziel: <1.5°C (Paris Agreement)

**Niederschlags-Anomalie**
- Prozentuale Abweichung vom Normalwert
- Regionale Unterschiede
- Extreme Ereignisse

**NDVI-Anomalie**
- Normalized Difference Vegetation Index
- Vegetationsgesundheit
- Dürre-Indikator

**CO2-Konzentration**
- Aktuell: ~410 ppm (2021)
- Vorindustriell: ~280 ppm
- Ziel: Netto-Null bis 2050

**Meeresspiegel-Anstieg**
- Aktuell: +20 cm seit 1901
- Projektion: +0.28-1.01 m bis 2100

### 2. Satelliten-Daten

**Quellen:**
- NASA Earth Observatory
- MODIS, Landsat, Sentinel
- NDVI-Karten
- Vegetations-Indizes

**Extraktion:**
- Firecrawl Search mit Bildern
- NASA-spezifische URLs
- NDVI-spezifische Quellen

### 3. Echtzeit-Daten

**Quellen:**
- Aktuelle Nachrichten
- Wetter-Updates
- Krisen-Berichte
- Live-Datenfeeds

**Zeitfenster:**
- Letzte 24 Stunden
- Aktuelle Bedingungen
- Live-Updates

## Agent-basierte Verarbeitung

### IPCC Enrichment Agent

```python
from ipcc_enrichment_agent import IPCCEnrichmentAgent

agent = IPCCEnrichmentAgent(firecrawl_api_key, openai_api_key)

# IPCC-Daten anreichern
enrichment = agent.enrich_with_ipcc_data(
    region="East Africa",
    record=record
)

# Satelliten-Daten
satellite_data = agent.enrich_with_satellite_data(
    region="East Africa"
)

# Echtzeit-Daten
real_time_data = agent.enrich_with_real_time_data(
    region="East Africa",
    record=record
)
```

### Dynamic Enrichment Orchestrator

```python
from ipcc_enrichment_agent import DynamicEnrichmentOrchestrator

orchestrator = DynamicEnrichmentOrchestrator(
    firecrawl_api_key,
    openai_api_key
)

# Umfassende Anreicherung
result = orchestrator.enrich_record_comprehensive(
    record,
    use_ipcc=True,
    use_satellite=True,
    use_real_time=True
)
```

## Output-Struktur

### EnrichmentData

```json
{
  "temperature_anomaly": 1.1,
  "precipitation_anomaly": -15.5,
  "ndvi_anomaly": -0.1383,
  "co2_concentration": 410,
  "current_temperature": 35.0,
  "current_precipitation": 50.0,
  "affected_population": 2000000,
  "key_facts": [
    "Severe drought conditions",
    "Water scarcity increasing"
  ],
  "ipcc_findings": [
    "Temperature anomaly exceeds 1.5°C threshold",
    "Precipitation patterns shifting"
  ],
  "trends": {
    "temperature": "increasing",
    "precipitation": "decreasing"
  },
  "satellite_images": [
    "https://earthobservatory.nasa.gov/..."
  ],
  "ndvi_maps": [
    "https://..."
  ]
}
```

## Integration mit bestehendem System

### Kombination mit Predictions

```python
from enriched_predictions import EnrichedPredictionPipeline
from ipcc_enrichment_agent import DynamicEnrichmentOrchestrator

# 1. Anreicherung
orchestrator = DynamicEnrichmentOrchestrator(...)
enrichment = orchestrator.enrich_record_comprehensive(record)

# 2. Predictions mit angereicherten Daten
pipeline = EnrichedPredictionPipeline(...)
predictions = pipeline.enrich_and_predict(
    record_id=record['id'],
    use_search=True,
    use_extract=True,
    use_llm=True
)

# 3. Kombiniere Ergebnisse
combined = {
    "enrichment": enrichment,
    "predictions": predictions,
    "ipcc_metrics": enrichment['ipcc_data'],
    "satellite_data": enrichment['satellite_data']
}
```

## Verwendung

### Demo ausführen

```bash
cd backend
python3 run_ipcc_enrichment.py
```

### In Code verwenden

```python
from ipcc_enrichment_agent import DynamicEnrichmentOrchestrator

orchestrator = DynamicEnrichmentOrchestrator(
    firecrawl_api_key="fc-...",
    openai_api_key="sk-..."
)

# Reichere Record an
result = orchestrator.enrich_record_comprehensive(
    record={
        'id': 1,
        'title': 'Drought in East Africa',
        'region': 'East Africa'
    },
    use_ipcc=True,
    use_satellite=True,
    use_real_time=True
)

# Nutze angereicherte Daten
ipcc_data = result['ipcc_data']
satellite_images = result['satellite_data']['satellite_images']
real_time_updates = result['real_time_data']['updates']
```

## Kosten-Management

### Firecrawl Credits
- **Search**: ~2 Credits pro 10 Ergebnisse
- **Mit Scraping**: ~1 Credit pro Ergebnis
- **Research-Kategorie**: Zusätzliche Kosten

### OpenAI Kosten
- **gpt-4o-mini**: ~$0.0002 pro Request
- **IPCC-Analysen**: ~500-1000 Tokens

### Empfehlungen
- Nutze `use_ipcc=True` für wichtige Records
- `use_satellite=True` nur wenn Visualisierungen benötigt
- `use_real_time=True` für aktuelle Updates
- Batch-Verarbeitung für mehrere Records

## Erweiterungen

### Geplante Features

1. **NASA API Integration**
   - Direkter Zugriff auf Satelliten-Daten
   - NDVI-Zeitreihen
   - Temperatur-Daten

2. **IPCC-Datenbank Integration**
   - Direkter Zugriff auf IPCC-Reports
   - Strukturierte Metadaten
   - Historische Daten

3. **Real-Time Feeds**
   - Wetter-APIs
   - Krisen-Datenbanken
   - Live-Updates

4. **Visualisierungs-Agent**
   - Automatische Karten-Generierung
   - NDVI-Visualisierungen
   - Trend-Diagramme

## Best Practices

### 1. Regionale Spezifität
- Nutze präzise Regionen für bessere Ergebnisse
- Kombiniere mehrere Regionen für Vergleich

### 2. Zeitliche Relevanz
- Echtzeit-Daten für aktuelle Situationen
- Historische Daten für Trends
- IPCC-Daten für Kontext

### 3. Datenqualität
- Validiere extrahierte Zahlen
- Prüfe Quellen-Verlässlichkeit
- Kombiniere mehrere Quellen

### 4. Kosten-Optimierung
- Nutze Caching für wiederholte Anfragen
- Batch-Verarbeitung für mehrere Records
- Selektive Anreicherung je nach Bedarf

## Beispiel-Workflow

```python
# 1. Hole Records aus DB
records = db.get_records(limit=10)

# 2. Reichere mit IPCC-Daten an
for record in records:
    enrichment = orchestrator.enrich_record_comprehensive(
        record,
        use_ipcc=True,
        use_satellite=True,
        use_real_time=True
    )
    
    # 3. Nutze für Predictions
    predictions = pipeline.enrich_and_predict(record['id'])
    
    # 4. Kombiniere Ergebnisse
    combined = {
        **enrichment,
        **predictions
    }
    
    # 5. Speichere in DB
    save_enriched_data(record['id'], combined)
```

## Nächste Schritte

1. ✅ IPCC-basierte Anreicherung implementiert
2. ✅ Satelliten-Daten-Integration
3. ✅ Echtzeit-Daten-Anreicherung
4. 🔄 NASA API Integration
5. 🔄 Visualisierungs-Agent
6. 🔄 Automatische Updates

