# Information Retrieval Übung: Tagesschau-Datensatz

Diese Übung beschäftigt sich mit Information Retrieval (IR) Techniken am Beispiel des "awesome-tagesschau" Datensatzes.

## Vorbereitung

### 1. Datensatz laden
Der Datensatz "awesome-tagesschau" für das Jahr 2023 kann von HuggingFace heruntergeladen werden:
- URL: https://huggingface.co/datasets/stefan-it/awesome-tagesschau

### 2. Pakete installieren
```bash
pip install -r requirements.txt
```

Benötigte Pakete:
- pandas
- scikit-learn
- chromadb
- sentence-transformers
- beautifulsoup4
- lxml
- datasets (für HuggingFace Datasets)
- jupyter (für Notebooks)

## Übungsstruktur

### Teil 1: Kosinus-Ähnlichkeit auf TF-IDF
- Verwendung von `TfidfVectorizer` und `cosine_similarity` aus scikit-learn
- Verständnis der TF-IDF Berechnung
- Evaluierung des IR-Systems

### Teil 2: ChromaDB und Embedding-Modelle
- Einführung in ChromaDB
- Vergleich verschiedener Embedding-Modelle
- Analyse der Ergebnisse

## Dateien

- `notebooks/` - Jupyter Notebooks für die Übung
- `scripts/` - Python-Skripte für Datenverarbeitung
- `data/` - Lokale Datenspeicherung (optional)
- `results/` - Ergebnisse und Visualisierungen

