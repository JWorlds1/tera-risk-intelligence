#!/usr/bin/env python3
"""
Multi-Modal Vektorraum für Geodaten-Prognose
Kombiniert: Text, Zahlen, Bilder, Geodaten
Basierend auf fire-enrich Architektur
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json
import numpy as np
from dataclasses import dataclass, asdict
from enum import Enum

sys.path.append(str(Path(__file__).parent))

from rich.console import Console
from rich.table import Table

console = Console()


class DataType(Enum):
    """Datentypen für Multi-Modal Matching"""
    TEXT = "text"
    NUMBER = "number"
    IMAGE = "image"
    GEOSPATIAL = "geospatial"
    TEMPORAL = "temporal"
    STRUCTURED = "structured"


@dataclass
class VectorEmbedding:
    """Vektor-Embedding für einen Datenpunkt"""
    id: str
    data_type: DataType
    embedding: np.ndarray  # Normalized vector
    metadata: Dict[str, Any]
    confidence: float
    timestamp: datetime


@dataclass
class MultiModalChunk:
    """Multi-Modal Chunk mit verschiedenen Datentypen"""
    chunk_id: str
    city: str
    coordinates: tuple  # (lat, lon)
    
    # Text-Daten
    text_content: str
    text_embedding: Optional[np.ndarray] = None
    
    # Numerische Daten
    numerical_data: Dict[str, float] = None  # temperature, precipitation, etc.
    numerical_embedding: Optional[np.ndarray] = None
    
    # Bild-Daten
    image_urls: List[str] = None
    image_embeddings: List[np.ndarray] = None  # CLIP embeddings
    
    # Geodaten
    geospatial_features: Dict[str, Any] = None  # bbox, polygon, etc.
    geospatial_embedding: Optional[np.ndarray] = None
    
    # Metadaten
    sources: List[str] = None
    timestamp: datetime = None
    confidence: float = 1.0
    
    def __post_init__(self):
        if self.numerical_data is None:
            self.numerical_data = {}
        if self.image_urls is None:
            self.image_urls = []
        if self.image_embeddings is None:
            self.image_embeddings = []
        if self.sources is None:
            self.sources = []
        if self.timestamp is None:
            self.timestamp = datetime.now()


class SimilarityMetrics:
    """Ähnlichkeitsmetriken für Multi-Modal Matching"""
    
    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Cosine Similarity für normalisierte Vektoren"""
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    @staticmethod
    def euclidean_distance(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Euklidische Distanz"""
        return np.linalg.norm(vec1 - vec2)
    
    @staticmethod
    def numerical_similarity(num1: float, num2: float, scale: float = 1.0) -> float:
        """Ähnlichkeit für numerische Werte (normalisiert)"""
        diff = abs(num1 - num2)
        return max(0.0, 1.0 - (diff / scale))
    
    @staticmethod
    def geospatial_similarity(
        coords1: tuple, 
        coords2: tuple, 
        threshold_km: float = 100.0
    ) -> float:
        """Geospatiale Ähnlichkeit basierend auf Distanz"""
        from math import radians, cos, sin, asin, sqrt
        
        def haversine(lon1, lat1, lon2, lat2):
            """Berechne Distanz zwischen zwei Koordinaten (km)"""
            lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371  # Erdradius in km
            return c * r
        
        distance_km = haversine(coords1[1], coords1[0], coords2[1], coords2[0])
        similarity = max(0.0, 1.0 - (distance_km / threshold_km))
        return similarity
    
    @staticmethod
    def multimodal_similarity(
        chunk1: MultiModalChunk,
        chunk2: MultiModalChunk,
        weights: Dict[str, float] = None
    ) -> float:
        """Kombinierte Multi-Modal Ähnlichkeit"""
        if weights is None:
            weights = {
                'text': 0.3,
                'numerical': 0.2,
                'image': 0.2,
                'geospatial': 0.3
            }
        
        similarities = {}
        
        # Text-Ähnlichkeit
        if chunk1.text_embedding is not None and chunk2.text_embedding is not None:
            similarities['text'] = SimilarityMetrics.cosine_similarity(
                chunk1.text_embedding, chunk2.text_embedding
            )
        
        # Numerische Ähnlichkeit (Durchschnitt über alle numerischen Werte)
        if chunk1.numerical_data and chunk2.numerical_data:
            num_sims = []
            for key in set(chunk1.numerical_data.keys()) & set(chunk2.numerical_data.keys()):
                # Skala basierend auf Wert-Typ
                scale = 10.0 if 'temperature' in key.lower() else 100.0
                sim = SimilarityMetrics.numerical_similarity(
                    chunk1.numerical_data[key],
                    chunk2.numerical_data[key],
                    scale
                )
                num_sims.append(sim)
            similarities['numerical'] = np.mean(num_sims) if num_sims else 0.0
        
        # Bild-Ähnlichkeit (Durchschnitt über alle Bilder)
        if chunk1.image_embeddings and chunk2.image_embeddings:
            image_sims = []
            for img1 in chunk1.image_embeddings:
                for img2 in chunk2.image_embeddings:
                    sim = SimilarityMetrics.cosine_similarity(img1, img2)
                    image_sims.append(sim)
            similarities['image'] = np.mean(image_sims) if image_sims else 0.0
        
        # Geospatiale Ähnlichkeit
        if chunk1.coordinates and chunk2.coordinates:
            similarities['geospatial'] = SimilarityMetrics.geospatial_similarity(
                chunk1.coordinates, chunk2.coordinates
            )
        
        # Gewichtete Kombination
        total_similarity = 0.0
        total_weight = 0.0
        
        for metric, weight in weights.items():
            if metric in similarities:
                total_similarity += similarities[metric] * weight
                total_weight += weight
        
        return total_similarity / total_weight if total_weight > 0 else 0.0


class MultiModalVectorSpace:
    """Multi-Modal Vektorraum für Geodaten-Prognose"""
    
    def __init__(self, embedding_dim: int = 1536):
        """
        Args:
            embedding_dim: Dimension für Text-Embeddings (OpenAI: 1536, CLIP: 512)
        """
        self.embedding_dim = embedding_dim
        self.chunks: List[MultiModalChunk] = []
        self.text_embeddings: Dict[str, np.ndarray] = {}
        self.image_embeddings: Dict[str, np.ndarray] = {}
        
        # Vektor-DB (vereinfacht, später: ChromaDB/Qdrant)
        self.vector_index: Dict[str, VectorEmbedding] = {}
    
    def add_chunk(self, chunk: MultiModalChunk):
        """Füge einen Multi-Modal Chunk hinzu"""
        self.chunks.append(chunk)
        
        # Indexiere Text-Embedding
        if chunk.text_embedding is not None:
            self.text_embeddings[chunk.chunk_id] = chunk.text_embedding
        
        # Indexiere Bild-Embeddings
        for i, img_emb in enumerate(chunk.image_embeddings):
            img_id = f"{chunk.chunk_id}_img_{i}"
            self.image_embeddings[img_id] = img_emb
    
    def search_similar(
        self,
        query_chunk: MultiModalChunk,
        top_k: int = 10,
        similarity_threshold: float = 0.5
    ) -> List[tuple]:
        """
        Suche ähnliche Chunks
        
        Returns:
            List of (chunk, similarity_score) tuples
        """
        results = []
        
        for chunk in self.chunks:
            similarity = SimilarityMetrics.multimodal_similarity(query_chunk, chunk)
            
            if similarity >= similarity_threshold:
                results.append((chunk, similarity))
        
        # Sortiere nach Ähnlichkeit
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]
    
    def search_by_location(
        self,
        coordinates: tuple,
        radius_km: float = 50.0,
        top_k: int = 10
    ) -> List[MultiModalChunk]:
        """Suche Chunks in geografischer Nähe"""
        results = []
        
        for chunk in self.chunks:
            if chunk.coordinates:
                distance_km = SimilarityMetrics.geospatial_similarity(
                    coordinates, chunk.coordinates, threshold_km=radius_km * 2
                )
                
                if distance_km > 0:
                    results.append((chunk, distance_km))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return [chunk for chunk, _ in results[:top_k]]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Hole Statistiken über den Vektorraum"""
        stats = {
            'total_chunks': len(self.chunks),
            'chunks_with_text': sum(1 for c in self.chunks if c.text_embedding is not None),
            'chunks_with_images': sum(1 for c in self.chunks if c.image_urls),
            'chunks_with_numerical': sum(1 for c in self.chunks if c.numerical_data),
            'chunks_with_geospatial': sum(1 for c in self.chunks if c.coordinates),
            'total_images': sum(len(c.image_urls) for c in self.chunks),
            'cities': list(set(c.city for c in self.chunks)),
            'embedding_dim': self.embedding_dim
        }
        
        return stats



