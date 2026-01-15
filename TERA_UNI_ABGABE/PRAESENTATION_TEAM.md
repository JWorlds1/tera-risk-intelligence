# 🌍 TERA - Risk Intelligence Platform
## Team-Präsentation | Universität Abgabe

---

## 🏗️ System-Architektur (Meta-Modell)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TERA ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│   │   FRONTEND   │◄──►│   BACKEND    │◄──►│    DATA      │         │
│   │   (Daniel)   │    │  (Ioannis)   │    │    (Dui)     │         │
│   └──────────────┘    └──────────────┘    └──────────────┘         │
│          │                   │                   │                  │
│          ▼                   ▼                   ▼                  │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│   │  MapLibre GL │    │   FastAPI    │    │  IPCC AR6    │         │
│   │  3D Hexagons │    │   Uvicorn    │    │  USGS Live   │         │
│   │  React/Vite  │    │   H3 Grid    │    │  ACLED 2024  │         │
│   └──────────────┘    └──────────────┘    └──────────────┘         │
│                              │                                      │
│                              ▼                                      │
│                    ┌──────────────────┐                            │
│                    │     SERVICES     │                            │
│                    │    (Mykyta)      │                            │
│                    ├──────────────────┤                            │
│                    │ • Risk Engine    │                            │
│                    │ • Tessellation   │                            │
│                    │ • Geocoding      │                            │
│                    └──────────────────┘                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 👥 Team-Aufteilung

### 🎨 FRONTEND - Daniel
**Datei:** `frontend/src/App.jsx`

**Kernfunktion:** 3D Hexagon-Visualisierung mit MapLibre GL

```javascript
// 3D Extrusion Layer - Risiko als Höhe
map.current.addLayer({
  id: 'hex3d',
  type: 'fill-extrusion',
  source: 'hex',
  paint: {
    'fill-extrusion-color': ['match', ['get', 'primary_risk'],
      'coastal_flood', '#00bfff',
      'drought', '#ff8c00',
      'seismic', '#9932cc',
      '#32cd32'],
    'fill-extrusion-height': ['get', 'height'],
    'fill-extrusion-opacity': 0.88
  }
})
```

**Features:** IPCC SSP-Szenarien, Animierte Hexagone, Popup-Details

---

### ⚙️ SERVICES - Mykyta
**Datei:** `backend/services/adaptive_tessellation.py`

**Kernfunktion:** Topographische Risiko-Zonierung

```python
RISK_ZONES_2026 = {
    'coastal': {
        'CRITICAL_COASTAL': {
            'risk_range': (0.80, 0.95),
            'elevation_max': 2,  # Meter über Meeresspiegel
            'description': 'Kritische Küstenzone'
        },
        'HIGH_FLOOD': {
            'risk_range': (0.60, 0.79),
            'elevation_max': 5
        }
    }
}
```

**Features:** H3 Hexagonal Grid, Wasser/Land-Erkennung, Multi-Hazard-Analyse

---

### 📊 DATA - Dui
**Datenquellen Integration**

| Quelle | Typ | Verwendung |
|--------|-----|------------|
| IPCC AR6 SSP2-4.5 | Klimaprognosen | Risiko-Szenarien 2025-2100 |
| USGS Earthquake | Live-API | Seismische Echtzeit-Daten |
| ACLED 2023/2024 | Konflikt-DB | Geopolitische Risiken |
| Copernicus DEM | Topographie | Elevation-basierte Zonierung |

**Kernlogik:** `backend/services/real_risk_engine.py`

```python
def calculate_multi_hazard_risk(lat, lon, city_type):
    risks = {
        'climate_risk': get_ipcc_projection(lat, lon),
        'seismic_risk': get_usgs_earthquakes(lat, lon),
        'conflict_risk': get_acled_events(lat, lon)
    }
    return aggregate_risks(risks)
```

---

### 🔧 BACKEND - Ioannis
**Datei:** `backend/main.py` + `backend/api/routes/analysis.py`

**API-Endpunkte:**

```python
@router.get("/risk-map")
async def get_risk_map(city: str, resolution: int = 10):
    """Generiert 1.376 H3-Hexagone mit Risiko-Daten"""
    geo = await geocode_city(city)
    features = tessellation_service.generate_hexagons_sync(
        lat=geo['lat'], lon=geo['lon'],
        city_name=city, resolution=resolution
    )
    return {'type': 'FeatureCollection', 'features': features}
```

**Stack:** FastAPI, Uvicorn, H3 v3.7.6, Pydantic

---

## 🚀 System starten

```bash
# SSH-Tunnel zum Server
ssh -i terraform/keys/geospatial-key.pem \
    -L 3006:localhost:3006 -L 8080:localhost:8080 \
    -N ubuntu@141.100.238.104

# Backend (auf Server)
cd /data/tera/backend && source /data/tera/venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8080

# Frontend (auf Server)
cd /data/tera/frontend && npm run dev -- --host 0.0.0.0 --port 3006

# Öffnen: http://localhost:3006
```

---

## 📈 Ergebnis: Miami Analyse

- **1.376 Risikozellen** mit H3-Tessellation
- **Topographische Erkennung:** Wasser vs. Land
- **IPCC Szenarien:** SSP1-1.9 (57%), SSP2-4.5 (75%), SSP5-8.5 (100%)
- **Empfehlungen:** Klimaanpassungsstrategie, Hochwasserschutz-Audit

---

*TERA - Transforming Earth Risk Analysis | 2026*
