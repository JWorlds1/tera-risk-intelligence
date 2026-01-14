# 🚀 Automatisierte Crawling-Pipeline

## Übersicht

Die Pipeline ermöglicht automatisiertes Crawling der drei Hauptwebseiten:
- **NASA Earth Observatory** (earthobservatory.nasa.gov)
- **UN Press** (press.un.org)
- **World Bank** (worldbank.org)

Alle extrahierten Daten werden in einer SQLite-Datenbank gespeichert und können für Analysen verwendet werden.

## 🏗️ Architektur

```
┌─────────────────────────────────────────────────────────┐
│              Pipeline Scheduler                          │
│  (Täglich 02:00, alle 6 Stunden, etc.)                  │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│           CrawlingPipeline                               │
│  - Erstellt Crawl-Jobs                                   │
│  - Koordiniert Orchestrator                             │
│  - Speichert in Datenbank                               │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│         ScrapingOrchestrator                             │
│  - Compliance Agent (robots.txt, Rate Limiting)         │
│  - Fetch Agent (HTTP Requests)                           │
│  - Extract Agent (Content Parsing)                      │
│  - Validate Agent (Data Validation)                    │
│  - Storage Agent (Files + Database)                      │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│           DatabaseManager                                │
│  - SQLite Datenbank                                      │
│  - Normalisierte Tabellen                                │
│  - Job-Tracking                                          │
└──────────────────────────────────────────────────────────┘
```

## 📊 Datenbank-Schema

### Haupttabellen

1. **records** - Alle extrahierten Records
   - `id`, `url`, `source_domain`, `source_name`
   - `title`, `summary`, `publish_date`, `region`
   - `content_type`, `language`, `full_text`
   - `fetched_at`, `created_at`, `updated_at`

2. **record_topics** - Topics/Tags pro Record
3. **record_links** - Links pro Record
4. **record_images** - Bilder pro Record

### Quellenspezifische Tabellen

- **nasa_records** - NASA-spezifische Daten (environmental_indicators, satellite_source)
- **un_press_records** - UN-spezifische Daten (meeting_coverage, security_council, speakers)
- **wfp_records** - WFP-spezifische Daten (crisis_type, affected_population)
- **worldbank_records** - World Bank-spezifische Daten (country, sector, project_id)

### Job-Tracking

- **crawl_jobs** - Tracking aller Crawl-Jobs mit Status, Statistiken, Fehlern

## 🚀 Verwendung

### 1. Prototyp ausführen (einmalig)

```bash
cd backend
python run_pipeline.py
```

Dies führt einen vollständigen Crawl für alle drei Quellen durch und zeigt:
- Aktuelle Datenbank-Statistiken
- Crawling-Ergebnisse
- Neue Records
- Aktualisierte Records

### 2. Automatisiertes Crawling starten

```bash
cd backend
python pipeline.py --scheduled
```

Dies startet den Scheduler mit folgenden Einstellungen:
- **Täglich um 02:00 Uhr**: Vollständiger Crawl aller Quellen
- **Alle 6 Stunden**: Inkrementeller Crawl

### 3. Manueller Crawl für spezifische Quellen

```python
from config import Config
from pipeline import CrawlingPipeline
import asyncio

config = Config()
pipeline = CrawlingPipeline(config)

# Nur NASA und UN Press crawlen
results = asyncio.run(pipeline.run_full_crawl(['NASA', 'UN Press']))
```

### 4. Datenbank abfragen

```bash
# SQLite Shell öffnen
sqlite3 ./data/climate_conflict.db

# Alle Records anzeigen
SELECT source_name, COUNT(*) FROM records GROUP BY source_name;

# Neueste Records
SELECT source_name, title, publish_date, region 
FROM records 
ORDER BY fetched_at DESC 
LIMIT 10;

# Records mit Topics
SELECT r.title, GROUP_CONCAT(rt.topic) as topics
FROM records r
LEFT JOIN record_topics rt ON r.id = rt.record_id
GROUP BY r.id
LIMIT 10;
```

## 📈 Monitoring

### Datenbank-Statistiken abrufen

```python
from database import DatabaseManager

db = DatabaseManager()
stats = db.get_statistics()

print(f"Total Records: {stats['total_records']}")
print(f"Records by Source: {stats['records_by_source']}")
print(f"Records last 24h: {stats['records_last_24h']}")
```

### Crawl-Jobs prüfen

```python
from database import DatabaseManager

db = DatabaseManager()

# Alle Jobs
jobs = db.get_crawl_jobs()

# Nur fehlgeschlagene Jobs
failed_jobs = db.get_crawl_jobs(status='failed')

# Jobs für eine bestimmte Quelle
nasa_jobs = db.get_crawl_jobs(source_name='NASA')
```

## ⚙️ Konfiguration

Die Pipeline verwendet die Konfiguration aus `config.py`:

- **RATE_LIMIT**: Rate Limiting (Standard: 1.0 req/s)
- **MAX_CONCURRENT**: Maximale parallele Requests (Standard: 3)
- **STORAGE_DIR**: Verzeichnis für Dateien (Standard: ./data)
- **HTTP_TIMEOUT**: Timeout für HTTP Requests (Standard: 20s)

## 🔄 Scheduler-Anpassung

Die Scheduler-Einstellungen können in `pipeline.py` angepasst werden:

```python
# Täglich um 03:00 Uhr
scheduler.schedule_daily_crawl("03:00")

# Stündlich um Minute 15
scheduler.schedule_hourly_crawl(15)

# Alle 4 Stunden
scheduler.schedule_interval_crawl(4)
```

## 📁 Dateistruktur

```
backend/
├── database.py          # Datenbank-Manager
├── pipeline.py         # Pipeline & Scheduler
├── orchestrator.py     # Orchestrator (aktualisiert)
├── run_pipeline.py      # Prototyp-Script
└── data/
    └── climate_conflict.db  # SQLite Datenbank
```

## ✅ Status

- ✅ Datenbank-Schema implementiert
- ✅ Database Manager mit CRUD-Operationen
- ✅ Pipeline-Scheduler für automatisiertes Crawling
- ✅ Orchestrator mit Datenbank-Integration
- ✅ Prototyp-Script für einmalige Ausführung
- ✅ Job-Tracking für Monitoring

## 🎯 Nächste Schritte

1. **Testing**: Pipeline mit echten Daten testen
2. **Monitoring**: Dashboard für Pipeline-Status
3. **Alerting**: Benachrichtigungen bei Fehlern
4. **Optimierung**: Performance-Tuning für große Datenmengen
5. **Backup**: Automatische Backups der Datenbank

## 🐛 Troubleshooting

### Datenbank wird nicht erstellt
- Prüfe Schreibrechte im `data/` Verzeichnis
- Prüfe ob SQLite installiert ist

### Pipeline stoppt nicht
- `Ctrl+C` zum Stoppen
- Prüfe laufende Prozesse: `ps aux | grep python`

### Keine Records in Datenbank
- Prüfe Logs für Fehler
- Prüfe ob URLs erreichbar sind
- Prüfe Rate Limiting Einstellungen

