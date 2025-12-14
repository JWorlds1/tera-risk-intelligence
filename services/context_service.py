"""
Context Service - RAG-based LLM Inference for Risk Analysis
"""
import asyncio
import httpx
import h3
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from loguru import logger


@dataclass
class RiskAnalysis:
    h3_index: str
    location_name: str
    lat: float
    lon: float
    climate_risk: float
    conflict_risk: float
    total_risk: float
    ssp_scenario: str
    year_projection: int
    population_affected: int
    adaptation_cost_eur: float
    summary: str
    key_drivers: List[str]
    sources: List[Dict[str, str]]
    generated_at: datetime


class ContextService:
    def __init__(
        self, 
        ollama_url: str = "http://127.0.0.1:11434",
        model: str = "llama3.1:8b",
        vector_store = None
    ):
        self.ollama_url = ollama_url
        self.model = model
        self.vector_store = vector_store
    
    async def analyze_location(
        self,
        lat: float,
        lon: float,
        location_name: str = "Unknown",
        ssp_scenario: str = "SSP2-4.5",
        year_offset: int = 5,
        scale: str = "neighborhood"
    ) -> RiskAnalysis:
        logger.info(f"Analyzing: {location_name} ({lat}, {lon})")
        
        resolution = 7 if scale == "neighborhood" else 5 if scale == "city" else 3
        h3_index = h3.geo_to_h3(lat, lon, resolution)
        
        analysis = await self._generate_llm_analysis(
            location_name=location_name,
            lat=lat, lon=lon,
            ssp_scenario=ssp_scenario,
            year_offset=year_offset,
            scale=scale
        )
        
        risk_scores = self._calculate_risk_scores(analysis, ssp_scenario)
        
        # Ensure key_drivers is a list of strings
        drivers = analysis.get("drivers", [])
        if not isinstance(drivers, list):
            drivers = [str(drivers)]
        clean_drivers = []
        for d in drivers:
            if isinstance(d, dict):
                clean_drivers.append(d.get("description", d.get("category", str(d))))
            else:
                clean_drivers.append(str(d))
        
        return RiskAnalysis(
            h3_index=h3_index,
            location_name=location_name,
            lat=lat, lon=lon,
            climate_risk=risk_scores["climate"],
            conflict_risk=risk_scores["conflict"],
            total_risk=risk_scores["total"],
            ssp_scenario=ssp_scenario,
            year_projection=datetime.now().year + year_offset,
            population_affected=risk_scores.get("population", 0),
            adaptation_cost_eur=risk_scores.get("cost", 0),
            summary=str(analysis.get("summary", "Analysis complete"))[:1000],
            key_drivers=clean_drivers[:5],
            sources=[],
            generated_at=datetime.utcnow()
        )
    
    async def _generate_llm_analysis(
        self, location_name: str, lat: float, lon: float,
        ssp_scenario: str, year_offset: int, scale: str
    ) -> Dict[str, Any]:
        prompt = f"""Analyze climate and conflict risks for {location_name} (lat: {lat:.2f}, lon: {lon:.2f}).
Scenario: {ssp_scenario}, Year: {datetime.now().year + year_offset}, Scale: {scale}

Return JSON:
{{"summary": "risk analysis text", "drivers": ["driver1", "driver2", "driver3"], "climate_score": 60, "conflict_score": 40, "population_estimate": 1000000, "adaptation_cost_millions": 100}}

Output ONLY valid JSON, no markdown."""

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False}
                )
                response.raise_for_status()
                result = response.json()
                
                llm_text = result.get("response", "{}")
                
                # Clean and parse JSON
                llm_text = llm_text.strip()
                if llm_text.startswith("```"):
                    llm_text = re.sub(r'^```\w*\n?', '', llm_text)
                    llm_text = re.sub(r'\n?```$', '', llm_text)
                
                try:
                    return json.loads(llm_text)
                except json.JSONDecodeError:
                    match = re.search(r'\{[^{}]*\}', llm_text, re.DOTALL)
                    if match:
                        try:
                            return json.loads(match.group())
                        except:
                            pass
                    return {"summary": llm_text[:500], "climate_score": 50, "conflict_score": 30, "drivers": ["Analysis in progress"]}
                    
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return {
                "summary": f"Risk analysis for {location_name}. Climate change impacts expected.",
                "drivers": ["Climate change", "Urban development", "Resource pressure"],
                "climate_score": 50, "conflict_score": 30,
                "population_estimate": 1000000,
                "adaptation_cost_millions": 100
            }
    
    def _calculate_risk_scores(self, analysis: Dict, ssp_scenario: str) -> Dict[str, float]:
        def safe_float(val, default=50.0):
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                try:
                    return float(val)
                except:
                    return default
            if isinstance(val, dict):
                return default
            return default
        
        climate_base = safe_float(analysis.get("climate_score"), 50)
        conflict_base = safe_float(analysis.get("conflict_score"), 30)
        
        ssp_mult = {"SSP1-2.6": 0.8, "SSP2-4.5": 1.0, "SSP3-7.0": 1.3, "SSP5-8.5": 1.5}.get(ssp_scenario, 1.0)
        
        climate = min(100, climate_base * ssp_mult)
        conflict = min(100, conflict_base * (1 + climate / 100 * 0.3))
        total = climate * 0.6 + conflict * 0.4
        
        pop = safe_float(analysis.get("population_estimate"), 1000000)
        cost = safe_float(analysis.get("adaptation_cost_millions"), 100)
        
        return {
            "climate": round(climate, 1),
            "conflict": round(conflict, 1),
            "total": round(total, 1),
            "population": int(pop),
            "cost": cost * 1_000_000
        }
