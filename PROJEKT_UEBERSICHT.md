# 🌍 Geospatial Intelligence - Komplette Projektübersicht

## 📊 Aktueller Stand

### Projekt-Status
- **Datenbank**: SQLite-basiert (`data/climate_conflict.db`)
- **Backend**: Python-basiert mit Multi-Agent-Architektur
- **Frontend**: Web-App mit interaktiven Karten (Folium/Leaflet)
- **Information Retrieval**: ChromaDB + TF-IDF für semantische Suche

---

## 🏗️ Architektur-Übersicht

### 1. Datenbank-Struktur (`backend/database.py`)

Die zentrale SQLite-Datenbank speichert alle extrahierten Daten:

#### Haupttabellen:

**`records`** - Zentrale Tabelle für alle Web-Records
- `id`, `url`, `source_domain`, `source_name`
- `title`, `summary`, `publish_date`, `region`
- `full_text`, `content_type`, `language`
- `primary_country_code`, `primary_latitude`, `primary_longitude`
- `geo_confidence`

**`record_topics`** - Topics/Tags pro Record
- `record_id`, `topic`

**`record_links`** - Links pro Record
- `record_id`, `link_url`

**`record_images`** - Bild-URLs pro Record
- `record_id`, `image_url`

**Quellenspezifische Tabellen:**
- `nasa_records` - NASA-spezifische Daten (environmental_indicators, satellite_source)
- `un_press_records` - UN Press Daten (meeting_coverage, security_council, speakers)
- `wfp_records` - World Food Programme Daten (crisis_type, affected_population)
- `worldbank_records` - World Bank Daten (country, sector, project_id)

**Geospatial-Tabellen:**
- `geo_locations` - Geografische Orte mit Koordinaten
- `region_mapping` - Region-Mappings
- `geocoding_cache` - Geocoding-Cache für Performance

**Kontexträume:**
- `country_context_spaces` - Länder-Kontexträume mit Risiko-Scores
- `regional_enrichment` - Regionale Anreicherungsdaten
- `regional_predictions` - Regionale Vorhersagen

**Job-Management:**
- `crawl_jobs` - Crawling-Jobs und Status

---

## 🔍 Daten-Extraktion: Text, Bilder, Zahlen

### 1. Text-Extraktion (`backend/extractors.py`)

**Quellen-spezifische Extraktoren:**

#### `NASAExtractor`
- Extrahiert: Titel, Zusammenfassung, Umweltindikatoren
- Besonderheiten: Satelliten-Quellen, Umwelt-Metriken

#### `UNPressExtractor`
- Extrahiert: Pressemitteilungen, Meeting-Coverage
- Besonderheiten: Security Council, Sprecher-Informationen

#### `WFPExtractor`
- Extrahiert: Krisen-Typen, betroffene Bevölkerungsgruppen
- Besonderheiten: Humanitäre Daten, Bevölkerungszahlen

#### `WorldBankExtractor`
- Extrahiert: Projekte, Sektoren, Länder
- Besonderheiten: Finanzdaten, Projekt-IDs

**AI-unterstützte Extraktion:**
- `EnhancedExtractor` (OpenAI) - Falls verfügbar
- `FirecrawlAgent` - Erweiterte Web-Extraktion mit Firecrawl API

**Text-Verarbeitung:**
- BeautifulSoup für HTML-Parsing
- Regelbasierte Extraktion pro Quelle
- Fallback auf Playwright für dynamische Seiten

---

### 2. Zahlen-Extraktion (`backend/data_extraction.py`)

**`NumberExtractor`** - Extrahiert strukturierte numerische Daten:

#### Extrahiert:
- **Temperaturen** (`temperatures`): °C/°F mit automatischer Konvertierung
- **Niederschlag** (`precipitation`): mm/inches mit Konvertierung
- **Bevölkerungszahlen** (`population_numbers`): Millionen/Milliarden/Thousand
- **Finanzbeträge** (`financial_amounts`): USD mit Multiplikatoren
- **Prozentsätze** (`percentages`): 0-100%
- **Datumsangaben** (`dates`): Verschiedene Formate
- **Betroffene Personen** (`affected_people`): Spezifische Metrik
- **Finanzierungsbeträge** (`funding_amount`): Spezifische Metrik
- **Orte** (`locations`): Erwähnte Orte im Text

#### Pattern-basiert:
- Regex-Patterns für jeden Datentyp
- Kontextuelle Erkennung (z.B. "million", "billion")
- Einheiten-Konvertierung (Fahrenheit→Celsius, inches→mm)
- Deduplizierung der Ergebnisse

**Beispiel:**
```python
extractor = NumberExtractor()
result = extractor.extract_all(text)
# result.temperatures = [35.0, 28.5]
# result.precipitation = [50.0, 1200.0]
# result.population_numbers = [2000000, 5000000]
# result.financial_amounts = [500000000.0]
```

---

### 3. Bild-Extraktion (`backend/image_processing.py`)

**`ImageProcessor`** - Verarbeitet Bilder für Multi-Modal-Analyse:

#### Features:
- **Download** von Bildern von URLs
- **CLIP-Embeddings** für semantische Bild-Analyse
- **EXIF-Daten** Extraktion (GPS-Koordinaten)
- **Batch-Verarbeitung** für mehrere Bilder

#### CLIP-Integration:
- Verwendet OpenAI CLIP-Modell (ViT-B/32)
- GPU-Unterstützung falls verfügbar
- Normalisierte Embeddings für Vektorraum

**`GeospatialImageAnalyzer`**:
- Analysiert Bilder für Städte/Regionen
- Extrahiert geospatiale Features
- Kombiniert Bild-Embeddings mit Koordinaten

**Bild-Quellen:**
- Aus `record_images` Tabelle
- Aus Firecrawl-Extraktion
- Aus Research-Daten

---

## 🔄 Datenfluss-Pipeline

### Stufe 1: Daten-Sammlung
```
Web-Seiten (NASA, UN, WFP, World Bank)
    ↓
Compliance Agent (robots.txt Check)
    ↓
Fetch Agent (HTTP → Playwright Fallback)
    ↓
Extract Agent (Quellen-spezifische Extraktoren)
    ↓
Validate Agent (Schema-Prüfung)
    ↓
DatabaseManager (SQLite Speicherung)
```

### Stufe 2: Meta-Extraktion
```
Records aus Datenbank
    ↓
Text-Extraktion (Titel, Summary, Full Text)
    ↓
Zahlen-Extraktion (NumberExtractor)
    ↓
Bild-Extraktion (ImageProcessor)
    ↓
Geocoding (Koordinaten zuordnen)
```

### Stufe 3: Vektorraum-Erstellung
```
Text → OpenAI Embeddings
Bilder → CLIP Embeddings
Zahlen → Normalisierte Features
    ↓
Multi-Modal Vektorraum
    ↓
ChromaDB Speicherung
```

### Stufe 4: Kontextraum-Generierung
```
Multi-Modal Daten
    ↓
LLM-Analyse (OpenAI/Ollama)
    ↓
Risiko-Bewertung
    ↓
Country Context Spaces
```

### Stufe 5: Visualisierung
```
Country Context Spaces
    ↓
Interactive Risk Map (Folium)
    ↓
Web-App (Flask)
```

---

## 📦 Hauptkomponenten

### Backend-Module:

**Datenbank:**
- `database.py` - Zentrale Datenbank-Verwaltung
- `schemas.py` - Daten-Schemas (PageRecord, NASARecord, etc.)

**Extraktion:**
- `extractors.py` - Quellen-spezifische Extraktoren
- `data_extraction.py` - Zahlen-Extraktion
- `image_processing.py` - Bild-Verarbeitung
- `geocoding.py` - Geocoding-Service

**Orchestrierung:**
- `orchestrator.py` - Haupt-Orchestrator
- `real_time_extractor.py` - Echtzeit-Extraktion
- `multi_stage_processing.py` - Mehrstufige Pipeline

**AI/LLM:**
- `ai_agents.py` - AI-Agenten (Firecrawl, OpenAI)
- `ipcc_enrichment_agent.py` - IPCC-Daten-Anreicherung
- `llm_predictions.py` - LLM-basierte Vorhersagen

**Geospatial:**
- `geospatial_context_pipeline.py` - Geospatial-Kontext-Pipeline
- `interactive_risk_map.py` - Interaktive Risiko-Karte
- `risk_scoring.py` - Risiko-Bewertung

**Information Retrieval:**
- `information_retrieval_exercise/` - ChromaDB + TF-IDF Übung
- `multimodal_vector_space.py` - Multi-Modal Vektorraum

**Web-App:**
- `web_app.py` - Flask Web-App
- `world_map_visualization.py` - Karten-Visualisierung

---

## 🗄️ Datenbank-Schema Details

### Records-Tabelle:
```sql
CREATE TABLE records (
    id INTEGER PRIMARY KEY,
    url TEXT UNIQUE,
    source_domain TEXT,
    source_name TEXT,  -- 'NASA', 'UN Press', 'WFP', 'World Bank'
    fetched_at TIMESTAMP,
    title TEXT,
    summary TEXT,
    publish_date TEXT,
    region TEXT,
    content_type TEXT,
    language TEXT DEFAULT 'en',
    full_text TEXT,
    primary_country_code TEXT,
    primary_latitude REAL,
    primary_longitude REAL,
    geo_confidence REAL
);
```

### Country Context Spaces:
```sql
CREATE TABLE country_context_spaces (
    id INTEGER PRIMARY KEY,
    country_code TEXT UNIQUE,
    country_name TEXT,
    latitude REAL,
    longitude REAL,
    risk_score REAL,
    risk_level TEXT,  -- 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'MINIMAL'
    climate_indicators TEXT,  -- JSON array
    conflict_indicators TEXT,  -- JSON array
    future_risks TEXT,  -- JSON array
    context_summary TEXT,
    data_sources TEXT,  -- JSON array
    geojson TEXT,
    bbox TEXT,
    last_updated TIMESTAMP
);
```

---

## 🔧 Extraktions-Prozess im Detail

### 1. Web-Crawling:
```python
# Orchestrator startet Crawling
orchestrator = ScrapingOrchestrator()
results = await orchestrator.scrape_all_sources(urls)

# Für jede URL:
# 1. Compliance Check
can_scrape = compliance_agent.can_scrape(url)

# 2. Fetch (HTTP → Playwright Fallback)
fetch_result = fetcher.fetch_with_fallback(url)

# 3. Extract (Quellen-spezifisch)
extractor = extractor_factory.get_extractor(url)
record = extractor.extract(fetch_result)

# 4. Validate
validation = validator.validate(record)

# 5. Store
db.insert_record(record)
```

### 2. Meta-Extraktion:
```python
# Aus Records:
text = f"{record.title} {record.summary} {record.full_text}"

# Zahlen extrahieren
number_extractor = NumberExtractor()
numbers = number_extractor.extract_all(text)
# → temperatures, precipitation, population_numbers, financial_amounts

# Bilder verarbeiten
image_processor = ImageProcessor()
for image_url in record.image_urls:
    embedding = image_processor.process_image_url(image_url)
    # → CLIP Embedding

# Geocoding
geocoder = GeocodingService()
coordinates = geocoder.geocode(record.region)
```

### 3. Kontextraum-Erstellung:
```python
# Multi-Modal Daten kombinieren
context_data = {
    'text_chunks': [...],
    'numerical_data': {...},
    'image_embeddings': [...],
    'coordinates': (lat, lon)
}

# LLM-Analyse
llm_agent = IPCCEnrichmentAgent()
context_space = await llm_agent.create_context_space(
    country_code="IN",
    data=context_data
)

# Speichern
db.save_context_space(context_space)
```

---

## 📊 Information Retrieval

### ChromaDB (`information_retrieval_exercise/`):

**Setup:**
- ChromaDB für Vektor-Speicherung
- Sentence-Transformers für Embeddings
- TF-IDF als Vergleichs-Baseline

**Notebooks:**
- `01_data_exploration.ipynb` - Daten-Exploration
- `02_tfidf_analysis.ipynb` - TF-IDF Analyse
- `03_chromadb_analysis.ipynb` - ChromaDB Analyse

**Daten:**
- Tagesschau 2023 Datensatz
- Vorbereitet als CSV/JSON

---

## 🎯 Geospatial-Pipeline

### Workflow:
```python
# 1. Extrahiere Länder-Daten
pipeline = GeospatialContextPipeline()
result = await pipeline.extract_country_data("IN", "India")

# 2. Analysiere mit LLM
context_space = await pipeline._analyze_with_ollama(
    country_code="IN",
    text_data=all_text_data
)

# 3. Speichere Kontextraum
pipeline._save_context_space(context_space)

# 4. Erstelle Karte
map_creator = InteractiveRiskMap()
map_path = map_creator.create_map()
```

### Risiko-Levels:
- 🔴 **CRITICAL** - Dunkelrot (#8B0000)
- 🟠 **HIGH** - Orange-Rot (#FF4500)
- 🟡 **MEDIUM** - Gold (#FFD700)
- 🟢 **LOW** - Hellgrün (#90EE90)
- ⚪ **MINIMAL** - Grau (#E0E0E0)

---

## 🚀 Schnellstart

### 1. Datenbank initialisieren:
```bash
python backend/database.py
```

### 2. Pipeline ausführen:
```bash
python backend/run_pipeline.py
```

### 3. Geocoding durchführen:
```bash
python backend/geocode_existing_records.py
```

### 4. Geospatial-Pipeline:
```bash
python backend/run_geospatial_pipeline.py
```

### 5. Web-App starten:
```bash
python backend/web_app.py
# → http://localhost:5000
```

---

## 📈 Aktuelle Statistiken

### Datenbank:
- Records: Gespeichert in `records` Tabelle
- Geocodierte Records: Mit `primary_latitude/longitude`
- Country Contexts: In `country_context_spaces`
- Bilder: In `record_images` Tabelle

### Extraktion:
- **Text**: Aus HTML via BeautifulSoup + Regelbasierte Extraktion
- **Zahlen**: Regex-Patterns + Kontextuelle Erkennung
- **Bilder**: URL-Extraktion + CLIP-Embeddings

---

## 🔮 Geplante Erweiterungen (aus Plan)

### HPC-Integration:
- MPI-basierte verteilte Risiko-Berechnung
- OpenCV-basierte Bildverarbeitung
- Agenten-basierte Kontextraum-Generierung

### Erweiterte Features:
- Sitemap-Crawler für automatische URL-Discovery
- Web-UI für Monitoring
- API-Server (FastAPI)
- Scheduler für regelmäßige Runs
- Duplikat-Erkennung via Hashing

---

## 📚 Wichtige Dateien

### Dokumentation:
- `README.md` - Haupt-README
- `DATA_PROCESSING_GUIDE.md` - Datenverarbeitungs-Guide
- `GEOSPATIAL_PIPELINE_README.md` - Geospatial-Pipeline
- `SYSTEM_STATUS.md` - System-Status

### Code:
- `backend/database.py` - Datenbank-Verwaltung
- `backend/extractors.py` - Text-Extraktion
- `backend/data_extraction.py` - Zahlen-Extraktion
- `backend/image_processing.py` - Bild-Verarbeitung
- `backend/geospatial_context_pipeline.py` - Geospatial-Pipeline

---

## 🎓 Zusammenfassung

**Das Projekt ist ein Multi-Agent-System für:**
1. ✅ Web-Scraping von Klima- und Konflikt-Daten
2. ✅ Strukturierte Extraktion (Text, Zahlen, Bilder)
3. ✅ Geospatial-Analyse und Risiko-Bewertung
4. ✅ Multi-Modal Vektorraum (Text + Bilder + Zahlen)
5. ✅ Interaktive Visualisierung auf Karten

**Datenbank:**
- SQLite-basiert mit normalisierten Tabellen
- Unterstützt mehrere Datenquellen (NASA, UN, WFP, World Bank)
- Geospatial-Daten mit Koordinaten
- Kontexträume für Länder/Regionen

**Extraktion:**
- **Text**: Regelbasierte + AI-unterstützte Extraktion
- **Zahlen**: Pattern-basierte Extraktion mit Kontext-Erkennung
- **Bilder**: URL-Extraktion + CLIP-Embeddings

**Visualisierung:**
- Interaktive Karten mit Folium/Leaflet
- Risiko-Zonen mit Farbcodierung
- Web-App für Daten-Exploration

