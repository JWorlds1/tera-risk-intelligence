# config.py - Zentrale Konfiguration
import os
from pathlib import Path
from dotenv import load_dotenv

# Lade .env falls vorhanden
load_dotenv()


class Config:
    """Zentrale Konfiguration für den Scraper"""
    
    # Rate Limiting
    RATE_LIMIT = float(os.getenv('RATE_LIMIT', '1.0'))
    MAX_CONCURRENT = int(os.getenv('MAX_CONCURRENT', '3'))
    
    # Storage
    STORAGE_DIR = os.getenv('STORAGE_DIR', './data')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Timeout-Settings
    HTTP_TIMEOUT = int(os.getenv('HTTP_TIMEOUT', '20'))
    PLAYWRIGHT_TIMEOUT = int(os.getenv('PLAYWRIGHT_TIMEOUT', '30000'))
    
    # AI & LangChain Konfiguration
    OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:latest')  # Verfügbares Modell auf diesem Rechner
    FIRECRAWL_API_KEY = os.getenv('FIRECRAWL_API_KEY', 'fc-a0b3b8aa31244c10b0f15b4f2d570ac7')
    
    # AI Modelle (kostenlos)
    AVAILABLE_MODELS = [
        'llama3.2:latest',  # Verfügbar auf diesem Rechner
        'llama2:7b',
        'mistral:7b', 
        'codellama:7b',
        'llamacpp'
    ]
    
    # AI-Extraktion aktivieren
    ENABLE_AI_EXTRACTION = os.getenv('ENABLE_AI_EXTRACTION', 'true').lower() == 'true'
    AI_CONFIDENCE_THRESHOLD = float(os.getenv('AI_CONFIDENCE_THRESHOLD', '0.7'))
    
    # Whitelisted Domains (zusätzliche können hier hinzugefügt werden)
    ALLOWED_DOMAINS = {
        "earthobservatory.nasa.gov",
        "nasa.gov",  # Root domain für Subdomains
        "press.un.org",
        "un.org",  # Root domain für Subdomains
        "wfp.org",
        "worldbank.org",
    }
    
    # User Agent - besserer Browser-User-Agent für bessere Kompatibilität
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    @classmethod
    def validate(cls):
        """Validiert Konfiguration"""
        assert cls.RATE_LIMIT > 0, "RATE_LIMIT muss > 0 sein"
        assert cls.MAX_CONCURRENT > 0, "MAX_CONCURRENT muss > 0 sein"
        
        # Erstelle Storage-Verzeichnis falls nicht vorhanden
        Path(cls.STORAGE_DIR).mkdir(parents=True, exist_ok=True)


# Validiere beim Import
Config.validate()

