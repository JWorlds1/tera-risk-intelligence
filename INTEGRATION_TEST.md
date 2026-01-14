# System Integration Test Guide

## Übersicht

Dieses Dokument beschreibt, wie das vollständig integrierte Climate Context Space System getestet wird.

## System-Komponenten

### Backend
- **H3 Grid Engine**: Generiert hexagonale H3-Grids
- **Context Tensor Engine**: Erstellt multidimensionale Kontext-Tensoren
- **SSP Scenario Engine**: Simuliert IPCC SSP-Szenarien
- **Risk Modeling Engine**: Berechnet Risiken nach IPCC-Framework
- **Action Recommendation Engine**: Generiert Handlungsempfehlungen
- **Data Acquisition Agents**: Beschafft Daten für alle 6 Dimensionen
- **Free LLM Manager**: Integriert kostenlose LLMs (Ollama)
- **Color Computation Engine**: Mathematische Farbberechnung
- **FastAPI Server**: REST API für Frontend

### Frontend
- **Google Maps 3D View**: 3D-Kartenvisualisierung
- **H3-js Integration**: Echte H3-Hexagon-Grids
- **Color Math**: Mathematische Farbfunktionen
- **API Client**: Backend-Kommunikation

## Test-Ablauf

### 1. Backend starten

```bash
cd backend
python api_server.py
```

Server läuft auf: http://localhost:8000
API Docs: http://localhost:8000/docs

### 2. Frontend starten

```bash
cd tera/tera---geospatial
npm install
npm run dev
```

Frontend läuft auf: http://localhost:5173 (oder anderer Port)

### 3. System-Test ausführen

```bash
cd backend
python test_system.py
```

Erwartete Ausgabe:
- ✓ H3 Grid Engine: 331 Zellen generiert
- ✓ Context Tensor Engine: Tensor erstellt
- ✓ SSP Scenario Engine: Projektion erfolgreich
- ✓ Risk Modeling Engine: Risiko berechnet
- ✓ Action Recommendation Engine: Empfehlungen generiert
- ✓ Color Computation Engine: Farben berechnet

### 4. Frontend-Backend Integration testen

1. Öffne Frontend im Browser
2. Gib eine Anfrage ein: "Analyze flood risk in Jakarta in 2030"
3. System sollte:
   - H3-Grid generieren
   - Kontext-Tensoren erstellen
   - Risiken berechnen
   - Farben mathematisch berechnen
   - Handlungsempfehlungen anzeigen

## API-Endpoints

### POST /api/context-space/analyze
Vollständige Analyse einer Region

**Request:**
```json
{
  "region_name": "Jakarta",
  "year_offset": 5,
  "scenario": "SSP2-4.5",
  "scale": "city"
}
```

**Response:**
```json
{
  "success": true,
  "region_name": "Jakarta",
  "scenario": "SSP2-4.5",
  "year": 2030,
  "cells": [...],
  "center": {"lat": -6.2088, "lng": 106.8456}
}
```

### GET /api/h3/grid
Generiert H3-Grid für Koordinaten

### GET /api/tensor/{h3_index}
Ruft Kontext-Tensor für eine Zelle ab

### GET /api/ssp/simulate
Simuliert SSP-Szenario

### GET /api/risk/calculate
Berechnet Risiko für eine Zelle

### GET /api/actions/recommend
Gibt Handlungsempfehlungen zurück

## Mathematische Farbberechnung

Die Farbberechnung verwendet:
- **Normalisierung**: Min-Max-Skalierung
- **Divergierende Transformation**: Zentriert bei 50, sigmoidale Funktion
- **Kontext-Adaptive Anpassung**: Wasser (Blau), Urban (Rot-Orange), Rural (Grün)
- **CIELAB-Farbraum**: Für wahrnehmungsgleiche Abstände
- **Polygonale Gradienten**: Radial und Nachbar-Interpolation

## Bekannte Einschränkungen

1. **Datenquellen**: Aktuell Placeholder-Daten, echte API-Integration folgt
2. **LLM**: Ollama muss lokal installiert sein für LLM-Features
3. **Geocoding**: Region-Namen müssen noch zu Koordinaten konvertiert werden

## Nächste Schritte

1. Echte API-Integration (Copernicus, NOAA, World Bank)
2. Geocoding-Service für Region-Namen
3. Caching-Layer für Performance
4. WebSocket-Support für Real-time Updates


