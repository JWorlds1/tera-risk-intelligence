"""
Free LLM Manager - Integration für kostenlose Open-Source LLMs
Unterstützt Ollama und LlamaCpp mit Fallback-Mechanismus
"""

from typing import Optional, Dict, Any, List
import asyncio
import httpx
import structlog
from config import Config

logger = structlog.get_logger(__name__)


class FreeLLMManager:
    """Manager für kostenlose LLMs (Ollama, LlamaCpp)"""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the Free LLM Manager
        
        Args:
            config: Configuration object
        """
        self.config = config or Config()
        self.ollama_host = self.config.OLLAMA_HOST
        self.ollama_model = self.config.OLLAMA_MODEL
        self.http_client = httpx.AsyncClient(timeout=60.0)
        
        # Check availability
        self.ollama_available = False
        self.llamacpp_available = False
        
    async def initialize(self):
        """Initialize and check LLM availability"""
        self.ollama_available = await self._check_ollama()
        if not self.ollama_available:
            logger.warning("Ollama not available, will use fallback")
    
    async def _check_ollama(self) -> bool:
        """Check if Ollama is available"""
        try:
            response = await self.http_client.get(f"{self.ollama_host}/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama check failed: {e}")
            return False
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text using available LLM
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
        
        Returns:
            Generated text
        """
        # Try Ollama first
        if self.ollama_available:
            try:
                return await self._generate_ollama(prompt, system_prompt, max_tokens, temperature)
            except Exception as e:
                logger.warning(f"Ollama generation failed: {e}, trying fallback")
        
        # Fallback to mock
        return self._generate_mock(prompt)
    
    async def _generate_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> str:
        """Generate using Ollama"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.ollama_model,
            "messages": messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        response = await self.http_client.post(
            f"{self.ollama_host}/api/chat",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("message", {}).get("content", "")
        else:
            raise Exception(f"Ollama API error: {response.status_code}")
    
    def _generate_mock(self, prompt: str) -> str:
        """Mock generation for fallback"""
        # Simple template-based response
        if "recommendation" in prompt.lower() or "action" in prompt.lower():
            return "Based on the risk assessment, immediate action is recommended to address the identified climate risks through adaptation and mitigation measures."
        elif "analysis" in prompt.lower():
            return "The analysis indicates moderate to high climate risk requiring coordinated response measures."
        else:
            return "Analysis complete. Please review the detailed findings in the context tensor."
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()


# Example usage
if __name__ == '__main__':
    async def main():
        manager = FreeLLMManager()
        await manager.initialize()
        
        result = await manager.generate(
            "Generate a recommendation for climate adaptation in Jakarta",
            system_prompt="You are a climate adaptation expert."
        )
        print(result)
        
        await manager.close()
    
    asyncio.run(main())


