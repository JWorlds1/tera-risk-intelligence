# Quick Start Guide: Information Retrieval Übung

## 1. Installation

```bash
# Installiere alle benötigten Pakete
pip install -r requirements.txt
```

## 2. Datensatz laden

### Option A: Mit Python-Skript
```bash
cd scripts
python 01_load_data.py
```

### Option B: Mit Jupyter Notebook
```bash
jupyter notebook notebooks/01_data_exploration.ipynb
```

Der Datensatz wird automatisch von HuggingFace heruntergeladen und im `data/` Verzeichnis gespeichert.

## 3. TF-IDF basiertes IR-System

### Mit Python-Skript
```bash
cd scripts
python 02_tfidf_ir.py
```

### Mit Jupyter Notebook
```bash
jupyter notebook notebooks/02_tfidf_analysis.ipynb
```

## 4. ChromaDB und Embeddings

### Mit Python-Skript
```bash
cd scripts
python 03_chromadb_ir.py
```

### Mit Jupyter Notebook
```bash
jupyter notebook notebooks/03_chromadb_analysis.ipynb
```

## Projektstruktur

```
information_retrieval_exercise/
├── README.md                 # Hauptdokumentation
├── QUICKSTART.md             # Diese Datei
├── requirements.txt          # Python-Abhängigkeiten
├── .gitignore               # Git-Ignore-Regeln
├── notebooks/               # Jupyter Notebooks
│   ├── 01_data_exploration.ipynb
│   ├── 02_tfidf_analysis.ipynb
│   └── 03_chromadb_analysis.ipynb
├── scripts/                 # Python-Skripte
│   ├── 01_load_data.py
│   ├── 02_tfidf_ir.py
│   ├── 03_chromadb_ir.py
│   └── create_notebooks.py
├── data/                    # Datenverzeichnis (wird erstellt)
│   ├── tagesschau_2023_prepared.csv
│   ├── chromadb/           # ChromaDB Datenbank
│   └── tfidf_model.pkl     # Gespeichertes TF-IDF Modell
└── results/                 # Ergebnisse und Visualisierungen
```

## Wichtige Hinweise

1. **Erster Durchlauf**: Beim ersten Ausführen werden die Daten von HuggingFace heruntergeladen. Dies kann einige Minuten dauern.

2. **ChromaDB**: Die ChromaDB-Datenbank wird im `data/chromadb/` Verzeichnis gespeichert und bleibt zwischen den Ausführungen erhalten.

3. **Embedding-Modelle**: Beim ersten Verwenden von Sentence Transformers werden die Modelle automatisch heruntergeladen (~100-500 MB).

4. **Speicher**: Für große Datensätze kann viel RAM benötigt werden. Bei Problemen reduzieren Sie die Anzahl der Dokumente in den Skripten.

## Übungsaufgaben

Folgen Sie den Anweisungen in den Notebooks:

1. **Datenexploration**: Verstehen Sie die Struktur des Datensatzes
2. **TF-IDF**: Implementieren und analysieren Sie ein TF-IDF basiertes IR-System
3. **ChromaDB**: Arbeiten Sie mit ChromaDB und vergleichen Sie verschiedene Embedding-Modelle

## Hilfe

Bei Problemen:
- Überprüfen Sie, ob alle Pakete installiert sind: `pip list`
- Stellen Sie sicher, dass Sie eine Internetverbindung haben (für HuggingFace Downloads)
- Prüfen Sie die Logs auf Fehlermeldungen

