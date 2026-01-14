# 🌍 Geospatial Intelligence Pipeline - Dokumentation

## Übersicht

Diese Pipeline erstellt **Kontexträume für jedes Land** durch:
1. **Firecrawl** - Web-Extraktion von Klima- und Konflikt-Daten
2. **Ollama** - LLM-Analyse für Kontextraum-Erstellung
3. **Geospatial-Analyse** - Risiko-Bewertung und Zonierung
4. **Interaktive Karte** - Visualisierung mit Risiko-Zonen und Farben
5. **Datenbank-Speicherung** - Persistente Speicherung aller Kontexträume

## 🚀 Schnellstart

### Voraussetzungen

1. **Firecrawl API Key** in `.env`:
```bash
FIRECRAWL_API_KEY=fc-your-key-here
```

2. **Ollama** installiert und laufend:
```bash
# Installiere Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Starte Ollama
ollama serve

# Installiere Modell
ollama pull llama3.2:latest
```

3. **Python-Abhängigkeiten**:
```bash
pip install folium requests aiohttp
```

### Pipeline ausführen

```bash
cd backend
python run_geospatial_pipeline.py
```

Dies führt automatisch aus:
1. ✅ Extraktion mit Firecrawl für alle kritischen Länder
2. ✅ Analyse mit Ollama für Kontextraum-Erstellung
3. ✅ Speicherung in Datenbank (`country_context_spaces` Tabelle)
4. ✅ Erstellung interaktiver Risiko-Karte

## 📊 Komponenten

### 1. Geospatial Context Pipeline (`geospatial_context_pipeline.py`)

**Funktionen:**
- Extrahiert Daten für jedes Land mit Firecrawl
- Analysiert Daten mit Ollama für Kontextraum-Erstellung
- Berechnet Risiko-Scores und Indikatoren
- Speichert Kontexträume in Datenbank

**Kontextraum-Struktur:**
```python
{
    "country_code": "IN",
    "country_name": "India",
    "risk_score": 0.75,
    "risk_level": "HIGH",
    "climate_indicators": ["drought", "flood", "heat_wave"],
    "conflict_indicators": ["displacement", "resource_conflict"],
    "future_risks": [
        {
            "type": "drought",
            "probability": 0.8,
            "timeframe": "short_term",
            "severity": "high"
        }
    ],
    "context_summary": "...",
    "data_sources": ["NASA", "UN", "World Bank"]
}
```

### 2. Interactive Risk Map (`interactive_risk_map.py`)

**Features:**
- 🗺️ **Interaktive Weltkarte** mit Folium/Leaflet
- 🎨 **Farbcodierte Risiko-Zonen** (CRITICAL, HIGH, MEDIUM, LOW, MINIMAL)
- 🔥 **Heatmap-Layer** für Risiko-Dichte
- 📍 **Marker** mit Popups für Details
- 🎯 **Risiko-Zonen** als Kreise basierend auf Risiko-Score
- 📊 **Legende** und Layer-Control

**Risiko-Farben:**
- 🔴 **CRITICAL** - Dunkelrot (#8B0000)
- 🟠 **HIGH** - Orange-Rot (#FF4500)
- 🟡 **MEDIUM** - Gold (#FFD700)
- 🟢 **LOW** - Hellgrün (#90EE90)
- ⚪ **MINIMAL** - Grau (#E0E0E0)

### 3. Datenbank-Schema

**Tabelle: `country_context_spaces`**
```sql
CREATE TABLE country_context_spaces (
    id INTEGER PRIMARY KEY,
    country_code TEXT UNIQUE NOT NULL,
    country_name TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    risk_score REAL DEFAULT 0.0,
    risk_level TEXT DEFAULT 'MINIMAL',
    climate_indicators TEXT,  -- JSON array
    conflict_indicators TEXT,  -- JSON array
    future_risks TEXT,  -- JSON array
    context_summary TEXT,
    data_sources TEXT,  -- JSON array
    geojson TEXT,  -- GeoJSON für Länder-Polygone
    bbox TEXT,  -- JSON bounding box
    last_updated TIMESTAMP,
    created_at TIMESTAMP
);
```

## 🔄 Workflow

### Schritt 1: Daten-Extraktion
```python
pipeline = GeospatialContextPipeline()
result = await pipeline.extract_country_data("IN", "India")
```

**Was passiert:**
1. Hole bestehende Records aus Datenbank
2. Firecrawl Search für zusätzliche Daten
3. Kombiniere alle Datenquellen

### Schritt 2: Ollama-Analyse
```python
context_space = await pipeline._analyze_with_ollama(
    country_code="IN",
    country_name="India",
    text_data=all_text_data
)
```

**Was passiert:**
1. Erstelle Analyse-Prompt mit kombinierten Daten
2. Rufe Ollama API auf
3. Parse JSON-Response mit Risiko-Daten
4. Erstelle strukturierten Kontextraum

### Schritt 3: Speicherung
```python
pipeline._save_context_space(context_space)
```

**Was passiert:**
1. Speichere Kontextraum in Datenbank
2. Update falls bereits vorhanden
3. Speichere GeoJSON und Bounding Box

### Schritt 4: Visualisierung
```python
map_creator = InteractiveRiskMap()
map_path = map_creator.create_map()
```

**Was passiert:**
1. Lade alle Kontexträume aus Datenbank
2. Erstelle interaktive Karte mit Folium
3. Füge Marker, Heatmap und Zonen hinzu
4. Speichere als HTML-Datei

## 📈 Nutzung

### Einzelnes Land analysieren

```python
from geospatial_context_pipeline import GeospatialContextPipeline

pipeline = GeospatialContextPipeline()
result = await pipeline.extract_country_data("IN", "India")
print(result['context_space'])
```

### Alle Länder verarbeiten

```python
pipeline = GeospatialContextPipeline()
context_spaces = await pipeline.process_all_countries()
print(f"Erstellt: {len(context_spaces)} Kontexträume")
```

### Karte erstellen

```python
from interactive_risk_map import InteractiveRiskMap

map_creator = InteractiveRiskMap()
map_path = map_creator.create_map("backend/data/my_map.html")
print(f"Karte gespeichert: {map_path}")
```

## 🎯 API-Endpunkte (für Web-App)

### Kontexträume abrufen

```python
@app.route('/api/context-spaces')
def get_context_spaces():
    """Hole alle Kontexträume"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM country_context_spaces")
        return jsonify([dict(row) for row in cursor.fetchall()])
```

### Kontextraum für Land

```python
@app.route('/api/context-space/<country_code>')
def get_context_space(country_code):
    """Hole Kontextraum für ein Land"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM country_context_spaces WHERE country_code = ?",
            (country_code,)
        )
        row = cursor.fetchone()
        return jsonify(dict(row) if row else {})
```

## 🔧 Konfiguration

### Ollama-Einstellungen

In `config.py`:
```python
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:latest"
```

### Firecrawl-Einstellungen

In `.env`:
```bash
FIRECRAWL_API_KEY=fc-your-key-here
```

### Kritische Länder

Die Liste der kritischen Länder kann in `geospatial_context_pipeline.py` angepasst werden:
```python
self.countries = [
    {"code": "IN", "name": "India"},
    {"code": "BD", "name": "Bangladesh"},
    # ... mehr Länder
]
```

## 📊 Output

### Datenbank
- **Tabelle**: `country_context_spaces`
- **Location**: `data/climate_conflict.db`

### Interaktive Karte
- **Datei**: `backend/data/interactive_risk_map.html`
- **Format**: HTML mit Folium/Leaflet
- **Features**: Marker, Heatmap, Zonen, Legende

## 🐛 Fehlerbehebung

### Ollama nicht erreichbar
```bash
# Prüfe ob Ollama läuft
curl http://localhost:11434/api/tags

# Starte Ollama
ollama serve
```

### Firecrawl API Fehler
```bash
# Prüfe API Key
echo $FIRECRAWL_API_KEY

# Prüfe Credits
# Siehe Firecrawl Dashboard
```

### Keine Kontexträume gefunden
```bash
# Führe Pipeline aus
python run_geospatial_pipeline.py

# Prüfe Datenbank
sqlite3 data/climate_conflict.db "SELECT COUNT(*) FROM country_context_spaces"
```

## 🚀 Erweiterungen

### GeoJSON-Polygone hinzufügen

Für echte Länder-Polygone:
```python
# Nutze pycountry oder geopy für Länder-Polygone
import pycountry
# ... GeoJSON für Länder-Polygone generieren
```

### Erweiterte Risiko-Berechnung

```python
# Nutze Machine Learning für Risiko-Vorhersage
from sklearn.ensemble import RandomForestClassifier
# ... Trainiere Modell auf historischen Daten
```

### Real-time Updates

```python
# Nutze WebSockets für Live-Updates
from flask_socketio import SocketIO
# ... Sende Updates an Frontend
```

## 📝 Beispiel-Output

### Kontextraum (JSON)
```json
{
  "country_code": "IN",
  "country_name": "India",
  "risk_score": 0.75,
  "risk_level": "HIGH",
  "climate_indicators": ["drought", "flood", "heat_wave"],
  "conflict_indicators": ["displacement"],
  "future_risks": [
    {
      "type": "drought",
      "probability": 0.8,
      "timeframe": "short_term",
      "severity": "high",
      "description": "Erhöhtes Dürre-Risiko durch Klimawandel"
    }
  ],
  "context_summary": "India faces significant climate risks...",
  "data_sources": ["NASA", "UN", "World Bank"]
}
```

### Interaktive Karte
- HTML-Datei mit vollständiger interaktiver Karte
- Marker für jedes Land mit Risiko-Level
- Heatmap für Risiko-Dichte
- Zonen für Risiko-Bereiche
- Popups mit Details

## 🎓 Best Practices

1. **Rate Limiting**: Respektiere Firecrawl und Ollama Limits
2. **Caching**: Nutze Geocoding-Cache für Performance
3. **Error Handling**: Behandle Fehler gracefully
4. **Monitoring**: Tracke API-Kosten und Credits
5. **Updates**: Aktualisiere Kontexträume regelmäßig

## 📚 Weitere Ressourcen

- [Firecrawl Docs](https://docs.firecrawl.dev)
- [Ollama Docs](https://ollama.ai/docs)
- [Folium Docs](https://python-visualization.github.io/folium/)
- [Geospatial Analysis Guide](./GEOSPATIAL_ANALYSIS.md)

