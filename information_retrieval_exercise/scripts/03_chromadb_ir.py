"""
ChromaDB basiertes Information Retrieval System mit Embeddings
"""
import chromadb
from chromadb.config import Settings
import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np

class ChromaDBIRSystem:
    """
    Information Retrieval System basierend auf ChromaDB und Embeddings
    """
    
    def __init__(self, collection_name="tagesschau_articles", 
                 embedding_model=None, persist_directory=None):
        """
        Initialisiert das ChromaDB IR System
        
        Args:
            collection_name: Name der ChromaDB Collection
            embedding_model: Name des Embedding-Modells (None = Standard)
            persist_directory: Verzeichnis zum Persistieren der Daten
        """
        # ChromaDB Client initialisieren
        if persist_directory:
            self.client = chromadb.PersistentClient(
                path=str(persist_directory),
                settings=Settings(anonymized_telemetry=False)
            )
        else:
            self.client = chromadb.Client(
                settings=Settings(anonymized_telemetry=False)
            )
        
        # Embedding-Modell laden
        if embedding_model:
            print(f"Lade Embedding-Modell: {embedding_model}")
            self.embedding_model = SentenceTransformer(embedding_model)
            self.use_custom_embedding = True
        else:
            print("Verwende Standard-Embedding-Modell von ChromaDB")
            self.embedding_model = None
            self.use_custom_embedding = False
        
        # Collection erstellen oder laden
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"Collection '{collection_name}' geladen")
        except:
            if self.use_custom_embedding:
                # Für custom embeddings müssen wir eine Funktion bereitstellen
                self.collection = self.client.create_collection(
                    name=collection_name,
                    embedding_function=self._embedding_function
                )
            else:
                self.collection = self.client.create_collection(
                    name=collection_name
                )
            print(f"Neue Collection '{collection_name}' erstellt")
    
    def _embedding_function(self, texts):
        """
        Custom Embedding-Funktion für ChromaDB
        
        Args:
            texts: Liste von Texten
        
        Returns:
            Liste von Embedding-Vektoren
        """
        if self.embedding_model is None:
            raise ValueError("Embedding-Modell nicht initialisiert")
        
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()
    
    def add_documents(self, documents, ids=None, metadatas=None):
        """
        Fügt Dokumente zur Collection hinzu
        
        Args:
            documents: Liste von Dokument-Texten
            ids: Liste von IDs (optional)
            metadatas: Liste von Metadaten-Dictionaries (optional)
        """
        print(f"Füge {len(documents)} Dokumente hinzu...")
        
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]
        
        if self.use_custom_embedding:
            # Bei custom embeddings müssen wir die Embeddings selbst berechnen
            embeddings = self._embedding_function(documents)
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                ids=ids,
                metadatas=metadatas
            )
        else:
            # ChromaDB berechnet Embeddings automatisch
            self.collection.add(
                documents=documents,
                ids=ids,
                metadatas=metadatas
            )
        
        print(f"✓ {len(documents)} Dokumente hinzugefügt")
        print(f"  Collection-Größe: {self.collection.count()}")
    
    def search(self, query, n_results=10, where=None, where_document=None):
        """
        Sucht nach ähnlichen Dokumenten
        
        Args:
            query: Suchanfrage (String)
            n_results: Anzahl der Ergebnisse
            where: Filter für Metadaten
            where_document: Filter für Dokument-Inhalt
        
        Returns:
            Dictionary mit Ergebnissen
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
            where_document=where_document
        )
        
        return results
    
    def get_collection_info(self):
        """
        Gibt Informationen über die Collection zurück
        """
        info = {
            'name': self.collection.name,
            'count': self.collection.count(),
            'metadata': self.collection.metadata
        }
        
        # Versuche Informationen über das Embedding-Modell zu bekommen
        try:
            # ChromaDB verwendet standardmäßig all-MiniLM-L6-v2
            info['default_embedding_model'] = 'all-MiniLM-L6-v2'
            info['embedding_dimension'] = 384  # Dimension von all-MiniLM-L6-v2
        except:
            pass
        
        return info
    
    def compare_models(self, query, documents_sample, models_to_compare=None):
        """
        Vergleicht verschiedene Embedding-Modelle
        
        Args:
            query: Suchanfrage
            documents_sample: Liste von Dokumenten für Vergleich
            models_to_compare: Liste von Modell-Namen zum Vergleichen
        """
        if models_to_compare is None:
            models_to_compare = [
                'all-MiniLM-L6-v2',  # ChromaDB Standard
                'paraphrase-multilingual-MiniLM-L12-v2',  # Multilingual
                'sentence-transformers/all-mpnet-base-v2'  # Größeres Modell
            ]
        
        print(f"\n=== Vergleich von Embedding-Modellen ===")
        print(f"Query: '{query}'\n")
        
        results_comparison = {}
        
        for model_name in models_to_compare:
            print(f"\n--- Modell: {model_name} ---")
            try:
                model = SentenceTransformer(model_name)
                query_embedding = model.encode([query])[0]
                doc_embeddings = model.encode(documents_sample)
                
                # Berechne Kosinus-Ähnlichkeit
                similarities = np.dot(doc_embeddings, query_embedding) / (
                    np.linalg.norm(doc_embeddings, axis=1) * np.linalg.norm(query_embedding)
                )
                
                top_indices = np.argsort(similarities)[::-1][:5]
                results_comparison[model_name] = [
                    (idx, similarities[idx]) for idx in top_indices
                ]
                
                print(f"Top 5 Ergebnisse:")
                for i, (idx, score) in enumerate(results_comparison[model_name], 1):
                    print(f"  {i}. Doc {idx}: {score:.4f}")
                    
            except Exception as e:
                print(f"  Fehler: {e}")
        
        return results_comparison

def evaluate_chromadb_search(ir_system, query, top_k=5):
    """
    Evaluierung einer Suchanfrage mit ChromaDB
    
    Args:
        ir_system: ChromaDBIRSystem Instanz
        query: Suchanfrage
        top_k: Anzahl Top-Ergebnisse
    """
    print(f"\n=== ChromaDB Suche: '{query}' ===\n")
    
    results = ir_system.search(query, n_results=top_k)
    
    if not results['documents'] or len(results['documents'][0]) == 0:
        print("Keine Ergebnisse gefunden.")
        return
    
    documents = results['documents'][0]
    distances = results['distances'][0] if 'distances' in results else None
    metadatas = results['metadatas'][0] if 'metadatas' in results else None
    
    for i, doc in enumerate(documents):
        print(f"\n--- Ergebnis {i+1} ---")
        if distances:
            # ChromaDB gibt Distanzen zurück, nicht Ähnlichkeiten
            # Kleinere Distanz = höhere Ähnlichkeit
            print(f"Distanz: {distances[i]:.4f}")
        if metadatas and metadatas[i]:
            print(f"Metadaten: {metadatas[i]}")
        
        # Zeige ersten 500 Zeichen
        preview = doc[:500] + "..." if len(doc) > 500 else doc
        print(f"Text: {preview}")

if __name__ == "__main__":
    # Beispiel-Verwendung
    data_dir = Path(__file__).parent.parent / "data"
    csv_path = data_dir / "tagesschau_2023_prepared.csv"
    chroma_dir = data_dir / "chromadb"
    
    if not csv_path.exists():
        print(f"Fehler: Datei {csv_path} nicht gefunden.")
        print("Bitte zuerst 01_load_data.py ausführen.")
    else:
        # Lade Daten
        df = pd.read_csv(csv_path)
        
        # Stelle sicher, dass wir eine Text-Spalte haben
        text_column = None
        for col in ['text', 'content', 'article', 'body']:
            if col in df.columns:
                text_column = col
                break
        
        if text_column is None:
            print("Warnung: Keine Text-Spalte gefunden. Verwende erste Spalte.")
            text_column = df.columns[0]
        
        documents = df[text_column].dropna().tolist()
        print(f"Geladene Dokumente: {len(documents)}")
        
        # Erstelle ChromaDB IR System mit Standard-Embedding
        print("\n=== ChromaDB mit Standard-Embedding ===")
        ir_system_standard = ChromaDBIRSystem(
            collection_name="tagesschau_standard",
            persist_directory=chroma_dir
        )
        
        # Füge Dokumente hinzu (nur ersten 1000 für Demo)
        sample_docs = documents[:1000] if len(documents) > 1000 else documents
        ids = [f"doc_{i}" for i in range(len(sample_docs))]
        metadatas = [{"index": i} for i in range(len(sample_docs))]
        
        ir_system_standard.add_documents(sample_docs, ids=ids, metadatas=metadatas)
        
        # Zeige Collection-Info
        info = ir_system_standard.get_collection_info()
        print(f"\nCollection-Info:")
        print(f"  Name: {info['name']}")
        print(f"  Anzahl Dokumente: {info['count']}")
        print(f"  Standard-Embedding-Modell: {info.get('default_embedding_model', 'N/A')}")
        print(f"  Embedding-Dimension: {info.get('embedding_dimension', 'N/A')}")
        
        # Teste Suche
        test_queries = [
            "Klimawandel",
            "Ukraine Krieg",
            "Bundesregierung"
        ]
        
        for query in test_queries:
            evaluate_chromadb_search(ir_system_standard, query, top_k=3)
        
        # Vergleich mit anderen Embedding-Modellen
        print("\n\n=== Vergleich verschiedener Embedding-Modelle ===")
        sample_for_comparison = sample_docs[:50]  # Kleinere Stichprobe für Vergleich
        comparison_results = ir_system_standard.compare_models(
            "Klimawandel",
            sample_for_comparison
        )

