#!/usr/bin/env python3
"""
Enriched Predictions - Kombiniert Firecrawl-Anreicherung mit Predictions
"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import time

sys.path.append(str(Path(__file__).parent))

from database import DatabaseManager
from firecrawl_enrichment import FirecrawlEnricher, CostTracker
from prediction_pipeline import PredictionPipeline
from data_extraction import NumberExtractor
from llm_predictions import LLMPredictor
from risk_scoring import RiskScorer
from ipcc_context_engine import IPCCContextEngine


class EnrichedPredictionPipeline:
    """Pipeline die Firecrawl-Anreicherung mit Predictions kombiniert"""
    
    def __init__(
        self,
        firecrawl_api_key: str,
        openai_api_key: Optional[str] = None,
        llm_provider: str = "openai",
        llm_model: str = "gpt-4o-mini"
    ):
        """
        Args:
            firecrawl_api_key: Firecrawl API Key
            openai_api_key: Optional OpenAI API Key (wird als ENV-Variable gesetzt)
            llm_provider: LLM Provider
            llm_model: LLM Model
        """
        # Setze OpenAI API Key falls vorhanden
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        
        self.db = DatabaseManager()
        self.cost_tracker = CostTracker()
        self.firecrawl_enricher = FirecrawlEnricher(firecrawl_api_key, self.cost_tracker)
        
        # Erstelle LLM Predictor mit Cost Tracker
        from llm_predictions import LLMPredictor
        llm_predictor = LLMPredictor(
            provider=llm_provider,
            model=llm_model,
            cost_tracker=self.cost_tracker
        )
        
        # Erstelle Prediction Pipeline mit custom LLM Predictor
        self.prediction_pipeline = PredictionPipeline(llm_provider=llm_provider, llm_model=llm_model)
        self.prediction_pipeline.llm_predictor = llm_predictor
        self.number_extractor = NumberExtractor()
        self.risk_scorer = RiskScorer()
        self.ipcc_context_engine = IPCCContextEngine()  # IPCC-Kontext-Engine
    
    def enrich_and_predict(
        self,
        record_id: int,
        use_search: bool = True,
        use_extract: bool = True,
        use_llm: bool = True
    ) -> Dict[str, Any]:
        """
        Reichere Record an und erstelle Predictions
        
        Args:
            record_id: ID des Records
            use_search: Ob Web-Suche verwendet werden soll
            use_extract: Ob Agent-Extraktion verwendet werden soll
            use_llm: Ob LLM-Predictions verwendet werden sollen
        
        Returns:
            Angereicherte Predictions
        """
        # Hole Record
        records = self.db.get_records(limit=1000)
        record = next((r for r in records if r.get('id') == record_id), None)
        
        if not record:
            return {"error": f"Record {record_id} not found"}
        
        result = {
            "record_id": record_id,
            "original_record": {
                "title": record.get('title'),
                "region": record.get('region'),
                "source": record.get('source_name')
            },
            "enrichment": {},
            "predictions": {},
            "costs": {}
        }
        
        # 1. Erstelle IPCC-Kontext für Firecrawl
        firecrawl_context = self.ipcc_context_engine.get_firecrawl_context(record)
        
        # 2. Firecrawl-Anreicherung mit IPCC-Kontext
        print(f"Enriching record {record_id} with Firecrawl (IPCC-based)...")
        enriched_record = self.firecrawl_enricher.enrich_record(
            record,
            use_search=use_search,
            use_extract=use_extract,
            ipcc_context=firecrawl_context
        )
        
        result["enrichment"] = enriched_record.get('firecrawl_enrichment', {})
        
        # 2. Kombiniere Original-Text mit angereicherten Daten
        combined_text = self._combine_texts(enriched_record)
        
        # 3. Extrahiere Zahlen aus kombiniertem Text
        extracted_numbers = self.number_extractor.extract_all(combined_text)
        
        # Füge extrahierte Daten aus Firecrawl Extract hinzu
        if enriched_record.get('firecrawl_enrichment', {}).get('extracted_data'):
            extract_data = enriched_record['firecrawl_enrichment']['extracted_data']
            if extract_data.get('temperatures'):
                extracted_numbers.temperatures.extend(extract_data['temperatures'])
            if extract_data.get('precipitation'):
                extracted_numbers.precipitation.extend(extract_data['precipitation'])
            if extract_data.get('affected_population'):
                extracted_numbers.affected_people = extract_data['affected_population']
            if extract_data.get('funding_amount'):
                extracted_numbers.funding_amount = extract_data['funding_amount']
        
        result["predictions"]["extracted_numbers"] = {
            "temperatures": extracted_numbers.temperatures,
            "precipitation": extracted_numbers.precipitation,
            "population_numbers": extracted_numbers.population_numbers,
            "financial_amounts": extracted_numbers.financial_amounts,
            "affected_people": extracted_numbers.affected_people,
            "funding_amount": extracted_numbers.funding_amount
        }
        
        # 4. Risk Scoring mit angereicherten Daten
        enriched_record_for_scoring = record.copy()
        enriched_record_for_scoring['full_text'] = combined_text
        risk_score = self.risk_scorer.calculate_risk(enriched_record_for_scoring)
        
        result["predictions"]["risk_score"] = {
            "total": risk_score.score,
            "climate_risk": risk_score.climate_risk,
            "conflict_risk": risk_score.conflict_risk,
            "urgency": risk_score.urgency,
            "level": self.risk_scorer.get_risk_level(risk_score.score),
            "indicators": risk_score.indicators
        }
        
        # 5. Erstelle IPCC-Kontext für LLM
        llm_ipcc_context = self.ipcc_context_engine.get_llm_context(
            record,
            {
                'temperatures': extracted_numbers.temperatures,
                'precipitation': extracted_numbers.precipitation,
                'affected_people': extracted_numbers.affected_people,
                'funding_amount': extracted_numbers.funding_amount
            }
        )
        
        # 6. LLM-Prediction mit IPCC-Kontext
        if use_llm:
            try:
                numbers_dict = {
                    'temperatures': extracted_numbers.temperatures,
                    'precipitation': extracted_numbers.precipitation,
                    'population_numbers': extracted_numbers.population_numbers,
                    'financial_amounts': extracted_numbers.financial_amounts,
                    'affected_people': extracted_numbers.affected_people,
                    'funding_amount': extracted_numbers.funding_amount
                }
                
                # Erweitere Record mit angereicherten Daten für LLM
                llm_record = record.copy()
                llm_record['summary'] = self._create_enriched_summary(enriched_record)
                
                llm_prediction = self.prediction_pipeline.llm_predictor.predict_risk(
                    llm_record,
                    numbers_dict,
                    ipcc_context=llm_ipcc_context  # IPCC-Kontext hinzufügen
                )
                
                result["predictions"]["llm_prediction"] = {
                    "prediction_text": llm_prediction.prediction_text,
                    "confidence": llm_prediction.confidence,
                    "reasoning": llm_prediction.reasoning,
                    "predicted_timeline": llm_prediction.predicted_timeline,
                    "key_factors": llm_prediction.key_factors,
                    "recommendations": llm_prediction.recommendations
                }
            except Exception as e:
                print(f"LLM prediction failed: {e}")
                result["predictions"]["llm_prediction"] = {"error": str(e)}
        
        # 6. Kosten-Tracking
        result["costs"] = self.cost_tracker.get_summary()
        
        # 7. Speichere angereicherte Daten
        self._save_enriched_data(record_id, result)
        
        return result
    
    def batch_enrich_and_predict(
        self,
        record_ids: Optional[List[int]] = None,
        limit: int = 10,
        use_search: bool = True,
        use_extract: bool = True,
        use_llm: bool = True
    ) -> Dict[str, Any]:
        """Batch-Verarbeitung mehrerer Records"""
        if record_ids is None:
            records = self.db.get_records(limit=limit)
            record_ids = [r['id'] for r in records]
        
        results = {
            "processed": 0,
            "errors": 0,
            "results": [],
            "total_costs": {}
        }
        
        for record_id in record_ids:
            try:
                result = self.enrich_and_predict(
                    record_id,
                    use_search=use_search,
                    use_extract=use_extract,
                    use_llm=use_llm
                )
                results["results"].append(result)
                results["processed"] += 1
                
                # Pause zwischen Requests um Rate Limits zu vermeiden
                time.sleep(1)
            
            except Exception as e:
                print(f"Error processing record {record_id}: {e}")
                results["errors"] += 1
        
        # Finale Kosten-Zusammenfassung
        results["total_costs"] = self.cost_tracker.get_summary()
        
        return results
    
    def _combine_texts(self, enriched_record: Dict[str, Any]) -> str:
        """Kombiniere Original-Text mit angereicherten Daten"""
        texts = [
            enriched_record.get('title', ''),
            enriched_record.get('summary', ''),
            enriched_record.get('full_text', '')
        ]
        
        # Füge Search-Results hinzu
        if enriched_record.get('firecrawl_enrichment', {}).get('search_results'):
            for result in enriched_record['firecrawl_enrichment']['search_results']:
                texts.append(result.get('title', ''))
                texts.append(result.get('description', ''))
                if result.get('markdown'):
                    texts.append(result.get('markdown', '')[:500])  # Limit
        
        # Füge Extracted Data hinzu
        if enriched_record.get('firecrawl_enrichment', {}).get('extracted_data'):
            extract_data = enriched_record['firecrawl_enrichment']['extracted_data']
            texts.append(json.dumps(extract_data))
        
        return ' '.join(filter(None, texts))
    
    def _create_enriched_summary(self, enriched_record: Dict[str, Any]) -> str:
        """Erstelle Summary mit angereicherten Daten"""
        original_summary = enriched_record.get('summary', '')
        
        # Füge relevante Search-Results hinzu
        if enriched_record.get('firecrawl_enrichment', {}).get('search_results'):
            additional_info = []
            for result in enriched_record['firecrawl_enrichment']['search_results'][:2]:
                if result.get('description'):
                    additional_info.append(result['description'][:200])
            
            if additional_info:
                original_summary += "\n\nZusätzliche Informationen: " + " ".join(additional_info)
        
        return original_summary
    
    def _save_enriched_data(self, record_id: int, result: Dict[str, Any]):
        """Speichere angereicherte Daten in DB"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Erstelle Tabelle für angereicherte Daten
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS enriched_data (
                    record_id INTEGER PRIMARY KEY,
                    enrichment_data TEXT,
                    predictions_data TEXT,
                    costs_data TEXT,
                    enriched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE
                )
            """)
            
            # Speichere Daten
            cursor.execute("""
                INSERT OR REPLACE INTO enriched_data (
                    record_id, enrichment_data, predictions_data, costs_data
                ) VALUES (?, ?, ?, ?)
            """, (
                record_id,
                json.dumps(result.get('enrichment', {})),
                json.dumps(result.get('predictions', {})),
                json.dumps(result.get('costs', {}))
            ))


# Beispiel-Nutzung
if __name__ == "__main__":
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY", "fc-a0b3b8aa31244c10b0f15b4f2d570ac7")
    openai_key = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY_HERE")
    
    pipeline = EnrichedPredictionPipeline(
        firecrawl_api_key=firecrawl_key,
        openai_api_key=openai_key
    )
    
    # Test mit einem Record
    print("Testing enriched predictions...")
    result = pipeline.enrich_and_predict(record_id=1, use_llm=True)
    
    print("\n✅ Enrichment Results:")
    print(f"Search Results: {len(result.get('enrichment', {}).get('search_results', []))}")
    print(f"Extracted Data: {bool(result.get('enrichment', {}).get('extracted_data'))}")
    
    print("\n✅ Predictions:")
    print(f"Risk Score: {result.get('predictions', {}).get('risk_score', {}).get('total', 0):.2f}")
    print(f"Extracted Numbers: {len(result.get('predictions', {}).get('extracted_numbers', {}).get('temperatures', []))}")
    
    print("\n💰 Costs:")
    print(json.dumps(result.get('costs', {}), indent=2))

