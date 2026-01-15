# TERA - Risk Intelligence Platform
## Projektbericht für Universitätsabgabe

**Datum:** Januar 2026  
**Kurs:** Geospatial Intelligence  
**Team:** Daniel, Mykyta, Dui, Ioannis

---

## 1. Executive Summary

TERA (Transforming Earth Risk Analysis) ist eine geospatiale Klimarisiko-Analyseplattform, die IPCC AR6-Klimaprojektionen mit Echtzeit-Gefahrendaten kombiniert. Das System ermöglicht die Visualisierung von Multi-Hazard-Risiken für beliebige Städte weltweit mit einer Auflösung von bis zu 1.376 hexagonalen Risikozellen.

**Kernmetriken:**
- 1.376 H3-Hexagone pro Stadtanalyse
- 8 Risikoarten (Küstenflut, Dürre, Seismik, etc.)
- 3 IPCC SSP-Szenarien (2025-2100)
- 10+ Städte-Presets (Miami, Jakarta, Tokyo, etc.)

---

## 2. Technische Architektur

### 2.1 Frontend (React/Vite)

Das Frontend nutzt MapLibre GL JS für 3D-Kartenvisualisierung mit Fill-Extrusion-Layers:

```javascript
// Hexagon-Layer mit Risiko-basierter Höhe
map.addLayer({
  id: 'hex3d',
  type: 'fill-extrusion',
  paint: {
    'fill-extrusion-height': ['get', 'height'],
    'fill-extrusion-color': ['match', ['get', 'primary_risk'],
      'coastal_flood', '#00bfff',
      'drought', '#ff8c00',
      '#32cd32'
    ]
  }
})
```

### 2.2 Backend (FastAPI)

RESTful API mit asynchroner Verarbeitung:

```python
@router.get("/risk-map")
async def get_risk_map(city: str, resolution: int = 10):
    geo = await geocode_city(city)
    features = tessellation_service.generate_hexagons_sync(
        lat=geo['lat'], lon=geo['lon'],
        city_name=city, resolution=resolution
    )
    return {'type': 'FeatureCollection', 'features': features}
```

### 2.3 Datenintegration

| Quelle | Typ | Update-Frequenz |
|--------|-----|-----------------|
| IPCC AR6 WG1/2 | Klimaprojektionen | Statisch |
| USGS Earthquake API | Seismische Daten | Echtzeit |
| ACLED | Konfliktdaten | Täglich |
| Copernicus DEM | Topographie | Statisch |

---

## 3. Implementierungsdetails

### 3.1 H3 Hexagonal Tessellation

Das System verwendet Uber's H3 (v3.7.6) für räumliche Indexierung:

```python
h3_index = h3.geo_to_h3(lat, lon, resolution=10)
boundary = h3.h3_to_geo_boundary(h3_index, geo_json=True)
```

**Resolution 10:** ~15m² pro Hexagon - optimal für urbane Risikoanalyse.

### 3.2 Topographische Zonierung

Automatische Erkennung von Geländetypen basierend auf Elevation:

```python
RISK_ZONES = {
    'CRITICAL_COASTAL': {
        'elevation_max': 2,  # Meter ü.M.
        'risk_range': (0.80, 0.95)
    },
    'HIGH_FLOOD': {
        'elevation_max': 5,
        'risk_range': (0.60, 0.79)
    }
}
```

### 3.3 IPCC SSP-Szenarien

Drei Szenarien für Zukunftsprojektionen:

| Szenario | Beschreibung | Miami 2100 |
|----------|--------------|------------|
| SSP1-1.9 | Nachhaltig | 57% Risiko |
| SSP2-4.5 | Mittel | 75% Risiko |
| SSP5-8.5 | Fossil | 100% Risiko |

---

## 4. Deployment

### 4.1 Server-Setup

```bash
# OpenStack Cloud Server
ssh ubuntu@141.100.238.104

# Backend mit virtualenv
cd /data/tera/backend
source /data/tera/venv/bin/activate  # H3 v3.7.6
python -m uvicorn main:app --host 0.0.0.0 --port 8080

# Frontend
cd /data/tera/frontend
npm run dev -- --host 0.0.0.0 --port 3006
```

### 4.2 Port-Forwarding

```bash
ssh -L 3006:localhost:3006 -L 8080:localhost:8080 ubuntu@141.100.238.104
```

---

## 5. Ergebnisse

### Miami Risikoanalyse

- **1.376 Risikozellen** generiert
- **Topographie:** Wasser vs. Land korrekt erkannt
- **Primärrisiko:** Coastal Flood (Küstenflut)
- **Empfehlungen:** Klimaanpassungsstrategie, Hochwasserschutz-Audit

---

## 6. Fazit

TERA demonstriert erfolgreich die Integration von:
- Geospatialer Analyse (H3-Tessellation)
- Klimawissenschaft (IPCC AR6)
- Echtzeit-Daten (USGS, ACLED)
- Moderner Web-Technologie (React, FastAPI)

Das System ist produktionsbereit und skalierbar für globale Anwendungen.

---

**Repository:** [GitHub - TERA](https://github.com/user/TERA_UNI_ABGABE)  
**Server:** 141.100.238.104  
**Kontakt:** Geospatial Intelligence Team

---

*Universität - Januar 2026*
