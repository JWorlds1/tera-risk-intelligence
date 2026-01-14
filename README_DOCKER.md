# 🐳 Docker Quick Start

## Für Studenten & GitHub/GitLab

### Schnellstart (3 Schritte)

```bash
# 1. Repository klonen
git clone <repository-url>
cd Geospatial_Intelligence

# 2. Pipeline ausführen
docker-compose -f docker-compose.pipeline.yml up --build pipeline

# 3. Dashboard öffnen (in neuem Terminal)
docker-compose -f docker-compose.pipeline.yml up dashboard
# Browser: http://localhost:5000
```

### Oder mit Quick-Start Script

```bash
chmod +x quickstart.sh
./quickstart.sh
```

## Was wird extrahiert?

Die Pipeline extrahiert Daten von:
- 🌍 **NASA Earth Observatory** - Umweltstress & Klimaveränderungen
- 🌐 **UN Press** - Politische & sicherheitspolitische Reaktionen  
- 💰 **World Bank** - Wirtschaftliche & strukturelle Verwundbarkeit

## Daten anzeigen

### Option 1: Web-Dashboard
```bash
docker-compose -f docker-compose.pipeline.yml up dashboard
# Öffne: http://localhost:5000
```

### Option 2: Test-Script
```bash
docker-compose -f docker-compose.pipeline.yml run --rm pipeline python test_extraction.py
```

### Option 3: Datenbank direkt
```bash
docker-compose -f docker-compose.pipeline.yml exec pipeline sqlite3 /app/data/climate_conflict.db
```

## Vollständige Dokumentation

Siehe [DOCKER_README.md](DOCKER_README.md) für detaillierte Anleitung.

