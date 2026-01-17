"""
ChromaDB Vector Store for Context Embeddings
Stores and retrieves context data with semantic search
"""
import chromadb
from chromadb.config import Settings
import httpx
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class ContextDocument:
    id: str
    h3_index: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


class VectorStore:
    """ChromaDB-based vector store for location contexts"""
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        self.client = chromadb.HttpClient(host=host, port=port)
        self.collection = None
        self.ollama_url = "http://localhost:11434"
    
    def init_collection(self, name: str = "tera_contexts"):
        """Initialize or get collection"""
        try:
            self.collection = self.client.get_or_create_collection(
                name=name,
                metadata={"description": "TERA location context embeddings"}
            )
            logger.info(f"Collection '{name}' initialized with {self.collection.count()} documents")
        except Exception as e:
            logger.error(f"Failed to init collection: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": "llama3.1:8b",
                    "prompt": text
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])
    
    def add_context(self, doc: ContextDocument) -> str:
        """Add a context document to the collection"""
        if not self.collection:
            self.init_collection()
        
        self.collection.add(
            ids=[doc.id],
            documents=[doc.content],
            metadatas=[{
                "h3_index": doc.h3_index,
                **doc.metadata
            }]
        )
        return doc.id
    
    def add_contexts_batch(self, docs: List[ContextDocument]):
        """Add multiple context documents"""
        if not self.collection:
            self.init_collection()
        
        self.collection.add(
            ids=[d.id for d in docs],
            documents=[d.content for d in docs],
            metadatas=[{"h3_index": d.h3_index, **d.metadata} for d in docs]
        )
        logger.info(f"Added {len(docs)} documents to vector store")
    
    def search_by_h3(self, h3_index: str, limit: int = 10) -> List[Dict]:
        """Get all contexts for a specific H3 cell"""
        if not self.collection:
            self.init_collection()
        
        results = self.collection.get(
            where={"h3_index": h3_index},
            limit=limit
        )
        
        return self._format_results(results)
    
    def semantic_search(self, query: str, limit: int = 10, h3_filter: str = None) -> List[Dict]:
        """Semantic search across all contexts"""
        if not self.collection:
            self.init_collection()
        
        where = {"h3_index": h3_filter} if h3_filter else None
        
        results = self.collection.query(
            query_texts=[query],
            n_results=limit,
            where=where
        )
        
        return self._format_query_results(results)
    
    def search_nearby_cells(self, h3_indexes: List[str], limit: int = 20) -> List[Dict]:
        """Search contexts in multiple H3 cells"""
        if not self.collection:
            self.init_collection()
        
        results = self.collection.get(
            where={"h3_index": {"$in": h3_indexes}},
            limit=limit
        )
        
        return self._format_results(results)
    
    def _format_results(self, results) -> List[Dict]:
        """Format ChromaDB results"""
        docs = []
        if results and results.get("ids"):
            for i, id in enumerate(results["ids"]):
                docs.append({
                    "id": id,
                    "content": results["documents"][i] if results.get("documents") else "",
                    "metadata": results["metadatas"][i] if results.get("metadatas") else {}
                })
        return docs
    
    def _format_query_results(self, results) -> List[Dict]:
        """Format ChromaDB query results"""
        docs = []
        if results and results.get("ids") and results["ids"][0]:
            for i, id in enumerate(results["ids"][0]):
                docs.append({
                    "id": id,
                    "content": results["documents"][0][i] if results.get("documents") else "",
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "distance": results["distances"][0][i] if results.get("distances") else 0
                })
        return docs
    
    def get_stats(self) -> Dict:
        """Get collection statistics"""
        if not self.collection:
            self.init_collection()
        
        return {
            "name": self.collection.name,
            "count": self.collection.count()
        }
