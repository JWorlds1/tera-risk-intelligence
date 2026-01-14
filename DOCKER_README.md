# 🐳 Docker Setup für Climate Conflict Pipeline

## Übersicht

Dieses Docker-Setup ermöglicht es, die gesamte Pipeline in einem Container auszuführen und mit Studenten zu teilen oder auf GitHub/GitLab zu pushen.

## 🚀 Schnellstart

### 1. Repository klonen/erhalten

```bash
git clone <repository-url>
cd Geospatial_Intelligence
```

### 2. Docker Container bauen und starten

```bash
# Pipeline einmalig ausführen
docker-compose -f docker-compose.pipeline.yml up --build pipeline

# Oder im Hintergrund
docker-compose -f docker-compose.pipeline.yml up -d pipeline
```

### 3. Dashboard anzeigen

```bash
# Dashboard starten
docker-compose -f docker-compose.pipeline.yml up dashboard

# Dashboard öffnen im Browser
# http://localhost:5000
```

### 4. Extraktionen testen

```bash
# Test-Script ausführen
docker-compose -f docker-compose.pipeline.yml run --rm pipeline python test_extraction.py
```

## 📦 Docker Services

### Pipeline Service
Führt einmalig einen vollständigen Crawl durch:
```bash
docker-compose -f docker-compose.pipeline.yml up pipeline
```

### Scheduler Service
Führt automatisiertes Crawling durch (täglich, alle 6 Stunden):
```bash
docker-compose -f docker-compose.pipeline.yml up scheduler
```

### Dashboard Service
Web-Dashboard zum Anzeigen der Daten:
```bash
docker-compose -f docker-compose.pipeline.yml up dashboard
```

## 🔧 Manuelle Docker-Befehle

### Container bauen
```bash
docker build -t climate-pipeline .
```

### Container ausführen
```bash
# Pipeline ausführen
docker run --rm -v $(pwd)/data:/app/data climate-pipeline python run_pipeline.py

# Test ausführen
docker run --rm -v $(pwd)/data:/app/data climate-pipeline python test_extraction.py

# Dashboard starten
docker run --rm -p 5000:5000 -v $(pwd)/data:/app/data climate-pipeline python dashboard_viewer.py
```

### In Container einloggen
```bash
docker-compose -f docker-compose.pipeline.yml exec pipeline bash
```

## 📊 Daten anzeigen

### 1. Web-Dashboard
```bash
# Dashboard starten
docker-compose -f docker-compose.pipeline.yml up dashboard

# Im Browser öffnen
open http://localhost:5000
```

### 2. Test-Script
```bash
docker-compose -f docker-compose.pipeline.yml run --rm pipeline python test_extraction.py
```

### 3. Datenbank direkt abfragen
```bash
# SQLite Shell im Container
docker-compose -f docker-compose.pipeline.yml exec pipeline sqlite3 /app/data/climate_conflict.db

# Oder lokal (wenn SQLite installiert)
sqlite3 ./data/climate_conflict.db
```

### 4. Datenbank-Statistiken
```sql
-- Gesamt Records
SELECT COUNT(*) FROM records;

-- Records pro Quelle
SELECT source_name, COUNT(*) FROM records GROUP BY source_name;

-- Neueste Records
SELECT source_name, title, publish_date, region 
FROM records 
ORDER BY fetched_at DESC 
LIMIT 10;
```

## 📁 Daten-Persistenz

Alle Daten werden im `./data` Verzeichnis gespeichert:
- `climate_conflict.db` - SQLite Datenbank
- `json/` - JSON-Dateien
- `csv/` - CSV-Dateien
- `parquet/` - Parquet-Dateien

Dieses Verzeichnis wird als Volume gemountet, sodass Daten auch nach Container-Stopp erhalten bleiben.

## 🧪 Testing

### Vollständiger Test-Workflow

```bash
# 1. Container bauen
docker-compose -f docker-compose.pipeline.yml build

# 2. Pipeline ausführen (Extraktion)
docker-compose -f docker-compose.pipeline.yml up pipeline

# 3. Extraktionen testen
docker-compose -f docker-compose.pipeline.yml run --rm pipeline python test_extraction.py

# 4. Dashboard starten
docker-compose -f docker-compose.pipeline.yml up dashboard
```

### Automatischer Test (für CI/CD)

```bash
# Setze AUTO_RUN Flag
docker run --rm \
  -e AUTO_RUN=true \
  -v $(pwd)/data:/app/data \
  climate-pipeline python test_extraction.py
```

## 🔍 Debugging

### Logs anzeigen
```bash
# Alle Logs
docker-compose -f docker-compose.pipeline.yml logs

# Pipeline Logs
docker-compose -f docker-compose.pipeline.yml logs pipeline

# Dashboard Logs
docker-compose -f docker-compose.pipeline.yml logs dashboard
```

### Container-Logs folgen
```bash
docker-compose -f docker-compose.pipeline.yml logs -f pipeline
```

### In Container einloggen
```bash
docker-compose -f docker-compose.pipeline.yml exec pipeline bash

# Dann im Container:
python test_extraction.py
python run_pipeline.py
sqlite3 /app/data/climate_conflict.db
```

## 📤 Für GitHub/GitLab vorbereiten

### 1. .gitignore prüfen
Stelle sicher, dass folgende Dateien ignoriert werden:
```
data/*.db
data/*.json
data/*.csv
data/*.parquet
__pycache__/
*.pyc
.env
```

### 2. README.md aktualisieren
Füge Docker-Anleitung hinzu (siehe DOCKER_README.md)

### 3. Repository pushen
```bash
git add .
git commit -m "Add Docker setup for pipeline"
git push origin main
```

### 4. Studenten können dann:
```bash
git clone <repository-url>
cd Geospatial_Intelligence
docker-compose -f docker-compose.pipeline.yml up --build pipeline
```

## 🎓 Für Studenten - Einfache Anleitung

### Schritt 1: Repository klonen
```bash
git clone <repository-url>
cd Geospatial_Intelligence
```

### Schritt 2: Docker installieren
- **macOS**: [Docker Desktop](https://www.docker.com/products/docker-desktop)
- **Windows**: [Docker Desktop](https://www.docker.com/products/docker-desktop)
- **Linux**: `sudo apt-get install docker.io docker-compose`

### Schritt 3: Pipeline ausführen
```bash
docker-compose -f docker-compose.pipeline.yml up --build pipeline
```

### Schritt 4: Daten anzeigen
```bash
# Option 1: Web-Dashboard
docker-compose -f docker-compose.pipeline.yml up dashboard
# Dann Browser öffnen: http://localhost:5000

# Option 2: Test-Script
docker-compose -f docker-compose.pipeline.yml run --rm pipeline python test_extraction.py
```

## 🐛 Troubleshooting

### Container startet nicht
```bash
# Logs prüfen
docker-compose -f docker-compose.pipeline.yml logs

# Container neu bauen
docker-compose -f docker-compose.pipeline.yml build --no-cache
```

### Datenbank nicht gefunden
```bash
# Prüfe ob data-Verzeichnis existiert
ls -la ./data

# Erstelle falls nicht vorhanden
mkdir -p ./data
```

### Port bereits belegt
```bash
# Ändere Port in docker-compose.pipeline.yml
ports:
  - "5001:5000"  # Statt 5000:5000
```

### Permission-Denied Fehler
```bash
# Prüfe Schreibrechte
chmod -R 755 ./data

# Oder ändere Owner
sudo chown -R $USER:$USER ./data
```

## 📝 Beispiel-Workflow

```bash
# 1. Projekt klonen
git clone <repo>
cd Geospatial_Intelligence

# 2. Pipeline ausführen
docker-compose -f docker-compose.pipeline.yml up pipeline

# 3. Warten bis fertig (oder im Hintergrund: -d)

# 4. Daten testen
docker-compose -f docker-compose.pipeline.yml run --rm pipeline python test_extraction.py

# 5. Dashboard starten
docker-compose -f docker-compose.pipeline.yml up dashboard

# 6. Browser öffnen: http://localhost:5000
```

## ✅ Checkliste für Deployment

- [ ] Docker installiert
- [ ] Repository geklont
- [ ] `docker-compose.pipeline.yml` vorhanden
- [ ] `Dockerfile` vorhanden
- [ ] `.dockerignore` vorhanden
- [ ] `data/` Verzeichnis erstellt
- [ ] Pipeline erfolgreich ausgeführt
- [ ] Dashboard läuft
- [ ] Daten sichtbar

## 🎉 Fertig!

Das System ist jetzt bereit für:
- ✅ Teilen mit Studenten
- ✅ Deployment auf GitHub/GitLab
- ✅ Automatisiertes Testing
- ✅ Einfache Reproduzierbarkeit

