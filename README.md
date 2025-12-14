# 🌍 TERA - Risk Intelligence Platform

**Environmental Peace & Conflict Prediction System**

Real-time geospatial risk analysis combining Earth System data with conflict intelligence for 2026-2027 forecasts.

![TERA Screenshot](docs/screenshot.png)

## ✨ Features

- 🗺️ **3D Hexagonal Risk Maps** - H3 grid visualization with MapLibre GL
- 🌀 **Hopf Fibration Animation** - Dynamic logo representing interconnected systems
- 📊 **IPCC SSP Scenarios** - Climate projections (SSP1-2.6 to SSP5-8.5)
- 🔥 **Real-time Fire Detection** - NASA FIRMS integration
- 🛰️ **Satellite Data** - Sentinel-2, MODIS, VIIRS via Planetary Computer
- 📈 **2026-2027 Forecasts** - Short-term risk predictions
- 🌡️ **Earth System Cycles** - Energy, Water, Carbon monitoring

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         TERA PLATFORM                           │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (React + Vite)                                        │
│  ├── MapLibre GL 3D Visualization                              │
│  ├── Hopf Fibration Logo                                       │
│  └── City Analysis Dashboard                                   │
├─────────────────────────────────────────────────────────────────┤
│  Backend (FastAPI)                                              │
│  ├── /api/analysis - Risk Analysis                             │
│  ├── /api/earth - Earth Data & Forecasts                       │
│  └── /api/scraping - Data Ingestion                            │
├─────────────────────────────────────────────────────────────────┤
│  Services                                                       │
│  ├── earth_data_service.py - NASA, Sentinel, ERA5              │
│  ├── forecast_engine.py - 2026-2027 Predictions                │
│  ├── adaptive_tessellation.py - H3 Risk Mapping                │
│  └── intelligent_risk.py - IPCC-based Risk Scoring             │
├─────────────────────────────────────────────────────────────────┤
│  Data Layer                                                     │
│  ├── PostgreSQL + PostGIS                                      │
│  ├── Redis (Cache)                                              │
│  ├── ChromaDB (Vectors)                                         │
│  └── Ollama (LLM)                                               │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL with PostGIS

### Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/tera-risk-intelligence.git
cd tera-risk-intelligence

# Start infrastructure
docker-compose up -d postgres redis chromadb ollama

# Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8080

# Frontend setup
cd frontend
npm install
npm run dev
```

### Access

- **Frontend**: http://localhost:3006
- **API Docs**: http://localhost:8080/docs
- **API**: http://localhost:8080

## 📡 Data Sources

| Source | Type | Latency | Usage |
|--------|------|---------|-------|
| NASA FIRMS | Fire Detection | NRT (3h) | Active fires |
| Sentinel-2 | Optical | 5 days | NDVI, Land Cover |
| ERA5 | Reanalysis | Monthly | Climate baseline |
| MODIS | Multispectral | Daily | LST, Vegetation |
| GOES-18 | Geostationary | 15 min | Clouds, Fire |

## 🌍 Earth System Cycles

The platform monitors key Earth system cycles:

### Energy Budget
- Shortwave/Longwave radiation
- Sensible/Latent heat flux
- Surface albedo

### Water Cycle
- Precipitation & Evapotranspiration
- Soil moisture
- Drought indices (SPI, SPEI)

### Carbon Cycle
- GPP/NPP (vegetation productivity)
- NDVI/LAI
- Fire emissions

## 📊 API Endpoints

```
GET  /api/analysis/analyze?city=Berlin    # City risk analysis
GET  /api/earth/forecast/city/berlin      # 2026-2027 forecast
GET  /api/earth/fires/current?country=DEU # Current fires
GET  /api/earth/cycles                    # Earth cycle info
GET  /api/earth/sources                   # Available data sources
```

## 🗄️ Database Schema

Key tables:
- `h3_topology` - Hexagonal grid with geography
- `h3_energy_budget` - Energy balance per cell
- `h3_water_cycle` - Water cycle variables
- `h3_carbon_cycle` - Carbon fluxes
- `h3_conflict` - Conflict baseline (ACLED)
- `forecasts` - 2026-2027 predictions
- `nrt_observations` - Real-time satellite data

## 🔮 Forecast Engine

The forecast engine generates short-term predictions based on:
- ERA5 climate reanalysis baseline
- IPCC AR6 regional amplification factors
- Physical Earth cycle models
- Current observation anomalies

```python
from services.forecast_engine import get_forecast_for_city

forecast = await get_forecast_for_city("Berlin")
# Returns Q1-Q4 2026 and Q1-Q2 2027 outlook
```

## 🐳 Docker Compose

```yaml
services:
  postgres:    # PostGIS database
  redis:       # Cache & queue
  chromadb:    # Vector store
  ollama:      # Local LLM
  backend:     # FastAPI
  frontend:    # React + Vite
```

## 📁 Project Structure

```
tera-risk-intelligence/
├── backend/
│   ├── api/routes/          # API endpoints
│   ├── services/            # Business logic
│   │   ├── earth_data_service.py
│   │   ├── forecast_engine.py
│   │   └── adaptive_tessellation.py
│   ├── db/                  # Database schemas
│   ├── agents/              # AI agents
│   └── main.py              # FastAPI app
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main component
│   │   └── components/
│   ├── index.html
│   └── vite.config.js
├── docker-compose.yml
└── README.md
```

## 🔧 Configuration

Environment variables (`.env`):

```env
DATABASE_URL=postgresql+asyncpg://tera:password@localhost:5432/tera
REDIS_URL=redis://localhost:6379/0
OLLAMA_URL=http://localhost:11434
CHROMA_URL=http://localhost:8000
```

## 📜 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Contact

For questions and support, open an issue on GitHub.

---

**Built with ❤️ for a safer, more predictable world.**

