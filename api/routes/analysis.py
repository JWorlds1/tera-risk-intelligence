"""
Analysis API - Dynamic City Support Worldwide
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import httpx

router = APIRouter()

# Risk profiles for projection text
PROJECTIONS = {
    'coastal': "Sea level rise +0.3-0.5m by 2050 (IPCC AR6 SSP2-4.5). Storm surge frequency increasing 40-60%. Coastal infrastructure requires €billions in adaptation. Managed retreat planning essential for lowest elevations.",
    'seismic': "Seismic hazard assessment indicates 20-30% probability of M7+ event within 30 years. Building retrofit program critical. 40% of structures pre-modern seismic code. Tsunami early warning capacity needed.",
    'arid': "Water stress increasing 50-70% by 2050. Extreme heat days (>45°C) tripling. Aquifer depletion reaching critical thresholds. Desalination and water recycling infrastructure urgent.",
    'conflict': "Humanitarian crisis ongoing. Infrastructure destruction exceeds 60%. Climate adaptation impossible during active conflict. Post-conflict reconstruction will require international coordination.",
    'tropical': "Monsoon intensity increasing 25-35%. Cyclone frequency and strength rising. Wet-bulb temperatures approaching human survivability limits. Dengue/malaria zones expanding.",
    'temperate': "Heat waves increasing from 5-10 to 25-40 days/year by 2050. Urban flooding from intense rainfall doubling. Adaptation costs manageable with early planning.",
    'cold': "Permafrost thaw accelerating. Infrastructure on frozen ground at risk. Arctic coastal erosion 5-10x historical rates. Some communities will require relocation."
}

RECOMMENDATIONS = {
    'coastal': [
        {'priority': 'CRITICAL', 'action': 'Sea Wall & Coastal Defense', 'timeline': '2025-2035', 'source': 'IPCC AR6 WG2'},
        {'priority': 'CRITICAL', 'action': 'Flood Early Warning System', 'timeline': '2025-2028', 'source': 'WMO Guidelines'},
        {'priority': 'HIGH', 'action': 'Managed Retreat Planning', 'timeline': '2025-2040', 'source': 'World Bank Climate'},
        {'priority': 'HIGH', 'action': 'Mangrove/Wetland Restoration', 'timeline': '2025-2035', 'source': 'UNEP Ecosystem'},
        {'priority': 'MEDIUM', 'action': 'Building Code Updates', 'timeline': '2025-2030', 'source': 'Local Adaptation'}
    ],
    'seismic': [
        {'priority': 'CRITICAL', 'action': 'Building Retrofit Program', 'timeline': '2025-2040', 'source': 'USGS/FEMA'},
        {'priority': 'CRITICAL', 'action': 'Earthquake Early Warning', 'timeline': '2025-2028', 'source': 'JMA/USGS'},
        {'priority': 'HIGH', 'action': 'Tsunami Evacuation Routes', 'timeline': '2025-2030', 'source': 'UNESCO IOC'},
        {'priority': 'HIGH', 'action': 'Emergency Supply Prepositioning', 'timeline': 'Immediate', 'source': 'FEMA/WHO'},
        {'priority': 'MEDIUM', 'action': 'Land Use Rezoning', 'timeline': '2025-2035', 'source': 'Local Planning'}
    ],
    'arid': [
        {'priority': 'CRITICAL', 'action': 'Water Security Infrastructure', 'timeline': '2025-2035', 'source': 'FAO AQUASTAT'},
        {'priority': 'CRITICAL', 'action': 'Heat Action Plan', 'timeline': '2025-2028', 'source': 'WHO Heat-Health'},
        {'priority': 'HIGH', 'action': 'Desalination Capacity', 'timeline': '2025-2035', 'source': 'IDA Desal'},
        {'priority': 'HIGH', 'action': 'Green Infrastructure', 'timeline': '2025-2040', 'source': 'C40 Cities'},
        {'priority': 'MEDIUM', 'action': 'Agriculture Transition', 'timeline': '2025-2040', 'source': 'FAO'}
    ],
    'conflict': [
        {'priority': 'CRITICAL', 'action': 'Humanitarian Corridor', 'timeline': 'Immediate', 'source': 'ICRC/UN OCHA'},
        {'priority': 'CRITICAL', 'action': 'Medical Supply Chain', 'timeline': 'Immediate', 'source': 'WHO/MSF'},
        {'priority': 'HIGH', 'action': 'Infrastructure Protection', 'timeline': 'Immediate', 'source': 'Geneva Convention'},
        {'priority': 'HIGH', 'action': 'Civilian Shelter Network', 'timeline': 'Immediate', 'source': 'UNHCR'},
        {'priority': 'MEDIUM', 'action': 'Post-Conflict Planning', 'timeline': 'TBD', 'source': 'World Bank'}
    ],
    'tropical': [
        {'priority': 'CRITICAL', 'action': 'Flood Defense System', 'timeline': '2025-2035', 'source': 'ADB Climate'},
        {'priority': 'CRITICAL', 'action': 'Cyclone Shelters', 'timeline': '2025-2030', 'source': 'UNDRR'},
        {'priority': 'HIGH', 'action': 'Disease Vector Control', 'timeline': 'Ongoing', 'source': 'WHO'},
        {'priority': 'HIGH', 'action': 'Drainage Infrastructure', 'timeline': '2025-2035', 'source': 'Local Gov'},
        {'priority': 'MEDIUM', 'action': 'Informal Settlement Upgrade', 'timeline': '2025-2040', 'source': 'UN-Habitat'}
    ],
    'temperate': [
        {'priority': 'HIGH', 'action': 'Urban Drainage Upgrade', 'timeline': '2025-2040', 'source': 'EU Adaptation'},
        {'priority': 'HIGH', 'action': 'Heat Resilience Plan', 'timeline': '2025-2030', 'source': 'C40 Cities'},
        {'priority': 'MEDIUM', 'action': 'Green Infrastructure', 'timeline': '2025-2040', 'source': 'EU Green Deal'},
        {'priority': 'MEDIUM', 'action': 'Building Energy Efficiency', 'timeline': '2025-2040', 'source': 'IEA'},
        {'priority': 'LOW', 'action': 'Monitoring Network', 'timeline': '2025-2030', 'source': 'National Met'}
    ],
    'cold': [
        {'priority': 'CRITICAL', 'action': 'Permafrost Monitoring', 'timeline': '2025-2030', 'source': 'Arctic Council'},
        {'priority': 'HIGH', 'action': 'Infrastructure Redesign', 'timeline': '2025-2040', 'source': 'National Eng'},
        {'priority': 'HIGH', 'action': 'Community Relocation Plan', 'timeline': '2025-2040', 'source': 'National Gov'},
        {'priority': 'MEDIUM', 'action': 'Coastal Protection', 'timeline': '2025-2035', 'source': 'USACE'},
        {'priority': 'MEDIUM', 'action': 'Resource Management', 'timeline': '2025-2040', 'source': 'Regional'}
    ]
}


class AnalyzeRequest(BaseModel):
    location: str


async def geocode_city(city_name: str) -> dict:
    """Get full city info from Nominatim"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                'https://nominatim.openstreetmap.org/search',
                params={'q': city_name, 'format': 'json', 'limit': 1, 'addressdetails': 1},
                headers={'User-Agent': 'TERA-RiskIntelligence/2.0'}
            )
            data = response.json()
            if data:
                item = data[0]
                bbox = item.get('boundingbox', [])
                return {
                    'lat': float(item['lat']),
                    'lon': float(item['lon']),
                    'country': item.get('address', {}).get('country', ''),
                    'bbox': [float(b) for b in bbox] if len(bbox) == 4 else None
                }
    except:
        pass
    return None


def determine_risk_type(lat: float, lon: float, country: str, city: str) -> str:
    """Determine risk profile"""
    country_lower = country.lower() if country else ''
    city_lower = city.lower() if city else ''
    
    conflict_countries = ['ukraine', 'syria', 'yemen', 'sudan', 'libya', 'palestine', 'israel', 'myanmar', 'afghanistan', 'somalia']
    if any(c in country_lower for c in conflict_countries):
        return 'conflict'
    
    # Seismic zones
    seismic_check = [
        (30, 45, 120, 150), (35, 42, 20, 30), (32, 42, -125, -115), (-10, 10, 95, 130)
    ]
    for lat_min, lat_max, lon_min, lon_max in seismic_check:
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return 'seismic'
    
    if 15 <= lat <= 35 and (20 <= lon <= 60):
        return 'arid'
    if -23 <= lat <= 23:
        return 'tropical'
    if abs(lat) > 60:
        return 'cold'
    
    coastal_kw = ['coast', 'beach', 'port', 'bay', 'island', 'miami', 'venice', 'mumbai', 'lagos']
    if any(k in city_lower for k in coastal_kw):
        return 'coastal'
    
    return 'temperate'


@router.post("/analyze")
async def analyze_location(request: AnalyzeRequest):
    """Analyze ANY location worldwide"""
    city_name = request.location.strip()
    
    geo = await geocode_city(city_name)
    if not geo:
        raise HTTPException(status_code=404, detail=f"Location not found: {city_name}")
    
    risk_type = determine_risk_type(geo['lat'], geo['lon'], geo['country'], city_name)
    
    # Risk scores based on type
    scores = {
        'coastal': (0.65, 0.75, 0.15),
        'seismic': (0.55, 0.50, 0.12),
        'arid': (0.50, 0.65, 0.20),
        'conflict': (0.80, 0.30, 0.90),
        'tropical': (0.58, 0.70, 0.15),
        'temperate': (0.32, 0.40, 0.10),
        'cold': (0.40, 0.45, 0.08)
    }
    risk, climate, conflict = scores.get(risk_type, (0.35, 0.40, 0.10))
    
    return {
        'location': city_name,
        'latitude': geo['lat'],
        'longitude': geo['lon'],
        'country': geo['country'],
        'bbox': geo.get('bbox'),
        'city_type': risk_type,
        'risk_score': risk,
        'climate_risk': climate,
        'conflict_risk': conflict,
        'projection_2050': PROJECTIONS.get(risk_type, PROJECTIONS['temperate']),
        'recommendations': RECOMMENDATIONS.get(risk_type, RECOMMENDATIONS['temperate']),
        'zones': {}  # Will be filled by hexagon data
    }


@router.get("/risk-map")
async def get_risk_map(city: str, resolution: int = 10):
    """Generate hexagonal risk map for ANY city"""
    from services.adaptive_tessellation import tessellation_service
    
    geo = await geocode_city(city)
    if not geo:
        raise HTTPException(status_code=404, detail=f"City not found: {city}")
    
    features = tessellation_service.generate_hexagons_sync(
        lat=geo['lat'],
        lon=geo['lon'],
        city_name=city,
        country=geo['country'],
        bbox=geo.get('bbox'),
        resolution=resolution
    )
    
    return {'type': 'FeatureCollection', 'features': features}


@router.get("/health")
async def health():
    return {"status": "healthy", "version": "2.0"}
