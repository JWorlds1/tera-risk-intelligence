#!/usr/bin/env python3
"""
IPCC-basierte Anreicherungs-Agenten
Agentenbasiertes System zur Anreicherung mit IPCC-Daten, Satellitenbildern, Echtzeit-Zuständen
"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
import time

sys.path.append(str(Path(__file__).parent))

from firecrawl_enrichment import FirecrawlEnricher, CostTracker
from data_extraction import NumberExtractor
from llm_predictions import LLMPredictor


@dataclass
class EnrichmentData:
    """Strukturierte Anreicherungsdaten"""
    # IPCC-basierte Metriken
    temperature_anomaly: Optional[float] = None  # Temperatur-Anomalie vs. vorindustriell
    precipitation_anomaly: Optional[float] = None  # Niederschlags-Anomalie
    ndvi_anomaly: Optional[float] = None  # NDVI-Anomalie (Vegetation)
    sea_level_rise: Optional[float] = None  # Meeresspiegel-Anstieg in cm
    co2_concentration: Optional[float] = None  # CO2-Konzentration in ppm
    
    # Risiko-Indikatoren
    climate_risk_score: Optional[float] = None
    conflict_risk_score: Optional[float] = None
    vulnerability_score: Optional[float] = None
    
    # Echtzeit-Daten
    current_temperature: Optional[float] = None
    current_precipitation: Optional[float] = None
    affected_population: Optional[int] = None
    
    # Fakten & Realitäten
    key_facts: List[str] = None
    ipcc_findings: List[str] = None
    real_time_conditions: Dict[str, Any] = None
    
    # Bilder & Visualisierungen
    satellite_images: List[str] = None  # URLs zu Satellitenbildern
    ndvi_maps: List[str] = None  # URLs zu NDVI-Karten
    
    # Dynamische Trends
    trends: Dict[str, str] = None  # {"temperature": "increasing", "precipitation": "decreasing"}
    
    def __post_init__(self):
        if self.key_facts is None:
            self.key_facts = []
        if self.ipcc_findings is None:
            self.ipcc_findings = []
        if self.real_time_conditions is None:
            self.real_time_conditions = {}
        if self.satellite_images is None:
            self.satellite_images = []
        if self.ndvi_maps is None:
            self.ndvi_maps = []
        if self.trends is None:
            self.trends = {}


class IPCCEnrichmentAgent:
    """Agent für IPCC-basierte Datenanreicherung"""
    
    def __init__(self, firecrawl_api_key: str, openai_api_key: Optional[str] = None):
        self.firecrawl_enricher = FirecrawlEnricher(firecrawl_api_key)
        self.number_extractor = NumberExtractor()
        self.llm_predictor = LLMPredictor(
            provider="openai",
            model="gpt-4o-mini",
            cost_tracker=self.firecrawl_enricher.cost_tracker
        )
        
        # IPCC-basierte Keywords für Suche
        self.ipcc_keywords = [
            "IPCC", "climate change", "global warming", "temperature anomaly",
            "precipitation anomaly", "sea level rise", "CO2 concentration",
            "NDVI", "vegetation index", "drought", "flood", "extreme weather"
        ]
    
    def enrich_with_ipcc_data(
        self,
        region: str,
        record: Dict[str, Any]
    ) -> EnrichmentData:
        """Reichere mit IPCC-basierten Daten an"""
        enrichment = EnrichmentData()
        
        # 1. Suche nach IPCC-relevanten Daten
        search_keywords = self._build_ipcc_keywords(region, record)
        search_results, _ = self.firecrawl_enricher.enrich_with_search(
            keywords=search_keywords,
            region=region,
            limit=10,
            scrape_content=True,
            categories=["research"]  # Suche in wissenschaftlichen Quellen
        )
        
        # 2. Extrahiere Zahlen aus Search-Results
        combined_text = self._combine_search_results(search_results)
        extracted_numbers = self.number_extractor.extract_all(combined_text)
        
        # 3. Analysiere mit LLM für IPCC-Findings
        ipcc_findings = self._extract_ipcc_findings(record, search_results)
        
        # 4. Berechne Anomalien basierend auf IPCC-Baseline
        enrichment.temperature_anomaly = self._calculate_temperature_anomaly(
            extracted_numbers.temperatures
        )
        enrichment.precipitation_anomaly = self._calculate_precipitation_anomaly(
            extracted_numbers.precipitation
        )
        enrichment.ndvi_anomaly = self._extract_ndvi_anomaly(combined_text)
        enrichment.co2_concentration = self._extract_co2_concentration(combined_text)
        
        # 5. Echtzeit-Daten
        enrichment.current_temperature = extracted_numbers.temperatures[0] if extracted_numbers.temperatures else None
        enrichment.current_precipitation = extracted_numbers.precipitation[0] if extracted_numbers.precipitation else None
        enrichment.affected_population = extracted_numbers.affected_people
        
        # 6. Fakten & Realitäten
        enrichment.key_facts = self._extract_key_facts(search_results)
        enrichment.ipcc_findings = ipcc_findings
        enrichment.real_time_conditions = self._extract_real_time_conditions(search_results)
        
        # 7. Trends
        enrichment.trends = self._analyze_trends(search_results, extracted_numbers)
        
        return enrichment
    
    def enrich_with_satellite_data(
        self,
        region: str,
        coordinates: Optional[Tuple[float, float]] = None
    ) -> Dict[str, Any]:
        """Reichere mit Satellitenbildern und NDVI-Daten an"""
        # Suche nach Satellitenbildern
        satellite_keywords = [
            f"{region} satellite",
            f"{region} NDVI",
            f"{region} vegetation index",
            f"{region} NASA Earth Observatory"
        ]
        
        # Suche nach Bildern
        image_results, _ = self.firecrawl_enricher.enrich_with_search(
            keywords=satellite_keywords,
            limit=5,
            scrape_content=False
        )
        
        # Extrahiere Bild-URLs
        satellite_images = []
        ndvi_maps = []
        
        for result in image_results:
            if 'nasa' in result.get('url', '').lower() or 'earthobservatory' in result.get('url', '').lower():
                satellite_images.append(result.get('url'))
            if 'ndvi' in result.get('title', '').lower() or 'vegetation' in result.get('title', '').lower():
                ndvi_maps.append(result.get('url'))
        
        return {
            "satellite_images": satellite_images[:5],
            "ndvi_maps": ndvi_maps[:5],
            "region": region,
            "coordinates": coordinates
        }
    
    def enrich_with_real_time_data(
        self,
        region: str,
        record: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Reichere mit Echtzeit-Daten an"""
        # Suche nach aktuellen Daten (letzte 24 Stunden)
        real_time_keywords = [
            f"{region} current conditions",
            f"{region} weather today",
            f"{region} latest news",
            f"{region} crisis update"
        ]
        
        # Firecrawl Search mit Zeitfilter
        search_results, _ = self.firecrawl_enricher.enrich_with_search(
            keywords=real_time_keywords,
            region=region,
            limit=10,
            scrape_content=True
        )
        
        # Extrahiere Echtzeit-Informationen
        real_time_data = {
            "timestamp": datetime.now().isoformat(),
            "region": region,
            "sources": [r.get('url') for r in search_results],
            "conditions": self._extract_real_time_conditions(search_results),
            "updates": []
        }
        
        for result in search_results:
            if result.get('markdown'):
                # Extrahiere aktuelle Zahlen
                text = result.get('markdown', '')[:1000]
                extracted = self.number_extractor.extract_all(text)
                
                update = {
                    "source": result.get('url'),
                    "title": result.get('title'),
                    "temperatures": extracted.temperatures,
                    "precipitation": extracted.precipitation,
                    "affected_people": extracted.affected_people,
                    "timestamp": datetime.now().isoformat()
                }
                real_time_data["updates"].append(update)
        
        return real_time_data
    
    def _build_ipcc_keywords(self, region: str, record: Dict[str, Any]) -> List[str]:
        """Baue IPCC-relevante Keywords"""
        keywords = [region]
        
        # Füge Record-spezifische Keywords hinzu
        if record.get('title'):
            title_words = record['title'].lower().split()
            keywords.extend([w for w in title_words if len(w) > 4])
        
        # IPCC-spezifische Keywords
        keywords.extend(self.ipcc_keywords)
        
        return keywords[:15]  # Limit
    
    def _combine_search_results(self, search_results: List[Dict]) -> str:
        """Kombiniere Search-Results zu Text"""
        texts = []
        for result in search_results:
            texts.append(result.get('title', ''))
            texts.append(result.get('description', ''))
            if result.get('markdown'):
                texts.append(result.get('markdown', '')[:2000])  # Limit
        return ' '.join(texts)
    
    def _extract_ipcc_findings(self, record: Dict, search_results: List[Dict]) -> List[str]:
        """Extrahiere IPCC-Findings mit LLM"""
        combined_text = self._combine_search_results(search_results)
        
        prompt = f"""Analysiere die folgenden Daten im Kontext der IPCC-Berichte:

Region: {record.get('region', 'N/A')}
Titel: {record.get('title', 'N/A')}

Daten:
{combined_text[:3000]}

Identifiziere die wichtigsten IPCC-relevanten Erkenntnisse:
1. Temperatur-Anomalien vs. vorindustriellem Niveau
2. Niederschlags-Veränderungen
3. Meeresspiegel-Anstieg
4. CO2-Konzentrationen
5. Extreme Wetterereignisse
6. Ökosystem-Veränderungen

Antworte im JSON-Format:
{{
    "findings": [
        "Finding 1",
        "Finding 2",
        ...
    ],
    "temperature_anomaly": 1.1,
    "precipitation_change": "+5%",
    "ipcc_relevance": "high/medium/low"
}}
"""
        
        try:
            response = self.llm_predictor._call_llm(prompt)
            data = json.loads(response)
            return data.get('findings', [])
        except:
            return []
    
    def _calculate_temperature_anomaly(self, temperatures: List[float]) -> Optional[float]:
        """Berechne Temperatur-Anomalie vs. vorindustriell (1850-1900 Baseline)"""
        if not temperatures:
            return None
        
        # IPCC Baseline: 1850-1900 Durchschnitt
        baseline = 13.5  # °C globale Durchschnittstemperatur vorindustriell
        
        # Berechne Anomalie
        avg_temp = sum(temperatures) / len(temperatures)
        anomaly = avg_temp - baseline
        
        return round(anomaly, 2)
    
    def _calculate_precipitation_anomaly(self, precipitation: List[float]) -> Optional[float]:
        """Berechne Niederschlags-Anomalie"""
        if not precipitation:
            return None
        
        # Vereinfachte Berechnung (kann mit historischen Daten verbessert werden)
        avg_precip = sum(precipitation) / len(precipitation)
        
        # Normalisierte Anomalie (in Prozent)
        # Annahme: Normal = 100mm/Monat
        normal = 100.0
        anomaly_percent = ((avg_precip - normal) / normal) * 100
        
        return round(anomaly_percent, 2)
    
    def _extract_ndvi_anomaly(self, text: str) -> Optional[float]:
        """Extrahiere NDVI-Anomalie aus Text"""
        import re
        
        # Suche nach NDVI-Anomalie-Patterns
        patterns = [
            r'ndvi[-\s]?anomaly[:\s]+(-?\d+\.?\d*)',
            r'anomaly[:\s]+(-?\d+\.?\d*).*ndvi',
            r'ndvi[:\s]+(-?\d+\.?\d*)',
        ]
        
        text_lower = text.lower()
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    return float(match.group(1))
                except:
                    continue
        
        return None
    
    def _extract_co2_concentration(self, text: str) -> Optional[float]:
        """Extrahiere CO2-Konzentration aus Text"""
        import re
        
        patterns = [
            r'co2[:\s]+(\d+)\s*ppm',
            r'carbon\s+dioxide[:\s]+(\d+)\s*ppm',
            r'(\d+)\s*ppm\s*co2',
        ]
        
        text_lower = text.lower()
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    return float(match.group(1))
                except:
                    continue
        
        return None
    
    def _extract_key_facts(self, search_results: List[Dict]) -> List[str]:
        """Extrahiere wichtige Fakten"""
        facts = []
        
        for result in search_results[:5]:
            if result.get('description'):
                facts.append(result['description'][:200])
        
        return facts
    
    def _extract_real_time_conditions(self, search_results: List[Dict]) -> Dict[str, Any]:
        """Extrahiere Echtzeit-Zustände"""
        conditions = {
            "sources_count": len(search_results),
            "latest_update": datetime.now().isoformat(),
            "key_indicators": []
        }
        
        for result in search_results:
            if result.get('title'):
                conditions["key_indicators"].append(result['title'][:100])
        
        return conditions
    
    def _analyze_trends(
        self,
        search_results: List[Dict],
        extracted_numbers: Any
    ) -> Dict[str, str]:
        """Analysiere Trends"""
        trends = {}
        
        # Temperatur-Trend
        if extracted_numbers.temperatures:
            temps = extracted_numbers.temperatures
            if len(temps) > 1:
                if temps[-1] > temps[0]:
                    trends["temperature"] = "increasing"
                elif temps[-1] < temps[0]:
                    trends["temperature"] = "decreasing"
                else:
                    trends["temperature"] = "stable"
        
        # Niederschlags-Trend
        if extracted_numbers.precipitation:
            precip = extracted_numbers.precipitation
            if len(precip) > 1:
                if precip[-1] > precip[0]:
                    trends["precipitation"] = "increasing"
                elif precip[-1] < precip[0]:
                    trends["precipitation"] = "decreasing"
                else:
                    trends["precipitation"] = "stable"
        
        return trends


class DynamicEnrichmentOrchestrator:
    """Orchestriert alle Anreicherungs-Agenten"""
    
    def __init__(self, firecrawl_api_key: str, openai_api_key: Optional[str] = None):
        self.ipcc_agent = IPCCEnrichmentAgent(firecrawl_api_key, openai_api_key)
        self.cost_tracker = self.ipcc_agent.firecrawl_enricher.cost_tracker
    
    def enrich_record_comprehensive(
        self,
        record: Dict[str, Any],
        use_ipcc: bool = True,
        use_satellite: bool = True,
        use_real_time: bool = True
    ) -> Dict[str, Any]:
        """Umfassende Anreicherung eines Records"""
        region = record.get('region', 'Global')
        
        enrichment_result = {
            "record_id": record.get('id'),
            "region": region,
            "enriched_at": datetime.now().isoformat(),
            "ipcc_data": {},
            "satellite_data": {},
            "real_time_data": {},
            "combined_enrichment": {}
        }
        
        # 1. IPCC-basierte Anreicherung
        if use_ipcc:
            try:
                ipcc_enrichment = self.ipcc_agent.enrich_with_ipcc_data(region, record)
                enrichment_result["ipcc_data"] = asdict(ipcc_enrichment)
            except Exception as e:
                print(f"IPCC enrichment failed: {e}")
        
        # 2. Satelliten-Daten
        if use_satellite:
            try:
                satellite_data = self.ipcc_agent.enrich_with_satellite_data(region)
                enrichment_result["satellite_data"] = satellite_data
            except Exception as e:
                print(f"Satellite enrichment failed: {e}")
        
        # 3. Echtzeit-Daten
        if use_real_time:
            try:
                real_time_data = self.ipcc_agent.enrich_with_real_time_data(region, record)
                enrichment_result["real_time_data"] = real_time_data
            except Exception as e:
                print(f"Real-time enrichment failed: {e}")
        
        # 4. Kombiniere alle Daten
        enrichment_result["combined_enrichment"] = self._combine_enrichments(
            enrichment_result["ipcc_data"],
            enrichment_result["satellite_data"],
            enrichment_result["real_time_data"]
        )
        
        # 5. Kosten-Tracking
        enrichment_result["costs"] = self.cost_tracker.get_summary()
        
        return enrichment_result
    
    def _combine_enrichments(
        self,
        ipcc_data: Dict,
        satellite_data: Dict,
        real_time_data: Dict
    ) -> Dict[str, Any]:
        """Kombiniere alle Anreicherungen"""
        combined = {
            "metrics": {},
            "visualizations": [],
            "facts": [],
            "trends": {},
            "risk_indicators": {}
        }
        
        # Metriken
        if ipcc_data.get('temperature_anomaly'):
            combined["metrics"]["temperature_anomaly"] = ipcc_data['temperature_anomaly']
        if ipcc_data.get('ndvi_anomaly'):
            combined["metrics"]["ndvi_anomaly"] = ipcc_data['ndvi_anomaly']
        if ipcc_data.get('current_temperature'):
            combined["metrics"]["current_temperature"] = ipcc_data['current_temperature']
        
        # Visualisierungen
        if satellite_data.get('satellite_images'):
            combined["visualizations"].extend(satellite_data['satellite_images'])
        if satellite_data.get('ndvi_maps'):
            combined["visualizations"].extend(satellite_data['ndvi_maps'])
        
        # Fakten
        if ipcc_data.get('key_facts'):
            combined["facts"].extend(ipcc_data['key_facts'])
        if ipcc_data.get('ipcc_findings'):
            combined["facts"].extend(ipcc_data['ipcc_findings'])
        
        # Trends
        if ipcc_data.get('trends'):
            combined["trends"] = ipcc_data['trends']
        
        # Risiko-Indikatoren
        if ipcc_data.get('climate_risk_score'):
            combined["risk_indicators"]["climate_risk"] = ipcc_data['climate_risk_score']
        if ipcc_data.get('conflict_risk_score'):
            combined["risk_indicators"]["conflict_risk"] = ipcc_data['conflict_risk_score']
        
        return combined


# Beispiel-Nutzung
if __name__ == "__main__":
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY", "fc-a0b3b8aa31244c10b0f15b4f2d570ac7")
    openai_key = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY_HERE")
    
    orchestrator = DynamicEnrichmentOrchestrator(firecrawl_key, openai_key)
    
    test_record = {
        'id': 1,
        'title': 'Drought conditions in East Africa',
        'region': 'East Africa',
        'summary': 'Severe drought affecting millions'
    }
    
    result = orchestrator.enrich_record_comprehensive(test_record)
    print(json.dumps(result, indent=2, default=str))

