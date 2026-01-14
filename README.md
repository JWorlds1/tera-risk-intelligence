# 🌍 TERA - Terrestrial Environmental Risk Analysis

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-61dafb.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)

**Environmental Peace & Conflict Prediction System**

Real-time geospatial risk analysis combining Earth System data with conflict intelligence for 2026-2100 projections.

![TERA Screenshot](docs/screenshot.png)

---

## ✨ Features

| Feature | Status | Description |
|---------|--------|-------------|
| 🗺️ **3D Hexagonal Risk Maps** | ✅ | H3 grid visualization with MapLibre GL |
| 🌀 **Hopf Fibration Animation** | ✅ | Dynamic logo representing interconnected systems |
| 📊 **IPCC SSP Scenarios** | ✅ | Climate projections (SSP1-1.9 to SSP5-8.5) |
| 🔥 **Real-time Fire Detection** | ✅ | NASA FIRMS integration |
| 🛰️ **Satellite Data** | ✅ | Sentinel-2, MODIS, VIIRS via Planetary Computer |
| 📈 **2026-2100 Forecasts** | ✅ | Long-term risk predictions |
| 🌡️ **Earth System Cycles** | ✅ | Energy, Water, Carbon monitoring |
| 🌋 **Seismic Analysis** | ✅ | USGS real-time earthquake data |
| ⚔️ **Conflict Monitoring** | ✅ | GDELT + ACLED integration |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TERA PLATFORM v2.0                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   FRONTEND  │    │   BACKEND   │    │  SERVICES   │    │    DATA     │  │
│  │             │    │             │    │             │    │             │  │
│  │  React 18   │◄──►│  FastAPI    │◄──►│ Tessellation│◄──►│  NASA/NOAA  │  │
│  │  MapLibre   │    │  Python 3.11│    │ Risk Engine │    │  IPCC AR6   │  │
│  │  Vite 5.4   │    │  Uvicorn    │    │ Geo-Coder   │    │  Copernicus │  │
│  │             │    │             │    │             │    │  USGS       │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | React 18 + MapLibre GL + Vite | 3D Visualization |
| Backend | FastAPI + Python 3.11 | REST API |
| Tessellation | H3-Py (Uber) | Hexagonal Grid |
| Data Sources | NASA, NOAA, USGS, Copernicus | Earth Observation |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

### Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/tera-geospatial.git
cd tera-geospatial

# Backend setup
cd tera_server_backup/backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
```

### Run Locally

```bash
# Terminal 1: Start Backend
cd tera_server_backup/backend
source venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8080

# Terminal 2: Start Frontend
cd tera_server_backup/frontend
npm run dev -- --port 3006
```

### Access

| Service | URL |
|---------|-----|
| 🌐 Frontend | http://localhost:3006 |
| 🔧 API | http://localhost:8080 |
| 📚 API Docs | http://localhost:8080/docs |

---

## 📡 Data Sources

| Source | Type | Latency | Usage |
|--------|------|---------|-------|
| NASA FIRMS | Fire Detection | 3h | Active fires |
| USGS | Seismic | 5min | Earthquakes M2.5+ |
| NOAA SST | Ocean | 6h | Sea Surface Temperature |
| Copernicus | Satellite | 1d | Marine currents |
| GDELT | Conflicts | 15min | Event database |
| IPCC AR6 | Climate | Static | SSP projections |

---

## 🗺️ Risk Categories

| Risk Type | Color | Icon | Description |
|-----------|-------|------|-------------|
| Coastal Flood | 🟦 | 🌊 | Sea level rise, storm surge |
| Flood | 🔵 | 💧 | Fluvial/pluvial flooding |
| Urban Flood | 🔷 | 🏙️ | Drainage overwhelm |
| Drought | 🟠 | ☀️ | Water scarcity |
| Heat Stress | 🔴 | 🌡️ | Extreme temperatures |
| Seismic | 🟣 | 🌋 | Earthquakes, tectonics |
| Conflict | ⚫ | ⚔️ | Armed conflicts |
| Stable | 🟢 | ✓ | Low risk |

---

## 📊 API Endpoints

```bash
# Analyze a city
POST /api/analysis/analyze
Body: { "location": "Miami" }

# Get risk map (H3 hexagons)
GET /api/analysis/risk-map?city=Miami&resolution=10

# Get temporal projection
GET /api/analysis/risk-map/temporal?city=Miami&year=2050&scenario=SSP2-4.5

# Earth data services
GET /api/earth/forecast/city/{city_name}
GET /api/earth/fires/current?country=DEU
GET /api/earth/cycles
```

---

## 🌍 Supported Cities

Pre-configured quick analysis for:

| Region | Cities |
|--------|--------|
| Americas | Miami, São Paulo |
| Europe | Berlin, Venice, Kyiv |
| Asia | Tokyo, Jakarta, Singapore, Mumbai |
| Africa | Cairo, Lagos |
| Oceania | Sydney (coming soon) |

*Any city worldwide can be analyzed via the search function.*

---

## 📁 Project Structure

```
tera-geospatial/
├── tera_server_backup/          # Main application
│   ├── backend/
│   │   ├── api/routes/          # API endpoints
│   │   ├── services/            # Business logic
│   │   │   ├── adaptive_tessellation.py
│   │   │   ├── forecast_engine.py
│   │   │   └── earth_data_service.py
│   │   ├── main.py              # FastAPI app
│   │   └── requirements.txt
│   └── frontend/
│       ├── src/
│       │   ├── App.jsx          # Main component
│       │   └── components/
│       ├── index.html
│       └── package.json
├── docs/
│   └── TERA_ROADMAP_2026.md     # Development roadmap
├── PROJEKTBERICHT_UNIVERSITAET.md  # University report (German)
└── README.md
```

---

## 🔮 Roadmap 2026

### Q1 2026
- [ ] Volcano API integration
- [ ] El Niño indices (ONI/MEI)
- [ ] Atmospheric pressure data

### Q2 2026
- [ ] Causal Graph Engine (pgmpy)
- [ ] Real-time data fusion (Redis Streams)
- [ ] WebSocket live updates

### Q3 2026
- [ ] Monte Carlo simulation (10,000+ runs)
- [ ] GPU acceleration
- [ ] Enterprise features

See [TERA_ROADMAP_2026.md](docs/TERA_ROADMAP_2026.md) for full details.

---

## 📜 Documentation

| Document | Description |
|----------|-------------|
| [PROJEKTBERICHT_UNIVERSITAET.md](PROJEKTBERICHT_UNIVERSITAET.md) | Full university project report (German) |
| [TERA_ROADMAP_2026.md](docs/TERA_ROADMAP_2026.md) | Development roadmap |
| [API Docs](http://localhost:8080/docs) | Interactive API documentation |

---

## 🔬 Scientific Foundation

This project is based on:

1. **IPCC AR6 (2021)** - Climate Change: The Physical Science Basis
2. **Uber H3 (2018)** - Hexagonal Hierarchical Geospatial Indexing
3. **NASA Earth Science** - Satellite observation data
4. **NOAA Climate Data** - Ocean and atmospheric analysis

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 📧 Contact

For questions and support, open an issue on GitHub.

---

**Built with ❤️ for climate research and peace**

*"The best way to predict the future is to create it." - Alan Kay*
