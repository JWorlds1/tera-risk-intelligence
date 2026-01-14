# 🌍 Risk Raster Generator - Iso-Risk Contours

## Übersicht

Implementierung der geometrischen Interpretation von Ähnlichkeitsmaßen nach **Jones & Furnas (1987)** für Risiko-Visualisierung auf Weltkarten.

**Paper**: "Pictures of Relevance: A Geometric Analysis of Similarity Measures"  
**Journal**: Journal of the American Society for Information Science, 38(6), 420-442

## 🎯 Konzept

### Iso-Similarity Contours (analog zu Höhenlinien)

Wie in der Geographie Höhenlinien (Isohypsen) gleiche Höhen verbinden, verbinden **Iso-Risk Contours** Punkte mit gleichen Risiko-Werten:

```
┌─────────────────────────────────┐
│   Höhenlinien (Geographie)      │
│   ──── 1000m                    │
│   ──── 800m                      │
│   ──── 600m                      │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│   Iso-Risk Contours (Risiko)    │
│   ──── CRITICAL (0.8)            │
│   ──── HIGH (0.6)                │
│   ──── MEDIUM (0.4)              │
└─────────────────────────────────┘
```

### Geometrische Interpretation

1. **Referenz-Vektor**: Bekannte Locations mit Risiko-Scores
2. **Raster-Grid**: Gleichmäßiges Gitter über die Weltkarte
3. **Interpolation**: Berechnung von Risiko-Scores für jeden Grid-Punkt
4. **Contour-Linien**: Verbindung von Punkten mit gleichen Risiko-Werten

## 🔧 Implementierung

### 1. Raster-Generierung

```python
from backend.risk_raster_generator import RiskRasterGenerator

generator = RiskRasterGenerator(
    resolution=1.0,  # 1 Grad ≈ 111km
    interpolation_method='rbf',  # Radial Basis Function
    max_interpolation_distance=10.0  # Max. Distanz für Interpolation
)

raster_data = generator.generate_raster()
```

### 2. Interpolations-Methoden

#### Radial Basis Function (RBF) - Empfohlen
- **Vorteile**: Glatte Interpolation, gut für unregelmäßige Daten
- **Nachteile**: Langsamer bei vielen Punkten
- **Verwendung**: Standard-Methode

#### Inverse Distance Weighting (IDW)
- **Vorteile**: Schnell, einfach
- **Nachteile**: Kann "Bull's Eye" Effekte haben
- **Verwendung**: Fallback wenn RBF fehlschlägt

#### Linear/Cubic Interpolation
- **Vorteile**: Sehr schnell
- **Nachteile**: Erfordert regelmäßiges Grid
- **Verwendung**: Für große Datensätze

### 3. Contour-Berechnung

```python
# Automatische Contour-Berechnung für jedes Risiko-Level
contours = generator.calculate_contours(
    lat_grid, lon_grid, risk_grid, mask
)

# Contours enthalten:
# - CRITICAL: 0.8, 0.85, 0.9, 0.95
# - HIGH: 0.6, 0.65, 0.7, 0.75
# - MEDIUM: 0.4, 0.45, 0.5, 0.55
# - LOW: 0.2, 0.25, 0.3, 0.35
```

## 📊 Verwendung

### Schritt 1: Frontend-Daten generieren

```bash
cd backend
python3 generate_frontend_data.py
```

### Schritt 2: Raster generieren

```bash
python3 risk_raster_generator.py
```

**Output**: `data/frontend/risk_raster.geojson`

### Schritt 3: Visualisierung im Frontend

1. Starte Web-App: `python3 web_app.py`
2. Öffne Browser: `http://localhost:5000`
3. Gehe zu **Karte-Tab**
4. Wähle **"Iso-Risk Contours"** im Visualisierungs-Dropdown

## 🎨 Visualisierung

### Contour-Linien
- **CRITICAL** (rot, gestrichelt): Risk ≥ 0.8
- **HIGH** (orange): Risk ≥ 0.6
- **MEDIUM** (gelb): Risk ≥ 0.4
- **LOW** (blau): Risk ≥ 0.2

### Heatmap-Overlay
- Farbverlauf: Blau → Cyan → Gelb → Orange → Rot
- Intensität basierend auf Risiko-Score
- Radius: 20px, Blur: 10px

## 📐 Geometrische Interpretation

### 2D-Vektorraum

Jeder Punkt im Raster wird als Vektor im 2D-Raum interpretiert:

```
Punkt P = (lat, lon)
Referenz-Vektoren R₁, R₂, ..., Rₙ = bekannte Locations

Risiko-Score(P) = f(Distanz(P, R₁), Distanz(P, R₂), ..., Distanz(P, Rₙ))
```

### Ähnlichkeits-Maße

1. **Euklidische Distanz**: Direkte Entfernung zwischen Punkten
2. **Gewichtete Distanz**: Berücksichtigt Risiko-Score der Referenz-Punkte
3. **Inverse Distanz**: Nähere Punkte haben mehr Einfluss

## 🔍 Beispiel-Output

### GeoJSON-Struktur

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [lon, lat]
      },
      "properties": {
        "risk_score": 0.65,
        "risk_level": "HIGH",
        "distance_to_nearest": 2.3
      }
    },
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[lon1, lat1], [lon2, lat2], ...]
      },
      "properties": {
        "level": "HIGH",
        "risk_value": 0.6,
        "type": "iso_risk_contour"
      }
    }
  ]
}
```

## ⚙️ Konfiguration

### Resolution (Raster-Auflösung)

- **0.5°** ≈ 55km - Sehr detailliert, langsam
- **1.0°** ≈ 111km - Empfohlen, ausgewogen
- **2.0°** ≈ 222km - Schnell, weniger detailliert

### Max. Interpolations-Distanz

- **5.0°** ≈ 555km - Konservativ, nur nahe Punkte
- **10.0°** ≈ 1110km - Empfohlen, gute Abdeckung
- **20.0°** ≈ 2220km - Sehr weitreichend, kann ungenau sein

## 🚀 Performance-Optimierung

### Für große Datensätze

1. **Reduziere Resolution**: `resolution=2.0`
2. **Limit bekannte Punkte**: Nur Locations mit Risk > 0.3
3. **Vereinfachte Contours**: Verwende `_calculate_simple_contours()`
4. **Regionale Bounds**: Generiere nur für bestimmte Regionen

```python
generator = RiskRasterGenerator(resolution=2.0)
raster_data = generator.generate_raster(
    bounds={
        'lat_min': 20,
        'lat_max': 50,
        'lon_min': -10,
        'lon_max': 40
    }
)
```

## 📈 Anwendungsfälle

### 1. Regionale Risiko-Analyse
- Identifiziere Hotspots
- Erkenne Risiko-Gradienten
- Plane Interventions-Strategien

### 2. Frühwarnsystem
- Erkenne sich ausbreitende Risiko-Zonen
- Verfolge Risiko-Entwicklung über Zeit
- Identifiziere kritische Schwellenwerte

### 3. Ressourcen-Allokation
- Priorisiere Regionen nach Risiko
- Optimiere Hilfs-Einsätze
- Planung von Infrastruktur

## 🔬 Wissenschaftlicher Hintergrund

### Jones & Furnas (1987) - Kernkonzepte

1. **Geometrische Interpretation**: Vektoren im n-dimensionalen Raum
2. **Iso-Similarity Contours**: Konturlinien gleicher Ähnlichkeit
3. **Referenz-Vektor**: Fester Query-Vektor als Referenz
4. **Ähnlichkeits-Maße**: Vergleich verschiedener Metriken

### Übertragung auf Risiko-Analyse

- **Vektor**: Geografische Koordinate (lat, lon)
- **Ähnlichkeit**: Risiko-Score
- **Referenz**: Bekannte Locations mit Risiko-Daten
- **Contours**: Iso-Risk-Linien

## 🐛 Troubleshooting

### Problem: Keine Contours sichtbar

**Lösung**:
1. Prüfe ob Raster generiert wurde: `ls data/frontend/risk_raster.geojson`
2. Prüfe ob Frontend-Daten vorhanden: `ls data/frontend/complete_data.json`
3. Generiere Raster neu: `python3 risk_raster_generator.py`

### Problem: Raster zu langsam

**Lösung**:
1. Erhöhe Resolution: `resolution=2.0`
2. Reduziere max_interpolation_distance: `max_interpolation_distance=5.0`
3. Verwende vereinfachte Contours (ohne Matplotlib)

### Problem: Unrealistische Interpolation

**Lösung**:
1. Reduziere max_interpolation_distance
2. Verwende mehr bekannte Punkte (generiere mehr Frontend-Daten)
3. Prüfe Koordinaten (keine Platzhalter 0,0)

## 📚 Referenzen

- **Jones, W. P., & Furnas, G. W. (1987)**. Pictures of Relevance: A Geometric Analysis of Similarity Measures. *Journal of the American Society for Information Science*, 38(6), 420-442.
- **Scipy Interpolation**: https://docs.scipy.org/doc/scipy/reference/interpolate.html
- **Leaflet Heat Plugin**: https://github.com/Leaflet/Leaflet.heat

## 🎯 Nächste Schritte

1. ✅ Raster-Generierung implementiert
2. ✅ Contour-Berechnung implementiert
3. ✅ Frontend-Integration
4. ⏳ Zeitreihen-Analyse (Risiko-Entwicklung über Zeit)
5. ⏳ 3D-Visualisierung (Risiko als "Höhe")
6. ⏳ Animierte Contours (Risiko-Entwicklung)

