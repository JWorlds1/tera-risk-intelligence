"""
Database Service
Async PostgreSQL with PostGIS support
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from config.settings import settings
from loguru import logger

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()


async def init_db():
    """Initialize database connection"""
    try:
        async with engine.begin() as conn:
            # Test connection
            result = await conn.execute(text("SELECT 1"))
            
            # Check PostGIS
            result = await conn.execute(text("SELECT PostGIS_Version()"))
            postgis_version = result.scalar()
            logger.info(f"PostGIS version: {postgis_version}")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context():
    """Context manager for database session"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Utility functions for PostGIS operations
async def execute_spatial_query(query: str, params: dict = None):
    """Execute a spatial query"""
    async with get_db_context() as session:
        result = await session.execute(text(query), params or {})
        return result.fetchall()


async def find_region_for_point(lat: float, lon: float) -> str:
    """Find administrative region containing a point"""
    query = """
        SELECT id, name, admin_level
        FROM admin_regions
        WHERE ST_Contains(geometry, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
        ORDER BY admin_level DESC
        LIMIT 1
    """
    result = await execute_spatial_query(query, {"lat": lat, "lon": lon})
    return result[0] if result else None


async def get_neighboring_regions(region_id: str):
    """Get neighboring regions (for risk spillover)"""
    query = """
        SELECT ar2.id, ar2.name
        FROM admin_regions ar1
        JOIN admin_regions ar2 ON ST_Touches(ar1.geometry, ar2.geometry)
        WHERE ar1.id = :region_id
        AND ar2.id != :region_id
    """
    return await execute_spatial_query(query, {"region_id": region_id})

