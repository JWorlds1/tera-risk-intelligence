#!/usr/bin/env python3
"""
Prediction Pipeline - Kombiniert LLM-Predictions mit numerischen Zeitreihenvorhersagen
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

sys.path.append(str(Path(__file__).parent))

from database import DatabaseManager
from data_extraction import NumberExtractor, ExtractedNumbers
from llm_predictions import LLMPredictor, LLMPrediction
from time_series_predictions import TimeSeriesPredictor, TimeSeriesPrediction
from risk_scoring import RiskScorer


class PredictionPipeline:
    """Haupt-Pipeline für Predictions"""
    
    def __init__(self, llm_provider: str = "openai", llm_model: str = "gpt-4o-mini"):
        self.db = DatabaseManager()
        self.number_extractor = NumberExtractor()
        self.llm_predictor = LLMPredictor(provider=llm_provider, model=llm_model)
        self.time_series_predictor = TimeSeriesPredictor()
        self.risk_scorer = RiskScorer()
    
    def process_record(self, record_id: int) -> Dict[str, Any]:
        """Verarbeite einen einzelnen Record und erstelle Predictions"""
        # Hole Record aus DB
        records = self.db.get_records(limit=1000)
        record = next((r for r in records if r.get('id') == record_id), None)
        
        if not record:
            return {"error": f"Record {record_id} not found"}
        
        # 1. Extrahiere numerische Daten
        text_content = f"{record.get('title', '')} {record.get('summary', '')} {record.get('full_text', '')}"
        extracted_numbers = self.number_extractor.extract_all(text_content)
        
        # 2. Berechne Risk Score
        risk_score = self.risk_scorer.calculate_risk(record)
        
        # 3. LLM-basierte Prediction
        llm_prediction = None
        try:
            numbers_dict = {
                'temperatures': extracted_numbers.temperatures,
                'precipitation': extracted_numbers.precipitation,
                'population_numbers': extracted_numbers.population_numbers,
                'financial_amounts': extracted_numbers.financial_amounts,
                'affected_people': extracted_numbers.affected_people,
                'funding_amount': extracted_numbers.funding_amount
            }
            llm_prediction = self.llm_predictor.predict_risk(record, numbers_dict)
        except Exception as e:
            print(f"Error in LLM prediction: {e}")
        
        # 4. Speichere Ergebnisse
        self._save_extracted_numbers(record_id, extracted_numbers)
        self._save_risk_score(record_id, risk_score)
        if llm_prediction:
            self._save_llm_prediction(llm_prediction)
        
        return {
            "record_id": record_id,
            "extracted_numbers": self._serialize_extracted_numbers(extracted_numbers),
            "risk_score": {
                "total": risk_score.score,
                "climate_risk": risk_score.climate_risk,
                "conflict_risk": risk_score.conflict_risk,
                "urgency": risk_score.urgency,
                "level": self.risk_scorer.get_risk_level(risk_score.score),
                "indicators": risk_score.indicators
            },
            "llm_prediction": self._serialize_llm_prediction(llm_prediction) if llm_prediction else None
        }
    
    def process_all_records(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Verarbeite alle Records"""
        records = self.db.get_records(limit=limit or 1000)
        
        results = {
            "processed": 0,
            "errors": 0,
            "results": []
        }
        
        for record in records:
            try:
                result = self.process_record(record['id'])
                results["results"].append(result)
                results["processed"] += 1
            except Exception as e:
                print(f"Error processing record {record.get('id')}: {e}")
                results["errors"] += 1
        
        return results
    
    def create_trend_predictions(
        self,
        region: Optional[str] = None,
        days_back: int = 90
    ) -> Dict[str, Any]:
        """Erstelle Trend-Vorhersagen für alle Metriken"""
        records = self.db.get_records(limit=1000)
        
        if region:
            records = [r for r in records if r.get('region') == region]
        
        # Filtere nach Zeitfenster
        cutoff_date = datetime.now() - timedelta(days=days_back)
        filtered_records = []
        for record in records:
            date = self._parse_date(record.get('publish_date') or record.get('fetched_at'))
            if date and date >= cutoff_date:
                filtered_records.append(record)
        
        predictions = {}
        
        # Risk Score Trend
        try:
            risk_prediction = self.time_series_predictor.predict_risk_score_trend(
                filtered_records, days_back
            )
            if risk_prediction:
                predictions["risk_score"] = self._serialize_time_series_prediction(risk_prediction)
        except Exception as e:
            print(f"Error predicting risk score trend: {e}")
        
        # Temperature Trend
        try:
            temp_prediction = self.time_series_predictor.predict_temperature_trend(
                filtered_records, region, days_back
            )
            if temp_prediction:
                predictions["temperature"] = self._serialize_time_series_prediction(temp_prediction)
        except Exception as e:
            print(f"Error predicting temperature trend: {e}")
        
        # Population Impact Trend
        try:
            pop_prediction = self.time_series_predictor.predict_population_impact(
                filtered_records, days_back
            )
            if pop_prediction:
                predictions["affected_population"] = self._serialize_time_series_prediction(pop_prediction)
        except Exception as e:
            print(f"Error predicting population impact: {e}")
        
        # LLM Trend Analysis
        try:
            llm_trend = self.llm_predictor.predict_trend(filtered_records, days_back)
            predictions["llm_trend_analysis"] = llm_trend
        except Exception as e:
            print(f"Error in LLM trend analysis: {e}")
        
        # Speichere Predictions
        self._save_trend_predictions(predictions, region, days_back)
        
        return {
            "region": region or "all",
            "time_window_days": days_back,
            "predictions": predictions,
            "records_analyzed": len(filtered_records)
        }
    
    def get_combined_prediction(self, record_id: int) -> Dict[str, Any]:
        """Kombiniere alle Prediction-Typen für einen Record"""
        record = self._get_record(record_id)
        if not record:
            return {"error": f"Record {record_id} not found"}
        
        # Hole alle Predictions
        extracted_numbers = self._get_extracted_numbers(record_id)
        risk_score = self._get_risk_score(record_id)
        llm_prediction = self._get_llm_prediction(record_id)
        
        # Erstelle kombinierte Vorhersage
        combined = {
            "record_id": record_id,
            "record": {
                "title": record.get('title'),
                "region": record.get('region'),
                "source": record.get('source_name'),
                "date": record.get('publish_date')
            },
            "extracted_data": extracted_numbers,
            "risk_assessment": risk_score,
            "llm_analysis": llm_prediction,
            "combined_prediction": self._combine_predictions(
                extracted_numbers, risk_score, llm_prediction
            )
        }
        
        return combined
    
    def _combine_predictions(
        self,
        extracted_numbers: Optional[Dict],
        risk_score: Optional[Dict],
        llm_prediction: Optional[Dict]
    ) -> Dict[str, Any]:
        """Kombiniere verschiedene Predictions zu einer Gesamtvorhersage"""
        combined = {
            "overall_risk": "UNKNOWN",
            "confidence": 0.0,
            "key_insights": [],
            "recommendations": [],
            "predicted_timeline": "unknown"
        }
        
        # Kombiniere Risk Scores
        if risk_score:
            combined["overall_risk"] = risk_score.get("level", "UNKNOWN")
            combined["confidence"] = 0.7  # Basis-Konfidenz für Risk Score
        
        # Füge LLM Insights hinzu
        if llm_prediction:
            combined["confidence"] = max(
                combined["confidence"],
                llm_prediction.get("confidence", 0.0)
            )
            combined["key_insights"] = llm_prediction.get("key_factors", [])
            combined["recommendations"] = llm_prediction.get("recommendations", [])
            combined["predicted_timeline"] = llm_prediction.get("predicted_timeline", "unknown")
        
        # Füge numerische Daten hinzu
        if extracted_numbers:
            if extracted_numbers.get("affected_people"):
                combined["key_insights"].append(
                    f"Betroffene Personen: {extracted_numbers['affected_people']:,}"
                )
            if extracted_numbers.get("funding_amount"):
                combined["key_insights"].append(
                    f"Finanzierungsbedarf: ${extracted_numbers['funding_amount']:,.0f}"
                )
        
        return combined
    
    def _save_extracted_numbers(self, record_id: int, extracted: ExtractedNumbers):
        """Speichere extrahierte Zahlen in DB"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Prüfe ob Tabelle existiert, sonst erstelle sie
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS extracted_numbers (
                    record_id INTEGER PRIMARY KEY,
                    temperatures TEXT,
                    precipitation TEXT,
                    population_numbers TEXT,
                    financial_amounts TEXT,
                    percentages TEXT,
                    dates TEXT,
                    affected_people INTEGER,
                    funding_amount REAL,
                    locations TEXT,
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE
                )
            """)
            
            # Speichere Daten
            cursor.execute("""
                INSERT OR REPLACE INTO extracted_numbers (
                    record_id, temperatures, precipitation, population_numbers,
                    financial_amounts, percentages, dates, affected_people,
                    funding_amount, locations
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_id,
                json.dumps(extracted.temperatures),
                json.dumps(extracted.precipitation),
                json.dumps(extracted.population_numbers),
                json.dumps(extracted.financial_amounts),
                json.dumps(extracted.percentages),
                json.dumps(extracted.dates),
                extracted.affected_people,
                extracted.funding_amount,
                json.dumps(extracted.locations)
            ))
    
    def _save_risk_score(self, record_id: int, risk_score):
        """Speichere Risk Score in DB"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS risk_scores (
                    record_id INTEGER PRIMARY KEY,
                    total_score REAL,
                    climate_risk REAL,
                    conflict_risk REAL,
                    urgency REAL,
                    risk_level TEXT,
                    indicators TEXT,
                    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                INSERT OR REPLACE INTO risk_scores (
                    record_id, total_score, climate_risk, conflict_risk,
                    urgency, risk_level, indicators
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                record_id,
                risk_score.score,
                risk_score.climate_risk,
                risk_score.conflict_risk,
                risk_score.urgency,
                self.risk_scorer.get_risk_level(risk_score.score),
                json.dumps(risk_score.indicators)
            ))
    
    def _save_llm_prediction(self, prediction: LLMPrediction):
        """Speichere LLM Prediction in DB"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS llm_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id INTEGER NOT NULL,
                    prediction_type TEXT,
                    prediction_text TEXT,
                    confidence REAL,
                    reasoning TEXT,
                    predicted_timeline TEXT,
                    key_factors TEXT,
                    recommendations TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                INSERT INTO llm_predictions (
                    record_id, prediction_type, prediction_text, confidence,
                    reasoning, predicted_timeline, key_factors, recommendations
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prediction.record_id,
                prediction.prediction_type,
                prediction.prediction_text,
                prediction.confidence,
                prediction.reasoning,
                prediction.predicted_timeline,
                json.dumps(prediction.key_factors),
                json.dumps(prediction.recommendations)
            ))
    
    def _save_trend_predictions(self, predictions: Dict, region: Optional[str], days_back: int):
        """Speichere Trend-Predictions"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trend_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    region TEXT,
                    time_window_days INTEGER,
                    metric_name TEXT,
                    current_value REAL,
                    predictions TEXT,
                    trend TEXT,
                    confidence REAL,
                    model_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            for metric_name, prediction_data in predictions.items():
                if isinstance(prediction_data, dict) and "current_value" in prediction_data:
                    cursor.execute("""
                        INSERT INTO trend_predictions (
                            region, time_window_days, metric_name, current_value,
                            predictions, trend, confidence, model_type
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        region,
                        days_back,
                        metric_name,
                        prediction_data.get("current_value"),
                        json.dumps(prediction_data.get("predictions", {})),
                        prediction_data.get("trend"),
                        prediction_data.get("confidence", 0.0),
                        prediction_data.get("model_type", "unknown")
                    ))
    
    def _get_record(self, record_id: int) -> Optional[Dict]:
        """Hole Record aus DB"""
        records = self.db.get_records(limit=1000)
        return next((r for r in records if r.get('id') == record_id), None)
    
    def _get_extracted_numbers(self, record_id: int) -> Optional[Dict]:
        """Hole extrahierte Zahlen aus DB"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM extracted_numbers WHERE record_id = ?", (record_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None
    
    def _get_risk_score(self, record_id: int) -> Optional[Dict]:
        """Hole Risk Score aus DB"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM risk_scores WHERE record_id = ?", (record_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None
    
    def _get_llm_prediction(self, record_id: int) -> Optional[Dict]:
        """Hole LLM Prediction aus DB"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM llm_predictions 
                WHERE record_id = ? 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (record_id,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                # Parse JSON-Strings zu Listen
                if result.get('key_factors'):
                    try:
                        result['key_factors'] = json.loads(result['key_factors'])
                    except (json.JSONDecodeError, TypeError):
                        result['key_factors'] = []
                if result.get('recommendations'):
                    try:
                        result['recommendations'] = json.loads(result['recommendations'])
                    except (json.JSONDecodeError, TypeError):
                        result['recommendations'] = []
                return result
        return None
    
    def _serialize_extracted_numbers(self, extracted: ExtractedNumbers) -> Dict:
        """Serialisiere ExtractedNumbers zu Dict"""
        return {
            "temperatures": extracted.temperatures,
            "precipitation": extracted.precipitation,
            "population_numbers": extracted.population_numbers,
            "financial_amounts": extracted.financial_amounts,
            "percentages": extracted.percentages,
            "dates": extracted.dates,
            "affected_people": extracted.affected_people,
            "funding_amount": extracted.funding_amount,
            "locations": extracted.locations
        }
    
    def _serialize_llm_prediction(self, prediction: LLMPrediction) -> Dict:
        """Serialisiere LLMPrediction zu Dict"""
        return {
            "prediction_type": prediction.prediction_type,
            "prediction_text": prediction.prediction_text,
            "confidence": prediction.confidence,
            "reasoning": prediction.reasoning,
            "predicted_timeline": prediction.predicted_timeline,
            "key_factors": prediction.key_factors,
            "recommendations": prediction.recommendations
        }
    
    def _serialize_time_series_prediction(self, prediction: TimeSeriesPrediction) -> Dict:
        """Serialisiere TimeSeriesPrediction zu Dict"""
        return {
            "metric_name": prediction.metric_name,
            "current_value": prediction.current_value,
            "predictions": prediction.predictions,
            "trend": prediction.trend,
            "confidence": prediction.confidence,
            "model_type": prediction.model_type
        }
    
    def _parse_date(self, date_str: Any) -> Optional[datetime]:
        """Parse Datum"""
        if isinstance(date_str, datetime):
            return date_str
        if not date_str:
            return None
        
        try:
            from dateutil import parser
            return parser.parse(str(date_str))
        except:
            return None


# Beispiel-Nutzung
if __name__ == "__main__":
    pipeline = PredictionPipeline()
    
    # Verarbeite alle Records
    print("Processing all records...")
    results = pipeline.process_all_records(limit=10)
    print(f"Processed: {results['processed']}, Errors: {results['errors']}")
    
    # Erstelle Trend-Predictions
    print("\nCreating trend predictions...")
    trends = pipeline.create_trend_predictions(days_back=90)
    print(f"Trend predictions created for {trends['records_analyzed']} records")

