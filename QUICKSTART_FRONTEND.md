# 🚀 Quick Start - Frontend & Testing

## 1. Pipeline testen (HTTP-only, ohne Playwright)

```bash
cd backend
python test_http_pipeline.py
```

Dies crawlt die drei Webseiten und speichert Daten in der Datenbank.

## 2. Geocoding durchführen

```bash
python geocode_existing_records.py
```

Fügt Koordinaten zu allen Records hinzu.

## 3. Frontend starten

```bash
python web_app.py
```

Öffnet Dashboard unter: **http://localhost:5000**

## 📊 Frontend-Features

### Tab 1: 🗺️ Karte
- Interaktive Weltkarte mit Leaflet
- Marker nach Risiko-Level gefärbt
- Klick auf Marker für Details
- Heatmap für Dichte-Visualisierung

### Tab 2: 📊 Records
- Liste aller extrahierten Records
- Risiko-Scores und Level
- Filter nach Quelle/Risiko-Level

### Tab 3: 🔮 Predictions
- Gefährdete Regionen identifiziert
- Risiko-Scores pro Region
- Indikatoren und Trends

### Tab 4: 📡 Datenquellen
- Welche Daten werden extrahiert
- Nützlichkeit für Predictions
- Beispiel-Felder

## 🔍 Welche Daten werden extrahiert?

### NASA Earth Observatory
- **Klima-Indikatoren**: Drought, Flood, Temperature, NDVI, etc.
- **Satelliten-Daten**: Landsat, MODIS, Sentinel
- **Regionale Umweltveränderungen**

### UN Press
- **Konflikt-Indikatoren**: Security Council, Meetings, Speakers
- **Politische Reaktionen** auf Klima-Events
- **Eskalations-Signale**

### World Bank
- **Wirtschaftliche Daten**: Projekte, Sektoren, Länder
- **Strukturelle Verwundbarkeit**
- **Finanzielle Unterstützung**

## 🎯 Für Predictions nutzbar

### Features für ML-Modelle:
1. **Klima-Features** (NASA) → Frühe Warnsignale
2. **Konflikt-Features** (UN) → Politische Reaktionen
3. **Wirtschaftliche Features** (World Bank) → Verwundbarkeit

### Prediction-Pipeline:
```
Daten crawlen → Features extrahieren → Model trainieren → Predictions
```

Siehe `DATA_ANALYSIS.md` für Details.

