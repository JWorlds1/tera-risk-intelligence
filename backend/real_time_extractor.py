# real_time_extractor.py - Garantierte Echtzeit-Extraktion mit Qualitätskontrolle
import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import structlog
from dataclasses import dataclass
from enum import Enum
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import Config
from compliance import ComplianceAgent
from fetchers import MultiAgentFetcher
from extractors import ExtractorFactory
from validators import ValidationAgent
from storage import StorageAgent
from ai_agents import ClimateConflictAgent
from strategic_urls import StrategicURLManager

logger = structlog.get_logger(__name__)

class ExtractionStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class ExtractionJob:
    id: str
    url: str
    source_name: str
    priority: int
    status: ExtractionStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    result: Optional[Dict] = None
    error: Optional[str] = None

class RealTimeExtractor:
    """Garantierte Echtzeit-Extraktion mit Qualitätskontrolle"""
    
    def __init__(self, config: Config):
        self.config = config
        self.compliance_agent = None
        self.fetcher = None
        self.extractor_factory = None
        self.validator = None
        self.storage_agent = None
        self.ai_agent = None
        self.strategic_urls = StrategicURLManager()
        
        # Job Management
        self.job_queue = asyncio.Queue()
        self.active_jobs: Dict[str, ExtractionJob] = {}
        self.completed_jobs: Dict[str, ExtractionJob] = {}
        
        # Real-time Stats
        self.stats = {
            'total_jobs': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'retry_count': 0,
            'avg_extraction_time': 0.0,
            'success_rate': 0.0,
            'last_update': datetime.now()
        }
        
        # WebSocket connections for real-time updates
        self.websocket_connections: List[WebSocket] = []
        
        # Quality Control
        self.quality_thresholds = {
            'min_content_length': 100,
            'max_extraction_time': 30.0,  # seconds
            'min_confidence_score': 0.7,
            'required_fields': ['title', 'summary', 'region', 'topics']
        }
    
    async def __aenter__(self):
        """Initialize all components"""
        self.compliance_agent = ComplianceAgent(self.config)
        self.fetcher = MultiAgentFetcher(self.config, self.compliance_agent)
        self.extractor_factory = ExtractorFactory(self.config)
        self.validator = ValidationAgent(self.config)
        self.storage_agent = StorageAgent(self.config)
        
        if self.config.ENABLE_AI_EXTRACTION:
            self.ai_agent = ClimateConflictAgent(self.config, self.config.FIRECRAWL_API_KEY)
        
        await self.compliance_agent.__aenter__()
        await self.fetcher.__aenter__()
        
        # Start background workers
        asyncio.create_task(self._job_processor())
        asyncio.create_task(self._stats_updater())
        asyncio.create_task(self._quality_monitor())
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup"""
        if self.compliance_agent:
            await self.compliance_agent.__aexit__(exc_type, exc_val, exc_tb)
        if self.fetcher:
            await self.fetcher.__aexit__(exc_type, exc_val, exc_tb)
    
    async def add_extraction_job(self, url: str, source_name: str, priority: int = 1) -> str:
        """Füge Extraktions-Job zur Queue hinzu"""
        job_id = hashlib.md5(f"{url}_{datetime.now()}".encode()).hexdigest()[:12]
        
        job = ExtractionJob(
            id=job_id,
            url=url,
            source_name=source_name,
            priority=priority,
            status=ExtractionStatus.PENDING,
            created_at=datetime.now()
        )
        
        await self.job_queue.put(job)
        self.active_jobs[job_id] = job
        self.stats['total_jobs'] += 1
        
        logger.info(f"Added extraction job {job_id} for {url}")
        await self._broadcast_update(f"job_added", job.__dict__)
        
        return job_id
    
    async def add_strategic_urls(self) -> List[str]:
        """Füge strategische URLs hinzu"""
        job_ids = []
        critical_urls = self.strategic_urls.get_critical_urls()
        
        for url_info in critical_urls:
            job_id = await self.add_extraction_job(
                url=url_info.url,
                source_name=url_info.category,
                priority=1 if url_info.priority.value <= 2 else 2
            )
            job_ids.append(job_id)
        
        logger.info(f"Added {len(job_ids)} strategic URLs to extraction queue")
        return job_ids
    
    async def _job_processor(self):
        """Hauptprozessor für Extraktions-Jobs"""
        while True:
            try:
                # Warte auf Job
                job = await self.job_queue.get()
                
                # Update Job Status
                job.status = ExtractionStatus.IN_PROGRESS
                job.started_at = datetime.now()
                
                logger.info(f"Processing job {job.id} for {job.url}")
                await self._broadcast_update(f"job_started", job.__dict__)
                
                # Extrahiere Daten
                success = await self._extract_data(job)
                
                if success:
                    job.status = ExtractionStatus.SUCCESS
                    job.completed_at = datetime.now()
                    self.stats['successful_extractions'] += 1
                    logger.info(f"Job {job.id} completed successfully")
                else:
                    # Retry Logic
                    if job.retry_count < job.max_retries:
                        job.retry_count += 1
                        job.status = ExtractionStatus.RETRYING
                        self.stats['retry_count'] += 1
                        
                        # Exponential backoff
                        delay = min(2 ** job.retry_count, 60)
                        await asyncio.sleep(delay)
                        await self.job_queue.put(job)
                        logger.info(f"Retrying job {job.id} (attempt {job.retry_count})")
                    else:
                        job.status = ExtractionStatus.FAILED
                        job.completed_at = datetime.now()
                        self.stats['failed_extractions'] += 1
                        logger.error(f"Job {job.id} failed after {job.max_retries} retries")
                
                # Update Stats
                await self._update_job_stats(job)
                await self._broadcast_update(f"job_completed", job.__dict__)
                
                # Move to completed
                self.completed_jobs[job.id] = job
                if job.id in self.active_jobs:
                    del self.active_jobs[job.id]
                
            except Exception as e:
                logger.error(f"Error in job processor: {e}")
                await asyncio.sleep(1)
    
    async def _extract_data(self, job: ExtractionJob) -> bool:
        """Extrahiere Daten für einen Job"""
        try:
            start_time = time.time()
            
            # 1. Compliance Check
            can_scrape, reason = await self.compliance_agent.can_scrape(job.url)
            if not can_scrape:
                job.error = f"Compliance check failed: {reason}"
                return False
            
            # 2. Fetch Data
            fetch_result = await self.fetcher.fetch_with_fallback(job.url)
            if not fetch_result.success:
                job.error = f"Fetch failed: {fetch_result.error}"
                return False
            
            # 3. Extract Data (try AI first, fallback to traditional)
            record = None
            
            # Try AI extraction first
            if self.config.ENABLE_AI_EXTRACTION and self.ai_agent:
                try:
                    record = await self.ai_agent.extract_with_ai_support(job.url, job.source_name)
                    if record:
                        logger.info(f"AI extraction successful for {job.url}")
                except Exception as e:
                    logger.warning(f"AI extraction failed, falling back to traditional: {e}")
            
            # Fallback to traditional extraction
            if not record:
                extractor = self.extractor_factory.get_extractor(job.url)
                record = extractor.extract(fetch_result)
            
            if not record:
                job.error = "No data extracted"
                return False
            
            # 4. Validate Data
            validation_result = self.validator.validate(record)
            if not validation_result.is_valid:
                job.error = f"Validation failed: {validation_result.errors}"
                return False
            
            # 5. Quality Check
            quality_score = await self._check_data_quality(record)
            if quality_score < self.quality_thresholds['min_confidence_score']:
                job.error = f"Quality check failed: score {quality_score:.2f}"
                return False
            
            # 6. Store Data
            stored_files = await self.storage_agent.store_all_formats([record], job.source_name, job.id)
            
            # 7. Update Job Result
            job.result = {
                'record': record.__dict__,
                'quality_score': quality_score,
                'extraction_time': time.time() - start_time,
                'stored_files': stored_files,
                'validation_warnings': validation_result.warnings
            }
            
            return True
            
        except Exception as e:
            job.error = f"Extraction error: {str(e)}"
            logger.error(f"Error extracting data for {job.url}: {e}")
            return False
    
    async def _check_data_quality(self, record) -> float:
        """Prüfe Datenqualität und gib Score zurück (0-1)"""
        score = 1.0
        
        # Prüfe erforderliche Felder
        required_fields = self.quality_thresholds['required_fields']
        for field in required_fields:
            if not hasattr(record, field) or not getattr(record, field):
                score -= 0.2
        
        # Prüfe Content-Länge
        if hasattr(record, 'summary') and record.summary:
            if len(record.summary) < self.quality_thresholds['min_content_length']:
                score -= 0.3
        
        # Prüfe Topics
        if hasattr(record, 'topics') and record.topics:
            if len(record.topics) < 2:
                score -= 0.1
        
        # Prüfe Region
        if hasattr(record, 'region') and not record.region:
            score -= 0.2
        
        return max(0.0, score)
    
    async def _update_job_stats(self, job: ExtractionJob):
        """Update Job-Statistiken"""
        if job.status == ExtractionStatus.SUCCESS and job.result:
            extraction_time = job.result.get('extraction_time', 0)
            
            # Update Durchschnittszeit
            total_successful = self.stats['successful_extractions']
            if total_successful > 0:
                current_avg = self.stats['avg_extraction_time']
                self.stats['avg_extraction_time'] = (
                    (current_avg * (total_successful - 1) + extraction_time) / total_successful
                )
        
        # Update Success Rate
        total_jobs = self.stats['total_jobs']
        if total_jobs > 0:
            self.stats['success_rate'] = self.stats['successful_extractions'] / total_jobs
        
        self.stats['last_update'] = datetime.now()
    
    async def _stats_updater(self):
        """Update Statistiken regelmäßig"""
        while True:
            try:
                await asyncio.sleep(10)  # Update every 10 seconds
                await self._broadcast_update("stats_update", self.stats)
            except Exception as e:
                logger.error(f"Error in stats updater: {e}")
    
    async def _quality_monitor(self):
        """Überwache Extraktionsqualität"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                # Prüfe aktuelle Jobs
                for job in list(self.active_jobs.values()):
                    if job.status == ExtractionStatus.IN_PROGRESS:
                        # Prüfe ob Job zu lange läuft
                        if job.started_at:
                            duration = (datetime.now() - job.started_at).total_seconds()
                            if duration > self.quality_thresholds['max_extraction_time']:
                                logger.warning(f"Job {job.id} running too long: {duration}s")
                                # Cancel job
                                job.status = ExtractionStatus.FAILED
                                job.error = "Timeout"
                
                # Prüfe Success Rate
                if self.stats['success_rate'] < 0.5:
                    logger.warning(f"Low success rate: {self.stats['success_rate']:.2%}")
                
            except Exception as e:
                logger.error(f"Error in quality monitor: {e}")
    
    async def _broadcast_update(self, event_type: str, data: Any):
        """Sende Update an alle WebSocket-Verbindungen"""
        if self.websocket_connections:
            message = {
                'type': event_type,
                'data': data,
                'timestamp': datetime.now().isoformat()
            }
            
            # Sende an alle Verbindungen
            disconnected = []
            for websocket in self.websocket_connections:
                try:
                    await websocket.send_text(json.dumps(message, default=str))
                except:
                    disconnected.append(websocket)
            
            # Entferne getrennte Verbindungen
            for ws in disconnected:
                self.websocket_connections.remove(ws)
    
    async def connect_websocket(self, websocket: WebSocket):
        """Verbinde WebSocket für Real-time Updates"""
        await websocket.accept()
        self.websocket_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.websocket_connections)}")
    
    async def disconnect_websocket(self, websocket: WebSocket):
        """Trenne WebSocket"""
        if websocket in self.websocket_connections:
            self.websocket_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.websocket_connections)}")
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Hole Job-Status"""
        if job_id in self.active_jobs:
            return self.active_jobs[job_id].__dict__
        elif job_id in self.completed_jobs:
            return self.completed_jobs[job_id].__dict__
        return None
    
    def get_all_jobs(self) -> Dict[str, List[Dict]]:
        """Hole alle Jobs"""
        return {
            'active': [job.__dict__ for job in self.active_jobs.values()],
            'completed': [job.__dict__ for job in self.completed_jobs.values()],
            'stats': self.stats
        }
    
    def get_quality_metrics(self) -> Dict[str, Any]:
        """Hole Qualitäts-Metriken"""
        return {
            'success_rate': self.stats['success_rate'],
            'avg_extraction_time': self.stats['avg_extraction_time'],
            'total_jobs': self.stats['total_jobs'],
            'quality_thresholds': self.quality_thresholds,
            'active_jobs_count': len(self.active_jobs),
            'completed_jobs_count': len(self.completed_jobs)
        }

# FastAPI App für Real-time API
app = FastAPI(title="Climate Conflict Real-time Extractor")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global extractor instance
extractor_instance = None

@app.on_event("startup")
async def startup_event():
    """Initialize extractor on startup"""
    global extractor_instance
    config = Config()
    extractor_instance = RealTimeExtractor(config)
    await extractor_instance.__aenter__()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global extractor_instance
    if extractor_instance:
        await extractor_instance.__aexit__(None, None, None)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint für Real-time Updates"""
    await extractor_instance.connect_websocket(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        await extractor_instance.disconnect_websocket(websocket)

@app.post("/api/extract")
async def extract_url(url: str, source_name: str, priority: int = 1):
    """API endpoint für URL-Extraktion"""
    if not extractor_instance:
        return {"error": "Extractor not initialized"}
    
    job_id = await extractor_instance.add_extraction_job(url, source_name, priority)
    return {"job_id": job_id, "status": "queued"}

@app.get("/api/jobs")
async def get_jobs():
    """API endpoint für alle Jobs"""
    if not extractor_instance:
        return {"error": "Extractor not initialized"}
    
    return extractor_instance.get_all_jobs()

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """API endpoint für Job-Status"""
    if not extractor_instance:
        return {"error": "Extractor not initialized"}
    
    status = extractor_instance.get_job_status(job_id)
    if not status:
        return {"error": "Job not found"}
    
    return status

@app.get("/api/quality")
async def get_quality_metrics():
    """API endpoint für Qualitäts-Metriken"""
    if not extractor_instance:
        return {"error": "Extractor not initialized"}
    
    return extractor_instance.get_quality_metrics()

@app.post("/api/strategic-urls")
async def add_strategic_urls():
    """API endpoint für strategische URLs"""
    if not extractor_instance:
        return {"error": "Extractor not initialized"}
    
    job_ids = await extractor_instance.add_strategic_urls()
    return {"job_ids": job_ids, "count": len(job_ids)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
