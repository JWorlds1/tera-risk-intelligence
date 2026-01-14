# 🚀 START HERE - Climate Conflict Intelligence System

## ✅ Was wurde erstellt

### 1. **Datenbank-System** ✅
- SQLite-Datenbank mit geospatial Tabellen
- Speichert alle extrahierten Daten
- Koordinaten & Länder-Codes für Visualisierung

### 2. **Crawling-Pipeline** ✅
- Extrahiert Daten von 3 Webseiten:
  - 🌍 **NASA Earth Observatory** - Klima-Daten
  - 🌐 **UN Press** - Konflikt-Daten
  - 💰 **World Bank** - Wirtschaftliche Daten

### 3. **Geocoding-System** ✅
- Fügt Koordinaten zu Records hinzu
- Länder-Codes für Filterung
- Region-Mapping für Standardisierung

### 4. **Risiko-Scoring** ✅
- Berechnet Climate Risk, Conflict Risk, Urgency
- Klassifiziert nach CRITICAL/HIGH/MEDIUM/LOW/MINIMAL

### 5. **Web-Frontend** ✅
- Interaktive Weltkarte
- Records-Liste mit Risiko-Scores
- Predictions für gefährdete Regionen
- Datenquellen-Übersicht

## 🚀 Schnellstart

### Option 1: Frontend starten (mit Demo-Daten)

```bash
cd backend
python web_app.py
```

Öffnen Sie: **http://localhost:5000**

### Option 2: Vollständige Pipeline

```bash
cd backend

# 1. Crawling
python test_http_pipeline.py

# 2. Geocoding
python geocode_existing_records.py

# 3. Frontend
python web_app.py
```

## 📊 Welche Daten werden extrahiert?

### NASA Earth Observatory
- **Environmental Indicators**: Drought, Flood, Temperature, NDVI, etc.
- **Satellite Sources**: Landsat, MODIS, Sentinel
- **Regionale Umweltveränderungen**

### UN Press
- **Konflikt-Indikatoren**: Security Council, Meetings, Speakers
- **Politische Reaktionen** auf Klima-Events
- **Eskalations-Signale**

### World Bank
- **Wirtschaftliche Daten**: Projekte, Sektoren, Länder
- **Strukturelle Verwundbarkeit**
- **Finanzielle Unterstützung**

## 🔮 Wie nutzen wir diese für Predictions?

### Features für ML-Modelle:

1. **Klima-Features** (NASA)
   - Drought frequency → Frühe Warnsignale
   - Temperature trends → Langfristige Risiken
   - Satellite data → Objektive Messungen

2. **Konflikt-Features** (UN Press)
   - Security Council mentions → Internationale Aufmerksamkeit
   - Meeting frequency → Eskalation
   - Conflict keywords → Politische Reaktionen

3. **Wirtschaftliche Features** (World Bank)
   - Project count → Strukturelle Unterstützung
   - Sector diversity → Verwundbarkeit
   - Funding levels → Finanzielle Kapazität

### Prediction-Pipeline:
```
Daten crawlen → Features extrahieren → Model trainieren → Predictions
```

Siehe `DATA_ANALYSIS.md` für Details.

## 📁 Wichtige Dateien

- `web_app.py` - Web-Frontend
- `test_http_pipeline.py` - Pipeline Test
- `geocode_existing_records.py` - Geocoding
- `risk_scoring.py` - Risiko-Berechnung
- `database.py` - Datenbank-Manager
- `DATA_ANALYSIS.md` - Datenanalyse & Prediction-Strategie

## 🎯 Nächste Schritte

1. ✅ **System erstellt** - Alle Komponenten vorhanden
2. ⏳ **Daten crawlen** - Pipeline testen
3. ⏳ **Geocoding** - Koordinaten hinzufügen
4. ⏳ **Frontend nutzen** - Daten visualisieren
5. ⏳ **Predictions** - ML-Modelle implementieren

## 📚 Dokumentation

- `DATA_ANALYSIS.md` - Welche Daten & wie für Predictions
- `FRONTEND_SUMMARY.md` - Frontend-Übersicht
- `GEOSPATIAL_STRATEGY.md` - Geospatial Strategie
- `QUICKSTART_FRONTEND.md` - Quick Start Guide

