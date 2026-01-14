# 🧪 Test-Anleitung - Extraktionen einsehen

## Schnelltest (5 Minuten)

### Schritt 1: Pipeline ausführen
```bash
docker-compose -f docker-compose.pipeline.yml up --build pipeline
```

**Was passiert:**
- Container wird gebaut
- Pipeline crawlt alle drei Webseiten (NASA, UN Press, World Bank)
- Daten werden in SQLite-Datenbank gespeichert
- Dauer: ~2-5 Minuten

### Schritt 2: Extraktionen anzeigen

**Option A: Web-Dashboard (Empfohlen)**
```bash
# In neuem Terminal
docker-compose -f docker-compose.pipeline.yml up dashboard

# Browser öffnen
open http://localhost:5000
```

**Option B: Test-Script**
```bash
docker-compose -f docker-compose.pipeline.yml run --rm pipeline python test_extraction.py
```

**Option C: Datenbank direkt**
```bash
docker-compose -f docker-compose.pipeline.yml exec pipeline sqlite3 /app/data/climate_conflict.db

# Dann SQL-Befehle:
SELECT COUNT(*) FROM records;
SELECT source_name, COUNT(*) FROM records GROUP BY source_name;
SELECT source_name, title, publish_date FROM records ORDER BY fetched_at DESC LIMIT 10;
```

## Was wird extrahiert?

### NASA Earth Observatory
- Titel, Zusammenfassung, Veröffentlichungsdatum
- Region, Topics
- Umweltindikatoren (NDVI, Temperatur, etc.)
- Satellitenquelle (Landsat, MODIS, etc.)

### UN Press
- Titel, Zusammenfassung, Veröffentlichungsdatum
- Region, Topics
- Security Council Meetings
- Sprecher

### World Bank
- Titel, Zusammenfassung, Veröffentlichungsdatum
- Land, Sektor
- Projekt-ID

## Datenstruktur prüfen

### Anzahl Records pro Quelle
```sql
SELECT source_name, COUNT(*) as count 
FROM records 
GROUP BY source_name;
```

### Neueste Records
```sql
SELECT 
    source_name,
    title,
    publish_date,
    region,
    fetched_at
FROM records
ORDER BY fetched_at DESC
LIMIT 20;
```

### Records mit Topics
```sql
SELECT 
    r.source_name,
    r.title,
    GROUP_CONCAT(rt.topic) as topics
FROM records r
LEFT JOIN record_topics rt ON r.id = rt.record_id
GROUP BY r.id
LIMIT 10;
```

### NASA-spezifische Daten
```sql
SELECT 
    r.title,
    r.region,
    n.satellite_source,
    n.environmental_indicators
FROM records r
JOIN nasa_records n ON r.id = n.record_id
LIMIT 10;
```

## Troubleshooting

### Keine Daten in Datenbank
```bash
# Prüfe ob Pipeline erfolgreich war
docker-compose -f docker-compose.pipeline.yml logs pipeline

# Prüfe Datenbank-Datei
ls -lh ./data/climate_conflict.db

# Pipeline erneut ausführen
docker-compose -f docker-compose.pipeline.yml up pipeline
```

### Dashboard zeigt keine Daten
```bash
# Prüfe ob Datenbank existiert
docker-compose -f docker-compose.pipeline.yml exec dashboard ls -la /app/data/

# Prüfe Dashboard-Logs
docker-compose -f docker-compose.pipeline.yml logs dashboard
```

### Container startet nicht
```bash
# Container neu bauen
docker-compose -f docker-compose.pipeline.yml build --no-cache

# Logs prüfen
docker-compose -f docker-compose.pipeline.yml logs
```

## Erwartete Ergebnisse

Nach erfolgreichem Crawl sollten Sie sehen:

- ✅ **NASA**: 2-10 Records
- ✅ **UN Press**: 20-50 Records  
- ✅ **World Bank**: 1-10 Records

**Gesamt:** ~30-70 Records in der Datenbank

## Nächste Schritte

1. ✅ Pipeline erfolgreich ausgeführt
2. ✅ Daten in Dashboard angezeigt
3. 📊 Daten analysieren (siehe `example_analysis.py`)
4. 🔄 Automatisiertes Crawling einrichten (Scheduler)
5. 📈 Erweiterte Analysen durchführen

## Hilfe

- **Docker-Probleme**: Siehe `DOCKER_README.md`
- **Pipeline-Details**: Siehe `PIPELINE_README.md`
- **Datenbank-Schema**: Siehe `database.py`

