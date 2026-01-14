#!/usr/bin/env python3
"""
IPCC Context Engine - Grundlage für Firecrawl und OpenAI Predictions
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


class IPCCContextEngine:
    """IPCC-basierter Kontext für Firecrawl und LLM"""
    
    def __init__(self):
        # IPCC-Kernaussagen (basierend auf AR6)
        self.ipcc_core_findings = {
            "temperature_baseline": {
                "pre_industrial": "1850-1900",
                "current_anomaly": "1.1°C",
                "target_1_5": "1.5°C",
                "target_2": "2.0°C"
            },
            "co2_concentrations": {
                "pre_industrial": 280,  # ppm
                "current": 410,  # ppm (2021)
                "target_net_zero": 2050
            },
            "sea_level_rise": {
                "since_1901": 20,  # cm
                "projection_2100_low": 28,  # cm (SSP1-1.9)
                "projection_2100_high": 101  # cm (SSP5-8.5)
            },
            "key_risks": [
                "Extreme heat events",
                "Heavy precipitation",
                "Drought",
                "Sea level rise",
                "Biodiversity loss",
                "Food insecurity",
                "Water scarcity",
                "Humanitarian crises",
                "Displacement and migration"
            ],
            "vulnerable_regions": [
                "Africa",
                "Small Island States",
                "Arctic",
                "Coastal areas",
                "Mountain regions",
                "Semi-arid areas"
            ]
        }
        
        # IPCC-basierte Keywords für Suche
        self.ipcc_search_keywords = {
            "temperature": [
                "temperature anomaly", "global warming", "heat wave",
                "extreme heat", "temperature increase", "warming trend"
            ],
            "precipitation": [
                "precipitation anomaly", "heavy rainfall", "drought",
                "water scarcity", "monsoon", "extreme precipitation"
            ],
            "sea_level": [
                "sea level rise", "coastal flooding", "ocean warming",
                "glacier melt", "ice sheet"
            ],
            "ecosystems": [
                "biodiversity loss", "ecosystem degradation", "species extinction",
                "habitat loss", "NDVI", "vegetation index"
            ],
            "human_impacts": [
                "food security", "water security", "displacement",
                "migration", "humanitarian crisis", "vulnerability"
            ],
            "emissions": [
                "CO2 concentration", "greenhouse gas emissions", "carbon budget",
                "net zero", "mitigation", "emissions reduction"
            ]
        }
    
    def get_firecrawl_context(
        self,
        record: Dict[str, Any],
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Erstelle IPCC-basierten Kontext für Firecrawl-Suche
        
        Args:
            record: Record aus der Datenbank
            focus_areas: Optional ["temperature", "precipitation", "sea_level", etc.]
        
        Returns:
            Kontext-Dict mit Keywords, Quellen, Kategorien
        """
        region = record.get('region', 'Global')
        title = record.get('title', '')
        summary = record.get('summary', '')
        
        # Bestimme relevante IPCC-Bereiche
        if focus_areas is None:
            focus_areas = self._detect_focus_areas(title + ' ' + summary)
        
        # Baue Keywords auf
        keywords = []
        for area in focus_areas:
            if area in self.ipcc_search_keywords:
                keywords.extend(self.ipcc_search_keywords[area])
        
        # Füge regionale Keywords hinzu
        keywords.append(region)
        keywords.append(f"{region} climate")
        keywords.append(f"{region} IPCC")
        
        # Füge Record-spezifische Keywords hinzu
        record_keywords = self._extract_record_keywords(record)
        keywords.extend(record_keywords)
        
        # Entferne Duplikate
        keywords = list(set(keywords))[:20]  # Limit auf 20
        
        # Bestimme Kategorien für Suche
        categories = []
        if any(kw in keywords for kw in ["research", "study", "analysis"]):
            categories.append("research")
        
        # Bestimme Quellen-Priorität
        sources_priority = [
            "nasa.gov",
            "ipcc.ch",
            "un.org",
            "worldbank.org",
            "nature.com",
            "science.org"
        ]
        
        return {
            "keywords": keywords,
            "categories": categories,
            "sources_priority": sources_priority,
            "ipcc_context": {
                "baseline_period": self.ipcc_core_findings["temperature_baseline"]["pre_industrial"],
                "current_anomaly": self.ipcc_core_findings["temperature_baseline"]["current_anomaly"],
                "target": self.ipcc_core_findings["temperature_baseline"]["target_1_5"]
            },
            "focus_areas": focus_areas,
            "region": region
        }
    
    def get_llm_context(
        self,
        record: Dict[str, Any],
        extracted_numbers: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Erstelle IPCC-basierten Kontext für LLM-Prompts
        
        Args:
            record: Record aus der Datenbank
            extracted_numbers: Optional extrahierte Zahlen
        
        Returns:
            Kontext-String für LLM-Prompt
        """
        region = record.get('region', 'Global')
        
        # IPCC-Baseline-Informationen
        ipcc_context = f"""
## IPCC-Kontext (AR6 - Sechster Sachstandsbericht):

**Temperatur-Baseline:**
- Vorindustriell (1850-1900): Referenzperiode
- Aktuelle Anomalie: {self.ipcc_core_findings['temperature_baseline']['current_anomaly']} über vorindustriellem Niveau
- Paris-Ziel: Begrenzung auf {self.ipcc_core_findings['temperature_baseline']['target_1_5']} (idealerweise) oder {self.ipcc_core_findings['temperature_baseline']['target_2']}

**CO2-Konzentration:**
- Vorindustriell: {self.ipcc_core_findings['co2_concentrations']['pre_industrial']} ppm
- Aktuell (2021): {self.ipcc_core_findings['co2_concentrations']['current']} ppm
- Ziel: Netto-Null bis {self.ipcc_core_findings['co2_concentrations']['target_net_zero']}

**Meeresspiegel-Anstieg:**
- Seit 1901: +{self.ipcc_core_findings['sea_level_rise']['since_1901']} cm
- Projektion 2100 (niedrig): +{self.ipcc_core_findings['sea_level_rise']['projection_2100_low']} cm
- Projektion 2100 (hoch): +{self.ipcc_core_findings['sea_level_rise']['projection_2100_high']} cm

**Hauptrisiken (laut IPCC):**
{chr(10).join(f"- {risk}" for risk in self.ipcc_core_findings['key_risks'][:5])}

**Besonders verwundbare Regionen:**
{chr(10).join(f"- {region}" for region in self.ipcc_core_findings['vulnerable_regions'][:5])}
"""
        
        # Regionale Kontext
        regional_context = f"""
## Regionale Kontext:

**Region:** {region}

**IPCC-Bewertung für diese Region:**
- Regionale Temperaturänderungen sind typischerweise stärker als der globale Durchschnitt
- Landoberflächen erwärmen sich stärker als Meeresoberflächen (Faktor 1.4-1.7)
- Semi-aride Gebiete zeigen besonders starke Erwärmungstrends
"""
        
        # Zahlen-Kontext
        numbers_context = ""
        if extracted_numbers:
            numbers_context = f"""
## Extrahiert Zahlen:

"""
            if extracted_numbers.get('temperatures'):
                temps = extracted_numbers['temperatures']
                avg_temp = sum(temps) / len(temps) if temps else 0
                anomaly = avg_temp - 13.5  # IPCC Baseline ~13.5°C
                numbers_context += f"- Durchschnittstemperatur: {avg_temp:.1f}°C\n"
                numbers_context += f"- Anomalie vs. vorindustriell: {anomaly:.2f}°C\n"
            
            if extracted_numbers.get('precipitation'):
                precip = extracted_numbers['precipitation']
                avg_precip = sum(precip) / len(precip) if precip else 0
                numbers_context += f"- Durchschnittsniederschlag: {avg_precip:.1f} mm\n"
            
            if extracted_numbers.get('affected_people'):
                numbers_context += f"- Betroffene Personen: {extracted_numbers['affected_people']:,}\n"
        
        return ipcc_context + regional_context + numbers_context
    
    def get_ipcc_prompt_template(self, analysis_type: str = "risk") -> str:
        """
        Erstelle IPCC-basierte Prompt-Templates
        
        Args:
            analysis_type: "risk", "trend", "impact", "mitigation"
        
        Returns:
            Prompt-Template
        """
        templates = {
            "risk": """
Analysiere die folgenden Daten im Kontext der IPCC-Bewertungen (AR6):

{ipcc_context}

{record_data}

{extracted_numbers}

**IPCC-basierte Risikobewertung:**

Bewerte das Risiko basierend auf:
1. Abweichung von IPCC-Baseline (vorindustriell 1850-1900)
2. Nähe zu IPCC-Schwellenwerten (1.5°C, 2.0°C)
3. IPCC-identifizierte Hauptrisiken
4. Regionale Vulnerabilität laut IPCC

**Bewertungskriterien (IPCC-basiert):**
- CRITICAL: Überschreitung kritischer Schwellenwerte, irreversible Schäden
- HIGH: Nahe an Schwellenwerten, hohe Vulnerabilität
- MEDIUM: Erhöhtes Risiko, aber Anpassung möglich
- LOW: Geringes Risiko, innerhalb sicherer Grenzen
- MINIMAL: Kein signifikantes Risiko

Antworte im JSON-Format:
{{
    "risk_level": "HIGH",
    "confidence": 0.85,
    "reasoning": "IPCC-basierte Begründung...",
    "ipcc_relevance": "high/medium/low",
    "baseline_comparison": "Anomalie vs. vorindustriell",
    "threshold_proximity": "Nähe zu 1.5°C/2.0°C",
    "timeline": "medium_term",
    "key_factors": ["IPCC-identifizierte Faktoren"],
    "recommendations": ["IPCC-basierte Empfehlungen"]
}}
""",
            "trend": """
Analysiere Trends im Kontext der IPCC-Projektionen (AR6):

{ipcc_context}

{records_data}

**IPCC-basierte Trend-Analyse:**

Vergleiche die beobachteten Trends mit:
1. IPCC-Szenarien (SSP1-1.9, SSP2-4.5, SSP5-8.5)
2. IPCC-Projektionen für diese Region
3. Erwartete Veränderungen laut IPCC

Antworte im JSON-Format:
{{
    "trends": [
        {{
            "region": "...",
            "trend": "increasing/decreasing/stable",
            "ipcc_scenario_match": "SSP1-1.9/SSP2-4.5/SSP5-8.5",
            "confidence": 0.8,
            "description": "IPCC-basierte Beschreibung"
        }}
    ],
    "ipcc_alignment": "Entspricht IPCC-Projektionen",
    "hotspots": ["..."],
    "forecast_3_months": "...",
    "forecast_6_months": "..."
}}
""",
            "impact": """
Bewerte Auswirkungen im Kontext der IPCC-Bewertungen (AR6):

{ipcc_context}

{record_data}

**IPCC-basierte Impact-Bewertung:**

Bewerte basierend auf:
1. IPCC-identifizierten Auswirkungen
2. Vulnerabilität laut IPCC
3. Anpassungsgrenzen (IPCC)
4. Verluste und Schäden (Loss & Damage)

Antworte im JSON-Format:
{{
    "humanitarian_impact": "HIGH",
    "economic_impact": "...",
    "geopolitical_impact": "...",
    "environmental_impact": "...",
    "ipcc_vulnerability_assessment": "...",
    "estimated_affected_people": 1000000,
    "estimated_funding_needed": 500000000
}}
"""
        }
        
        return templates.get(analysis_type, templates["risk"])
    
    def _detect_focus_areas(self, text: str) -> List[str]:
        """Erkenne relevante IPCC-Fokusbereiche aus Text"""
        text_lower = text.lower()
        focus_areas = []
        
        if any(kw in text_lower for kw in ["temperature", "heat", "warming", "anomaly"]):
            focus_areas.append("temperature")
        
        if any(kw in text_lower for kw in ["precipitation", "rain", "drought", "water"]):
            focus_areas.append("precipitation")
        
        if any(kw in text_lower for kw in ["sea level", "coastal", "ocean", "glacier"]):
            focus_areas.append("sea_level")
        
        if any(kw in text_lower for kw in ["biodiversity", "ecosystem", "species", "ndvi", "vegetation"]):
            focus_areas.append("ecosystems")
        
        if any(kw in text_lower for kw in ["food", "water security", "displacement", "migration", "crisis"]):
            focus_areas.append("human_impacts")
        
        if any(kw in text_lower for kw in ["co2", "emissions", "carbon", "mitigation"]):
            focus_areas.append("emissions")
        
        return focus_areas if focus_areas else ["temperature", "precipitation"]  # Default
    
    def _extract_record_keywords(self, record: Dict[str, Any]) -> List[str]:
        """Extrahiere Keywords aus Record"""
        keywords = []
        
        if record.get('title'):
            title_words = record['title'].lower().split()
            keywords.extend([w for w in title_words if len(w) > 4])
        
        if record.get('summary'):
            summary_words = record['summary'].lower().split()
            keywords.extend([w for w in summary_words if len(w) > 4])
        
        if record.get('topics'):
            keywords.extend([t.lower() for t in record['topics']])
        
        return keywords[:10]  # Limit


# Beispiel-Nutzung
if __name__ == "__main__":
    engine = IPCCContextEngine()
    
    test_record = {
        'title': 'Severe drought in East Africa',
        'region': 'East Africa',
        'summary': 'Worst drought in 40 years affecting millions'
    }
    
    # Firecrawl-Kontext
    firecrawl_context = engine.get_firecrawl_context(test_record)
    print("Firecrawl Context:")
    print(json.dumps(firecrawl_context, indent=2))
    
    # LLM-Kontext
    llm_context = engine.get_llm_context(test_record)
    print("\nLLM Context:")
    print(llm_context)

