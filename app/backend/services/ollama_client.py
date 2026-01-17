"""
Ollama LLM Client
Local LLM for entity extraction
"""
import httpx
import json
from typing import Optional, Dict, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from models.schemas import ExtractedEntity, EventType
from loguru import logger


EXTRACTION_PROMPT = """You are an expert at extracting geospatial entities from news articles.

Extract ALL locations, events, and severity levels from the following text.
Output ONLY valid JSON in this exact format:
{
  "entities": [
    {
      "location": "City or Region Name",
      "country": "Country Name",
      "event_type": "flood|drought|conflict|heatwave|storm|wildfire|earthquake|famine",
      "severity": 1-10,
      "confidence": 0.0-1.0,
      "summary": "Brief description"
    }
  ]
}

Rules:
- severity: 1=minimal, 5=moderate, 10=catastrophic
- confidence: how certain you are about this extraction
- event_type MUST be one of: flood, drought, conflict, heatwave, storm, wildfire, earthquake, famine
- If no entities found, return {"entities": []}

TEXT:
{text}

JSON OUTPUT:"""


class OllamaClient:
    """Client for local Ollama LLM"""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
    
    async def health_check(self) -> bool:
        """Check if Ollama is running"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
    
    async def list_models(self) -> List[str]:
        """List available models"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate(self, prompt: str, stream: bool = False) -> str:
        """Generate text from prompt"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": stream,
                    "options": {
                        "temperature": 0.1,  # Low for extraction
                        "num_predict": 2000
                    }
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama error: {response.text}")
            
            data = response.json()
            return data.get("response", "")
    
    async def extract_entities(self, text: str) -> List[ExtractedEntity]:
        """Extract geospatial entities from text using LLM"""
        if not text or len(text) < 50:
            return []
        
        # Truncate if too long
        if len(text) > 8000:
            text = text[:8000] + "..."
        
        prompt = EXTRACTION_PROMPT.format(text=text)
        
        try:
            response = await self.generate(prompt)
            
            # Parse JSON from response
            # Find JSON in response (LLM might add extra text)
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            
            if json_start == -1 or json_end == 0:
                logger.warning("No JSON found in LLM response")
                return []
            
            json_str = response[json_start:json_end]
            data = json.loads(json_str)
            
            entities = []
            for e in data.get("entities", []):
                try:
                    # Validate event type
                    event_type = e.get("event_type", "").lower()
                    if event_type not in [et.value for et in EventType]:
                        event_type = "conflict"  # Default
                    
                    entity = ExtractedEntity(
                        location=e.get("location", "Unknown"),
                        event_type=EventType(event_type),
                        severity=max(1, min(10, int(e.get("severity", 5)))),
                        confidence=max(0, min(1, float(e.get("confidence", 0.5)))),
                        summary=e.get("summary")
                    )
                    entities.append(entity)
                except Exception as parse_error:
                    logger.warning(f"Failed to parse entity: {parse_error}")
                    continue
            
            logger.info(f"Extracted {len(entities)} entities from text")
            return entities
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return []
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return []
    
    async def summarize(self, text: str, max_length: int = 200) -> str:
        """Summarize text"""
        prompt = f"""Summarize this text in {max_length} characters or less. Focus on:
- Location(s) affected
- Type of event/crisis
- Impact/severity

TEXT:
{text[:4000]}

SUMMARY:"""
        
        try:
            return await self.generate(prompt)
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return ""

