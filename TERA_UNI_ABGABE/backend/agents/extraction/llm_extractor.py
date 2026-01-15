"""
TERA LLM Extraction Agent
Uses local Ollama for entity extraction
"""
import json
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from loguru import logger
import httpx


class ExtractedEntity(BaseModel):
    """Extracted geospatial entity from text"""
    location: str
    coordinates: Optional[List[float]] = None  # [lat, lon]
    event_type: str  # conflict, disaster, drought, flood, etc.
    severity: int = Field(ge=1, le=10)  # 1-10 scale
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)
    raw_text_snippet: Optional[str] = None


class LLMExtractor:
    """Extract structured data from text using local LLM"""
    
    EXTRACTION_PROMPT = """You are a geospatial intelligence analyst. Extract location and event information from the following text.

Output ONLY valid JSON in this exact format:
{
    "location": "City/Region name",
    "coordinates": [latitude, longitude] or null,
    "event_type": "conflict|drought|flood|earthquake|wildfire|famine|other",
    "severity": 1-10,
    "summary": "Brief 1-sentence summary"
}

Text to analyze:
{text}

JSON Output:"""

    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3.1:8b"):
        self.ollama_url = ollama_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def extract(self, text: str) -> Optional[ExtractedEntity]:
        """Extract entities from text using LLM"""
        prompt = self.EXTRACTION_PROMPT.format(text=text[:3000])
        
        try:
            response = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 500
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                raw_output = result.get("response", "")
                
                # Parse JSON from response
                try:
                    # Find JSON in response
                    json_start = raw_output.find('{')
                    json_end = raw_output.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = raw_output[json_start:json_end]
                        data = json.loads(json_str)
                        
                        return ExtractedEntity(
                            location=data.get("location", "Unknown"),
                            coordinates=data.get("coordinates"),
                            event_type=data.get("event_type", "other"),
                            severity=min(10, max(1, int(data.get("severity", 5)))),
                            summary=data.get("summary", ""),
                            confidence=0.8,
                            raw_text_snippet=text[:200]
                        )
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse LLM JSON: {e}")
                    
        except Exception as e:
            logger.error(f"LLM extraction error: {e}")
        
        return None
    
    async def batch_extract(self, texts: List[str]) -> List[ExtractedEntity]:
        """Extract from multiple texts"""
        entities = []
        for text in texts:
            entity = await self.extract(text)
            if entity:
                entities.append(entity)
        return entities
    
    async def close(self):
        await self.client.aclose()
