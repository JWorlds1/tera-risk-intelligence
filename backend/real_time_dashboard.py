# real_time_dashboard.py - Real-time Dashboard für Extraktions-Überwachung
import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import structlog
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from real_time_extractor import RealTimeExtractor
from quality_control import DataQualityController
from config import Config

logger = structlog.get_logger(__name__)

# FastAPI App
app = FastAPI(title="Climate Conflict Real-time Dashboard")

# Templates
templates = Jinja2Templates(directory="templates")

# Global instances
extractor_instance = None
quality_controller = None

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global extractor_instance, quality_controller
    config = Config()
    extractor_instance = RealTimeExtractor(config)
    quality_controller = DataQualityController(config)
    await extractor_instance.__aenter__()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global extractor_instance
    if extractor_instance:
        await extractor_instance.__aexit__(None, None, None)

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Dashboard connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Dashboard disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected dashboards"""
        if self.active_connections:
            message_str = json.dumps(message, default=str)
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(message_str)
                except:
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for conn in disconnected:
                self.active_connections.remove(conn)

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "Climate Conflict Real-time Dashboard"
    })

@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket for real-time dashboard updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and send periodic updates
            await asyncio.sleep(1)
            
            # Send real-time data
            if extractor_instance:
                data = {
                    "type": "dashboard_update",
                    "timestamp": datetime.now().isoformat(),
                    "stats": extractor_instance.stats,
                    "jobs": extractor_instance.get_all_jobs(),
                    "quality": quality_controller.get_quality_trends() if quality_controller else {}
                }
                await manager.broadcast(data)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/dashboard/overview")
async def get_dashboard_overview():
    """Get dashboard overview data"""
    if not extractor_instance:
        return {"error": "Extractor not initialized"}
    
    # Get basic stats
    stats = extractor_instance.stats
    jobs = extractor_instance.get_all_jobs()
    quality = quality_controller.get_quality_trends() if quality_controller else {}
    
    # Calculate additional metrics
    total_jobs = stats['total_jobs']
    success_rate = stats['success_rate']
    avg_time = stats['avg_extraction_time']
    
    # Job status breakdown
    active_count = len(jobs['active'])
    completed_count = len(jobs['completed'])
    
    # Recent activity (last 10 jobs)
    recent_jobs = jobs['completed'][-10:] if jobs['completed'] else []
    
    return {
        "overview": {
            "total_jobs": total_jobs,
            "active_jobs": active_count,
            "completed_jobs": completed_count,
            "success_rate": success_rate,
            "avg_extraction_time": avg_time,
            "last_update": stats['last_update'].isoformat()
        },
        "recent_activity": recent_jobs,
        "quality_metrics": quality,
        "system_health": {
            "status": "healthy" if success_rate > 0.7 else "warning",
            "uptime": "running",
            "last_error": None
        }
    }

@app.get("/api/dashboard/jobs")
async def get_jobs_detailed():
    """Get detailed jobs information"""
    if not extractor_instance:
        return {"error": "Extractor not initialized"}
    
    jobs = extractor_instance.get_all_jobs()
    
    # Add quality information to jobs
    for job in jobs['completed']:
        if job.get('result') and 'record' in job['result']:
            # Add quality analysis if available
            pass
    
    return jobs

@app.get("/api/dashboard/quality")
async def get_quality_analysis():
    """Get quality analysis"""
    if not quality_controller:
        return {"error": "Quality controller not initialized"}
    
    trends = quality_controller.get_quality_trends()
    performance = quality_controller.get_field_performance()
    
    return {
        "trends": trends,
        "field_performance": performance,
        "quality_history_count": len(quality_controller.quality_history)
    }

@app.get("/api/dashboard/alerts")
async def get_alerts():
    """Get system alerts and warnings"""
    alerts = []
    
    if extractor_instance:
        stats = extractor_instance.stats
        
        # Success rate alert
        if stats['success_rate'] < 0.5:
            alerts.append({
                "type": "warning",
                "message": f"Low success rate: {stats['success_rate']:.1%}",
                "timestamp": datetime.now().isoformat(),
                "action": "Check extraction quality and retry failed jobs"
            })
        
        # High retry count alert
        if stats['retry_count'] > stats['total_jobs'] * 0.3:
            alerts.append({
                "type": "warning",
                "message": f"High retry count: {stats['retry_count']} retries",
                "timestamp": datetime.now().isoformat(),
                "action": "Investigate extraction issues"
            })
        
        # Long extraction time alert
        if stats['avg_extraction_time'] > 30:
            alerts.append({
                "type": "info",
                "message": f"Slow extraction: {stats['avg_extraction_time']:.1f}s average",
                "timestamp": datetime.now().isoformat(),
                "action": "Consider optimizing extraction process"
            })
    
    if quality_controller:
        trends = quality_controller.get_quality_trends()
        
        # Quality trend alert
        if trends.get('score_trend') == 'decreasing':
            alerts.append({
                "type": "warning",
                "message": "Quality scores are decreasing",
                "timestamp": datetime.now().isoformat(),
                "action": "Review extraction quality and improve data sources"
            })
    
    return {
        "alerts": alerts,
        "alert_count": len(alerts),
        "last_check": datetime.now().isoformat()
    }

@app.post("/api/dashboard/retry-failed")
async def retry_failed_jobs():
    """Retry all failed jobs"""
    if not extractor_instance:
        return {"error": "Extractor not initialized"}
    
    failed_jobs = [
        job for job in extractor_instance.completed_jobs.values()
        if job.status.value == "failed"
    ]
    
    retry_count = 0
    for job in failed_jobs:
        # Reset job status and add back to queue
        job.status = extractor_instance.ExtractionStatus.PENDING
        job.retry_count = 0
        job.error = None
        job.result = None
        
        await extractor_instance.job_queue.put(job)
        retry_count += 1
    
    return {
        "message": f"Retrying {retry_count} failed jobs",
        "retry_count": retry_count
    }

@app.post("/api/dashboard/clear-completed")
async def clear_completed_jobs():
    """Clear completed jobs to free memory"""
    if not extractor_instance:
        return {"error": "Extractor not initialized"}
    
    cleared_count = len(extractor_instance.completed_jobs)
    extractor_instance.completed_jobs.clear()
    
    return {
        "message": f"Cleared {cleared_count} completed jobs",
        "cleared_count": cleared_count
    }

# Background task for periodic updates
async def periodic_updates():
    """Send periodic updates to dashboard"""
    while True:
        try:
            await asyncio.sleep(5)  # Update every 5 seconds
            
            if extractor_instance and manager.active_connections:
                # Get current stats
                stats = extractor_instance.stats
                jobs = extractor_instance.get_all_jobs()
                
                # Create update message
                update = {
                    "type": "periodic_update",
                    "timestamp": datetime.now().isoformat(),
                    "stats": stats,
                    "active_jobs_count": len(jobs['active']),
                    "completed_jobs_count": len(jobs['completed'])
                }
                
                await manager.broadcast(update)
                
        except Exception as e:
            logger.error(f"Error in periodic updates: {e}")
            await asyncio.sleep(10)

# Start background task
@app.on_event("startup")
async def start_background_tasks():
    asyncio.create_task(periodic_updates())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
