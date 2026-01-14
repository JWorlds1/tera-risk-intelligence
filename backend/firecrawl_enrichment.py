#!/usr/bin/env python3
"""
Firecrawl Enrichment Module - Nutzt Firecrawl zur Datenanreicherung
"""
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import json
import time

try:
    from firecrawl import Firecrawl
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False
    print("Warning: Firecrawl not available. Install with: pip install firecrawl-py")


@dataclass
class CostTracker:
    """Trackt API-Kosten"""
    firecrawl_credits_used: float = 0.0
    openai_tokens_used: int = 0
    openai_cost_usd: float = 0.0
    requests_made: int = 0
    start_time: datetime = None
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()
    
    def add_firecrawl_cost(self, credits: float):
        """Addiere Firecrawl Credits"""
        self.firecrawl_credits_used += credits
        self.requests_made += 1
    
    def add_openai_cost(self, tokens: int, cost_per_1k_tokens: float = 0.01):
        """Addiere OpenAI Kosten (default: $0.01 per 1k tokens für gpt-4o-mini)"""
        self.openai_tokens_used += tokens
        self.openai_cost_usd += (tokens / 1000) * cost_per_1k_tokens
    
    def get_summary(self) -> Dict[str, Any]:
        """Gebe Kosten-Zusammenfassung"""
        runtime = (datetime.now() - self.start_time).total_seconds()
        return {
            "firecrawl_credits_used": self.firecrawl_credits_used,
            "firecrawl_credits_remaining": 20000 - self.firecrawl_credits_used,
            "openai_tokens_used": self.openai_tokens_used,
            "openai_cost_usd": round(self.openai_cost_usd, 4),
            "requests_made": self.requests_made,
            "runtime_seconds": round(runtime, 2)
        }


class FirecrawlEnricher:
    """Nutzt Firecrawl zur Datenanreicherung"""
    
    def __init__(self, api_key: str, cost_tracker: Optional[CostTracker] = None):
        """
        Args:
            api_key: Firecrawl API Key
            cost_tracker: Optional Cost Tracker für Monitoring
        """
        if not FIRECRAWL_AVAILABLE:
            raise ImportError("firecrawl-py not installed. Install with: pip install firecrawl-py")
        
        self.client = Firecrawl(api_key=api_key)
        self.cost_tracker = cost_tracker or CostTracker()
    
    def enrich_with_search(
        self,
        keywords: List[str],
        region: Optional[str] = None,
        limit: int = 10,
        scrape_content: bool = True,
        categories: Optional[List[str]] = None,
        ipcc_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict], float]:
        """
        Suche nach relevanten Informationen basierend auf Keywords
        
        Args:
            keywords: Liste von Keywords/Buzzwords
            region: Region für Suche (z.B. "East Africa", "Germany")
            limit: Anzahl der Ergebnisse
            scrape_content: Ob Content gescraped werden soll
            categories: Optional ["github", "research", "pdf"]
        
        Returns:
            (results, credits_used)
        """
        query = " ".join(keywords)
        
        # Erweitere Query mit IPCC-Kontext
        if ipcc_context:
            # Füge IPCC-relevante Keywords hinzu
            ipcc_keywords = ipcc_context.get('keywords', [])
            if ipcc_keywords:
                query += " " + " ".join(ipcc_keywords[:5])
            
            # Füge Baseline-Information hinzu
            if ipcc_context.get('ipcc_context'):
                query += " IPCC AR6 climate change"
        else:
            # Standard IPCC-Kontext
            query += " IPCC climate change global warming"
        
        try:
            scrape_options = None
            if scrape_content:
                scrape_options = {
                    "formats": ["markdown", "links"],
                    "onlyMainContent": True
                }
            
            search_params = {
                "query": query,
                "limit": limit
            }
            
            if region:
                search_params["location"] = region
            
            if categories:
                search_params["categories"] = categories
            elif ipcc_context and ipcc_context.get('categories'):
                # Nutze Kategorien aus IPCC-Kontext
                search_params["categories"] = ipcc_context['categories']
            else:
                # Standard: Suche in Research-Kategorie für IPCC-Daten
                search_params["categories"] = ["research"]
            
            if scrape_options:
                search_params["scrape_options"] = scrape_options
            
            # Firecrawl Search
            results = self.client.search(**search_params)
            
            # Kosten: 2 credits per 10 search results (ohne Scraping)
            # Mit Scraping: Standard Scraping-Kosten
            credits_used = 2.0 if not scrape_content else (limit * 1.0)  # Schätzung
            self.cost_tracker.add_firecrawl_cost(credits_used)
            
            # Verarbeite Ergebnisse
            enriched_results = []
            if results and isinstance(results, dict):
                web_results = results.get('data', {}).get('web', [])
                for result in web_results:
                    enriched_results.append({
                        'url': result.get('url'),
                        'title': result.get('title'),
                        'description': result.get('description'),
                        'markdown': result.get('markdown'),
                        'links': result.get('links', []),
                        'category': result.get('category'),
                        'source': 'firecrawl_search'
                    })
            
            return enriched_results, credits_used
        
        except Exception as e:
            print(f"Error in Firecrawl search: {e}")
            return [], 0.0
    
    def enrich_with_map(
        self,
        base_url: str,
        location: Optional[Dict[str, str]] = None
    ) -> Tuple[List[str], float]:
        """
        Mappe alle URLs einer Website
        
        Args:
            base_url: Basis-URL der Website
            location: Optional {"country": "US", "languages": ["en"]}
        
        Returns:
            (urls, credits_used)
        """
        try:
            map_params = {"url": base_url}
            if location:
                map_params["location"] = location
            
            result = self.client.map(**map_params)
            
            # Kosten: ~1 credit pro Map-Operation
            credits_used = 1.0
            self.cost_tracker.add_firecrawl_cost(credits_used)
            
            urls = []
            if result and isinstance(result, dict):
                data = result.get('data', {})
                if isinstance(data, list):
                    urls = [item.get('url') for item in data if item.get('url')]
                elif isinstance(data, dict):
                    urls = data.get('links', [])
            
            return urls, credits_used
        
        except Exception as e:
            print(f"Error in Firecrawl map: {e}")
            return [], 0.0
    
    def enrich_with_crawl(
        self,
        start_url: str,
        max_depth: int = 2,
        limit: int = 50,
        scrape_options: Optional[Dict] = None
    ) -> Tuple[List[Dict], float]:
        """
        Crawle eine Website
        
        Args:
            start_url: Start-URL
            max_depth: Maximale Crawl-Tiefe
            limit: Maximale Anzahl von Seiten
            scrape_options: Optional Scraping-Optionen
        
        Returns:
            (crawled_data, credits_used)
        """
        try:
            # Firecrawl API v1 Syntax
            crawl_params = {
                "url": start_url,
                "maxDepth": max_depth,
                "limit": limit
            }
            
            if scrape_options:
                crawl_params.update(scrape_options)
            else:
                crawl_params.update({
                    "formats": ["markdown"],
                    "onlyMainContent": True
                })
            
            result = self.client.crawl_url(**crawl_params) if hasattr(self.client, 'crawl_url') else self.client.crawl(**crawl_params)
            
            # Kosten: ~1 credit pro gecrawlte Seite
            credits_used = min(limit, 50) * 1.0  # Schätzung
            self.cost_tracker.add_firecrawl_cost(credits_used)
            
            crawled_data = []
            if result and isinstance(result, dict):
                data = result.get('data', [])
                if isinstance(data, list):
                    crawled_data = data
            
            return crawled_data, credits_used
        
        except Exception as e:
            print(f"Error in Firecrawl crawl: {e}")
            return [], 0.0
    
    def enrich_with_extract(
        self,
        url: str,
        extraction_schema: Dict[str, Any],
        location: Optional[Dict[str, str]] = None
    ) -> Tuple[Dict, float]:
        """
        Agent-basierte Extraktion mit Schema
        
        Args:
            url: URL zum Extrahieren
            extraction_schema: Schema für Extraktion (siehe Firecrawl Extract Docs)
            location: Optional Location-Settings
        
        Returns:
            (extracted_data, credits_used)
        """
        try:
            # Firecrawl extract API - korrekte Syntax
            if hasattr(self.client, 'extract_url'):
                result = self.client.extract_url(url=url, schema=extraction_schema)
            elif hasattr(self.client, 'extract'):
                result = self.client.extract(url=url, schema=extraction_schema)
            else:
                # Fallback: Verwende scrape_url mit extract-Parameter
                result = self.client.scrape_url(
                    url=url,
                    params={
                        "formats": ["markdown"],
                        "onlyMainContent": True,
                        "extract": extraction_schema
                    }
                )
            
            # Kosten: ~2-5 credits pro Extract (abhängig von Komplexität)
            credits_used = 3.0  # Schätzung
            self.cost_tracker.add_firecrawl_cost(credits_used)
            
            extracted_data = {}
            if result and isinstance(result, dict):
                extracted_data = result.get('data', {})
            
            return extracted_data, credits_used
        
        except Exception as e:
            print(f"Error in Firecrawl extract: {e}")
            return {}, 0.0
    
    def enrich_record(
        self,
        record: Dict[str, Any],
        use_search: bool = True,
        use_extract: bool = True,
        ipcc_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Reichere einen Record mit Firecrawl-Daten an (IPCC-basiert)
        
        Args:
            record: Record aus der Datenbank
            use_search: Ob Web-Suche verwendet werden soll
            use_extract: Ob Agent-basierte Extraktion verwendet werden soll
            ipcc_context: Optional IPCC-Kontext für bessere Suche
        
        Returns:
            Angereicherter Record
        """
        enriched = record.copy()
        enriched['firecrawl_enrichment'] = {
            'enriched_at': datetime.now().isoformat(),
            'methods_used': [],
            'ipcc_based': ipcc_context is not None
        }
        
        # Extrahiere Keywords aus Record
        keywords = self._extract_keywords(record)
        
        # Nutze IPCC-Kontext Keywords falls vorhanden
        if ipcc_context and ipcc_context.get('keywords'):
            keywords = list(set(keywords + ipcc_context['keywords'][:10]))
        
        # 1. Web-Suche für zusätzliche Informationen (IPCC-basiert)
        if use_search and keywords:
            try:
                search_results, credits = self.enrich_with_search(
                    keywords=keywords,
                    region=record.get('region'),
                    limit=5,
                    scrape_content=True,
                    ipcc_context=ipcc_context  # IPCC-Kontext übergeben
                )
                enriched['firecrawl_enrichment']['search_results'] = search_results
                enriched['firecrawl_enrichment']['methods_used'].append('search')
                enriched['firecrawl_enrichment']['search_credits'] = credits
            except Exception as e:
                print(f"Search enrichment failed: {e}")
        
        # 2. Agent-basierte Extraktion wenn URL vorhanden (IPCC-basiert)
        if use_extract and record.get('url'):
            try:
                # Schema für Climate/Conflict-Daten mit IPCC-Fokus
                schema = {
                    "type": "object",
                    "properties": {
                        "temperatures": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Temperaturen in Celsius (IPCC-Baseline: vorindustriell 1850-1900)"
                        },
                        "temperature_anomaly": {
                            "type": "number",
                            "description": "Temperatur-Anomalie vs. vorindustriell in °C"
                        },
                        "precipitation": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Niederschlag in mm"
                        },
                        "precipitation_anomaly": {
                            "type": "number",
                            "description": "Niederschlags-Anomalie in Prozent"
                        },
                        "ndvi_anomaly": {
                            "type": "number",
                            "description": "NDVI-Anomalie (Vegetationsindex)"
                        },
                        "co2_concentration": {
                            "type": "number",
                            "description": "CO2-Konzentration in ppm (IPCC-Baseline: 280 ppm vorindustriell)"
                        },
                        "affected_population": {
                            "type": "number",
                            "description": "Anzahl betroffener Personen"
                        },
                        "funding_amount": {
                            "type": "number",
                            "description": "Finanzierungsbetrag in USD"
                        },
                        "risk_indicators": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "IPCC-identifizierte Risiko-Indikatoren"
                        },
                        "ipcc_findings": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Relevante IPCC-Erkenntnisse (AR6)"
                        },
                        "key_events": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Wichtige klimabezogene Ereignisse"
                        }
                    }
                }
                
                extracted, credits = self.enrich_with_extract(
                    url=record['url'],
                    extraction_schema=schema
                )
                enriched['firecrawl_enrichment']['extracted_data'] = extracted
                enriched['firecrawl_enrichment']['methods_used'].append('extract')
                enriched['firecrawl_enrichment']['extract_credits'] = credits
            except Exception as e:
                print(f"Extract enrichment failed: {e}")
        
        return enriched
    
    def _extract_keywords(self, record: Dict[str, Any]) -> List[str]:
        """Extrahiere Keywords aus Record"""
        keywords = []
        
        # Aus Titel
        if record.get('title'):
            title_words = record['title'].lower().split()
            keywords.extend([w for w in title_words if len(w) > 4])
        
        # Aus Summary
        if record.get('summary'):
            summary_words = record['summary'].lower().split()
            keywords.extend([w for w in summary_words if len(w) > 4])
        
        # Aus Region
        if record.get('region'):
            keywords.append(record['region'].lower())
        
        # Aus Topics
        if record.get('topics'):
            keywords.extend([t.lower() for t in record['topics']])
        
        # Entferne Duplikate und häufige Stopwords
        stopwords = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'}
        keywords = [k for k in set(keywords) if k not in stopwords and len(k) > 3]
        
        return keywords[:10]  # Limit auf 10 Keywords


# Beispiel-Nutzung
if __name__ == "__main__":
    api_key = os.getenv("FIRECRAWL_API_KEY", "fc-a0b3b8aa31244c10b0f15b4f2d570ac7")
    
    enricher = FirecrawlEnricher(api_key)
    
    # Test Search
    print("Testing Firecrawl Search...")
    results, credits = enricher.enrich_with_search(
        keywords=["drought", "East Africa", "climate"],
        limit=3
    )
    print(f"Found {len(results)} results, used {credits} credits")
    
    # Kosten-Zusammenfassung
    print("\nCost Summary:")
    print(json.dumps(enricher.cost_tracker.get_summary(), indent=2))

