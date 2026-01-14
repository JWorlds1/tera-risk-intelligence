# 🌍 Geospatial Intelligence - Strategie & Implementierung

## 📊 Aktuelle Situation

### Was funktioniert:
- ✅ **Text-basierte Region-Extraktion** ("East Africa", "Middle East")
- ✅ **Datenbank-Schema** für Records
- ✅ **Pipeline** für automatisiertes Crawling

### Was fehlt für Geospatial Visualisierung:
- ❌ **Koordinaten** (lat/lon) für Mapping
- ❌ **Länder-Codes** (ISO 3166) für Filterung
- ❌ **GeoJSON** für Region-Polygone
- ❌ **Bounding Boxes** für Spatial Queries

## 🎯 Strategie

### Phase 1: Geocoding-Integration (JETZT)

**1. Geocoding-Service** (`geocoding.py`) ✅ ERSTELLT
- Nominatim API (kostenlos, OpenStreetMap)
- Caching für Performance
- Rate Limiting (1 req/s)
- Region-Mapping für Standardisierung

**2. Datenbank-Erweiterung** ✅ ERSTELLT
- `geo_locations` Tabelle
- `region_mapping` Tabelle  
- `geocoding_cache` Tabelle
- Erweiterte `records` Tabelle mit Koordinaten

**3. Pipeline-Integration** ⏳ NÄCHSTER SCHRITT
- Geocoding nach Extraktion
- Batch-Processing
- Retry-Logic

### Phase 2: Crawling-Strategie

#### A) Während Extraktion:
1. **Region-Text extrahieren** (bereits vorhanden)
2. **Länder-Namen erkennen** (NER - Named Entity Recognition)
3. **Koordinaten aus Text extrahieren** (falls vorhanden)

#### B) Nach Extraktion (Post-Processing):
1. **Geocoding** für alle Records ohne Koordinaten
2. **Region-Normalisierung** (z.B. "East Africa" → Länder-Codes)
3. **Confidence-Scoring** für Geocoding-Qualität

### Phase 3: Speicherungs-Strategie

#### Datenbank-Struktur:
```
records (Haupttabelle)
  ├── primary_country_code (ISO 3166-1 alpha-2)
  ├── primary_latitude
  ├── primary_longitude
  └── geo_confidence

geo_locations (Mehrere Locations pro Record)
  ├── location_type (country/region/city/point)
  ├── country_code
  ├── latitude/longitude
  ├── geojson (für Polygone)
  └── bbox (Bounding Box)
```

#### Warum diese Struktur?
- **Flexibilität**: Ein Record kann mehrere Locations haben
- **Präzision**: Verschiedene Location-Types (Region vs. Stadt)
- **Performance**: Indizes auf Koordinaten für Spatial Queries
- **Erweiterbarkeit**: GeoJSON für komplexe Polygone

## 🔄 Crawling-Strategie

### Option A: Synchron (Einfach)
```
1. Crawl → Extract → Validate → Store
2. Geocode alle neuen Records
3. Update records mit Koordinaten
```

**Vorteile:**
- Einfach zu implementieren
- Sofortige Koordinaten verfügbar

**Nachteile:**
- Langsamer (1 req/s für Geocoding)
- Blockiert Pipeline

### Option B: Asynchron (Empfohlen)
```
1. Crawl → Extract → Validate → Store (ohne Geocoding)
2. Separater Geocoding-Job läuft parallel
3. Update records asynchron
```

**Vorteile:**
- Pipeline bleibt schnell
- Geocoding kann retry machen
- Skalierbar

**Nachteile:**
- Komplexer
- Records haben initial keine Koordinaten

### Option C: Hybrid (Beste Lösung)
```
1. Crawl → Extract → Validate → Store
2. Quick Geocoding für bekannte Regionen (Cache)
3. Batch-Geocoding für Rest (asynchron)
```

**Vorteile:**
- Schnell für bekannte Regionen
- Vollständig für alle Records
- Skalierbar

## 📈 Visualisierungs-Möglichkeiten

### Mit geospatial Daten:

1. **Heatmaps**
   - Nach Region/Land
   - Nach Konflikt-Risiko
   - Nach Zeit

2. **Clustering**
   - Nach geografischer Nähe
   - Nach Thema

3. **Timeline-Maps**
   - Veränderung über Zeit
   - Animation

4. **Filter**
   - Nach Länder-Codes
   - Nach Bounding Box
   - Nach Region

5. **GeoJSON Overlays**
   - Region-Polygone
   - Custom Shapes

## 🚀 Implementierungs-Plan

### Schritt 1: Geocoding-Service testen ✅
```bash
python backend/geocoding.py
```

### Schritt 2: Datenbank-Migration
```python
# Database wird automatisch erweitert beim ersten Start
# Keine manuelle Migration nötig
```

### Schritt 3: Pipeline erweitern
```python
# In pipeline.py:
# - Geocoding nach Extraktion
# - Batch-Processing
# - Update records
```

### Schritt 4: Testen
```bash
# 1. Pipeline ausführen
python backend/run_pipeline.py

# 2. Geocoding durchführen
python backend/geocode_records.py

# 3. Daten prüfen
python backend/test_extraction.py
```

## 📊 Beispiel-Datenfluss

### Vorher (aktuell):
```json
{
  "title": "Drought in East Africa",
  "region": "East Africa",
  "country": null
}
```

### Nachher (mit Geocoding):
```json
{
  "title": "Drought in East Africa",
  "region": "East Africa",
  "country": null,
  "primary_country_code": "KE",
  "primary_latitude": 1.0,
  "primary_longitude": 38.0,
  "geo_confidence": 0.9,
  "geo_locations": [
    {
      "type": "region",
      "name": "East Africa",
      "country_codes": ["KE", "ET", "SO", "UG", "TZ"],
      "latitude": 1.0,
      "longitude": 38.0
    }
  ]
}
```

## ✅ Nächste Schritte

1. ✅ **Geocoding-Service** erstellt
2. ✅ **Datenbank erweitert**
3. ⏳ **Pipeline integrieren** (nächster Schritt)
4. ⏳ **Testen mit echten Daten**
5. ⏳ **Visualisierung implementieren**

## 🎯 Empfehlung

**Für schnelle Ergebnisse:**
- Option C (Hybrid) implementieren
- Geocoding für bekannte Regionen sofort
- Batch-Geocoding für Rest asynchron

**Für Produktion:**
- Separate Geocoding-Service
- Retry-Logic für fehlgeschlagene Geocodings
- Monitoring für Geocoding-Qualität

