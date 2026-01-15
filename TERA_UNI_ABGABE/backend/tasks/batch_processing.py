"""
Celery Tasks for Global Batch Processing
"""
import asyncio
from celery import Celery
from loguru import logger
from config.settings import settings

app = Celery(
    "tera_batch",
    broker=settings.redis_url,
    backend=settings.redis_url
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    task_track_started=True,
)


@app.task(name="tasks.fetch_nasa_events")
def fetch_nasa_events():
    """Fetch latest NASA EONET events"""
    from agents.scraper import NASAEONETScraper
    import asyncpg
    
    async def run():
        pool = await asyncpg.create_pool(
            settings.database_url.replace("postgresql+asyncpg://", "postgresql://"),
            min_size=2, max_size=5
        )
        
        async with NASAEONETScraper(db_pool=pool) as scraper:
            events = await scraper.fetch_all_categories()
            total = sum(len(e) for e in events.values())
            
            for category, cat_events in events.items():
                await scraper.store_events(cat_events)
            
            logger.info(f"Fetched and stored {total} NASA events")
        
        await pool.close()
        return {"events_processed": total}
    
    return asyncio.run(run())


@app.task(name="tasks.generate_h3_grid")
def generate_h3_grid(min_lat: float, min_lon: float, max_lat: float, max_lon: float, resolution: int = 7):
    """Generate H3 grid for a region"""
    from data.h3_grid_generator import get_h3_cells_for_bbox, store_h3_cells
    import asyncpg
    
    async def run():
        pool = await asyncpg.create_pool(
            settings.database_url.replace("postgresql+asyncpg://", "postgresql://"),
            min_size=2, max_size=5
        )
        
        cells = get_h3_cells_for_bbox(min_lat, min_lon, max_lat, max_lon, resolution)
        await store_h3_cells(pool, cells)
        
        await pool.close()
        return {"cells_created": len(cells)}
    
    return asyncio.run(run())


@app.task(name="tasks.analyze_region")
def analyze_region(lat: float, lon: float, name: str, scenario: str = "SSP2-4.5"):
    """Analyze a region and store results"""
    from services.context_service import ContextService
    from services.vector_store import VectorStore
    
    async def run():
        vector_store = VectorStore()
        vector_store.init_collection()
        
        service = ContextService(
            ollama_url=settings.ollama_url,
            model=settings.ollama_model,
            vector_store=vector_store
        )
        
        analysis = await service.analyze_location(
            lat=lat, lon=lon,
            location_name=name,
            ssp_scenario=scenario
        )
        
        return {
            "location": name,
            "h3_index": analysis.h3_index,
            "total_risk": analysis.total_risk,
            "summary": analysis.summary[:200]
        }
    
    return asyncio.run(run())


@app.task(name="tasks.batch_analyze_cities")
def batch_analyze_cities(country_code: str = None, limit: int = 100):
    """Batch analyze cities"""
    import asyncpg
    
    async def run():
        pool = await asyncpg.create_pool(
            settings.database_url.replace("postgresql+asyncpg://", "postgresql://"),
            min_size=2, max_size=5
        )
        
        query = """
            SELECT name, ST_Y(geom) as lat, ST_X(geom) as lon, country_code
            FROM cities
            WHERE population > 100000
        """
        if country_code:
            query += f" AND country_code = '{country_code}'"
        query += f" ORDER BY population DESC LIMIT {limit}"
        
        async with pool.acquire() as conn:
            cities = await conn.fetch(query)
        
        await pool.close()
        
        results = []
        for city in cities:
            try:
                result = analyze_region.delay(
                    city["lat"], city["lon"], 
                    city["name"], "SSP2-4.5"
                )
                results.append({"city": city["name"], "task_id": result.id})
            except Exception as e:
                logger.error(f"Failed to queue {city['name']}: {e}")
        
        return {"queued": len(results)}
    
    return asyncio.run(run())
