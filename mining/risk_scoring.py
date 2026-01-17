# risk_scoring.py - Risiko-Scoring für Klimagefährdung
from typing import Dict, List, Optional
from datetime import datetime
import re
from dataclasses import dataclass

@dataclass
class RiskScore:
    """Risiko-Score für einen Record"""
    record_id: int
    climate_risk: float  # 0.0 - 1.0
    conflict_risk: float  # 0.0 - 1.0
    urgency: float  # 0.0 - 1.0
    indicators: List[str]
    score: float  # Gesamt-Score (gewichteter Durchschnitt)


class RiskScorer:
    """Berechnet Risiko-Scores für Klimagefährdung"""
    
    def __init__(self):
        # Klima-Indikatoren (Gewichtung)
        self.climate_indicators = {
            'drought': 0.9,
            'flood': 0.8,
            'heat_wave': 0.7,
            'desertification': 0.85,
            'sea_level_rise': 0.9,
            'glacier_melt': 0.8,
            'crop_failure': 0.85,
            'water_scarcity': 0.9,
            'famine': 0.95,
            'wildfire': 0.75,
            'storm': 0.7,
            'monsoon_failure': 0.85,
            'permafrost_thaw': 0.7,
            'coral_bleaching': 0.65,
            'saltwater_intrusion': 0.8
        }
        
        # Konflikt-Indikatoren
        self.conflict_indicators = {
            'conflict': 0.8,
            'war': 0.95,
            'violence': 0.75,
            'crisis': 0.7,
            'emergency': 0.8,
            'displacement': 0.85,
            'migration': 0.75,
            'refugee': 0.8,
            'unrest': 0.7,
            'instability': 0.75,
            'tension': 0.65,
            'dispute': 0.6,
            'terrorism': 0.9,
            'insurgency': 0.85
        }
        
        # Dringlichkeits-Indikatoren
        self.urgency_indicators = {
            'urgent': 0.9,
            'critical': 0.95,
            'emergency': 0.9,
            'immediate': 0.85,
            'severe': 0.8,
            'worsening': 0.75,
            'escalating': 0.8,
            'crisis': 0.85
        }
    
    def calculate_risk(self, record: Dict) -> RiskScore:
        """Berechne Risiko-Score für einen Record"""
        # Kombiniere Text-Felder
        text_fields = [
            record.get('title', ''),
            record.get('summary', ''),
            record.get('full_text', '')
        ]
        combined_text = ' '.join(filter(None, text_fields)).lower()
        
        # Berechne Climate Risk
        climate_risk = self._calculate_indicator_score(combined_text, self.climate_indicators)
        
        # Berechne Conflict Risk
        conflict_risk = self._calculate_indicator_score(combined_text, self.conflict_indicators)
        
        # Berechne Urgency
        urgency = self._calculate_indicator_score(combined_text, self.urgency_indicators)
        
        # Sammle gefundene Indikatoren
        indicators = []
        for indicator in self.climate_indicators.keys():
            if indicator in combined_text:
                indicators.append(indicator)
        for indicator in self.conflict_indicators.keys():
            if indicator in combined_text and indicator not in indicators:
                indicators.append(indicator)
        
        # Gesamt-Score (gewichteter Durchschnitt)
        # Climate Risk: 40%, Conflict Risk: 40%, Urgency: 20%
        total_score = (
            climate_risk * 0.4 +
            conflict_risk * 0.4 +
            urgency * 0.2
        )
        
        return RiskScore(
            record_id=record.get('id'),
            climate_risk=climate_risk,
            conflict_risk=conflict_risk,
            urgency=urgency,
            indicators=indicators,
            score=total_score
        )
    
    def _calculate_indicator_score(self, text: str, indicators: Dict[str, float]) -> float:
        """Berechne Score basierend auf Indikatoren"""
        if not text:
            return 0.0
        
        scores = []
        for indicator, weight in indicators.items():
            # Suche nach Indicator im Text
            pattern = r'\b' + re.escape(indicator) + r'\b'
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            if matches > 0:
                # Score basierend auf Häufigkeit (capped)
                indicator_score = min(matches * weight / 3.0, weight)
                scores.append(indicator_score)
        
        if not scores:
            return 0.0
        
        # Durchschnitt der gefundenen Indikatoren
        return min(sum(scores) / len(scores), 1.0)
    
    def get_risk_level(self, score: float) -> str:
        """Konvertiere Score zu Risiko-Level"""
        if score >= 0.8:
            return "CRITICAL"
        elif score >= 0.6:
            return "HIGH"
        elif score >= 0.4:
            return "MEDIUM"
        elif score >= 0.2:
            return "LOW"
        else:
            return "MINIMAL"


# Beispiel-Nutzung
if __name__ == "__main__":
    scorer = RiskScorer()
    
    test_record = {
        'id': 1,
        'title': 'Severe drought in East Africa causes food crisis',
        'summary': 'Worst drought in 40 years leads to crop failure and displacement',
        'region': 'East Africa'
    }
    
    risk = scorer.calculate_risk(test_record)
    print(f"Climate Risk: {risk.climate_risk:.2f}")
    print(f"Conflict Risk: {risk.conflict_risk:.2f}")
    print(f"Urgency: {risk.urgency:.2f}")
    print(f"Total Score: {risk.score:.2f}")
    print(f"Risk Level: {scorer.get_risk_level(risk.score)}")
    print(f"Indicators: {', '.join(risk.indicators)}")

