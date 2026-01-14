<!-- 2e30b5b5-2e67-48f1-8c60-5ca8db57e373 a0addce6-7cf2-490f-8d28-3dcc4a5e9e44 -->
# HPC-basierte Risiko-Vorhersage mit OpenCV und Agenten-Kontexträumen

## Übersicht

Entwicklung einer vollständigen HPC-Pipeline für:

1. **MPI-basierte verteilte Risikoberechnung** auf Supercomputern (GSI Darmstadt)
2. **OpenCV-basierte Bildverarbeitung** der Risiko-Vorhersage-Ergebnisse
3. **Agenten-basierte Kontextraum-Generierung** pro Land/Region (IPCC + Web-Daten)
4. **Geospatial Mapping** der Ergebnisse auf interaktive Karten

## Architektur-Komponenten

### 1. HPC MPI Risk Prediction (`backend/hpc/mpi_risk_prediction.py`)

**Erweitert bestehende `risk_scoring.py` für verteilte Berechnung:**

- **DistributedDataManager**: Lädt Records aus SQLite und verteilt sie über MPI Ranks
- **ParallelRiskScorer**: Berechnet Risk Scores parallel auf allen Ranks
- **MPIAggregator**: Sammelt und validiert Ergebnisse von allen Ranks
- **Checkpointing**: Speichert Fortschritt für lange Läufe
- **Geospatial Aggregation**: Gruppiert Ergebnisse nach Regionen/Ländern

**Integration mit bestehendem System:**

- Nutzt `RiskScorer` aus `backend/risk_scoring.py`
- Liest aus `backend/database.py` (DatabaseManager)
- Speichert Ergebnisse in `data/hpc_results/`

### 2. OpenCV Risk Visualization (`backend/hpc/opencv_risk_processor.py`)

**Neue Datei für OpenCV-basierte Bildverarbeitung:**

- **RiskHeatmapGenerator**: Erstellt Heatmaps aus Risk Scores mit `cv2.applyColorMap`
- **RiskContourDetector**: Identifiziert Risiko-Konturen mit `cv2.findContours`
- **GeospatialRasterProcessor**: Verarbeitet geospatiale Raster-Daten
- **RiskSegmentation**: Segmentiert Karten nach Risk Levels mit `cv2.watershed` oder `cv2.grabCut`
- **OverlayGenerator**: Erstellt Overlays für Karten-Visualisierung

**Features:**

- Konvertiert Risk Scores zu Bild-Rastern (lat/lon → Pixel)
- Erstellt Farb-Heatmaps (Blau=Low, Rot=Critical)
- Identifiziert kritische Regionen durch Kontur-Analyse
- Generiert GeoJSON-Polygone aus Konturen für Karten

### 3. Country Context Agent System (`backend/agents/country_context_agent.py`)

**Neue Agenten-Klasse für Kontextraum-Generierung:**

- **CountryContextAgent**: Haupt-Agent pro Land
- **IPCCDataExtractor**: Extrahiert IPCC-spezifische Daten
- **WebDataExtractor**: Extrahiert allgemeine Web-Informationen
- **MultiModalContextBuilder**: Erstellt Kontexträume aus Text, Zahlen, Bildern

**Kontextraum-Struktur:**

```python
@dataclass
class CountryContextSpace:
    country_code: str
    country_name: str
    # IPCC-Daten
    ipcc_data: Dict[str, Any]  # Temperaturen, Niederschlag, etc.
    ipcc_findings: List[str]
    # Web-Daten
    web_text_data: List[str]  # Extrahiertes Text
    web_numerical_data: Dict[str, float]  # Zahlen
    web_images: List[str]  # Bild-URLs
    # Embeddings
    text_embeddings: np.ndarray  # OpenAI embeddings
    image_embeddings: np.ndarray  # CLIP embeddings
    numerical_features: np.ndarray  # Normalisierte Zahlen
    # Geospatial
    coordinates: Tuple[float, float]
    bounding_box: Dict[str, float]
```

**Integration:**

- Nutzt `IPCCEnrichmentAgent` aus `backend/ipcc_enrichment_agent.py`
- Nutzt `ImageProcessor` aus `backend/image_processing.py`
- Nutzt `FirecrawlEnricher` für Web-Extraktion
- Nutzt `NumberExtractor` für Zahlen-Extraktion

### 4. Batch Country Processing (`backend/agents/batch_country_processor.py`)

**Parallele Verarbeitung aller Länder:**

- Lädt Liste aller Länder (195 Länder)
- Verteilt Länder über Worker-Prozesse
- Führt `CountryContextAgent` für jedes Land aus
- Speichert Kontexträume in `data/country_contexts/`

**Parallelisierung:**

- Asyncio-basiert für I/O-bound Tasks (Web-Requests)
- Multiprocessing für CPU-bound Tasks (Embeddings)

### 5. Geospatial Mapping Integration (`backend/hpc/map_integration.py`)

**Integration mit bestehender Karten-Visualisierung:**

- **HPCResultMapper**: Mappt HPC-Ergebnisse auf bestehende Karten
- **OpenCVOverlayRenderer**: Rendert OpenCV-Overlays für Folium-Karten
- **ContextSpaceVisualizer**: Visualisiert Kontexträume auf Karten

**Erweitert:**

- `backend/world_map_visualization.py` für HPC-Ergebnisse
- `backend/web_app.py` für neue API-Endpunkte

**Neue API-Endpunkte:**

- `/api/hpc/results` - HPC-Berechnungsergebnisse
- `/api/hpc/heatmap` - OpenCV-generierte Heatmap
- `/api/country-contexts` - Länder-Kontexträume
- `/api/map/hpc-overlay` - OpenCV-Overlay für Karte

### 6. SLURM Job Scripts (`scripts/hpc/`)

**Job-Scripts für GSI Darmstadt:**

- `run_mpi_risk_prediction.sh` - MPI Risk Prediction Job
- `run_country_context_agents.sh` - Batch Country Processing
- `run_opencv_processing.sh` - OpenCV Bildverarbeitung

## Datenfluss

```
1. SQLite DB (Records)
   ↓
2. MPI Risk Prediction (HPC)
   → Verteilte Berechnung über Ranks
   → Aggregation & Validierung
   ↓
3. HPC Results (JSON/Parquet)
   ↓
4. OpenCV Processing
   → Heatmap-Generierung
   → Kontur-Erkennung
   → Segmentierung
   ↓
5. OpenCV Outputs (Images + GeoJSON)
   ↓
6. Country Context Agents (Parallel)
   → IPCC-Daten-Extraktion
   → Web-Daten-Extraktion
   → Multi-Modal Embeddings
   ↓
7. Country Context Spaces (JSON)
   ↓
8. Map Integration
   → Folium-Karten mit Overlays
   → Web-App Visualisierung
```

## Datei-Struktur

```
backend/
├── hpc/
│   ├── __init__.py
│   ├── mpi_risk_prediction.py      # MPI-basierte verteilte Berechnung
│   ├── opencv_risk_processor.py    # OpenCV Bildverarbeitung
│   └── map_integration.py          # Integration mit Karten
├── agents/
│   ├── __init__.py
│   ├── country_context_agent.py   # Haupt-Agent für Länder-Kontexträume
│   └── batch_country_processor.py # Batch-Verarbeitung aller Länder
scripts/
└── hpc/
    ├── run_mpi_risk_prediction.sh
    ├── run_country_context_agents.sh
    └── run_opencv_processing.sh
data/
├── hpc_results/                    # HPC-Berechnungsergebnisse
│   ├── mpi_scores_*.json
│   └── validation_report.json
├── opencv_outputs/                  # OpenCV-generierte Bilder
│   ├── heatmaps/
│   ├── contours/
│   └── overlays/
└── country_contexts/               # Länder-Kontexträume
    ├── {country_code}_context.json
    └── embeddings/
```

## Implementierungs-Schritte

### Phase 1: HPC MPI Risk Prediction

1. Erstelle `backend/hpc/mpi_risk_prediction.py`
2. Implementiere `DistributedDataManager` für Datenverteilung
3. Implementiere `ParallelRiskScorer` mit MPI
4. Implementiere `MPIAggregator` für Ergebnis-Sammlung
5. Erstelle SLURM Job-Script
6. Teste mit lokalem MPI (4-8 Ranks)

### Phase 2: OpenCV Risk Processing

1. Erstelle `backend/hpc/opencv_risk_processor.py`
2. Implementiere `RiskHeatmapGenerator`
3. Implementiere `RiskContourDetector`
4. Implementiere `GeospatialRasterProcessor`
5. Implementiere `RiskSegmentation`
6. Teste mit Beispiel-Risk-Scores

### Phase 3: Country Context Agents

1. Erstelle `backend/agents/country_context_agent.py`
2. Implementiere `CountryContextAgent` mit IPCC + Web-Extraktion
3. Implementiere `MultiModalContextBuilder`
4. Erstelle `backend/agents/batch_country_processor.py`
5. Teste mit einzelnen Ländern

### Phase 4: Map Integration

1. Erstelle `backend/hpc/map_integration.py`
2. Erweitere `backend/world_map_visualization.py` für HPC-Ergebnisse
3. Erweitere `backend/web_app.py` mit neuen API-Endpunkten
4. Integriere OpenCV-Overlays in Folium-Karten
5. Teste vollständige Visualisierung

## Abhängigkeiten

**Neue Pakete:**

- `mpi4py` - MPI für Python
- `opencv-python` - OpenCV für Bildverarbeitung
- `opencv-contrib-python` - Erweiterte OpenCV-Features (optional)

**Bestehende Pakete (bereits vorhanden):**

- `numpy` - Numerische Operationen
- `folium` - Karten-Visualisierung
- `PIL/Pillow` - Bild-Verarbeitung
- `asyncio` - Asynchrone Verarbeitung

## Validierung & Testing

1. **MPI Validation**: Prüfe auf Duplikate, konsistente Scores
2. **OpenCV Validation**: Vergleiche Heatmaps mit manuellen Checks
3. **Agent Validation**: Prüfe Kontextraum-Vollständigkeit pro Land
4. **Map Validation**: Teste Karten-Visualisierung mit echten Daten

## Performance-Ziele

- **MPI**: 10.000+ Records/Sekunde auf 128 Ranks
- **OpenCV**: Heatmap-Generierung < 1 Sekunde pro Region
- **Agents**: 195 Länder in < 2 Stunden (parallel)
- **Map Rendering**: Interaktive Karte lädt in < 3 Sekunden

### To-dos

- [ ] Erstelle backend/hpc/ Verzeichnis und mpi_risk_prediction.py mit DistributedDataManager, ParallelRiskScorer, MPIAggregator
- [ ] Erstelle opencv_risk_processor.py mit RiskHeatmapGenerator, RiskContourDetector, GeospatialRasterProcessor, RiskSegmentation
- [ ] Erstelle backend/agents/ Verzeichnis und country_context_agent.py mit CountryContextAgent, IPCCDataExtractor, WebDataExtractor, MultiModalContextBuilder
- [ ] Erstelle batch_country_processor.py für parallele Verarbeitung aller 195 Länder
- [ ] Erstelle map_integration.py und erweitere world_map_visualization.py sowie web_app.py für HPC-Ergebnisse und OpenCV-Overlays
- [ ] Erstelle SLURM Job-Scripts in scripts/hpc/ für GSI Darmstadt
- [ ] Implementiere Tests und Validierung für MPI, OpenCV, Agents und Map-Integration