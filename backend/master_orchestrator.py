#!/usr/bin/env python3
"""
Master-Orchestrator für das Climate Conflict Intelligence System
Koordiniert alle Agenten und ermöglicht Datenaustausch zwischen ihnen
"""
import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import defaultdict
import structlog

from config import Config
from database import DatabaseManager
from orchestrator import ScrapingOrchestrator
from ipcc_enrichment_agent import DynamicEnrichmentOrchestrator
from enriched_predictions import EnrichedPredictionPipeline
from risk_scoring import RiskScorer
from geocoding import GeocodingService

logger = structlog.get_logger(__name__)


@dataclass
class AgentMessage:
    """Nachricht zwischen Agenten"""
    sender: str
    receiver: Optional[str]  # None = Broadcast
    message_type: str  # 'data', 'request', 'response', 'status'
    payload: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AgentMessageBus:
    """Message Bus für Agent-Kommunikation"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[callable]] = defaultdict(list)
        self.message_history: List[AgentMessage] = []
        self.max_history = 1000
    
    def subscribe(self, agent_name: str, callback: callable):
        """Agent abonnieren"""
        self.subscribers[agent_name].append(callback)
        logger.info(f"Agent {agent_name} subscribed to message bus")
    
    def publish(self, message: AgentMessage):
        """Nachricht veröffentlichen"""
        self.message_history.append(message)
        if len(self.message_history) > self.max_history:
            self.message_history.pop(0)
        
        # Sende an spezifischen Empfänger oder alle Subscriber
        if message.receiver:
            if message.receiver in self.subscribers:
                for callback in self.subscribers[message.receiver]:
                    try:
                        callback(message)
                    except Exception as e:
                        logger.error(f"Error in callback for {message.receiver}: {e}")
        else:
            # Broadcast
            for agent_name, callbacks in self.subscribers.items():
                for callback in callbacks:
                    try:
                        callback(message)
                    except Exception as e:
                        logger.error(f"Error in callback for {agent_name}: {e}")
    
    def get_messages(self, agent_name: Optional[str] = None, message_type: Optional[str] = None) -> List[AgentMessage]:
        """Hole Nachrichten aus der Historie"""
        messages = self.message_history
        
        if agent_name:
            messages = [m for m in messages if m.receiver == agent_name or m.sender == agent_name]
        
        if message_type:
            messages = [m for m in messages if m.message_type == message_type]
        
        return messages


class MasterOrchestrator:
    """Master-Orchestrator koordiniert alle Agenten"""
    
    def __init__(self, config: Config):
        self.config = config
        self.message_bus = AgentMessageBus()
        
        # Initialisiere alle Komponenten
        self.db = DatabaseManager()
        self.scraper = None
        self.enrichment_orchestrator = None
        self.prediction_pipeline = None
        self.risk_scorer = RiskScorer()
        self.geocoder = GeocodingService()
        
        # Regionale Fokus-Regionen
        self.critical_regions = {
            'Germany': {
                'countries': ['DE'],
                'keywords': ['Germany', 'Deutschland', 'German'],
                'priority': 1
            },
            'Europe': {
                'countries': ['DE', 'FR', 'IT', 'ES', 'PL', 'NL', 'BE', 'AT', 'CH', 'CZ', 'SE', 'NO', 'DK', 'FI'],
                'keywords': ['Europe', 'Europa', 'European', 'EU'],
                'priority': 2
            }
        }
        
        # Status-Tracking
        self.status = {
            'scraping': {'running': False, 'last_run': None, 'records_processed': 0},
            'enrichment': {'running': False, 'last_run': None, 'records_enriched': 0},
            'prediction': {'running': False, 'last_run': None, 'predictions_created': 0},
            'geocoding': {'running': False, 'last_run': None, 'records_geocoded': 0}
        }
    
    async def initialize(self):
        """Initialisiere alle Agenten"""
        logger.info("Initializing Master Orchestrator...")
        
        # Initialisiere Scraping-Orchestrator
        self.scraper = ScrapingOrchestrator(self.config, use_database=True)
        await self.scraper.__aenter__()
        
        # Initialisiere Enrichment-Orchestrator
        firecrawl_key = self.config.FIRECRAWL_API_KEY
        openai_key = os.getenv('OPENAI_API_KEY')
        self.enrichment_orchestrator = DynamicEnrichmentOrchestrator(
            firecrawl_api_key=firecrawl_key,
            openai_api_key=openai_key
        )
        
        # Initialisiere Prediction Pipeline
        self.prediction_pipeline = EnrichedPredictionPipeline(
            firecrawl_api_key=firecrawl_key,
            openai_api_key=openai_key
        )
        
        # Subscribe Agents zum Message Bus
        self._setup_agent_subscriptions()
        
        logger.info("Master Orchestrator initialized successfully")
    
    def _setup_agent_subscriptions(self):
        """Richte Agent-Subscriptions ein"""
        # Scraper sendet neue Records
        # Enrichment Agent hört auf neue Records
        # Prediction Agent hört auf angereicherte Records
        pass
    
    async def run_full_pipeline(
        self,
        sources: Optional[List[str]] = None,
        enrich: bool = True,
        predict: bool = True,
        geocode: bool = True,
        focus_regions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Führe die komplette Pipeline aus:
        1. Scraping
        2. Enrichment
        3. Geocoding
        4. Prediction
        """
        results = {
            'scraping': {},
            'enrichment': {},
            'geocoding': {},
            'prediction': {},
            'regional_data': {}
        }
        
        # 1. Scraping
        logger.info("Starting scraping phase...")
        self.status['scraping']['running'] = True
        try:
            scraping_stats = await self.scraper.run_scraping_session()
            results['scraping'] = scraping_stats
            self.status['scraping']['last_run'] = datetime.now()
            self.status['scraping']['records_processed'] = scraping_stats.get('records_stored', 0)
            
            # Benachrichtige andere Agenten über neue Records
            self.message_bus.publish(AgentMessage(
                sender='scraper',
                receiver=None,  # Broadcast
                message_type='data',
                payload={'action': 'records_added', 'count': scraping_stats.get('records_stored', 0)}
            ))
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            results['scraping']['error'] = str(e)
        finally:
            self.status['scraping']['running'] = False
        
        # 2. Geocoding (wichtig für regionale Filterung)
        if geocode:
            logger.info("Starting geocoding phase...")
            self.status['geocoding']['running'] = True
            try:
                geocoding_results = await self._geocode_records(focus_regions)
                results['geocoding'] = geocoding_results
                self.status['geocoding']['last_run'] = datetime.now()
                self.status['geocoding']['records_geocoded'] = geocoding_results.get('geocoded', 0)
            except Exception as e:
                logger.error(f"Geocoding failed: {e}")
                results['geocoding']['error'] = str(e)
            finally:
                self.status['geocoding']['running'] = False
        
        # 3. Enrichment
        if enrich:
            logger.info("Starting enrichment phase...")
            self.status['enrichment']['running'] = True
            try:
                enrichment_results = await self._enrich_records(focus_regions)
                results['enrichment'] = enrichment_results
                self.status['enrichment']['last_run'] = datetime.now()
                self.status['enrichment']['records_enriched'] = enrichment_results.get('enriched', 0)
                
                # Benachrichtige Prediction Agent
                self.message_bus.publish(AgentMessage(
                    sender='enrichment',
                    receiver='prediction',
                    message_type='data',
                    payload={'action': 'records_enriched', 'count': enrichment_results.get('enriched', 0)}
                ))
            except Exception as e:
                logger.error(f"Enrichment failed: {e}")
                results['enrichment']['error'] = str(e)
            finally:
                self.status['enrichment']['running'] = False
        
        # 4. Prediction
        if predict:
            logger.info("Starting prediction phase...")
            self.status['prediction']['running'] = True
            try:
                prediction_results = await self._create_predictions(focus_regions)
                results['prediction'] = prediction_results
                self.status['prediction']['last_run'] = datetime.now()
                self.status['prediction']['predictions_created'] = prediction_results.get('predictions', 0)
            except Exception as e:
                logger.error(f"Prediction failed: {e}")
                results['prediction']['error'] = str(e)
            finally:
                self.status['prediction']['running'] = False
        
        # 5. Regionale Daten aggregieren
        if focus_regions:
            logger.info("Aggregating regional data...")
            results['regional_data'] = self._aggregate_regional_data(focus_regions)
        
        return results
    
    async def _geocode_records(self, focus_regions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Geocode Records, fokussiere auf bestimmte Regionen"""
        records = self.db.get_records(limit=1000)
        
        if focus_regions:
            # Filtere Records nach Regionen
            filtered_records = []
            for record in records:
                region = (record.get('region') or '').lower()
                country_code = record.get('primary_country_code', '')
                
                for focus_region in focus_regions:
                    region_config = self.critical_regions.get(focus_region, {})
                    keywords = region_config.get('keywords', [])
                    countries = region_config.get('countries', [])
                    
                    if any(kw.lower() in region for kw in keywords) or country_code in countries:
                        filtered_records.append(record)
                        break
            
            records = filtered_records
        
        geocoded = 0
        for record in records:
            if record.get('primary_latitude') and record.get('primary_longitude'):
                continue  # Bereits geocoded
            
            region = record.get('region')
            if region:
                try:
                    geo_result = self.geocoder.geocode(region)
                    if geo_result and geo_result.latitude:
                        # Update in DB
                        with self.db.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE records SET
                                    primary_country_code = ?,
                                    primary_latitude = ?,
                                    primary_longitude = ?,
                                    geo_confidence = ?
                                WHERE id = ?
                            """, (
                                geo_result.country_code,
                                geo_result.latitude,
                                geo_result.longitude,
                                geo_result.confidence,
                                record['id']
                            ))
                        geocoded += 1
                except Exception as e:
                    logger.warning(f"Geocoding failed for {region}: {e}")
        
        return {'geocoded': geocoded, 'total': len(records)}
    
    async def _enrich_records(self, focus_regions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Reichere Records an, fokussiere auf bestimmte Regionen"""
        records = self.db.get_records(limit=100)
        
        if focus_regions:
            # Filtere nach Regionen
            filtered_records = []
            for record in records:
                region = (record.get('region') or '').lower()
                country_code = record.get('primary_country_code', '')
                
                for focus_region in focus_regions:
                    region_config = self.critical_regions.get(focus_region, {})
                    keywords = region_config.get('keywords', [])
                    countries = region_config.get('countries', [])
                    
                    if any(kw.lower() in region for kw in keywords) or country_code in countries:
                        filtered_records.append(record)
                        break
            
            records = filtered_records
        
        enriched = 0
        for record in records:
            try:
                enrichment_result = self.enrichment_orchestrator.enrich_record_comprehensive(
                    record,
                    use_ipcc=True,
                    use_satellite=True,
                    use_real_time=True
                )
                
                # Speichere in DB
                self.prediction_pipeline._save_enriched_data(
                    record['id'],
                    {'enrichment': enrichment_result}
                )
                
                enriched += 1
                
                # Sende Nachricht an andere Agenten
                self.message_bus.publish(AgentMessage(
                    sender='enrichment',
                    receiver=None,
                    message_type='data',
                    payload={
                        'action': 'record_enriched',
                        'record_id': record['id'],
                        'region': record.get('region')
                    }
                ))
                
            except Exception as e:
                logger.warning(f"Enrichment failed for record {record.get('id')}: {e}")
        
        return {'enriched': enriched, 'total': len(records)}
    
    async def _create_predictions(self, focus_regions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Erstelle Predictions für Records"""
        records = self.db.get_records(limit=50)
        
        if focus_regions:
            # Filtere nach Regionen
            filtered_records = []
            for record in records:
                region = (record.get('region') or '').lower()
                country_code = record.get('primary_country_code', '')
                
                for focus_region in focus_regions:
                    region_config = self.critical_regions.get(focus_region, {})
                    keywords = region_config.get('keywords', [])
                    countries = region_config.get('countries', [])
                    
                    if any(kw.lower() in region for kw in keywords) or country_code in countries:
                        filtered_records.append(record)
                        break
            
            records = filtered_records
        
        predictions_created = 0
        for record in records:
            try:
                result = self.prediction_pipeline.enrich_and_predict(
                    record_id=record['id'],
                    use_search=True,
                    use_extract=True,
                    use_llm=True
                )
                
                if result and not result.get('error'):
                    predictions_created += 1
            except Exception as e:
                logger.warning(f"Prediction failed for record {record.get('id')}: {e}")
        
        return {'predictions': predictions_created, 'total': len(records)}
    
    def _aggregate_regional_data(self, focus_regions: List[str]) -> Dict[str, Any]:
        """Aggregiere Daten für fokussierte Regionen"""
        regional_data = {}
        
        for region_name in focus_regions:
            region_config = self.critical_regions.get(region_name, {})
            keywords = region_config.get('keywords', [])
            countries = region_config.get('countries', [])
            
            # Hole Records für diese Region
            all_records = self.db.get_records(limit=1000)
            region_records = []
            
            for record in all_records:
                region = record.get('region', '').lower()
                country_code = record.get('primary_country_code', '')
                
                if any(kw.lower() in region for kw in keywords) or country_code in countries:
                    region_records.append(record)
            
            # Berechne Statistiken
            risk_distribution = defaultdict(int)
            sources = defaultdict(int)
            total_risk_score = 0
            
            for record in region_records:
                risk = self.risk_scorer.calculate_risk(record)
                level = self.risk_scorer.get_risk_level(risk.score)
                risk_distribution[level] += 1
                sources[record.get('source_name', 'Unknown')] += 1
                total_risk_score += risk.score
            
            avg_risk = total_risk_score / len(region_records) if region_records else 0
            
            regional_data[region_name] = {
                'total_records': len(region_records),
                'risk_distribution': dict(risk_distribution),
                'average_risk_score': avg_risk,
                'sources': dict(sources),
                'records_with_coordinates': sum(1 for r in region_records if r.get('primary_latitude')),
                'records_enriched': sum(1 for r in region_records if self._has_enrichment(r['id']))
            }
        
        return regional_data
    
    def _has_enrichment(self, record_id: int) -> bool:
        """Prüfe ob Record angereichert wurde"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM enriched_data WHERE record_id = ?", (record_id,))
            return cursor.fetchone() is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Hole aktuellen Status"""
        db_stats = self.db.get_statistics()
        
        return {
            'status': self.status,
            'database': db_stats,
            'message_bus': {
                'subscribers': len(self.message_bus.subscribers),
                'messages': len(self.message_bus.message_history)
            }
        }
    
    async def cleanup(self):
        """Cleanup"""
        if self.scraper:
            await self.scraper.__aexit__(None, None, None)


# Import für os.getenv
import os


async def main():
    """Main entry point"""
    config = Config()
    orchestrator = MasterOrchestrator(config)
    
    try:
        await orchestrator.initialize()
        
        # Führe Pipeline aus mit Fokus auf Deutschland und Europa
        results = await orchestrator.run_full_pipeline(
            enrich=True,
            predict=True,
            geocode=True,
            focus_regions=['Germany', 'Europe']
        )
        
        print("\n✅ Pipeline completed successfully!")
        print(f"Scraping: {results['scraping'].get('records_stored', 0)} records")
        print(f"Geocoding: {results['geocoding'].get('geocoded', 0)} records")
        print(f"Enrichment: {results['enrichment'].get('enriched', 0)} records")
        print(f"Predictions: {results['prediction'].get('predictions', 0)} predictions")
        
        # Zeige regionale Daten
        if results.get('regional_data'):
            print("\n📊 Regional Data:")
            for region, data in results['regional_data'].items():
                print(f"  {region}: {data['total_records']} records, avg risk: {data['average_risk_score']:.2f}")
        
    except Exception as e:
        logger.error(f"Master orchestrator error: {e}", exc_info=True)
    finally:
        await orchestrator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

