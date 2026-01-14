"""
TERA Configuration Settings
Pydantic-based configuration management
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    APP_NAME: str = "TERA"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://tera:tera_secure_2025@localhost:5432/tera"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Ollama LLM
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"  # Use 8b for 62GB RAM, 70b needs 128GB+
    OLLAMA_TIMEOUT: int = 120
    
    # ChromaDB
    CHROMA_URL: str = "http://localhost:8000"
    CHROMA_COLLECTION: str = "tera_vectors"
    
    # Scraping
    SCRAPE_RATE_LIMIT: float = 1.0  # requests per second
    SCRAPE_MAX_CONCURRENT: int = 5
    USER_AGENT: str = "TERA-Bot/1.0 (Environmental Research)"
    
    # Risk Calculation
    RISK_SPILLOVER_FACTOR: float = 0.2
    HIGH_RISK_THRESHOLD: float = 8.0
    
    # Paths
    DATA_DIR: str = "/app/data"
    IMAGES_DIR: str = "/app/data/images"
    MODELS_DIR: str = "/app/data/models"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()


settings = get_settings()

