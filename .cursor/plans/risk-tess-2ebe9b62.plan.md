---
name: Erweitertes Risiko-Tessellations- und Mapping-System
overview: ""
todos:
  - id: 8c83012b-eb81-4b63-a6e9-30e49c7cced0
    content: Erweiterte Risiko-Taxonomie im ContextTensor definieren (mcp_maps_server.ts)
    status: pending
  - id: 63970990-9aa6-43a4-8c80-013d072c7b62
    content: Prozedural-adaptive generateRiskProfile() Funktion implementieren
    status: pending
  - id: b3501d0f-5087-40a5-8c52-6664b4f86b90
    content: Neue geometry_transforms.ts mit Form-Modifikationen pro Risikotyp
    status: pending
  - id: 3da6267c-1ed7-4503-8e38-934d65452ba3
    content: Risikotyp-spezifische Farbpaletten in color_math.ts
    status: pending
  - id: 380f3859-06be-4a85-a568-1718ee811673
    content: Risikotyp-spezifische Animationen in animation_engine.ts
    status: pending
  - id: 2c9457b3-2b89-4a9f-bdb5-bf7c059c1dd9
    content: Multi-Layer-System fuer ueberlagerte Risiken in map_app.ts
    status: pending
  - id: 681e8afc-988f-4878-af96-b32ab6ae8e16
    content: Dynamische Farblegende und erweitertes Zonen-Panel
    status: pending
  - id: 2a8d6af4-fed8-4736-8806-3b6d071167ec
    content: "ML-Pipeline-Integration: Prithvi/Chronos fuer Backend-Prediktion"
    status: pending
  - id: 4e2f0098-ccf7-4356-9c07-04854427d7b8
    content: LoRA Fine-Tuning Setup fuer lokale Modelle (Ollama/Axolotl)
    status: pending
  - id: 3ac463a6-299b-4caa-8f4c-06c5c926f14b
    content: "Backend physical_models.py: ERA5, OpenQuake, Aqueduct Integration"
    status: pending
  - id: f55fad42-0d1a-46c9-a0f9-8dcf9ea2e625
    content: "Harmonisierungs-Layer: Physik-Modelle zu H3-Tensor Mapping"
    status: pending
  - id: d3c5de77-8c93-4bf5-865c-29094ac1200f
    content: LLM-Schnittstelle fuer Modell-Erklaerung und Interpretation
    status: pending
---

# Erweitertes Risiko-Tessellations- und Mapping-System

## Architektur-Uebersicht

Das System erweitert die bestehende H3-Hexagonal-Visualisierung um eine **multi-dimensionale Risiko-Taxonomie** mit geometrisch differenzierten Darstellungen. Die Kernidee: Jeder Risikotyp hat eine eigene "visuelle Signatur" durch Kombination von Farbe, Hoehe, Form und Animation.

---

## Phase 1: Risiko-Taxonomie-Engine (Server)

**Datei:** [`mcp_maps_server.ts`](tera/tera---geospatial/mcp_maps_server.ts)

### 1.1 Erweitertes ContextTensor Interface

```typescript
interface RiskCategory {
  type: 'seismic' | 'tsunami' | 'coastal_flood' | 'urban_flood' | 
        'drought' | 'conflict' | 'heat' | 'storm' | 'stable';
  intensity: number;  // 0-100
  confidence: number; // 0-1 (Unsicherheit)
  subtype?: string;   // z.B. "fault_proximity", "liquefaction"
}

interface ExtendedContextTensor extends ContextTensor {
  riskCategories: RiskCategory[];
  dominantRisk: RiskCategory;
  zoneClassification: string; // z.B. "FAULT_PROXIMITY", "TSUNAMI_ZONE"
}
```

### 1.2 Prozedural-Adaptive Risiko-Generierung

Neue Funktion `generateRiskProfile()` die basierend auf:

- Geographische Lage (Kuestennaehe = Tsunami/Coastal Flood)
- Tektonische Zonen (Noise-basierte Fault Lines)
- Terrain (Elevation = Amplification-Risk)
- Urban Density (Urban Flood, Heat Island)

---

## Phase 2: Geometrische Visualisierungs-Engine (Client)

**Dateien:** [`map_app.ts`](tera/tera---geospatial/map_app.ts), neue Datei `geometry_transforms.ts`

### 2.1 Risikotyp zu Geometrie Mapping

| Risikotyp | Farbe | Hoehe-Formel | Form-Modifikation |

|-----------|-------|--------------|-------------------|

| Seismisch (Fault) | Rot-Violett | Sehr hoch (300-500m) | Gezackte Kanten |

| Seismisch (Liquefaction) | Orange | Mittel (150-250m) | Wellige Oberflaeche |

| Tsunami | Cyan-Blau | Niedrig-Mittel | Gestreckte Hexagone zur Kueste |

| Coastal Flood | Dunkelblau | Sehr niedrig | Flach, transparent |

| Urban Flood | Tuerkis | Mittel | Standard Hexagon |

| Duerre | Braun-Gelb | Niedrig | Risse/Segmentierung |

| Konflikt | Rot-Schwarz | Hoch, pulsierend | Standard |

| Stabil | Gruen | Minimal | Standard Hexagon |

### 2.2 Layer-System

```typescript
type LayerMode = 'composite' | 'seismic' | 'climate' | 'conflict' | 
                 'vulnerability' | 'single_risk';
```

Implementierung von gestapelten transparenten Layern wenn mehrere Risiken auf einem Hexagon liegen.

---

## Phase 3: Farb- und Animations-System

**Dateien:** [`color_math.ts`](tera/tera---geospatial/color_math.ts), [`animation_engine.ts`](tera/tera---geospatial/neue_visuell/animation_engine.ts)

### 3.1 Risikotyp-Farbpaletten

```typescript
const RISK_PALETTES: Record<RiskType, ColorPalette> = {
  seismic: { low: '#FED976', mid: '#FD8D3C', high: '#BD0026' },
  tsunami: { low: '#9ECAE1', mid: '#4292C6', high: '#084594' },
  coastal_flood: { low: '#C7E9C0', mid: '#41AB5D', high: '#006D2C' },
  drought: { low: '#FFFFB2', mid: '#FEB24C', high: '#8B4513' },
  conflict: { low: '#FBB4AE', mid: '#E31A1C', high: '#67000D' }
};
```

### 3.2 Animations-Differenzierung

- **Seismisch**: Vibrierende/Pulsierende Animation
- **Tsunami**: Wellenartige Ausbreitung von der Kueste
- **Duerre**: Langsames Verblassen/Austrocknen
- **Konflikt**: Schnelles Pulsieren

---

## Phase 4: UI-Erweiterungen

**Datei:** [`map_app.ts`](tera/tera---geospatial/map_app.ts), [`index.css`](tera/tera---geospatial/index.css)

### 4.1 Erweiterte Legende

Dynamische Farblegende basierend auf aktiven Risikotypen in der aktuellen Analyse.

### 4.2 Zonen-Panel

Erweiterung des Cell-Inspection-Panels um:

- Alle aktiven Risikokategorien der Zelle
- Konfidenz-Indikatoren
- Empfohlene Handlungen pro Risikotyp

---

## Implementierungs-Reihenfolge

1. **Server**: Erweiterte Risiko-Taxonomie und Tensor-Generierung
2. **Geometrie**: Neue `geometry_transforms.ts` mit Form-Modifikationen
3. **Farben**: Erweiterung von `color_math.ts` mit Risiko-Paletten
4. **Animation**: Risikotyp-spezifische Animationen
5. **UI**: Legende, Panel-Erweiterungen, Layer-Controls

---

## Technische Entscheidungen

- **H3 vs. Custom Hexagons**: Beibehaltung der echten H3-Library fuer stabile Geometrie
- **Deformation**: WebGL-Shader fuer komplexe Formtransformationen (optional)
- **Performance**: Batch-Rendering und Level-of-Detail fuer grosse Grids

---

## Phase 5: Lokale ML-Modelle fuer Risiko-Prediktion

Fuer die numerische Risiko-Vorhersage sind klassische LLMs nicht ideal. Stattdessen gibt es spezialisierte Modelle:

### 5.1 Geospatiale Foundation Models

| Modell | Beschreibung | Use Case | Lokal? |

|--------|--------------|----------|--------|

| **Prithvi (IBM/NASA)** | 100M Parameter, vortrainiert auf HLS Sentinel-2 Daten | Flood Mapping, Wildfire Scars, Crop Classification | Ja, HuggingFace |

| **ClimaX (Microsoft)** | Foundation Model fuer Wetter/Klima | Temperatur, Niederschlag, Extremereignisse | Ja, Open Source |

| **SatCLIP** | Kontrastives Lernen auf Satellitendaten | Geospatiale Embeddings | Ja |

### 5.2 Time Series Foundation Models

| Modell | Beschreibung | Use Case | Lokal? |

|--------|--------------|----------|--------|

| **Chronos (Amazon)** | T5-basiert, Zero-Shot Forecasting | Zeitreihen-Prognose ohne Fine-Tuning | Ja, HuggingFace |

| **TimesFM (Google)** | 200M Parameter, pretrained auf 100B Zeitpunkte | Langzeit-Prognosen | Ja, Open Source |

| **Lag-Llama** | Decoder-only LLM fuer Zeitreihen | Probabilistische Forecasts | Ja |

### 5.3 Tabular/Risk-Specific Models

| Modell | Beschreibung | Use Case | Lokal? |

|--------|--------------|----------|--------|

| **TabPFN** | Prior-Data Fitted Network | Tabular Prediction ohne Training | Ja, sehr klein |

| **TabDDPM** | Diffusion fuer Tabellendaten | Synthetische Risikodaten-Generierung | Ja |

| **FinDiff** | Finanzdaten-Diffusion | Stress Testing, Szenario-Modellierung | Ja |

| **XGBoost/LightGBM** | Gradient Boosting | Klassisches Risk Scoring | Ja, sehr schnell |

### 5.4 Diffusion Models fuer Probabilistische Risiko-Vorhersage

| Modell | Staerke | Schwaeche |

|--------|---------|-----------|

| **Diffolio** | Multivariate Korrelationen, Portfolio-Risk | Finanz-fokussiert |

| **TimeGrad** | Zeitreihen-Diffusion | Rechenintensiv |

| **CSDI** | Conditional Score-based Diffusion | Imputation + Forecasting |

### 5.5 Empfohlene Architektur fuer dein Projekt

```
┌─────────────────────────────────────────────────────────────┐
│                    RISIKO-PREDIKTION PIPELINE               │
├─────────────────────────────────────────────────────────────┤
│  1. Geospatiale Features    │  Prithvi / SatCLIP            │
│     (Satellit, Terrain)     │  → Embeddings extrahieren     │
├─────────────────────────────────────────────────────────────┤
│  2. Klima-Zeitreihen        │  Chronos / TimesFM            │
│     (Temperatur, Precip)    │  → Prognose 2030-2050         │
├─────────────────────────────────────────────────────────────┤
│  3. Risk Fusion             │  XGBoost / TabPFN             │
│     (Alle Features)         │  → Finaler Risk Score 0-100   │
├─────────────────────────────────────────────────────────────┤
│  4. Unsicherheits-          │  TabDDPM / Diffolio           │
│     Quantifizierung         │  → Konfidenzintervalle        │
└─────────────────────────────────────────────────────────────┘
```

### 5.6 Fine-Tuning Strategie

- **LoRA (Low-Rank Adaptation)**: Reduziert Fine-Tuning-Kosten um 70%
- **Axolotl**: Open-Source Toolkit fuer LLM Fine-Tuning
- **Ollama**: Lokale Ausfuehrung von Llama, Mistral, Gemma
- **PEFT (Parameter-Efficient Fine-Tuning)**: Fuer kleine Datensaetze

### 5.7 Hardware-Anforderungen

| Modell-Groesse | Min. VRAM | Empfohlen |

|----------------|-----------|-----------|

| TabPFN (klein) | 4 GB | CPU genuegt |

| Chronos-Base | 8 GB | RTX 3060 |

| Prithvi | 16 GB | RTX 4080 |

| TimesFM | 24 GB | RTX 4090 / A100 |

---

## Phase 6: Physikalische und Geografische Modelle

Integration von wissenschaftlich validierten physikalischen Modellen die geografische Dynamik erfassen und mit der LLM-Schnittstelle sowie Visualisierung verlinkt sind.

### 6.1 Klimamodelle und Datenquellen

| Modell/Quelle | Beschreibung | API/Zugang | Daten |

|---------------|--------------|------------|-------|

| **ERA5 (Copernicus)** | Klima-Reanalyse 1940-heute | CDS API (Python) | Temp, Precip, Wind, Pressure |

| **CMIP6** | Klimaprojektionen bis 2100 | ESGF, CDS | SSP1-5 Szenarien |

| **WorldClim 2.1** | Hochaufgeloeste Klimadaten | Direct Download | 1km Raster, historisch |

| **CHIRPS** | Precipitation-Daten | API | Taegliche Niederschlagsdaten |

### 6.2 Seismische Modelle

| Modell | Organisation | Beschreibung | Open Source? |

|--------|--------------|--------------|--------------|

| **OpenQuake** | GEM Foundation | Probabilistische seismische Hazard-Analyse | Ja, Python |

| **USGS ShakeMap** | USGS | Echtzeit-Erschuetterungskarten | API verfuegbar |

| **GFZ SHARE** | GFZ Potsdam | Europaeische seismische Gefaehrdung | Ja |

| **Global Seismic Hazard Map** | GSHAP | Globale PGA-Werte | Download |

### 6.3 Hydrologische Modelle

| Modell | Beschreibung | Use Case | API? |

|--------|--------------|----------|------|

| **GLOFRIS** | Global Flood Risk with IMAGE Scenarios | Fluviale Ueberflutung | WRI Aqueduct |

| **Aqueduct Floods** | WRI Global Flood Analyzer | Kuestenflut + River Flood | REST API |

| **PCR-GLOBWB** | Global Hydrological Model | Wasserbilanz, Duerre | Open Source |

| **CoSMoS** | Coastal Storm Modeling System | Sturmflut-Simulation | USGS |

### 6.4 Geologische und Tektonische Modelle

| Modell | Beschreibung | Daten |

|--------|--------------|-------|

| **GEM Active Faults** | Globale Stoerungszonen-Datenbank | Fault Lines, Slip Rates |

| **GEBCO** | Bathymetrie und Topographie | Ozean-/Landoberflaeche |

| **SRTM/ASTER DEM** | Digitales Hoehenmodell | 30m Aufloesung global |

| **NASA SEDAC** | Socioeconomic Data | Population, GDP, Infrastructure |

### 6.5 Modell-zu-Tensor Mapping Architektur

```
┌─────────────────────────────────────────────────────────────────────┐
│                 PHYSIKALISCHE MODELL-INTEGRATION                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │   ERA5      │    │  OpenQuake  │    │  Aqueduct   │             │
│  │   Klima     │    │  Seismik    │    │  Flood      │             │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘             │
│         │                  │                  │                     │
│         ▼                  ▼                  ▼                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              HARMONISIERUNGS-LAYER                          │   │
│  │  - Einheitliche Koordinaten (H3 Index)                      │   │
│  │  - Normalisierung 0-100                                     │   │
│  │  - Zeitliche Aggregation (Jahrzehnte)                       │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             │                                       │
│                             ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              CONTEXT TENSOR GENERATOR                        │   │
│  │  - Physik → dimensions.climate/geography                    │   │
│  │  - Seismik → riskCategories.seismic                         │   │
│  │  - Hydro → riskCategories.flood/coastal                     │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             │                                       │
│                             ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              LLM INTERPRETATION LAYER                        │   │
│  │  - Tensor → Natuerlichsprachliche Erklaerung                │   │
│  │  - Unsicherheits-Kommunikation                              │   │
│  │  - Handlungsempfehlungen                                    │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             │                                       │
│                             ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              VISUALISIERUNGS-ENGINE                          │   │
│  │  - Tensor → Geometrie (Hoehe, Form)                         │   │
│  │  - RiskCategory → Farbe + Animation                         │   │
│  │  - Konfidenz → Transparenz                                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.6 Backend API Endpunkte (Neu)

Neue Datei: `backend/services/physical_models.py`

```python
class PhysicalModelService:
    async def get_climate_data(self, lat, lng, scenario, year):
        # ERA5 + CMIP6 Fusion
        pass
    
    async def get_seismic_hazard(self, lat, lng):
        # OpenQuake PGA Abfrage
        pass
    
    async def get_flood_risk(self, lat, lng, return_period):
        # Aqueduct API
        pass
    
    async def harmonize_to_tensor(self, h3_index):
        # Alle Modelle zu ContextTensor
        pass
```

### 6.7 LLM-Schnittstelle fuer Modell-Erklaerung

```typescript
// Erweiterung mcp_maps_server.ts
interface ModelExplanation {
  physicalBasis: string;      // "Basierend auf CMIP6 SSP2-4.5..."
  dataSource: string[];       // ["ERA5", "OpenQuake", "Aqueduct"]
  confidence: number;         // 0-1
  lastUpdate: Date;
  scientificReference: string; // "IPCC AR6 WG1 Ch.4"
}
```

### 6.8 Animations-Mapping pro Physikalischem Prozess

| Physikalischer Prozess | Animation | Dauer | Trigger |

|------------------------|-----------|-------|---------|

| Seismische Welle | Radiale Ausbreitung vom Epizentrum | 3-5s | Click auf Fault |

| Tsunami | Wellenfront von Kueste landeinwaerts | 5-8s | Click auf Tsunami-Zone |

| Sturmflut | Steigende Wasserhoehe (Polygone senken) | 4-6s | Layer-Wechsel |

| Hitze-Insel | Pulsierendes Rot im Stadtzentrum | Loop | Urban-Layer aktiv |

| Duerre-Ausbreitung | Farbverlauf Gruen→Braun | 3s | Drought-Layer |

### 6.9 Daten-Pipeline (Offline-Faehig)

```
1. PRE-COMPUTE (Naechtlich/Woechentlich):
   - ERA5 Daten fuer alle Zielregionen cachen
   - OpenQuake Hazard Maps vorberechnen
   - Aqueduct Flood Maps speichern

2. RUNTIME:
   - H3-Index → Cache-Lookup
   - Falls nicht gecached → Fallback auf prozedurale Generierung
   - LLM interpretiert Tensor + generiert Erklaerung

3. USER-TRIGGERED:
   - Detailabfrage → Live-API-Call (optional)
   - Historische Analyse → Zeitreihen-Abruf
```