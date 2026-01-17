"""
TERA Configuration Settings
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "TERA"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database
    database_url: str = "postgresql+asyncpg://tera:tera_secure_2025@localhost:5432/tera"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Ollama
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.1:8b"
    
    # ChromaDB
    chroma_url: str = "http://localhost:8000"
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        text = str(value).strip().lower()
        if text in {"true", "1", "yes", "y", "on"}:
            return True
        if text in {"false", "0", "no", "n", "off", "warn", "warning", "error", "info"}:
            return False
        return False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
