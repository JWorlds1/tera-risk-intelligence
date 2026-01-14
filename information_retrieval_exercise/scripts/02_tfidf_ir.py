"""
TF-IDF basiertes Information Retrieval System
"""
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path
import pickle

class TFIDFIRSystem:
    """
    Information Retrieval System basierend auf TF-IDF und Kosinus-Ähnlichkeit
    """
    
    def __init__(self, max_features=None, ngram_range=(1, 1), 
                 min_df=1, max_df=1.0, norm='l2', use_idf=True):
        """
        Initialisiert das TF-IDF IR System
        
        Args:
            max_features: Maximale Anzahl Features (None = alle)
            ngram_range: Tuple (min_n, max_n) für N-Gramme
            min_df: Minimale Dokument-Frequenz (int oder float)
            max_df: Maximale Dokument-Frequenz (float)
            norm: Normalisierung ('l2', 'l1', None)
            use_idf: Ob IDF verwendet werden soll
        """
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            min_df=min_df,
            max_df=max_df,
            norm=norm,
            use_idf=use_idf,
            lowercase=True,
            stop_words=None,  # Kann auf 'english' gesetzt werden
            token_pattern=r'(?u)\b\w\w+\b'
        )
        self.documents = None
        self.tfidf_matrix = None
        self.feature_names = None
        
    def fit_transform(self, documents):
        """
        Trainiert das Modell und transformiert Dokumente
        
        Args:
            documents: Liste von Dokument-Texten
        
        Returns:
            TF-IDF Matrix (n_documents x n_features)
        """
        print(f"Verarbeite {len(documents)} Dokumente...")
        
        self.documents = documents
        
        # fit_transform: Trainiert das Modell UND transformiert die Daten
        # - fit: Lernt das Vokabular und IDF-Werte aus den Dokumenten
        # - transform: Wendet die gelernten Transformationen an
        self.tfidf_matrix = self.vectorizer.fit_transform(documents)
        self.feature_names = self.vectorizer.get_feature_names_out()
        
        print(f"TF-IDF Matrix Shape: {self.tfidf_matrix.shape}")
        print(f"Anzahl Features: {len(self.feature_names)}")
        
        return self.tfidf_matrix
    
    def search(self, query, top_k=10):
        """
        Sucht nach ähnlichen Dokumenten
        
        Args:
            query: Suchanfrage (String)
            top_k: Anzahl der Top-Ergebnisse
        
        Returns:
            Liste von Tupeln (index, similarity_score)
        """
        if self.tfidf_matrix is None:
            raise ValueError("Modell muss zuerst mit fit_transform trainiert werden")
        
        # Transformiere Query zu TF-IDF Vektor
        query_vector = self.vectorizer.transform([query])
        
        # Berechne Kosinus-Ähnlichkeit
        similarities = cosine_similarity(query_vector, self.tfidf_matrix)[0]
        
        # Sortiere nach Ähnlichkeit (absteigend)
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = [(idx, similarities[idx]) for idx in top_indices if similarities[idx] > 0]
        
        return results
    
    def get_tfidf_info(self):
        """
        Gibt Informationen über die TF-IDF Berechnung zurück
        """
        if self.tfidf_matrix is None:
            return None
        
        info = {
            'idf_values': self.vectorizer.idf_,
            'vocabulary': dict(self.vectorizer.vocabulary_),
            'feature_names': self.feature_names.tolist(),
            'matrix_shape': self.tfidf_matrix.shape,
            'matrix_density': self.tfidf_matrix.nnz / (self.tfidf_matrix.shape[0] * self.tfidf_matrix.shape[1])
        }
        
        return info
    
    def save(self, filepath):
        """Speichert das Modell"""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'vectorizer': self.vectorizer,
                'documents': self.documents,
                'tfidf_matrix': self.tfidf_matrix,
                'feature_names': self.feature_names
            }, f)
        print(f"Modell gespeichert: {filepath}")
    
    def load(self, filepath):
        """Lädt ein gespeichertes Modell"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.vectorizer = data['vectorizer']
            self.documents = data['documents']
            self.tfidf_matrix = data['tfidf_matrix']
            self.feature_names = data['feature_names']
        print(f"Modell geladen: {filepath}")

def evaluate_search(ir_system, query, documents, top_k=5):
    """
    Evaluierung einer Suchanfrage
    
    Args:
        ir_system: TFIDFIRSystem Instanz
        query: Suchanfrage
        documents: Liste der Dokumente
        top_k: Anzahl Top-Ergebnisse
    """
    print(f"\n=== Suche: '{query}' ===\n")
    
    results = ir_system.search(query, top_k=top_k)
    
    if not results:
        print("Keine Ergebnisse gefunden.")
        return
    
    for i, (idx, score) in enumerate(results, 1):
        print(f"\n--- Ergebnis {i} (Score: {score:.4f}) ---")
        doc = documents[idx]
        # Zeige ersten 500 Zeichen
        preview = doc[:500] + "..." if len(doc) > 500 else doc
        print(f"Index: {idx}")
        print(f"Text: {preview}")

if __name__ == "__main__":
    # Beispiel-Verwendung
    data_dir = Path(__file__).parent.parent / "data"
    csv_path = data_dir / "tagesschau_2023_prepared.csv"
    
    if not csv_path.exists():
        print(f"Fehler: Datei {csv_path} nicht gefunden.")
        print("Bitte zuerst 01_load_data.py ausführen.")
    else:
        # Lade Daten
        df = pd.read_csv(csv_path)
        
        # Stelle sicher, dass wir eine Text-Spalte haben
        # (Anpassen je nach Datensatz-Struktur)
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
        
        # Erstelle IR System
        ir_system = TFIDFIRSystem(
            max_features=10000,
            ngram_range=(1, 2),  # Unigramme und Bigramme
            min_df=2,  # Wort muss in mindestens 2 Dokumenten vorkommen
            max_df=0.95,  # Wort darf in max. 95% der Dokumente vorkommen
            norm='l2'
        )
        
        # Trainiere Modell
        ir_system.fit_transform(documents)
        
        # Zeige TF-IDF Informationen
        info = ir_system.get_tfidf_info()
        print(f"\nMatrix-Dichte: {info['matrix_density']:.4f}")
        print(f"Top 10 Features (nach IDF):")
        top_features_idx = np.argsort(info['idf_values'])[:10]
        for idx in top_features_idx:
            print(f"  {info['feature_names'][idx]}: IDF={info['idf_values'][idx]:.4f}")
        
        # Teste Suche
        test_queries = [
            "Klimawandel",
            "Ukraine Krieg",
            "Bundesregierung",
            "Wirtschaft"
        ]
        
        for query in test_queries:
            evaluate_search(ir_system, query, documents, top_k=3)
        
        # Speichere Modell
        model_path = data_dir / "tfidf_model.pkl"
        ir_system.save(model_path)

