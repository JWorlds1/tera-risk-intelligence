# 🧠 Multi-Modal Vektorraum Strategie

## 🎯 Ziel
Vektorraum für Geodaten-Prognose mit:
- **Text** (Artikel, Beschreibungen)
- **Zahlen** (Temperaturen, Niederschlag, etc.)
- **Bilder** (Satellitenbilder, Karten, Fotos)
- **Geodaten** (Koordinaten, Polygone, Bounding Boxes)

## 📊 Vektorraum-Architektur

### 1. Multi-Modal Chunks

Jeder Chunk enthält:
```python
MultiModalChunk(
    chunk_id: str,
    city: str,
    coordinates: (lat, lon),
    
    # Text-Embedding (OpenAI text-embedding-3-large: 1536 dim)
    text_embedding: np.ndarray[1536],
    
    # Numerische Embedding (normalisierte Werte: 128 dim)
    numerical_embedding: np.ndarray[128],
    
    # Bild-Embeddings (CLIP ViT-B/32: 512 dim)
    image_embeddings: List[np.ndarray[512]],
    
    # Geospatial-Embedding (Koordinaten + Features: 64 dim)
    geospatial_embedding: np.ndarray[64]
)
```

### 2. Ähnlichkeitsmetriken

#### Text-Ähnlichkeit
- **Cosine Similarity** für Text-Embeddings
- Normalisierte Vektoren (L2-Norm = 1)
- Range: [-1, 1] → [0, 1] für Similarity

#### Numerische Ähnlichkeit
- **Skalierte Euklidische Distanz**
- Normalisiert nach Wert-Typ:
  - Temperaturen: Skala 10°C
  - Niederschlag: Skala 100mm
  - Bevölkerung: Logarithmische Skala

#### Bild-Ähnlichkeit
- **CLIP Cosine Similarity**
- Vergleich aller Bild-Paare
- Durchschnitt über alle Paare

#### Geospatiale Ähnlichkeit
- **Haversine-Distanz** (km)
- Exponential-Decay: `exp(-distance/threshold)`
- Threshold: 100km für Städte

#### Kombinierte Multi-Modal Ähnlichkeit
```python
similarity = (
    w_text * text_sim +
    w_numerical * numerical_sim +
    w_image * image_sim +
    w_geospatial * geospatial_sim
) / (w_text + w_numerical + w_image + w_geospatial)
```

**Gewichtungen:**
- Text: 0.3
- Numerical: 0.2
- Image: 0.2
- Geospatial: 0.3

### 3. Ranking-Strategien

#### 1. Ähnlichkeits-Ranking
- Sortiere nach kombinierter Multi-Modal Similarity
- Top-K Ergebnisse (z.B. Top 10)

#### 2. Geografisches Ranking
- Filter nach Radius (z.B. 50km)
- Sortiere nach geografischer Nähe

#### 3. Zeitliches Ranking
- Gewichte neuere Daten höher
- Exponential-Decay: `exp(-age_days/30)`

#### 4. Confidence-Ranking
- Gewichte Daten mit höherer Confidence
- Kombiniere mit Ähnlichkeit

### 4. Vektor-DB Implementierung

#### Option 1: ChromaDB (Empfohlen)
```python
import chromadb
from chromadb.config import Settings

client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./data/chroma_db"
))

# Collection für Multi-Modal Daten
collection = client.create_collection(
    name="geospatial_chunks",
    metadata={"hnsw:space": "cosine"}
)
```

#### Option 2: Qdrant
- Bessere Performance für große Datenmengen
- Native Multi-Vector Support
- Geospatiale Indizes

#### Option 3: Pinecone
- Managed Service
- Einfache Integration
- Kostenpflichtig

## 🔄 Agenten-Orchestrierung

### Sequenzielle Phasen (basierend auf fire-enrich)

```
Phase 1: DISCOVERY
  ↓ (URLs, Grundinfos)
Phase 2: CRAWL
  ↓ (Daten + Bilder)
Phase 3: ENRICH
  ↓ (Zahlen, IPCC-Daten)
Phase 4: UPDATE
  ↓ (Datenbank-Update)
Phase 5: PREDICT
  ↓ (Risiko-Prognosen)
Phase 6: SEARCH
  ↓ (Vektorraum-Suche)
```

### Agenten-Details

#### 1. DiscoveryAgent
- **Input**: Stadt-Name, Koordinaten
- **Output**: URLs, Grundinfos
- **Tools**: Crawl4AI
- **Dependencies**: keine

#### 2. CrawlAgent
- **Input**: URLs von DiscoveryAgent
- **Output**: Gecrawlte Daten + Bilder
- **Tools**: Crawl4AI, Image Download
- **Dependencies**: DISCOVERY

#### 3. EnrichAgent
- **Input**: Gecrawlte Daten
- **Output**: Zahlen, IPCC-Daten, strukturierte Daten
- **Tools**: Firecrawl, NumberExtractor
- **Dependencies**: CRAWL

#### 4. UpdateAgent
- **Input**: Angereicherte Daten
- **Output**: Aktualisierte Datenbank-Records
- **Tools**: DatabaseManager
- **Dependencies**: ENRICH

#### 5. PredictAgent
- **Input**: Angereicherte Daten
- **Output**: Risiko-Prognosen
- **Tools**: RiskScorer, LLM
- **Dependencies**: ENRICH

#### 6. SearchAgent
- **Input**: Query-Chunk
- **Output**: Ähnliche Chunks aus Vektorraum
- **Tools**: MultiModalVectorSpace
- **Dependencies**: ENRICH

## 🖼️ Bild-Integration

### Bild-Quellen
1. **Satellitenbilder** (NASA, Copernicus)
2. **Karten** (OpenStreetMap, Google Maps)
3. **Fotos** (News-Artikel, Social Media)
4. **Visualisierungen** (Klima-Karten, Heatmaps)

### Bild-Verarbeitung
1. **Download** von URLs
2. **CLIP-Embedding** Extraktion
3. **Geospatiale Features** aus EXIF
4. **Normalisierung** für Vektorraum

### CLIP-Modell
- **Modell**: ViT-B/32 (OpenAI CLIP)
- **Embedding-Dimension**: 512
- **Verwendung**: Bild-zu-Bild und Bild-zu-Text Similarity

## 📈 Ranking & Retrieval

### Retrieval-Strategien

#### 1. Hybrid Search
- Kombiniere Keyword-Suche + Vektor-Suche
- BM25 für Keywords + Cosine für Embeddings

#### 2. Re-Ranking
- Erste Phase: Vektor-Suche (Top 100)
- Zweite Phase: Multi-Modal Re-Ranking (Top 10)

#### 3. Filtered Search
- Geografischer Filter (Radius)
- Zeitlicher Filter (Datum-Range)
- Confidence-Filter (min. Confidence)

### Ranking-Faktoren

1. **Ähnlichkeit** (Multi-Modal): 40%
2. **Geografische Nähe**: 20%
3. **Aktualität**: 20%
4. **Confidence**: 10%
5. **Datenqualität**: 10%

## 🚀 Implementierungs-Plan

### Phase 1: Basis-Vektorraum ✅
- [x] MultiModalChunk Datastruktur
- [x] SimilarityMetrics
- [x] MultiModalVectorSpace Klasse

### Phase 2: Bild-Integration
- [ ] CLIP-Installation
- [ ] ImageProcessor
- [ ] Bild-Embedding Extraktion

### Phase 3: Agenten-Orchestrierung
- [x] BaseAgent Interface
- [x] Sequenzielle Agenten
- [x] AgentOrchestrator

### Phase 4: Vektor-DB Integration
- [ ] ChromaDB Setup
- [ ] Multi-Modal Indizierung
- [ ] Retrieval-Implementierung

### Phase 5: Testing & Optimierung
- [ ] Ähnlichkeitsmetriken testen
- [ ] Ranking optimieren
- [ ] Performance-Tuning

## 💡 Best Practices

1. **Embedding-Normalisierung**: Immer L2-normalisieren für Cosine Similarity
2. **Batch-Processing**: Verarbeite Bilder in Batches
3. **Caching**: Cache Embeddings für wiederholte Queries
4. **Inkrementelles Update**: Füge neue Chunks hinzu ohne Re-Indexierung
5. **Monitoring**: Track Similarity-Scores und Retrieval-Qualität

## 📚 Referenzen

- [fire-enrich Architecture](https://github.com/firecrawl/fire-enrich)
- [CLIP Paper](https://arxiv.org/abs/2103.00020)
- [ChromaDB Documentation](https://docs.trychroma.com)
- [Multi-Modal Retrieval](https://www.pinecone.io/learn/multi-modal-search/)



