# 🌍 TERA - Risk Intelligence Platform

> **T**ransforming **E**arth **R**isk **A**nalysis  
> Geospatiale Klimarisiko-Analyse mit IPCC AR6 Projektionen

![Version](https://img.shields.io/badge/Version-2026-blue)
![Status](https://img.shields.io/badge/Status-Production-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🚀 Schnellstart

### 1. SSH-Tunnel starten
```bash
ssh -i terraform/keys/geospatial-key.pem \
    -L 3006:localhost:3006 \
    -L 8080:localhost:8080 \
    -N ubuntu@141.100.238.104
```

### 2. Backend starten (auf Server)
```bash
cd /data/tera/backend
source /data/tera/venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8080
```

### 3. Frontend starten (auf Server)
```bash
cd /data/tera/frontend
npm run dev -- --host 0.0.0.0 --port 3006
```

### 4. Browser öffnen
```
http://localhost:3006
```

---

## ✨ Features

| Feature | Beschreibung |
|---------|-------------|
| 🗺️ **H3 Hexagonal Grid** | 1.376+ Risikozellen pro Stadt |
| 🌊 **Topographische Erkennung** | Automatische Wasser/Land-Klassifikation |
| 📊 **IPCC AR6 Szenarien** | SSP1-1.9, SSP2-4.5, SSP5-8.5 Projektionen |
| 🌋 **Multi-Hazard-Analyse** | Küstenflut, Dürre, Seismik, Konflikt |
| 🛰️ **Live-Daten** | USGS Erdbeben, ACLED Konflikte |
| 📱 **3D Visualisierung** | MapLibre GL mit Extrusion-Layers |

---

## 🏗️ Architektur

```
TERA/
├── backend/                 # FastAPI Server
│   ├── main.py             # Einstiegspunkt
│   ├── api/routes/         # API-Endpunkte
│   │   └── analysis.py     # /risk-map, /analyze
│   └── services/           # Business-Logik
│       ├── adaptive_tessellation.py
│       └── real_risk_engine.py
│
├── frontend/               # React/Vite
│   ├── src/App.jsx        # Hauptkomponente
│   └── package.json       # Dependencies
│
└── docs/                   # Dokumentation
```

---

## 📡 API-Endpunkte

| Endpoint | Methode | Beschreibung |
|----------|---------|-------------|
| `/api/analysis/analyze` | POST | Stadt-Risikoanalyse |
| `/api/analysis/risk-map` | GET | H3-Hexagon GeoJSON |
| `/api/v2/drivers` | GET | Kausale Treiber |
| `/api/v2/live/earthquakes` | GET | USGS Echtzeit |

---

## 📦 Technologie-Stack

- **Frontend:** React, Vite, MapLibre GL JS
- **Backend:** FastAPI, Uvicorn, Python 3.11
- **Daten:** H3 v3.7.6, GeoJSON, IPCC AR6
- **Server:** Ubuntu 22.04, OpenStack Cloud

---

## 👥 Team

| Rolle | Verantwortlich |
|-------|----------------|
| Frontend | Daniel |
| Services | Mykyta |
| Data | Dui |
| Backend | Ioannis |

---

## 📄 Lizenz

MIT License - 2026

---

*Universität Projekt - Geospatial Intelligence*
