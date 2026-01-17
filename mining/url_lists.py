# url_lists.py - URL Management for Climate Conflict Early Warning System
from typing import Dict, List
import structlog

logger = structlog.get_logger(__name__)


class URLManager:
    """Manages URLs for all data sources"""
    
    def __init__(self):
        self.sources = {
            "NASA": {
                "base_url": "https://earthobservatory.nasa.gov",
                "urls": [
                    "https://earthobservatory.nasa.gov/global-maps",
                    "https://earthobservatory.nasa.gov/world-of-change",
                    "https://earthobservatory.nasa.gov/features",
                    "https://earthobservatory.nasa.gov/images",
                    "https://earthobservatory.nasa.gov/EO/EO_Archive.php",
                ]
            },
            "UN Press": {
                "base_url": "https://press.un.org/en",
                "urls": [
                    "https://press.un.org/en/content/press-releases",
                    "https://press.un.org/en/content/meetings-coverage",
                    "https://press.un.org/en/content/statements",
                    "https://press.un.org/en/content/briefings",
                ]
            },
            "WFP": {
                "base_url": "https://www.wfp.org/news",
                "urls": [
                    "https://www.wfp.org/news",
                    "https://www.wfp.org/news/press-release",
                    "https://www.wfp.org/news/story",
                    "https://www.wfp.org/news/feature",
                ]
            },
            "World Bank": {
                "base_url": "https://www.worldbank.org/en/news",
                "urls": [
                    "https://www.worldbank.org/en/news",
                    "https://www.worldbank.org/en/news/press-release",
                    "https://www.worldbank.org/en/news/feature",
                    "https://www.worldbank.org/en/news/speech",
                ]
            }
        }
    
    def get_all_urls(self) -> Dict[str, List[str]]:
        """Get all URLs organized by source"""
        return {source: data["urls"] for source, data in self.sources.items()}
    
    def get_source_urls(self, source_name: str) -> List[str]:
        """Get URLs for a specific source"""
        return self.sources.get(source_name, {}).get("urls", [])
    
    def get_urls_for_source(self, source: str) -> List[str]:
        """Get URLs for a specific source with mapping"""
        # Map lowercase to uppercase keys
        source_mapping = {
            'nasa': 'NASA',
            'un': 'UN Press',
            'wfp': 'WFP',
            'worldbank': 'World Bank'
        }
        
        source_key = source_mapping.get(source.lower(), source.upper())
        return self.sources.get(source_key, {}).get("urls", [])
    
    def add_url(self, source_name: str, url: str):
        """Add a URL to a specific source"""
        if source_name in self.sources:
            self.sources[source_name]["urls"].append(url)
        else:
            self.sources[source_name] = {"base_url": "", "urls": [url]}
    
    def get_stats(self) -> Dict[str, int]:
        """Get URL statistics"""
        return {
            source: len(data["urls"]) 
            for source, data in self.sources.items()
        }