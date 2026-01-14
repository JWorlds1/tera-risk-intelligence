<!-- 029189cb-7ab3-4575-a56b-1f24a02157ff f3046b99-098d-47bc-b776-f671bac1a7cf -->
# Integration des Globalen Klima-Kontextraum-Systems

## Übersicht

Integration des Design-Frameworks aus dem Dokument in das bestehende System:

- **Frontend**: Google Maps 3D View mit feingranularem H3-Grid, lokal angepassten Flächen, globalen Zusammenhängen
- **Backend**: Agenten-basierte Datenverarbeitung mit Firecrawl/crawl4ai, kostenlosen Open-Source LLMs, echte Datenquellen

## Architektur

### Frontend (tera/tera---geospatial/)

- **Bestehend**: Google Maps 3D, LitElement, TypeScript, simuliertes H3-Grid
- **Neu**: Echte H3-Bibliothek, erweiterte Kontext-Tensor-Visualisierung, SSP-Szenarien-UI, Handlungsempfehlungs-Panel

### Backend (backend/)

- **Bestehend**: Firecrawl, crawl4ai, Agenten-Systeme, Datenbank
- **Neu**: H3-Grid-Generator, Kontext-Tensor-Engine, SSP-Szenarien-Simulator, Handlungsempfehlungs-Engine, kostenlose LLM-Integration

## Implementierungs-Phasen

### Phase 1: H3-Grid-System (Frontend & Backend)

**Frontend:**

- `tera/tera---geospatial/package.json`: `h3-js` hinzufügen
- `tera/tera---geospatial/mcp_maps_server.ts`: Simuliertes Grid durch echte H3-API ersetzen
- `h3.h3ToGeoBoundary()` für Hexagon-Grenzen
- `h3.geoToH3()` für Koordinaten-zu-H3-Index
- Dynamische Auflösung basierend auf Zoom-Level

**Backend:**

- `backend/h3_grid_engine.py` (neu): H3-Grid-Generator
- Generiert H3-Zellen für gegebene Region
- Unterstützt Auflösungen: neighborhood (res 10-11), city (res 8-9), region (res 6-7)
- API-Endpoint: `/api/h3/grid?region=...&resolution=...`

### Phase 2: Multidimensionaler Kontext-Tensor

**Backend:**

- `backend/context_tensor_engine.py` (neu): Kontext-Tensor-Generator
- 6 Dimensionen: Klima, Geografie, Sozioökonomie, Infrastruktur, Vulnerabilität, Unstrukturierte Daten
- Integration mit echten Datenquellen:
- Copernicus Climate Data Store (ERA5) via API
- NOAA Gridded Data
- World Bank Open Data API
- OpenStreetMap (OSM) für Infrastruktur
- Firecrawl für unstrukturierte Daten
- Aggregation pro H3-Zelle (Durchschnitt, Mehrheitswert, Dichte)

**Frontend:**

- `tera/tera---geospatial/map_app.ts`: Erweiterte Tensor-Visualisierung
- Layer-Toggle für einzelne Dimensionen
- Farbcodierung nach Kontext-Tensor-Werten
- Detail-Panel mit allen 6 Dimensionen

### Phase 3: SSP-Szenarien-Simulation

**Backend:**

- `backend/ssp_scenario_engine.py` (neu): SSP-Simulator
- Implementiert SSP1-5 Szenarien
- Projektionen für zukünftige Zeitpunkte (2025-2100)
- Kopplung mit Klimamodellen (RCPs)
- API-Endpoint: `/api/ssp/simulate?region=...&scenario=...&year=...`

**Frontend:**

- `tera/tera---geospatial/map_app.ts`: Szenarien-UI
- Dropdown für SSP-Auswahl (SSP1-5)
- Zeit-Slider für Jahr (2025-2100)
- Vergleichsansicht (Split-Screen für 2 Szenarien)

### Phase 4: Risikomodellierung (IPCC-Framework)

**Backend:**

- `backend/risk_modeling_engine.py` (neu): Risikobewertung
- Formel: Risk = Hazard × Exposure × Vulnerability
- Berechnung pro H3-Zelle
- Normalisierung und Scoring (0-100)
- API-Endpoint: `/api/risk/calculate?h3_index=...&scenario=...`

**Frontend:**

- `tera/tera---geospatial/map_app.ts`: Risiko-Visualisierung
- Divergierende Farbpalette (Grün → Gelb → Rot) für Risiko-Score
- Unsicherheits-Visualisierung (Transparenz/Sättigung)
- Risiko-Histogramm im Detail-Panel

### Phase 5: Handlungsempfehlungs-Engine

**Backend:**

- `backend/action_recommendation_engine.py` (neu): Empfehlungs-System
- Maßnahmen-Datenbank (Action-Base) aus UNFCCC, wissenschaftlichen Quellen
- Matching-Logik: Filter nach Risiko-Typ, Kontext-Bedingungen
- Ranking: Kosten, Co-Benefits, Umsetzbarkeit
- LLM-Synthese mit kostenlosen LLMs (Ollama, LlamaCpp)
- API-Endpoint: `/api/actions/recommend?h3_index=...&risk_score=...`

**Frontend:**

- `tera/tera---geospatial/map_app.ts`: Handlungsempfehlungs-Panel
- Top-3 Empfehlungen pro Zelle
- Kosten, Timeline, Co-Benefits
- LLM-generierte Beschreibungen

### Phase 6: Datenquellen-Integration (Backend-Agenten)

**Backend:**

- `backend/data_acquisition_agents.py` (neu): Agenten für Datenbeschaffung
- **Klima-Agent**: Copernicus, NOAA APIs
- **Sozioökonomie-Agent**: World Bank API, GPW
- **Infrastruktur-Agent**: OSM Overpass API
- **Vulnerabilität-Agent**: ND-GAIN, World Bank GovData360
- **Unstrukturierte-Daten-Agent**: Firecrawl + crawl4ai
- Alle Agenten nutzen kostenlose/open-source LLMs (Ollama) für Extraktion

**Integration:**

- `backend/agent_orchestrator.py`: Erweitern um neue Agenten
- `backend/context_tensor_engine.py`: Nutzt Agenten-Outputs

### Phase 7: Kostenlose LLM-Integration

**Backend:**

- `backend/free_llm_manager.py` (neu): Manager für kostenlose LLMs
- Ollama-Integration (Llama 2, Mistral, CodeLlama)
- LlamaCpp für lokale Inferenz
- Fallback-Mechanismus (Ollama → LlamaCpp → Mock)
- Verwendung in:
- Handlungsempfehlungs-Synthese
- Kontext-Tensor-Analyse
- Unstrukturierte Daten-Extraktion

**Konfiguration:**

- `backend/config.py`: LLM-Konfiguration
- `backend/requirements.txt`: `ollama`, `llama-cpp-python` hinzufügen

### Phase 8: Farbstrategie & Visualisierung

**Frontend:**

- `tera/tera---geospatial/map_app.ts`: Farbstrategie implementieren
- Divergierende Palette für Risiko: `#2ca25f` (Grün) → `#ffffbf` (Gelb) → `#de2d26` (Rot)
- Sequentielle Paletten für Einzelindikatoren
- Unsicherheit: Transparenz/Sättigung
- ColorBrewer-konforme Paletten

**CSS:**

- `tera/tera---geospatial/index.css`: Farb-Variablen definieren

### Phase 9: API-Integration Frontend ↔ Backend

**Backend:**

- `backend/api_server.py` (neu): FastAPI-Server
- Endpoints:
- `POST /api/context-space/analyze`: Vollständige Analyse
- `GET /api/h3/grid`: H3-Grid generieren
- `GET /api/tensor/{h3_index}`: Kontext-Tensor abrufen
- `GET /api/ssp/simulate`: SSP-Szenario simulieren
- `GET /api/risk/calculate`: Risiko berechnen
- `GET /api/actions/recommend`: Handlungsempfehlungen

**Frontend:**

- `tera/tera---geospatial/api_client.ts` (neu): API-Client
- TypeScript-Client für Backend-APIs
- Error-Handling, Retry-Logik
- Integration in `map_app.ts`

### Phase 10: Terrain-Anpassung & Globale Zusammenhänge

**Frontend:**

- `tera/tera---geospatial/map_app.ts`: Terrain-Anpassung
- Höhen-Daten für Extrusion (bereits vorhanden, erweitern)
- Lokale Anpassung der Hexagon-Höhe basierend auf Elevation
- Globale Zusammenhänge: Visualisierung von Verbindungen zwischen Zellen

**Backend:**

- `backend/global_context_analyzer.py` (neu): Globale Zusammenhänge
- Analysiert Verbindungen zwischen Regionen
- Kaskadeneffekte, Fernwirkungen
- LLM-basierte Analyse mit kostenlosen LLMs

## Technische Details

### H3-Bibliothek

- Frontend: `h3-js` (npm)
- Backend: `h3` (Python)

### Kostenlose LLMs

- Ollama (lokal)
- LlamaCpp (lokal)
- Fallback: Mock-Daten

### Datenquellen

- Copernicus: REST API
- NOAA: REST API
- World Bank: REST API
- OSM: Overpass API
- Firecrawl: API (bestehend)
- crawl4ai: Lokal (bestehend)

### Mathematische Farbberechnung (Kontext-basiert)

**Backend (`backend/color_computation_engine.py`):**

- **Normalisierung**: Min-Max-Skalierung `(value - min) / (max - min)`, Z-Score, Robust Scaling
- **Gewichtete Kombination**: `final_score = Σ(weight_i × dimension_i) / Σ(weight_i)`
- **Divergierende Transformation**: 
- `t = (score - 50) / 50` (zentriert bei 50)
- `t < 0`: Grün→Gelb, `t > 0`: Gelb→Rot
- Sigmoidale Funktion: `t_smooth = sigmoid(t × 2)` für sanftere Übergänge
- **Kontext-Adaptive Gewichtung**: Basierend auf Landnutzung, Geografie, Layer-Modus
- **Unsicherheits-Metrik**: Standardabweichung → Alpha-Kanal (Transparenz)

**Frontend (`tera/tera---geospatial/color_math.ts`):**

- **RGB-Interpolation**: Lineare Interpolation `lerp(color1, color2, t)`
- **Divergierende Palette**: Mathematische Transformation mit Breakpoint bei 50
- **Polygonale Gradienten**: 
- Radial: `intensity = 1 - (distance_from_center / radius)`
- Nachbar-Interpolation: `color = Σ(neighbor_color × distance_weight) / Σ(distance_weight)`
- **CIELAB-Farbraum**: RGB→XYZ→CIELAB Konvertierung für wahrnehmungsgleiche Abstände
- **Kontext-Adaptive Färbung**: Wasser (konstant Blau), Urban (Rot-Orange), Rural (Grün-Braun)

**Farbpaletten:**

- ColorBrewer-konform
- Divergierend für Risiko: `#2ca25f` (Grün) → `#ffffbf` (Gelb) → `#de2d26` (Rot)
- Sequentiel für Indikatoren

## Dateien-Übersicht

### Neu zu erstellen:

- `backend/h3_grid_engine.py`
- `backend/context_tensor_engine.py`
- `backend/ssp_scenario_engine.py`
- `backend/risk_modeling_engine.py`
- `backend/action_recommendation_engine.py`
- `backend/data_acquisition_agents.py`
- `backend/free_llm_manager.py`
- `backend/api_server.py`
- `backend/global_context_analyzer.py`
- `tera/tera---geospatial/api_client.ts`

### Zu erweitern:

- `tera/tera---geospatial/mcp_maps_server.ts`: Echte H3-Integration
- `tera/tera---geospatial/map_app.ts`: Erweiterte Visualisierung
- `backend/agent_orchestrator.py`: Neue Agenten integrieren
- `backend/config.py`: Neue Konfigurationen
- `backend/requirements.txt`: Neue Dependencies
- `tera/tera---geospatial/package.json`: H3-Bibliothek

### To-dos

- [ ] Frontend: H3-js Bibliothek integrieren und simuliertes Grid ersetzen
- [ ] Backend: H3-Grid-Engine mit Python h3-Bibliothek erstellen
- [ ] Kontext-Tensor-Engine mit 6 Dimensionen und echten Datenquellen implementieren
- [ ] SSP-Szenarien-Simulator für zukünftige Projektionen implementieren
- [ ] Risikomodellierung nach IPCC-Framework (Hazard × Exposure × Vulnerability)
- [ ] Handlungsempfehlungs-Engine mit Maßnahmen-Datenbank und kostenlosen LLMs
- [ ] Datenbeschaffungs-Agenten für alle 6 Tensor-Dimensionen erstellen
- [ ] Kostenlose LLM-Integration (Ollama, LlamaCpp) für Synthese und Analyse
- [ ] FastAPI-Server mit allen Endpoints für Frontend-Backend-Kommunikation
- [ ] Frontend API-Client und Integration in map_app.ts
- [ ] Farbstrategie implementieren (divergierend für Risiko, sequentiell für Indikatoren)
- [ ] Terrain-Anpassung und globale Zusammenhänge visualisieren