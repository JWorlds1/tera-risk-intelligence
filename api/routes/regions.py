"""
TERA Regions API
"""
from fastapi import APIRouter
from typing import List, Dict, Any

router = APIRouter()


@router.get("/")
async def list_regions():
    """List all risk regions"""
    return {
        "regions": [],
        "count": 0
    }


@router.get("/{region_id}")
async def get_region(region_id: int):
    """Get a specific region"""
    return {
        "id": region_id,
        "name": "Demo Region",
        "risk_score": 0.0
    }
