# 🌍 Geospatial Intelligence - Datenbank-Strategie

## Aktuelle Situation

### Was wird aktuell extrahiert:
- ✅ **Region** (Text): "East Africa", "Middle East", etc.
- ✅ **Country** (Text): "Syria", "Central African Republic" (nur World Bank)
- ❌ **Keine Koordinaten** (lat/lon)
- ❌ **Keine Länder-Codes** (ISO 3166)
- ❌ **Keine GeoJSON** Polygone
- ❌ **Keine Bounding Boxes**

### Problem für Geospatial Visualisierung:
- Region-Namen sind nicht standardisiert
- Keine präzisen Koordinaten für Mapping
- Keine Möglichkeit für Heatmaps oder Clustering
- Schwierig für interaktive Karten

## 🎯 Anforderungen für Geospatial Intelligence

### 1. Geografische Daten
- **Koordinaten** (lat/lon) für jeden Record
- **Länder-Codes** (ISO 3166-1 alpha-2/alpha-3)
- **Region-Polygone** (GeoJSON) für größere Gebiete
- **Bounding Boxes** für schnelle Spatial Queries
- **Administrative Ebenen** (Country → Region → Sub-region)

### 2. Crawling-Strategie

#### A) Geocoding während Extraktion
- **Named Entity Recognition (NER)** für Länder/Städte
- **Geocoding API** (Nominatim/OpenStreetMap - kostenlos)
- **Fallback**: Region → Länder-Mapping

#### B) Post-Processing
- **Batch-Geocoding** nach Extraktion
- **Region-Normalisierung** (z.B. "East Africa" → ISO-Codes)
- **Koordinaten-Validierung**

### 3. Datenbank-Erweiterung

#### Neue Tabellen:
```sql
-- Geografische Metadaten
CREATE TABLE geo_locations (
    id INTEGER PRIMARY KEY,
    record_id INTEGER,
    location_type TEXT,  -- 'country', 'region', 'city', 'point'
    name TEXT,
    country_code TEXT,  -- ISO 3166-1 alpha-2
    country_code_3 TEXT, -- ISO 3166-1 alpha-3
    latitude REAL,
    longitude REAL,
    geojson TEXT,  -- GeoJSON für Polygone
    bbox_min_lat REAL,
    bbox_max_lat REAL,
    bbox_min_lon REAL,
    bbox_max_lon REAL,
    confidence REAL,  -- 0.0-1.0
    FOREIGN KEY (record_id) REFERENCES records(id)
);

-- Region-Mapping (Standardisierung)
CREATE TABLE region_mapping (
    id INTEGER PRIMARY KEY,
    region_name TEXT UNIQUE,
    normalized_name TEXT,
    country_codes TEXT,  -- JSON array
    geojson TEXT,
    bbox TEXT  -- JSON
);

-- Geocoding Cache
CREATE TABLE geocoding_cache (
    id INTEGER PRIMARY KEY,
    location_text TEXT UNIQUE,
    country_code TEXT,
    latitude REAL,
    longitude REAL,
    geojson TEXT,
    cached_at TIMESTAMP
);
```

#### Erweiterte Records-Tabelle:
```sql
ALTER TABLE records ADD COLUMN primary_country_code TEXT;
ALTER TABLE records ADD COLUMN primary_latitude REAL;
ALTER TABLE records ADD COLUMN primary_longitude REAL;
ALTER TABLE records ADD COLUMN geo_confidence REAL;
```

## 🔄 Crawling-Strategie

### Phase 1: Basis-Extraktion (aktuell)
1. Text-basierte Region-Extraktion
2. Länder-Namen erkennen
3. In Datenbank speichern

### Phase 2: Geocoding (neu)
1. **Named Entity Recognition** für Länder/Städte
2. **Geocoding** via Nominatim (kostenlos, OpenStreetMap)
3. **Koordinaten** extrahieren
4. **Länder-Codes** zuordnen
5. **GeoJSON** generieren (für Regionen)

### Phase 3: Normalisierung
1. Region-Namen standardisieren
2. Mehrdeutige Namen auflösen
3. Confidence-Scores berechnen

## 🛠️ Implementierungs-Plan

### Schritt 1: Geocoding-Service
```python
# backend/geocoding.py
- Nominatim API Integration
- Caching für Performance
- Batch-Geocoding
- Error Handling
```

### Schritt 2: NER für Geografie
```python
# backend/geo_extractors.py
- Länder-Namen erkennen
- Städte erkennen
- Region-Namen normalisieren
- Koordinaten extrahieren (falls im Text)
```

### Schritt 3: Datenbank-Erweiterung
```python
# database.py erweitern
- geo_locations Tabelle
- region_mapping Tabelle
- geocoding_cache Tabelle
- Spatial Indizes
```

### Schritt 4: Pipeline-Integration
```python
# pipeline.py erweitern
- Geocoding nach Extraktion
- Batch-Processing
- Retry-Logic
```

## 📊 Beispiel-Datenstruktur

### Vorher (aktuell):
```json
{
  "title": "Drought in East Africa",
  "region": "East Africa",
  "country": null
}
```

### Nachher (geospatial):
```json
{
  "title": "Drought in East Africa",
  "region": "East Africa",
  "country": null,
  "geo_locations": [
    {
      "type": "region",
      "name": "East Africa",
      "country_codes": ["KE", "ET", "SO", "UG", "TZ"],
      "latitude": 1.0,
      "longitude": 38.0,
      "geojson": {...},
      "confidence": 0.9
    }
  ],
  "primary_country_code": "KE",
  "primary_latitude": 1.0,
  "primary_longitude": 38.0
}
```

## 🎨 Visualisierungs-Möglichkeiten

### Mit geospatial Daten:
- ✅ **Heatmaps** nach Region/Land
- ✅ **Clustering** nach Nähe
- ✅ **Timeline-Maps** (Veränderung über Zeit)
- ✅ **Filter** nach Länder-Codes
- ✅ **Bounding Box Queries** (schnelle Spatial Queries)
- ✅ **GeoJSON Overlays** auf Karten

## 🚀 Nächste Schritte

1. ✅ **Analyse** (dieses Dokument)
2. ⏳ **Geocoding-Service** implementieren
3. ⏳ **NER für Geografie** hinzufügen
4. ⏳ **Datenbank erweitern**
5. ⏳ **Pipeline integrieren**
6. ⏳ **Testen mit echten Daten**

## 📚 Ressourcen

- **Nominatim API**: https://nominatim.org/release-docs/develop/api/Overview/
- **ISO 3166**: https://www.iso.org/iso-3166-country-codes.html
- **GeoJSON**: https://geojson.org/
- **Spatial SQLite**: https://www.gaia-gis.it/fossil/libspatialite/

