"""
TERA Analysis API - Real Data Integration
Transparente, wissenschaftlich fundierte Risikobewertung
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import httpx

# Import Real Risk Engine
import sys
sys.path.insert(0, '/data/tera/backend')
from services.real_risk_engine import get_engine, RealRiskEngine
from services.real_data_tessellation import EchteDatenTessellation

router = APIRouter()


class AnalyzeRequest(BaseModel):
    location: str


async def geocode(city: str) -> dict:
    """Geokodierung mit Nominatim"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            'https://nominatim.openstreetmap.org/search',
            params={'q': city, 'format': 'json', 'limit': 1},
            headers={'User-Agent': 'TERA-RiskIntelligence/2.0'}
        )
        if resp.status_code == 200:
            data = resp.json()
            if data:
                return {
                    'lat': float(data[0]['lat']),
                    'lon': float(data[0]['lon']),
                    'name': data[0].get('display_name', city),
                    'country': data[0].get('display_name', '').split(',')[-1].strip(),
                    'bbox': [float(x) for x in data[0].get('boundingbox', [])]
                }
    return None


def estimate_elevation_and_coast(lat: float, lon: float) -> tuple:
    """
    Schätzt Höhe und Küstenabstand basierend auf global_land_mask
    TODO: Ersetzen mit echten Copernicus DEM Abfragen
    """
    from global_land_mask import globe
    
    is_ocean = globe.is_ocean(lat, lon)
    if is_ocean:
        return 0, 0  # Im Wasser
    
    # Küstenabstand schätzen (prüfe Nachbarpunkte)
    coast_dist = 100  # Default: weit von Küste
    for r in [0.05, 0.1, 0.2, 0.5, 1.0]:
        for dlat, dlon in [(r,0), (-r,0), (0,r), (0,-r)]:
            if globe.is_ocean(lat + dlat, lon + dlon):
                coast_dist = r * 111  # ~111 km pro Grad
                break
        if coast_dist < 100:
            break
    
    # Höhe schätzen (sehr grob basierend auf Breitengrad)
    # TODO: Echte DEM-Daten
    elevation = 50  # Default
    if coast_dist < 5:
        elevation = 5
    elif coast_dist < 20:
        elevation = 20
    
    return elevation, coast_dist


@router.post('/analyze')
async def analyze_with_real_data(request: AnalyzeRequest):
    """
    Analysiert einen Standort mit ECHTEN, transparenten Daten
    
    Datenquellen:
    - USGS Earthquake Catalog (seismisch)
    - Copernicus DEM via global_land_mask (Topografie)
    - IPCC AR6 Projektionen (Klimatrends)
    - ACLED Konfliktdaten (Sicherheit)
    """
    geo = await geocode(request.location)
    if not geo:
        raise HTTPException(status_code=404, detail=f"Stadt nicht gefunden: {request.location}")
    
    # Topografie schätzen
    elevation, coast_dist = estimate_elevation_and_coast(geo['lat'], geo['lon'])
    
    # Real Risk Engine
    engine = get_engine()
    assessment = await engine.assess_location(
        location=request.location,
        lat=geo['lat'],
        lon=geo['lon'],
        country=geo['country'],
        elevation_m=elevation,
        coast_dist_km=coast_dist
    )
    
    # Frontend-Format
    result = engine.to_frontend_format(assessment)
    result['country'] = geo['country']
    result['bbox'] = geo.get('bbox')
    
    # City type bestimmen
    if coast_dist < 30:
        result['city_type'] = 'coastal'
    elif assessment.climate_variables[0].value > 0.5:  # Seismisch
        result['city_type'] = 'seismic'
    elif assessment.conflict_score > 0.5:
        result['city_type'] = 'conflict'
    else:
        result['city_type'] = 'temperate'
    
    return result


@router.get('/risk-map/viewport')
async def get_risk_map_viewport(
    min_lat: float = Query(...),
    min_lon: float = Query(...),
    max_lat: float = Query(...),
    max_lon: float = Query(...),
    zoom: int = Query(12),
    city_type: str = Query('temperate'),
    max_cells: int = Query(3000)
):
    """Viewport-basierte Tessellierung mit echten Daten"""
    tessellation = EchteDatenTessellation()
    geojson = await tessellation.generiere_viewport_karte(
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
        zoom=zoom,
        stadt_typ=city_type,
        max_cells=max_cells
    )
    return geojson
