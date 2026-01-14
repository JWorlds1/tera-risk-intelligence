"""
Hilfsskript zum Erstellen der Jupyter Notebooks
"""
import json
from pathlib import Path

def create_tfidf_notebook():
    """Erstellt das TF-IDF Analyse Notebook"""
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# TF-IDF Analyse und Information Retrieval\n",
                    "\n",
                    "In diesem Notebook implementieren wir ein TF-IDF basiertes IR-System und analysieren dessen Funktionsweise."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import pandas as pd\n",
                    "import numpy as np\n",
                    "from sklearn.feature_extraction.text import TfidfVectorizer\n",
                    "from sklearn.metrics.pairwise import cosine_similarity\n",
                    "import matplotlib.pyplot as plt\n",
                    "import seaborn as sns\n",
                    "from pathlib import Path\n",
                    "\n",
                    "sns.set_style(\"whitegrid\")"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 1. Daten laden"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "data_dir = Path('../data')\n",
                    "csv_path = data_dir / 'tagesschau_2023_prepared.csv'\n",
                    "\n",
                    "df = pd.read_csv(csv_path)\n",
                    "print(f\"Geladene Artikel: {len(df)}\")\n",
                    "\n",
                    "# Identifiziere Text-Spalte\n",
                    "text_column = None\n",
                    "for col in ['text', 'content', 'article', 'body']:\n",
                    "    if col in df.columns:\n",
                    "        text_column = col\n",
                    "        break\n",
                    "\n",
                    "if text_column is None:\n",
                    "    text_column = df.columns[0]\n",
                    "\n",
                    "documents = df[text_column].dropna().tolist()\n",
                    "print(f\"Verwendete Text-Spalte: {text_column}\")\n",
                    "print(f\"Anzahl Dokumente: {len(documents)}\")"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 2. TF-IDF Vectorizer initialisieren\n",
                    "\n",
                    "### Verständnisfragen:\n",
                    "1. Was bedeutet `fit_transform`?\n",
                    "2. Wie wird TF-IDF in scikit-learn berechnet?\n",
                    "3. Welche Normalisierungsoptionen gibt es?"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Initialisiere TF-IDF Vectorizer\n",
                    "vectorizer = TfidfVectorizer(\n",
                    "    max_features=10000,\n",
                    "    ngram_range=(1, 2),\n",
                    "    min_df=2,\n",
                    "    max_df=0.95,\n",
                    "    norm='l2',\n",
                    "    use_idf=True,\n",
                    "    smooth_idf=True,\n",
                    "    sublinear_tf=False,\n",
                    "    lowercase=True,\n",
                    "    stop_words=None\n",
                    ")\n",
                    "\n",
                    "print(\"TF-IDF Vectorizer Parameter:\")\n",
                    "print(f\"  max_features: {vectorizer.max_features}\")\n",
                    "print(f\"  ngram_range: {vectorizer.ngram_range}\")\n",
                    "print(f\"  min_df: {vectorizer.min_df}\")\n",
                    "print(f\"  max_df: {vectorizer.max_df}\")\n",
                    "print(f\"  norm: {vectorizer.norm}\")\n",
                    "print(f\"  use_idf: {vectorizer.use_idf}\")"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 3. TF-IDF Matrix berechnen\n",
                    "\n",
                    "### Was passiert bei `fit_transform`?\n",
                    "- **fit**: Lernt das Vokabular aus allen Dokumenten und berechnet IDF-Werte\n",
                    "- **transform**: Wendet die gelernten Transformationen an und erstellt TF-IDF Vektoren"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Berechne TF-IDF Matrix\n",
                    "print(\"Berechne TF-IDF Matrix...\")\n",
                    "tfidf_matrix = vectorizer.fit_transform(documents)\n",
                    "\n",
                    "print(f\"\\nTF-IDF Matrix Shape: {tfidf_matrix.shape}\")\n",
                    "print(f\"  Anzahl Dokumente: {tfidf_matrix.shape[0]}\")\n",
                    "print(f\"  Anzahl Features: {tfidf_matrix.shape[1]}\")\n",
                    "print(f\"  Matrix-Dichte: {tfidf_matrix.nnz / (tfidf_matrix.shape[0] * tfidf_matrix.shape[1]):.4f}\")\n",
                    "\n",
                    "# Zeige Feature-Namen\n",
                    "feature_names = vectorizer.get_feature_names_out()\n",
                    "print(f\"\\nErste 20 Features: {feature_names[:20].tolist()}\")"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 4. IDF-Werte analysieren"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Zeige IDF-Werte\n",
                    "idf_values = vectorizer.idf_\n",
                    "\n",
                    "print(f\"IDF-Werte:\")\n",
                    "print(f\"  Min: {idf_values.min():.4f}\")\n",
                    "print(f\"  Max: {idf_values.max():.4f}\")\n",
                    "print(f\"  Mean: {idf_values.mean():.4f}\")\n",
                    "print(f\"  Median: {np.median(idf_values):.4f}\")\n",
                    "\n",
                    "# Top Features nach IDF (seltene Wörter)\n",
                    "top_idf_indices = np.argsort(idf_values)[-20:][::-1]\n",
                    "print(f\"\\nTop 20 Features nach IDF (seltene Wörter):\")\n",
                    "for idx in top_idf_indices:\n",
                    "    print(f\"  {feature_names[idx]}: {idf_values[idx]:.4f}\")\n",
                    "\n",
                    "# Bottom Features nach IDF (häufige Wörter)\n",
                    "bottom_idf_indices = np.argsort(idf_values)[:20]\n",
                    "print(f\"\\nBottom 20 Features nach IDF (häufige Wörter):\")\n",
                    "for idx in bottom_idf_indices:\n",
                    "    print(f\"  {feature_names[idx]}: {idf_values[idx]:.4f}\")"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 5. Visualisierung der IDF-Verteilung"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "plt.figure(figsize=(12, 5))\n",
                    "\n",
                    "plt.subplot(1, 2, 1)\n",
                    "plt.hist(idf_values, bins=50, edgecolor='black')\n",
                    "plt.xlabel('IDF-Wert')\n",
                    "plt.ylabel('Anzahl Features')\n",
                    "plt.title('Verteilung der IDF-Werte')\n",
                    "plt.axvline(idf_values.mean(), color='r', linestyle='--', label=f'Mean: {idf_values.mean():.4f}')\n",
                    "plt.legend()\n",
                    "\n",
                    "plt.subplot(1, 2, 2)\n",
                    "plt.boxplot(idf_values)\n",
                    "plt.ylabel('IDF-Wert')\n",
                    "plt.title('Boxplot der IDF-Werte')\n",
                    "\n",
                    "plt.tight_layout()\n",
                    "plt.show()"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 6. Suchfunktion implementieren"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "def search(query, top_k=10):\n",
                    "    \"\"\"\n",
                    "    Sucht nach ähnlichen Dokumenten\n",
                    "    \"\"\"\n",
                    "    # Transformiere Query zu TF-IDF Vektor\n",
                    "    query_vector = vectorizer.transform([query])\n",
                    "    \n",
                    "    # Berechne Kosinus-Ähnlichkeit\n",
                    "    similarities = cosine_similarity(query_vector, tfidf_matrix)[0]\n",
                    "    \n",
                    "    # Sortiere nach Ähnlichkeit\n",
                    "    top_indices = np.argsort(similarities)[::-1][:top_k]\n",
                    "    \n",
                    "    results = [(idx, similarities[idx]) for idx in top_indices if similarities[idx] > 0]\n",
                    "    \n",
                    "    return results"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 7. Test-Suchen durchführen"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "test_queries = [\n",
                    "    \"Klimawandel\",\n",
                    "    \"Ukraine Krieg\",\n",
                    "    \"Bundesregierung\",\n",
                    "    \"Wirtschaft\"\n",
                    "]\n",
                    "\n",
                    "for query in test_queries:\n",
                    "    print(f\"\\n{'='*60}\")\n",
                    "    print(f\"Suche: '{query}'\")\n",
                    "    print(f\"{'='*60}\")\n",
                    "    \n",
                    "    results = search(query, top_k=5)\n",
                    "    \n",
                    "    if not results:\n",
                    "        print(\"Keine Ergebnisse gefunden.\")\n",
                    "        continue\n",
                    "    \n",
                    "    for i, (idx, score) in enumerate(results, 1):\n",
                    "        print(f\"\\n--- Ergebnis {i} (Score: {score:.4f}) ---\")\n",
                    "        doc = documents[idx]\n",
                    "        preview = doc[:300] + \"...\" if len(doc) > 300 else doc\n",
                    "        print(f\"Index: {idx}\")\n",
                    "        print(f\"Text: {preview}\")"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 8. Analyse und Verbesserungsvorschläge\n",
                    "\n",
                    "### Diskussionspunkte:\n",
                    "1. Wie finden Sie das IR-System?\n",
                    "2. Was wären nächste Schritte zur Verbesserung?\n",
                    "3. Welche Vorverarbeitungsschritte könnten helfen?\n",
                    "4. Welche Informationen sind noch im Datensatz enthalten?"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Analysiere Metadaten im Datensatz\n",
                    "print(\"Verfügbare Spalten im Datensatz:\")\n",
                    "for col in df.columns:\n",
                    "    print(f\"  - {col}: {df[col].dtype}\")\n",
                    "    if df[col].dtype == 'object':\n",
                    "        unique_count = df[col].nunique()\n",
                    "        print(f\"    Unique Werte: {unique_count}\")\n",
                    "        if unique_count < 20:\n",
                    "            print(f\"    Werte: {df[col].unique()[:10].tolist()}\")"
                ]
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.8.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    
    return notebook

def create_chromadb_notebook():
    """Erstellt das ChromaDB Analyse Notebook"""
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# ChromaDB und Embedding-Modelle\n",
                    "\n",
                    "In diesem Notebook arbeiten wir mit ChromaDB und vergleichen verschiedene Embedding-Modelle."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import chromadb\n",
                    "from chromadb.config import Settings\n",
                    "import pandas as pd\n",
                    "from sentence_transformers import SentenceTransformer\n",
                    "import numpy as np\n",
                    "from pathlib import Path\n",
                    "import matplotlib.pyplot as plt\n",
                    "import seaborn as sns\n",
                    "\n",
                    "sns.set_style(\"whitegrid\")"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 1. Daten laden"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "data_dir = Path('../data')\n",
                    "csv_path = data_dir / 'tagesschau_2023_prepared.csv'\n",
                    "\n",
                    "df = pd.read_csv(csv_path)\n",
                    "\n",
                    "# Identifiziere Text-Spalte\n",
                    "text_column = None\n",
                    "for col in ['text', 'content', 'article', 'body']:\n",
                    "    if col in df.columns:\n",
                    "        text_column = col\n",
                    "        break\n",
                    "\n",
                    "if text_column is None:\n",
                    "    text_column = df.columns[0]\n",
                    "\n",
                    "documents = df[text_column].dropna().tolist()\n",
                    "print(f\"Geladene Dokumente: {len(documents)}\")\n",
                    "\n",
                    "# Verwende Stichprobe für Demo\n",
                    "sample_docs = documents[:1000] if len(documents) > 1000 else documents\n",
                    "print(f\"Verwendete Dokumente: {len(sample_docs)}\")"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 2. ChromaDB initialisieren"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Erstelle persistente ChromaDB Instanz\n",
                    "chroma_dir = data_dir / 'chromadb'\n",
                    "chroma_dir.mkdir(exist_ok=True)\n",
                    "\n",
                    "client = chromadb.PersistentClient(\n",
                    "    path=str(chroma_dir),\n",
                    "    settings=Settings(anonymized_telemetry=False)\n",
                    ")\n",
                    "\n",
                    "print(f\"ChromaDB Client erstellt\")\n",
                    "print(f\"Persistenz-Verzeichnis: {chroma_dir}\")"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 3. Collection erstellen und Dokumente hinzufügen"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Erstelle oder lade Collection\n",
                    "collection_name = \"tagesschau_articles\"\n",
                    "\n",
                    "try:\n",
                    "    collection = client.get_collection(name=collection_name)\n",
                    "    print(f\"Collection '{collection_name}' geladen\")\n",
                    "    print(f\"  Anzahl Dokumente: {collection.count()}\")\n",
                    "except:\n",
                    "    collection = client.create_collection(name=collection_name)\n",
                    "    print(f\"Neue Collection '{collection_name}' erstellt\")\n",
                    "    \n",
                    "    # Füge Dokumente hinzu\n",
                    "    print(f\"\\nFüge {len(sample_docs)} Dokumente hinzu...\")\n",
                    "    \n",
                    "    ids = [f\"doc_{i}\" for i in range(len(sample_docs))]\n",
                    "    metadatas = [{\"index\": i} for i in range(len(sample_docs))]\n",
                    "    \n",
                    "    collection.add(\n",
                    "        documents=sample_docs,\n",
                    "        ids=ids,\n",
                    "        metadatas=metadatas\n",
                    "    )\n",
                    "    \n",
                    "    print(f\"✓ {len(sample_docs)} Dokumente hinzugefügt\")\n",
                    "    print(f\"  Collection-Größe: {collection.count()}\")"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 4. Was können wir sofort beobachten?\n",
                    "\n",
                    "ChromaDB hat automatisch:\n",
                    "- Embeddings für alle Dokumente berechnet\n",
                    "- Eine persistente Datenbank erstellt\n",
                    "- Indizierung für schnelle Suche durchgeführt"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Zeige Collection-Informationen\n",
                    "print(f\"Collection-Name: {collection.name}\")\n",
                    "print(f\"Anzahl Dokumente: {collection.count()}\")\n",
                    "print(f\"Metadaten: {collection.metadata}\")"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 5. Standard-Embedding-Modell von ChromaDB\n",
                    "\n",
                    "ChromaDB verwendet standardmäßig **all-MiniLM-L6-v2** von Sentence Transformers."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Lade das Standard-Modell\n",
                    "standard_model = SentenceTransformer('all-MiniLM-L6-v2')\n",
                    "\n",
                    "print(\"Standard-Embedding-Modell: all-MiniLM-L6-v2\")\n",
                    "print(f\"Embedding-Dimension: {standard_model.get_sentence_embedding_dimension()}\")\n",
                    "print(f\"\\nModell-Informationen:\")\n",
                    "print(f\"  - Multilingual: Nein (nur Englisch)\")\n",
                    "print(f\"  - Modell-Größe: ~80 MB\")\n",
                    "print(f\"  - Max Sequence Length: 256 Tokens\")\n",
                    "print(f\"  - Training: Paraphrase Mining auf 1B+ sentence pairs\")"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 6. Suche mit ChromaDB"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "def chromadb_search(query, n_results=5):\n",
                    "    \"\"\"\n",
                    "    Sucht in ChromaDB Collection\n",
                    "    \"\"\"\n",
                    "    results = collection.query(\n",
                    "        query_texts=[query],\n",
                    "        n_results=n_results\n",
                    "    )\n",
                    "    \n",
                    "    return results\n",
                    "\n",
                    "# Test-Suchen\n",
                    "test_queries = [\n",
                    "    \"Klimawandel\",\n",
                    "    \"Ukraine Krieg\",\n",
                    "    \"Bundesregierung\"\n",
                    "]\n",
                    "\n",
                    "for query in test_queries:\n",
                    "    print(f\"\\n{'='*60}\")\n",
                    "    print(f\"ChromaDB Suche: '{query}'\")\n",
                    "    print(f\"{'='*60}\")\n",
                    "    \n",
                    "    results = chromadb_search(query, n_results=3)\n",
                    "    \n",
                    "    if not results['documents'] or len(results['documents'][0]) == 0:\n",
                    "        print(\"Keine Ergebnisse gefunden.\")\n",
                    "        continue\n",
                    "    \n",
                    "    documents = results['documents'][0]\n",
                    "    distances = results['distances'][0] if 'distances' in results else None\n",
                    "    \n",
                    "    for i, doc in enumerate(documents):\n",
                    "        print(f\"\\n--- Ergebnis {i+1} ---\")\n",
                    "        if distances:\n",
                    "            print(f\"Distanz: {distances[i]:.4f}\")\n",
                    "        preview = doc[:300] + \"...\" if len(doc) > 300 else doc\n",
                    "        print(f\"Text: {preview}\")"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 7. Vergleich verschiedener Embedding-Modelle"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Modelle zum Vergleich\n",
                    "models_to_compare = [\n",
                    "    ('all-MiniLM-L6-v2', 'ChromaDB Standard (Englisch)'),\n",
                    "    ('paraphrase-multilingual-MiniLM-L12-v2', 'Multilingual MiniLM'),\n",
                    "    ('sentence-transformers/all-mpnet-base-v2', 'MPNet Base (größer, besser)')\n",
                    "]\n",
                    "\n",
                    "def compare_models(query, documents_sample, models):\n",
                    "    \"\"\"\n",
                    "    Vergleicht verschiedene Embedding-Modelle\n",
                    "    \"\"\"\n",
                    "    print(f\"\\n{'='*60}\")\n",
                    "    print(f\"Vergleich von Embedding-Modellen\")\n",
                    "    print(f\"Query: '{query}'\")\n",
                    "    print(f\"{'='*60}\\n\")\n",
                    "    \n",
                    "    results_comparison = {}\n",
                    "    \n",
                    "    for model_name, description in models:\n",
                    "        print(f\"\\n--- {description} ({model_name}) ---\")\n",
                    "        try:\n",
                    "            model = SentenceTransformer(model_name)\n",
                    "            \n",
                    "            # Berechne Embeddings\n",
                    "            query_embedding = model.encode([query])[0]\n",
                    "            doc_embeddings = model.encode(documents_sample)\n",
                    "            \n",
                    "            # Berechne Kosinus-Ähnlichkeit\n",
                    "            similarities = np.dot(doc_embeddings, query_embedding) / (\n",
                    "                np.linalg.norm(doc_embeddings, axis=1) * np.linalg.norm(query_embedding)\n",
                    "            )\n",
                    "            \n",
                    "            top_indices = np.argsort(similarities)[::-1][:5]\n",
                    "            results_comparison[model_name] = [\n",
                    "                (idx, similarities[idx]) for idx in top_indices\n",
                    "            ]\n",
                    "            \n",
                    "            print(f\"Top 5 Ergebnisse:\")\n",
                    "            for i, (idx, score) in enumerate(results_comparison[model_name], 1):\n",
                    "                print(f\"  {i}. Doc {idx}: {score:.4f}\")\n",
                    "            \n",
                    "            print(f\"  Embedding-Dimension: {model.get_sentence_embedding_dimension()}\")\n",
                    "            \n",
                    "        except Exception as e:\n",
                    "            print(f\"  Fehler: {e}\")\n",
                    "    \n",
                    "    return results_comparison\n",
                    "\n",
                    "# Führe Vergleich durch\n",
                    "sample_for_comparison = sample_docs[:50]\n",
                    "comparison_results = compare_models(\n",
                    "    \"Klimawandel\",\n",
                    "    sample_for_comparison,\n",
                    "    models_to_compare\n",
                    ")"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 8. Modell-Leaderboard\n",
                    "\n",
                    "Informationen über Embedding-Modelle finden Sie auf:\n",
                    "- https://huggingface.co/spaces/mteb/leaderboard\n",
                    "- https://www.sbert.net/docs/pretrained_models.html"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 9. Eigenschaften von Embedding-Modelle\n",
                    "\n",
                    "### Diskussionspunkte:\n",
                    "1. Welche Eigenschaften kennzeichnen Embedding-Modelle?\n",
                    "2. Welche Probleme könnte es mit dem Standard-Modell bei deutschen Texten geben?\n",
                    "3. Welche Vorverarbeitungsschritte sollten durchgeführt werden?"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Analysiere mögliche Probleme mit Standard-Modell\n",
                    "print(\"Mögliche Probleme mit all-MiniLM-L6-v2 für deutsche Texte:\")\n",
                    "print(\"  1. Modell wurde primär auf englischen Texten trainiert\")\n",
                    "print(\"  2. Deutsche Wörter werden möglicherweise nicht optimal dargestellt\")\n",
                    "print(\"  3. Semantische Ähnlichkeiten könnten für deutsche Begriffe ungenau sein\")\n",
                    "print(\"\\nLösungsansätze:\")\n",
                    "print(\"  - Verwende multilinguale Modelle (z.B. paraphrase-multilingual-MiniLM-L12-v2)\")\n",
                    "print(\"  - Text-Vorverarbeitung: Normalisierung, Stemming, Lemmatisierung\")\n",
                    "print(\"  - Stopword-Entfernung für deutsche Sprache\")\n",
                    "print(\"  - Entfernung von HTML-Tags und Sonderzeichen\")\n",
                    "print(\"  - Satz-Segmentierung für längere Texte\")"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 10. Vorverarbeitung für bessere Ergebnisse"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "from bs4 import BeautifulSoup\n",
                    "import re\n",
                    "\n",
                    "def preprocess_text(text):\n",
                    "    \"\"\"\n",
                    "    Vorverarbeitung von Texten\n",
                    "    \"\"\"\n",
                    "    if pd.isna(text):\n",
                    "        return \"\"\n",
                    "    \n",
                    "    # Entferne HTML-Tags\n",
                    "    text = BeautifulSoup(text, 'html.parser').get_text()\n",
                    "    \n",
                    "    # Normalisiere Whitespace\n",
                    "    text = re.sub(r'\\s+', ' ', text)\n",
                    "    \n",
                    "    # Entferne URLs\n",
                    "    text = re.sub(r'http\\S+|www\\.\\S+', '', text)\n",
                    "    \n",
                    "    # Entferne E-Mail-Adressen\n",
                    "    text = re.sub(r'\\S+@\\S+', '', text)\n",
                    "    \n",
                    "    # Trim\n",
                    "    text = text.strip()\n",
                    "    \n",
                    "    return text\n",
                    "\n",
                    "# Teste Vorverarbeitung\n",
                    "if len(sample_docs) > 0:\n",
                    "    original = sample_docs[0]\n",
                    "    processed = preprocess_text(original)\n",
                    "    \n",
                    "    print(\"Original (erste 200 Zeichen):\")\n",
                    "    print(original[:200])\n",
                    "    print(\"\\nVorverarbeitet (erste 200 Zeichen):\")\n",
                    "    print(processed[:200])\n",
                    "    print(f\"\\nLänge Original: {len(original)}\")\n",
                    "    print(f\"Länge Vorverarbeitet: {len(processed)}\")"
                ]
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.8.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    
    return notebook

if __name__ == "__main__":
    notebooks_dir = Path(__file__).parent.parent / "notebooks"
    
    # Erstelle TF-IDF Notebook
    tfidf_notebook = create_tfidf_notebook()
    with open(notebooks_dir / "02_tfidf_analysis.ipynb", "w", encoding="utf-8") as f:
        json.dump(tfidf_notebook, f, indent=1, ensure_ascii=False)
    print("✓ TF-IDF Notebook erstellt")
    
    # Erstelle ChromaDB Notebook
    chromadb_notebook = create_chromadb_notebook()
    with open(notebooks_dir / "03_chromadb_analysis.ipynb", "w", encoding="utf-8") as f:
        json.dump(chromadb_notebook, f, indent=1, ensure_ascii=False)
    print("✓ ChromaDB Notebook erstellt")

