"""
FastAPI Server - API Endpoints für Frontend-Backend-Kommunikation
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime

from h3_grid_engine import H3GridEngine
from context_tensor_engine import ContextTensorEngine
from ssp_scenario_engine import SSPScenarioEngine, SSPScenario
from risk_modeling_engine import RiskModelingEngine
from action_recommendation_engine import ActionRecommendationEngine
from data_acquisition_agents import DataAcquisitionOrchestrator
from free_llm_manager import FreeLLMManager
from color_computation_engine import ColorComputationEngine
from global_context_analyzer import GlobalContextAnalyzer
from config import Config

app = FastAPI(title="Climate Context Space API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
config = Config()
h3_engine = H3GridEngine()
tensor_engine = ContextTensorEngine(config)
ssp_engine = SSPScenarioEngine()
risk_engine = RiskModelingEngine()
llm_manager = FreeLLMManager(config)
action_engine = ActionRecommendationEngine(llm_manager)
data_orchestrator = DataAcquisitionOrchestrator(config)
color_engine = ColorComputationEngine()
global_analyzer = GlobalContextAnalyzer(config)


# Pydantic models
class H3GridRequest(BaseModel):
    center_lat: float
    center_lng: float
    scale: str = "city"
    region_name: str = "Unknown"


class ContextSpaceAnalysisRequest(BaseModel):
    region_name: str
    year_offset: int = 5
    scenario: str = "SSP2-4.5"
    scale: str = "city"


class RiskCalculationRequest(BaseModel):
    h3_index: str
    scenario: Optional[str] = None


@app.on_event("startup")
async def startup():
    """Initialize services on startup"""
    await data_orchestrator.initialize()
    await llm_manager.initialize()
    await global_analyzer.initialize()


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    await data_orchestrator.close()
    await llm_manager.close()
    await tensor_engine.close()
    await global_analyzer.close()


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Climate Context Space API", "version": "1.0.0"}


@app.post("/api/h3/grid")
async def generate_h3_grid(request: H3GridRequest):
    """
    Generate H3 grid for a region
    
    Args:
        request: H3GridRequest with coordinates and scale
    
    Returns:
        H3 grid data
    """
    try:
        grid = h3_engine.generate_grid(
            center_lat=request.center_lat,
            center_lng=request.center_lng,
            scale=request.scale,
            region_name=request.region_name
        )
        
        return {
            "success": True,
            "cells": [
                {
                    "h3_index": cell.h3_index,
                    "center_lat": cell.center_lat,
                    "center_lng": cell.center_lng,
                    "boundary": cell.boundary
                }
                for cell in grid.cells
            ],
            "center": {
                "lat": grid.center_lat,
                "lng": grid.center_lng
            },
            "resolution": grid.resolution,
            "scale": grid.scale
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tensor/{h3_index}")
async def get_tensor(h3_index: str, year: Optional[int] = None):
    """
    Get context tensor for an H3 cell
    
    Args:
        h3_index: H3 cell index
        year: Year for temporal data
    
    Returns:
        Context tensor
    """
    try:
        cell = h3_engine.get_cell_by_index(h3_index)
        if not cell:
            raise HTTPException(status_code=404, detail="H3 cell not found")
        
        tensor = await tensor_engine.generate_tensor_for_cell(cell, year)
        
        # Convert to dict
        return {
            "h3_index": tensor.h3_index,
            "timestamp": tensor.timestamp.isoformat() if tensor.timestamp else None,
            "dimensions": {
                "climate": {
                    "temp_mean": tensor.dimensions.get('climate', {}).temp_mean if hasattr(tensor.dimensions.get('climate', {}), 'temp_mean') else 0.0,
                    "precipitation": tensor.dimensions.get('climate', {}).precipitation if hasattr(tensor.dimensions.get('climate', {}), 'precipitation') else 0.0,
                },
                "geography": {
                    "elevation": tensor.dimensions.get('geography', {}).elevation if hasattr(tensor.dimensions.get('geography', {}), 'elevation') else 0.0,
                    "land_cover_class": tensor.dimensions.get('geography', {}).land_cover_class if hasattr(tensor.dimensions.get('geography', {}), 'land_cover_class') else 'Unknown',
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/context-space/analyze")
async def analyze_context_space(request: ContextSpaceAnalysisRequest):
    """
    Full context space analysis
    
    Args:
        request: Analysis request
    
    Returns:
        Complete analysis with grid, tensors, risks, and recommendations
    """
    try:
        # Generate H3 grid
        grid = h3_engine.generate_grid(
            center_lat=0.0,  # Would geocode region_name
            center_lng=0.0,
            scale=request.scale,
            region_name=request.region_name
        )
        
        # Generate tensors
        tensors = await tensor_engine.generate_tensors_for_grid(grid, request.year_offset + datetime.now().year)
        
        # Apply SSP scenario
        projected_tensors = ssp_engine.simulate_region(
            request.region_name,
            request.scenario,
            request.year_offset + datetime.now().year,
            tensors
        )
        
        # Calculate risks
        risk_scores_list = risk_engine.calculate_risk_for_grid(projected_tensors)
        
        # Generate recommendations
        cells_data = []
        for i, (tensor, risk_scores) in enumerate(zip(projected_tensors, risk_scores_list)):
            recommendations = action_engine.recommend_actions(
                tensor.h3_index,
                risk_scores,
                tensor
            )
            
            # Compute color
            color, alpha = color_engine.compute_final_color(tensor, 'composite')
            
            cells_data.append({
                "h3_index": tensor.h3_index,
                "center": {
                    "lat": grid.cells[i].center_lat,
                    "lng": grid.cells[i].center_lng
                },
                "boundary": grid.cells[i].boundary,
                "risk_scores": risk_scores,
                "color": {
                    "r": color.r,
                    "g": color.g,
                    "b": color.b,
                    "alpha": alpha
                },
                "recommendations": recommendations
            })
        
        return {
            "success": True,
            "region_name": request.region_name,
            "scenario": request.scenario,
            "year": request.year_offset + datetime.now().year,
            "scale": request.scale,
            "cells": cells_data,
            "center": {
                "lat": grid.center_lat,
                "lng": grid.center_lng
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ssp/simulate")
async def simulate_ssp(
    region_name: str,
    scenario: str = "SSP2-4.5",
    year: int = 2050
):
    """
    Simulate SSP scenario
    
    Args:
        region_name: Region name
        scenario: SSP scenario string
        year: Target year
    
    Returns:
        SSP projection
    """
    try:
        ssp_scenario = ssp_engine.parse_scenario(scenario)
        if not ssp_scenario:
            raise HTTPException(status_code=400, detail=f"Invalid scenario: {scenario}")
        
        projection = ssp_engine.project_to_year(ssp_scenario, year)
        
        return {
            "success": True,
            "scenario": projection.scenario.value,
            "year": projection.year,
            "projection": {
                "population_growth": projection.population_growth,
                "gdp_growth": projection.gdp_growth,
                "temperature_increase": projection.temperature_increase,
                "precipitation_change": projection.precipitation_change
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/risk/calculate")
async def calculate_risk(
    h3_index: str,
    scenario: Optional[str] = None
):
    """
    Calculate risk for an H3 cell
    
    Args:
        h3_index: H3 cell index
        scenario: Optional SSP scenario
    
    Returns:
        Risk scores
    """
    try:
        cell = h3_engine.get_cell_by_index(h3_index)
        if not cell:
            raise HTTPException(status_code=404, detail="H3 cell not found")
        
        tensor = await tensor_engine.generate_tensor_for_cell(cell)
        
        # Apply scenario if provided
        if scenario:
            ssp_scenario = ssp_engine.parse_scenario(scenario)
            if ssp_scenario:
                projection = ssp_engine.project_to_year(ssp_scenario, datetime.now().year + 5)
                tensor = ssp_engine.apply_projection_to_tensor(tensor, projection)
        
        risk_scores = risk_engine.calculate_risk_for_cell(tensor)
        
        return {
            "success": True,
            "h3_index": h3_index,
            "risk_scores": risk_scores
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/actions/recommend")
async def recommend_actions(
    h3_index: str,
    risk_score: Optional[float] = None
):
    """
    Get action recommendations for an H3 cell
    
    Args:
        h3_index: H3 cell index
        risk_score: Optional risk score override
    
    Returns:
        Action recommendations
    """
    try:
        cell = h3_engine.get_cell_by_index(h3_index)
        if not cell:
            raise HTTPException(status_code=404, detail="H3 cell not found")
        
        tensor = await tensor_engine.generate_tensor_for_cell(cell)
        risk_scores = risk_engine.calculate_risk_for_cell(tensor)
        
        if risk_score is not None:
            risk_scores['total_risk'] = risk_score
        
        recommendations = action_engine.recommend_actions(
            h3_index,
            risk_scores,
            tensor
        )
        
        return {
            "success": True,
            "h3_index": h3_index,
            "recommendations": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

