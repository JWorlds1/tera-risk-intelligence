#!/usr/bin/env python3
"""
Time Series Prediction Module - Numerische Zeitreihenvorhersagen
"""
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import PolynomialFeatures
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available. Install with: pip install scikit-learn")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("Warning: pandas not available. Install with: pip install pandas")


@dataclass
class TimeSeriesPrediction:
    """Zeitreihenvorhersage"""
    metric_name: str  # "temperature", "precipitation", "risk_score", etc.
    current_value: float
    predictions: Dict[str, float]  # {"1_month": 25.5, "3_months": 26.0, "6_months": 26.5}
    trend: str  # "increasing", "decreasing", "stable"
    confidence: float  # 0.0 - 1.0
    historical_data: List[Tuple[datetime, float]]
    model_type: str  # "linear", "polynomial", "moving_average"


class TimeSeriesPredictor:
    """Erstellt Zeitreihenvorhersagen aus numerischen Daten"""
    
    def __init__(self):
        self.models = {}
    
    def predict_from_records(
        self,
        records: List[Dict[str, Any]],
        metric: str = "risk_score",
        days_back: int = 90
    ) -> Optional[TimeSeriesPrediction]:
        """
        Erstelle Vorhersage aus Records
        
        Args:
            records: Liste von Records mit numerischen Daten
            metric: Metrik zum Vorhersagen ("risk_score", "temperature", "precipitation", etc.)
            days_back: Anzahl Tage zurück für historische Daten
        """
        # Extrahiere Zeitreihendaten
        time_series = self._extract_time_series(records, metric, days_back)
        
        if len(time_series) < 3:
            return None  # Nicht genug Daten
        
        # Sortiere nach Datum
        time_series.sort(key=lambda x: x[0])
        
        # Erstelle Vorhersage
        return self._predict(time_series, metric)
    
    def predict_risk_score_trend(
        self,
        records: List[Dict[str, Any]],
        days_back: int = 90
    ) -> Optional[TimeSeriesPrediction]:
        """Spezielle Methode für Risk Score Vorhersagen"""
        # Berechne Risk Scores für jeden Record
        from risk_scoring import RiskScorer
        scorer = RiskScorer()
        
        scored_records = []
        for record in records:
            risk = scorer.calculate_risk(record)
            scored_records.append({
                **record,
                'risk_score': risk.score,
                'climate_risk': risk.climate_risk,
                'conflict_risk': risk.conflict_risk,
                'urgency': risk.urgency
            })
        
        return self.predict_from_records(scored_records, "risk_score", days_back)
    
    def predict_temperature_trend(
        self,
        records: List[Dict[str, Any]],
        region: Optional[str] = None,
        days_back: int = 90
    ) -> Optional[TimeSeriesPrediction]:
        """Vorhersage von Temperaturtrends"""
        # Filtere nach Region wenn angegeben
        filtered_records = records
        if region:
            filtered_records = [r for r in records if r.get('region') == region]
        
        # Extrahiere Temperaturen aus Records
        from data_extraction import NumberExtractor
        extractor = NumberExtractor()
        
        time_series = []
        for record in filtered_records:
            # Parse Datum
            date = self._parse_date(record.get('publish_date') or record.get('fetched_at'))
            if not date:
                continue
            
            # Extrahiere Temperaturen
            text = f"{record.get('title', '')} {record.get('summary', '')} {record.get('full_text', '')}"
            extracted = extractor.extract_all(text)
            
            if extracted.temperatures:
                # Verwende Durchschnitt wenn mehrere Temperaturen
                avg_temp = np.mean(extracted.temperatures)
                time_series.append((date, avg_temp))
        
        if len(time_series) < 3:
            return None
        
        time_series.sort(key=lambda x: x[0])
        return self._predict(time_series, "temperature")
    
    def predict_population_impact(
        self,
        records: List[Dict[str, Any]],
        days_back: int = 90
    ) -> Optional[TimeSeriesPrediction]:
        """Vorhersage von Bevölkerungsauswirkungen"""
        from data_extraction import NumberExtractor
        extractor = NumberExtractor()
        
        time_series = []
        for record in records:
            date = self._parse_date(record.get('publish_date') or record.get('fetched_at'))
            if not date:
                continue
            
            text = f"{record.get('title', '')} {record.get('summary', '')} {record.get('full_text', '')}"
            extracted = extractor.extract_all(text)
            
            if extracted.affected_people:
                time_series.append((date, float(extracted.affected_people)))
        
        if len(time_series) < 3:
            return None
        
        time_series.sort(key=lambda x: x[0])
        return self._predict(time_series, "affected_population")
    
    def _extract_time_series(
        self,
        records: List[Dict[str, Any]],
        metric: str,
        days_back: int
    ) -> List[Tuple[datetime, float]]:
        """Extrahiere Zeitreihendaten aus Records"""
        time_series = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for record in records:
            # Parse Datum
            date = self._parse_date(record.get('publish_date') or record.get('fetched_at'))
            if not date or date < cutoff_date:
                continue
            
            # Extrahiere Metrik-Wert
            value = None
            
            if metric == "risk_score":
                from risk_scoring import RiskScorer
                scorer = RiskScorer()
                risk = scorer.calculate_risk(record)
                value = risk.score
            
            elif metric in ["temperature", "precipitation", "affected_population"]:
                from data_extraction import NumberExtractor
                extractor = NumberExtractor()
                text = f"{record.get('title', '')} {record.get('summary', '')} {record.get('full_text', '')}"
                extracted = extractor.extract_all(text)
                
                if metric == "temperature" and extracted.temperatures:
                    value = np.mean(extracted.temperatures)
                elif metric == "precipitation" and extracted.precipitation:
                    value = np.mean(extracted.precipitation)
                elif metric == "affected_population" and extracted.affected_people:
                    value = float(extracted.affected_people)
            
            if value is not None:
                time_series.append((date, value))
        
        return time_series
    
    def _predict(
        self,
        time_series: List[Tuple[datetime, float]],
        metric_name: str
    ) -> TimeSeriesPrediction:
        """Erstelle Vorhersage aus Zeitreihendaten"""
        if not time_series:
            raise ValueError("Time series is empty")
        
        # Konvertiere zu Arrays
        dates = [ts[0] for ts in time_series]
        values = np.array([ts[1] for ts in time_series])
        
        # Konvertiere Datum zu numerischen Werten (Tage seit erstem Datum)
        first_date = dates[0]
        days_since_start = np.array([(d - first_date).days for d in dates])
        
        # Erstelle Vorhersagen
        predictions = {}
        
        if SKLEARN_AVAILABLE and len(time_series) >= 5:
            # Verwende Linear Regression für Vorhersagen
            X = days_since_start.reshape(-1, 1)
            y = values
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Vorhersagen für verschiedene Zeithorizonte
            future_days = [30, 90, 180]  # 1, 3, 6 Monate
            for days in future_days:
                future_day = days_since_start[-1] + days
                pred_value = model.predict([[future_day]])[0]
                predictions[f"{days}_days"] = float(pred_value)
            
            # Trend bestimmen
            slope = model.coef_[0]
            if slope > 0.01:
                trend = "increasing"
            elif slope < -0.01:
                trend = "decreasing"
            else:
                trend = "stable"
            
            # Konfidenz basierend auf R²
            score = model.score(X, y)
            confidence = max(0.0, min(1.0, score))
            
            model_type = "linear"
        
        else:
            # Fallback: Moving Average
            window = min(7, len(values) // 2)
            if window < 1:
                window = 1
            
            ma = np.convolve(values, np.ones(window)/window, mode='valid')
            last_ma = ma[-1] if len(ma) > 0 else values[-1]
            
            # Einfache Extrapolation
            recent_trend = (values[-1] - values[0]) / len(values) if len(values) > 1 else 0
            
            for days in [30, 90, 180]:
                pred_value = last_ma + (recent_trend * days / len(values))
                predictions[f"{days}_days"] = float(pred_value)
            
            trend = "increasing" if recent_trend > 0 else "decreasing" if recent_trend < 0 else "stable"
            confidence = 0.5  # Niedrige Konfidenz für einfache Methode
            model_type = "moving_average"
        
        return TimeSeriesPrediction(
            metric_name=metric_name,
            current_value=float(values[-1]),
            predictions=predictions,
            trend=trend,
            confidence=confidence,
            historical_data=time_series,
            model_type=model_type
        )
    
    def _parse_date(self, date_str: Any) -> Optional[datetime]:
        """Parse Datum aus verschiedenen Formaten"""
        if isinstance(date_str, datetime):
            return date_str
        
        if not date_str:
            return None
        
        # Versuche verschiedene Formate
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(str(date_str), fmt)
            except ValueError:
                continue
        
        # Fallback: Versuche mit dateutil
        try:
            from dateutil import parser
            return parser.parse(str(date_str))
        except:
            return None


# Beispiel-Nutzung
if __name__ == "__main__":
    predictor = TimeSeriesPredictor()
    
    # Mock Daten
    test_records = [
        {
            'id': 1,
            'title': 'Drought conditions worsen',
            'publish_date': '2025-01-01',
            'risk_score': 0.3
        },
        {
            'id': 2,
            'title': 'Water scarcity increases',
            'publish_date': '2025-01-15',
            'risk_score': 0.4
        },
        {
            'id': 3,
            'title': 'Crisis escalates',
            'publish_date': '2025-02-01',
            'risk_score': 0.5
        },
    ]
    
    prediction = predictor.predict_from_records(test_records, "risk_score", days_back=90)
    if prediction:
        print(json.dumps(asdict(prediction), indent=2, default=str))

