#!/usr/bin/env python3
"""
LLM Prediction Module - Nutzt LLMs für semantische Analysen und Vorhersagen
"""
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import json

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI not available. Install with: pip install openai")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


@dataclass
class LLMPrediction:
    """LLM-basierte Vorhersage"""
    record_id: int
    prediction_type: str  # "risk", "trend", "impact", "urgency"
    prediction_text: str
    confidence: float  # 0.0 - 1.0
    reasoning: str
    predicted_timeline: Optional[str] = None  # "short_term", "medium_term", "long_term"
    key_factors: List[str] = None
    recommendations: List[str] = None
    
    def __post_init__(self):
        if self.key_factors is None:
            self.key_factors = []
        if self.recommendations is None:
            self.recommendations = []


class LLMPredictor:
    """Nutzt LLMs für semantische Analysen und Vorhersagen"""
    
    def __init__(self, provider: str = "openai", model: str = "gpt-4o-mini", cost_tracker=None):
        """
        Args:
            provider: "openai" oder "anthropic"
            model: Modellname (z.B. "gpt-4o-mini", "claude-3-haiku")
        """
        self.provider = provider
        self.model = model
        self.cost_tracker = cost_tracker
        
        if provider == "openai" and OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self.client = OpenAI(api_key=api_key)
        elif provider == "anthropic" and ANTHROPIC_AVAILABLE:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            self.client = None
            print(f"Warning: {provider} not available. Using mock predictions.")
    
    def predict_risk(self, record: Dict[str, Any], extracted_numbers: Dict[str, Any], ipcc_context: Optional[str] = None) -> LLMPrediction:
        """Vorhersage des Risikos basierend auf Text und Zahlen mit IPCC-Kontext"""
        text_content = self._combine_text_fields(record)
        numbers_summary = self._format_numbers_summary(extracted_numbers)
        
        # Füge IPCC-Kontext hinzu falls vorhanden
        ipcc_section = ""
        if ipcc_context:
            ipcc_section = f"\n\n{ipcc_context}\n\n"
        
        prompt = f"""Analysiere das folgende Dokument im Kontext der IPCC-Bewertungen (AR6 - Sechster Sachstandsbericht) und Klima- und Konfliktrisiken:
{ipcc_section}

Titel: {record.get('title', 'N/A')}
Zusammenfassung: {record.get('summary', 'N/A')}
Region: {record.get('region', 'N/A')}
Quelle: {record.get('source_name', 'N/A')}

Extrahiert Zahlen:
{numbers_summary}

Volltext (Auszug):
{text_content[:2000]}

**IPCC-basierte Bewertung:**

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
"""
        
        response = self._call_llm(prompt)
        return self._parse_risk_prediction(response, record.get('id'))
    
    def predict_trend(self, records: List[Dict[str, Any]], time_window_days: int = 90, ipcc_context: Optional[str] = None) -> Dict[str, Any]:
        """Vorhersage von Trends basierend auf mehreren Records mit IPCC-Kontext"""
        if not records:
            return {"error": "No records provided"}
        
        # Gruppiere nach Region/Quelle
        records_summary = self._summarize_records(records)
        
        # Füge IPCC-Kontext hinzu
        ipcc_section = ""
        if ipcc_context:
            ipcc_section = f"\n\n{ipcc_context}\n\n"
        
        prompt = f"""Analysiere die folgenden Klima- und Konflikt-Daten aus den letzten {time_window_days} Tagen im Kontext der IPCC-Projektionen (AR6):
{ipcc_section}

{records_summary}

**IPCC-basierte Trend-Analyse:**

Vergleiche die beobachteten Trends mit:
1. IPCC-Szenarien (SSP1-1.9, SSP2-4.5, SSP5-8.5)
2. IPCC-Projektionen für diese Region
3. Erwartete Veränderungen laut IPCC

Bitte identifiziere:
1. Haupttrends (steigend, fallend, stabil) im Vergleich zu IPCC-Projektionen
2. Regionale Hotspots (IPCC-identifizierte verwundbare Regionen)
3. Eskalationsrisiken (Nähe zu IPCC-Schwellenwerten)
4. Zeitliche Vorhersage für die nächsten 3-6 Monate

Antworte im JSON-Format:
{{
    "trends": [
        {{
            "region": "...",
            "trend": "increasing",
            "ipcc_scenario_match": "SSP1-1.9/SSP2-4.5/SSP5-8.5",
            "risk_type": "climate",
            "confidence": 0.8,
            "description": "IPCC-basierte Beschreibung"
        }}
    ],
    "ipcc_alignment": "Entspricht IPCC-Projektionen",
    "hotspots": ["..."],
    "escalation_risks": ["..."],
    "forecast_3_months": "...",
    "forecast_6_months": "..."
}}
"""
        
        response = self._call_llm(prompt)
        return self._parse_trend_prediction(response)
    
    def predict_impact(self, record: Dict[str, Any], extracted_numbers: Dict[str, Any]) -> Dict[str, Any]:
        """Vorhersage der Auswirkungen"""
        text_content = self._combine_text_fields(record)
        numbers_summary = self._format_numbers_summary(extracted_numbers)
        
        prompt = f"""Bewerte die potenziellen Auswirkungen dieses Ereignisses:

Titel: {record.get('title', 'N/A')}
Zusammenfassung: {record.get('summary', 'N/A')}
Region: {record.get('region', 'N/A')}

Extrahiert Zahlen:
{numbers_summary}

Volltext:
{text_content[:2000]}

Bitte bewerte:
1. Humanitäre Auswirkungen (Hoch/Mittel/Niedrig)
2. Wirtschaftliche Auswirkungen
3. Geopolitische Auswirkungen
4. Umweltauswirkungen
5. Geschätzte Anzahl betroffener Menschen
6. Geschätzter finanzieller Bedarf

Antworte im JSON-Format:
{{
    "humanitarian_impact": "HIGH",
    "economic_impact": "...",
    "geopolitical_impact": "...",
    "environmental_impact": "...",
    "estimated_affected_people": 1000000,
    "estimated_funding_needed": 500000000
}}
"""
        
        response = self._call_llm(prompt)
        return self._parse_impact_prediction(response)
    
    def _call_llm(self, prompt: str) -> str:
        """Rufe LLM API auf"""
        if not self.client:
            # Mock response für Tests
            return json.dumps({
                "risk_level": "MEDIUM",
                "confidence": 0.7,
                "reasoning": "Mock prediction - LLM not configured",
                "timeline": "medium_term",
                "key_factors": ["climate change", "regional instability"],
                "recommendations": ["Monitor situation", "Prepare response"]
            })
        
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Du bist ein Experte für Klima- und Konfliktrisiko-Analysen. Antworte immer im JSON-Format."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                
                # Track Kosten
                if self.cost_tracker and hasattr(response, 'usage'):
                    usage = response.usage
                    total_tokens = usage.total_tokens if usage else 0
                    # gpt-4o-mini: $0.15/$0.60 per 1M tokens (input/output)
                    # Schätzung: ~70% input, 30% output
                    cost_per_1k = 0.00015 if total_tokens < 1000 else 0.0006
                    self.cost_tracker.add_openai_cost(total_tokens, cost_per_1k)
                
                return response.choices[0].message.content
            
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text
        
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return json.dumps({"error": str(e)})
    
    def _combine_text_fields(self, record: Dict[str, Any]) -> str:
        """Kombiniere Text-Felder"""
        fields = [
            record.get('title', ''),
            record.get('summary', ''),
            record.get('full_text', '')
        ]
        return ' '.join(filter(None, fields))
    
    def _format_numbers_summary(self, extracted_numbers: Dict[str, Any]) -> str:
        """Formatiere extrahierte Zahlen für Prompt"""
        if not extracted_numbers:
            return "Keine Zahlen extrahiert"
        
        summary = []
        if extracted_numbers.get('temperatures'):
            summary.append(f"Temperaturen: {extracted_numbers['temperatures']}")
        if extracted_numbers.get('precipitation'):
            summary.append(f"Niederschlag: {extracted_numbers['precipitation']}")
        if extracted_numbers.get('population_numbers'):
            summary.append(f"Bevölkerung: {extracted_numbers['population_numbers']}")
        if extracted_numbers.get('financial_amounts'):
            summary.append(f"Finanzbeträge: {extracted_numbers['financial_amounts']}")
        if extracted_numbers.get('affected_people'):
            summary.append(f"Betroffene Personen: {extracted_numbers['affected_people']}")
        if extracted_numbers.get('funding_amount'):
            summary.append(f"Finanzierung: ${extracted_numbers['funding_amount']:,.0f}")
        
        return '\n'.join(summary) if summary else "Keine relevanten Zahlen gefunden"
    
    def _summarize_records(self, records: List[Dict[str, Any]]) -> str:
        """Erstelle Zusammenfassung mehrerer Records"""
        summary_parts = []
        for i, record in enumerate(records[:20], 1):  # Limit auf 20
            summary_parts.append(
                f"{i}. [{record.get('source_name', 'Unknown')}] {record.get('title', 'N/A')}\n"
                f"   Region: {record.get('region', 'N/A')}\n"
                f"   Datum: {record.get('publish_date', 'N/A')}\n"
            )
        return '\n'.join(summary_parts)
    
    def _parse_risk_prediction(self, response: str, record_id: int) -> LLMPrediction:
        """Parse LLM Response zu LLMPrediction"""
        try:
            data = json.loads(response)
            return LLMPrediction(
                record_id=record_id,
                prediction_type="risk",
                prediction_text=f"Risk Level: {data.get('risk_level', 'UNKNOWN')}",
                confidence=float(data.get('confidence', 0.5)),
                reasoning=data.get('reasoning', ''),
                predicted_timeline=data.get('timeline'),
                key_factors=data.get('key_factors', []),
                recommendations=data.get('recommendations', [])
            )
        except (json.JSONDecodeError, KeyError) as e:
            return LLMPrediction(
                record_id=record_id,
                prediction_type="risk",
                prediction_text="Error parsing prediction",
                confidence=0.0,
                reasoning=f"Error: {str(e)}"
            )
    
    def _parse_trend_prediction(self, response: str) -> Dict[str, Any]:
        """Parse Trend-Vorhersage"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Failed to parse trend prediction"}
    
    def _parse_impact_prediction(self, response: str) -> Dict[str, Any]:
        """Parse Impact-Vorhersage"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Failed to parse impact prediction"}


# Beispiel-Nutzung
if __name__ == "__main__":
    # Mock test ohne API Key
    predictor = LLMPredictor(provider="openai", model="gpt-4o-mini")
    
    test_record = {
        'id': 1,
        'title': 'Severe drought in East Africa',
        'summary': 'Worst drought in 40 years',
        'region': 'East Africa',
        'source_name': 'NASA'
    }
    
    test_numbers = {
        'temperatures': [35.0],
        'precipitation': [50.0],
        'affected_people': 2000000
    }
    
    prediction = predictor.predict_risk(test_record, test_numbers)
    print(json.dumps(asdict(prediction), indent=2, default=str))

