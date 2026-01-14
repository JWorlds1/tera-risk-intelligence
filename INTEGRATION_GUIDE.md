# 🔗 System-Integration Guide

## Übersicht

Dieses Dokument beschreibt, wie alle Komponenten des Climate Conflict Intelligence Systems zusammenarbeiten.

## 🏗️ Architektur

```
┌─────────────────────────────────────────────────────────┐
│              Master Orchestrator                         │
│         (Koordiniert alle Agenten)                      │
└──────────────┬──────────────────────────────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼───┐  ┌──▼───┐  ┌───▼────┐
│Scraper│  │Enrich│  │Predict │
│Agent  │  │Agent │  │Agent   │
└───┬───┘  └──┬───┘  └───┬────┘
    │         │          │
    └─────────┼──────────┘
              │
         ┌────▼────┐
         │Database │
         │Manager  │
         └────┬────┘
              │
         ┌────▼────┐
         │ Frontend│
         │  (Web)  │
         └─────────┘
```

## 📦 Komponenten

### 1. Master Orchestrator (`master_orchestrator.py`)

**Zweck**: Koordiniert alle Agenten und ermöglicht Datenaustausch

**Features**:
- Message Bus für Agent-Kommunikation
- Pipeline-Koordination (Scraping → Enrichment → Geocoding → Prediction)
- Regionale Fokus-Regionen (Deutschland, Europa)
- Status-Tracking für alle Komponenten

**Verwendung**:
```python
from master_orchestrator import MasterOrchestrator
from config import Config

config = Config()
orchestrator = MasterOrchestrator(config)
await orchestrator.initialize()

# Führe komplette Pipeline aus
results = await orchestrator.run_full_pipeline(
    enrich=True,
    predict=True,
    geocode=True,
    focus_regions=['Germany', 'Europe']
)
```

### 2. Scraping Orchestrator (`orchestrator.py`)

**Zweck**: Extrahiert Daten von Webseiten

**Komponenten**:
- Compliance Agent (robots.txt, Rate Limiting)
- Multi-Agent Fetcher (HTTP + Playwright Fallback)
- Extractor Factory (NASA, UN, World Bank)
- Validation Agent
- Storage Agent

**Datenquellen**:
- NASA Earth Observatory
- UN Press
- World Bank News

### 3. Enrichment Agent (`ipcc_enrichment_agent.py`)

**Zweck**: Reichert Daten mit zusätzlichen Informationen an

**Features**:
- IPCC-basierte Datenanreicherung
- Satelliten-Daten
- Echtzeit-Daten
- Firecrawl Integration

**Verwendung**:
```python
from ipcc_enrichment_agent import DynamicEnrichmentOrchestrator

enricher = DynamicEnrichmentOrchestrator(
    firecrawl_api_key="...",
    openai_api_key="..."
)

enrichment = enricher.enrich_record_comprehensive(
    record,
    use_ipcc=True,
    use_satellite=True,
    use_real_time=True
)
```

### 4. Database Manager (`database.py`)

**Zweck**: Zentrale Datenbank-Verwaltung

**Tabellen**:
- `records` - Haupttabelle für alle Records
- `enriched_data` - Angereicherte Daten
- `regional_enrichment` - Regionale Aggregationen
- `regional_predictions` - Regionale Vorhersagen
- `geo_locations` - Geografische Daten
- `nasa_records`, `un_press_records`, `worldbank_records` - Source-spezifische Daten

**Verwendung**:
```python
from database import DatabaseManager

db = DatabaseManager()

# Records einfügen
record_id, is_new = db.insert_record(record)

# Records abrufen
records = db.get_records(limit=100, source_name='NASA')

# Statistiken
stats = db.get_statistics()
```

### 5. Frontend (`web_app.py`)

**Zweck**: Web-Interface für Datenvisualisierung

**Endpoints**:
- `/` - Hauptdashboard
- `/api/stats` - Statistiken
- `/api/records` - Records mit Risiko-Scores
- `/api/regional-data` - Regionale Daten (Deutschland/Europa)
- `/api/regional-records` - Records für spezifische Region
- `/api/map-data` - Daten für Karte
- `/api/predictions` - Vorhersagen
- `/api/enrichment` - Enrichment-Statistiken

**Tabs**:
1. **Karte** - Interaktive Weltkarte mit Risiko-Markern
2. **Records** - Liste aller Records mit Risiko-Scores
3. **Regionen** - Regionale Übersicht (Deutschland/Europa)
4. **Enrichment** - Angereicherte Daten
5. **Predictions** - Vorhersagen für gefährdete Regionen
6. **Datenquellen** - Informationen zu Datenquellen

## 🔄 Datenfluss

### 1. Scraping Phase
```
URLs → Compliance Check → Fetch → Extract → Validate → Store in DB
```

### 2. Enrichment Phase
```
Records → IPCC Enrichment → Satellite Data → Real-time Data → Store in enriched_data
```

### 3. Geocoding Phase
```
Records → Geocoding Service → Update coordinates → Store in records
```

### 4. Prediction Phase
```
Records + Enrichment → Risk Scoring → Predictions → Store in regional_predictions
```

### 5. Frontend Display
```
Database → API Endpoints → Frontend → User
```

## 🌍 Regionale Fokus-Regionen

### Deutschland
- **Keywords**: Germany, Deutschland, German
- **Country Codes**: DE
- **Priorität**: 1

### Europa
- **Keywords**: Europe, Europa, European, EU
- **Country Codes**: DE, FR, IT, ES, PL, NL, BE, AT, CH, CZ, SE, NO, DK, FI
- **Priorität**: 2

## 📊 Agent-Kommunikation

### Message Bus

Agenten kommunizieren über einen Message Bus:

```python
from master_orchestrator import AgentMessage, AgentMessageBus

message_bus = AgentMessageBus()

# Nachricht senden
message = AgentMessage(
    sender='scraper',
    receiver='enrichment',
    message_type='data',
    payload={'action': 'records_added', 'count': 10}
)
message_bus.publish(message)

# Nachrichten abonnieren
def handle_message(message):
    print(f"Received: {message.payload}")

message_bus.subscribe('enrichment', handle_message)
```

## 🧪 Testing

### Integrationstest

```bash
python backend/test_integration.py
```

Testet:
- ✅ Datenbank-Verbindung
- ✅ Scraping-Komponenten
- ✅ Enrichment-Komponenten
- ✅ Geocoding
- ✅ Prediction-Komponenten
- ✅ Regionale Daten-Aggregation
- ✅ Frontend API

## 🚀 Verwendung

### 1. Komplette Pipeline ausführen

```bash
python backend/master_orchestrator.py
```

Führt aus:
1. Scraping von allen Datenquellen
2. Geocoding der Records
3. Enrichment mit IPCC-Daten
4. Erstellung von Predictions
5. Aggregation regionaler Daten

### 2. Frontend starten

```bash
python backend/web_app.py
```

Öffne im Browser: `http://localhost:5000`

### 3. Einzelne Komponenten testen

```bash
# Scraping
python backend/run_pipeline.py

# Enrichment
python backend/run_ipcc_enrichment.py

# Predictions
python backend/run_enriched_predictions.py
```

## 🔧 Konfiguration

### Environment Variables

```bash
# Firecrawl API
FIRECRAWL_API_KEY=fc-...

# OpenAI API (optional)
OPENAI_API_KEY=sk-...

# Rate Limiting
RATE_LIMIT=1.0
MAX_CONCURRENT=3

# Storage
STORAGE_DIR=./data
```

### Config (`config.py`)

Alle Konfigurationen werden zentral in `config.py` verwaltet.

## 📈 Monitoring

### Status abfragen

```python
status = orchestrator.get_status()
print(status)
```

Zeigt:
- Status aller Komponenten
- Datenbank-Statistiken
- Message Bus Status

### Logs

Strukturierte Logs mit `structlog`:
- Scraping-Aktivitäten
- Enrichment-Prozesse
- Fehler und Warnungen

## 🐛 Troubleshooting

### Problem: Keine Records in Datenbank

**Lösung**: Führe Scraping-Pipeline aus
```bash
python backend/run_pipeline.py
```

### Problem: Enrichment schlägt fehl

**Lösung**: Prüfe Firecrawl API Key
```python
# In config.py oder .env
FIRECRAWL_API_KEY=fc-...
```

### Problem: Frontend zeigt keine Daten

**Lösung**: 
1. Prüfe ob Datenbank existiert: `./data/climate_conflict.db`
2. Prüfe API-Endpoints: `curl http://localhost:5000/api/stats`
3. Prüfe Browser-Konsole für Fehler

### Problem: Geocoding funktioniert nicht

**Lösung**: Geocoding-Service benötigt Internet-Verbindung. Prüfe:
- Internet-Verbindung
- Geocoding-Service-API (falls verwendet)

## 📝 Best Practices

1. **Immer Master Orchestrator verwenden** für vollständige Pipeline
2. **Regionale Fokus-Regionen** definieren für bessere Performance
3. **Message Bus** nutzen für Agent-Kommunikation
4. **Datenbank-Indizes** verwenden für Performance
5. **Strukturierte Logs** für Debugging

## 🔮 Erweiterungen

### Neue Regionen hinzufügen

In `master_orchestrator.py`:
```python
self.critical_regions['NewRegion'] = {
    'countries': ['XX'],
    'keywords': ['Keyword1', 'Keyword2'],
    'priority': 3
}
```

### Neue Datenquellen hinzufügen

1. Erstelle Extractor in `extractors.py`
2. Füge zu `ExtractorFactory` hinzu
3. Füge URLs zu `url_lists.py` hinzu

### Neue Enrichment-Methoden

1. Erweitere `IPCCEnrichmentAgent`
2. Füge zu `DynamicEnrichmentOrchestrator` hinzu
3. Update Datenbank-Schema falls nötig

## 📚 Weitere Dokumentation

- `README.md` - Allgemeine Übersicht
- `PIPELINE_README.md` - Pipeline-Details
- `AGENT_README.md` - Agent-System
- `FRONTEND_SUMMARY.md` - Frontend-Details

