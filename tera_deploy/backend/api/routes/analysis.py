"""
Context Space Analysis Routes
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
import h3

from models.schemas import (
    AnalyzeRequest, AnalyzeResponse, H3Cell, ContextTensor, 
    RiskScores, Coordinates, Scenario
)
from services.risk_engine import RiskEngine
from services.geocoding import GeocodingService
from loguru import logger

router = APIRouter()


@router.post("/context-space", response_model=AnalyzeResponse)
async def analyze_context_space(request: AnalyzeRequest):
    """
    Analyze a region using H3 hexagonal grid and context tensors.
    Returns risk scores and recommended actions for each cell.
    """
    logger.info(f"Analyzing: {request.region_name} | Scale: {request.scale} | Scenario: {request.scenario}")
    
    # Geocode region
    geocoder = GeocodingService()
    location = await geocoder.geocode(request.region_name)
    
    if not location:
        raise HTTPException(status_code=404, detail=f"Location not found: {request.region_name}")
    
    # Determine H3 resolution based on scale
    resolution_map = {
        "neighborhood": 10,  # ~80m cells
        "city": 8,          # ~460m cells  
        "region": 6         # ~3.2km cells
    }
    resolution = request.resolution or resolution_map.get(request.scale, 8)
    
    # Generate H3 grid
    center_h3 = h3.geo_to_h3(location["lat"], location["lon"], resolution)
    
    # Get surrounding cells (k-ring)
    k_ring_size = {"neighborhood": 4, "city": 8, "region": 12}.get(request.scale, 8)
    h3_indices = list(h3.k_ring(center_h3, k_ring_size))
    
    # Calculate year
    current_year = 2025
    target_year = current_year + request.year_offset
    
    # Generate cells with risk data
    risk_engine = RiskEngine()
    cells = []
    
    for h3_idx in h3_indices:
        # Get cell boundary
        boundary = h3.h3_to_geo_boundary(h3_idx, geo_json=True)
        centroid = h3.h3_to_geo(h3_idx)
        
        # Calculate context tensor and risk
        tensor = await risk_engine.calculate_tensor(
            h3_index=h3_idx,
            lat=centroid[0],
            lon=centroid[1],
            scenario=request.scenario,
            year=target_year
        )
        
        # Generate recommended actions
        actions = risk_engine.generate_actions(tensor)
        
        cell = H3Cell(
            h3_index=h3_idx,
            resolution=resolution,
            centroid=Coordinates(lat=centroid[0], lon=centroid[1]),
            boundary=[Coordinates(lat=pt[1], lon=pt[0]) for pt in boundary],
            tensor=tensor,
            actions=actions
        )
        cells.append(cell)
    
    # Calculate global statistics
    total_risk = sum(c.tensor.scores.total_risk for c in cells) / len(cells)
    affected_pop = sum(c.tensor.socio.population_density * 0.5 for c in cells)  # Simplified
    total_cost = sum(sum(a.get("cost", 0) for a in c.actions) for c in cells)
    
    return AnalyzeResponse(
        region_name=request.region_name,
        year=target_year,
        scenario=request.scenario,
        scale=request.scale,
        grid_center=Coordinates(lat=location["lat"], lon=location["lon"]),
        cells=cells,
        global_stats={
            "avgRisk": total_risk,
            "affectedPopulation": affected_pop,
            "totalCost": total_cost,
            "cellCount": len(cells)
        }
    )


@router.get("/scenarios")
async def list_scenarios():
    """List available IPCC scenarios"""
    return {
        "scenarios": [
            {"id": "SSP1-2.6", "name": "Sustainability", "description": "Low emissions, strong mitigation"},
            {"id": "SSP2-4.5", "name": "Middle of the Road", "description": "Intermediate emissions"},
            {"id": "SSP3-7.0", "name": "Regional Rivalry", "description": "High emissions, limited adaptation"},
            {"id": "SSP5-8.5", "name": "Fossil-fueled Development", "description": "Very high emissions"}
        ]
    }


@router.get("/cell/{h3_index}")
async def get_cell_details(h3_index: str):
    """Get detailed information for a specific H3 cell"""
    if not h3.h3_is_valid(h3_index):
        raise HTTPException(status_code=400, detail="Invalid H3 index")
    
    centroid = h3.h3_to_geo(h3_index)
    boundary = h3.h3_to_geo_boundary(h3_index, geo_json=True)
    
    risk_engine = RiskEngine()
    tensor = await risk_engine.calculate_tensor(
        h3_index=h3_index,
        lat=centroid[0],
        lon=centroid[1],
        scenario=Scenario.SSP2_45,
        year=2030
    )
    
    return {
        "h3_index": h3_index,
        "resolution": h3.h3_get_resolution(h3_index),
        "centroid": {"lat": centroid[0], "lon": centroid[1]},
        "boundary": [{"lat": pt[1], "lon": pt[0]} for pt in boundary],
        "tensor": tensor.model_dump(),
        "neighbors": list(h3.k_ring(h3_index, 1))
    }

