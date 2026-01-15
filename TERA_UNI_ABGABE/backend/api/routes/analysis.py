"""
TERA Analysis API - REAL DATA 2026 Edition
Echte USGS, IPCC AR6, Firecrawl Integration
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict
import httpx
import sys
sys.path.insert(0, '/data/tera/backend')

# Real Data Engines
from services.real_risk_engine import get_engine
from services.firecrawl_service import FireCrawlService
from global_land_mask import globe
from services.realtime_intelligence import realtime_service
from services.llm_precision_engine import precision_engine
# Enhanced Risk Engine mit Datenfusion
try:
    from services.enhanced_risk_engine import enhanced_risk_engine
except ImportError:
    enhanced_risk_engine = None


router = APIRouter()

# Firecrawl für Echtzeit-News
firecrawl = FireCrawlService()

# ============================================================
# IPCC AR6 SSP2-4.5 PROJECTIONS FOR 2026
# ============================================================
PROJECTIONS_2026 = {
    'coastal': """📊 IPCC AR6 SSP2-4.5 Projektion 2026:
• Meeresspiegel: +4-6mm über 2024 (Trend: 3.7mm/Jahr)
• Sturmflutrisiko: +15-20% durch wärmere Ozeane
• Korallenbleiche: 50% der Riffe gefährdet
Datenquelle: IPCC AR6 WG1 Chapter 9, NASA GSFC""",
    
    'seismic': """📊 USGS Seismische Prognose 2026:
• 30-Jahres-Wahrscheinlichkeit M7+: Berechnet aus historischen Daten
• Aftershock-Sequenzen: Basiert auf Omori-Utsu Modell
• Tsunami-Risiko: Bei M>7.5 in Subduktionszonen
Datenquelle: USGS Earthquake Catalog (Echtzeit)""",

    'arid': """📊 ERA5/IPCC Dürre-Projektion 2026:
• Temperaturanomalie: +0.3-0.5°C über 1991-2020 Mittel
• Extreme Hitzetage (>40°C): +5-10 Tage/Jahr
• Wasserstress-Index: Kritisch bei <500m³/Kopf/Jahr
Datenquelle: ERA5 Reanalyse, IPCC AR6 WG2""",

    'conflict': """📊 ACLED/GDELT Konflikt-Analyse 2026:
• Ereignisdichte: Basiert auf letzten 90 Tagen
• Eskalationstrend: ML-Vorhersage aus historischen Mustern
• Humanitäre Lage: OCHA/ReliefWeb Echtzeit-Indikatoren
Datenquelle: ACLED, GDELT, UN OCHA""",

    'tropical': """📊 Tropische Prognose 2026:
• Zyklon-Intensität: +5-10% Windgeschwindigkeit (SST-Trend)
• Monsun-Variabilität: Erhöht durch IOD/ENSO
• Überschwemmungsrisiko: +25% in Deltaregionen
Datenquelle: NOAA NHC, JMA, ERA5""",

    'temperate': """📊 Gemäßigte Zone 2026:
• Hitzewellen: 15-25 Tage/Jahr (vs. 5-10 historisch)
• Starkregenereignisse: +20% Intensität
• Urban Heat Island: +2-4°C in Innenstädten
Datenquelle: ERA5, Copernicus C3S""",

    'cold': """📊 Arktis/Subarktis 2026:
• Permafrost-Taupunkt: -50cm Tiefe in Risikogebieten
• Küstenerosion: 2-5m/Jahr an exponierten Küsten
• Eistage: -15-20 Tage vs. 1990er
Datenquelle: NSIDC, Copernicus ADS"""
}

RECOMMENDATIONS = {
    'coastal': [
        {'priority': 'CRITICAL', 'action': 'Hochwasserschutz-Audit', 'timeline': 'Q1 2026', 'source': 'IPCC AR6 WG2'},
        {'priority': 'CRITICAL', 'action': 'Frühwarnsystem aktivieren', 'timeline': 'Q2 2026', 'source': 'WMO'},
        {'priority': 'HIGH', 'action': 'Evakuierungsrouten prüfen', 'timeline': 'Q1 2026', 'source': 'UNDRR'}
    ],
    'seismic': [
        {'priority': 'CRITICAL', 'action': 'Gebäude-Retrofit', 'timeline': '2025-2030', 'source': 'USGS/FEMA'},
        {'priority': 'CRITICAL', 'action': 'Erdbeben-Frühwarnung', 'timeline': 'Q1 2026', 'source': 'USGS ShakeAlert'},
        {'priority': 'HIGH', 'action': 'Notfall-Kit vorbereiten', 'timeline': 'Sofort', 'source': 'FEMA Ready.gov'}
    ],
    'arid': [
        {'priority': 'CRITICAL', 'action': 'Wasserspeicher ausbauen', 'timeline': '2026', 'source': 'FAO'},
        {'priority': 'CRITICAL', 'action': 'Hitzeaktionsplan', 'timeline': 'Q2 2026', 'source': 'WHO'},
        {'priority': 'HIGH', 'action': 'Bewässerung optimieren', 'timeline': '2026', 'source': 'IWMI'}
    ],
    'conflict': [
        {'priority': 'CRITICAL', 'action': 'Humanitärer Korridor', 'timeline': 'Sofort', 'source': 'ICRC'},
        {'priority': 'CRITICAL', 'action': 'Medizinische Versorgung', 'timeline': 'Sofort', 'source': 'MSF'},
        {'priority': 'HIGH', 'action': 'Ziviler Schutzraum', 'timeline': 'Sofort', 'source': 'UNHCR'}
    ],
    'tropical': [
        {'priority': 'CRITICAL', 'action': 'Zyklon-Schutzräume', 'timeline': 'Q1 2026', 'source': 'UNDRR'},
        {'priority': 'HIGH', 'action': 'Drainage-System', 'timeline': '2026', 'source': 'World Bank'},
        {'priority': 'HIGH', 'action': 'Krankheitsüberwachung', 'timeline': 'Laufend', 'source': 'WHO'}
    ],
    'temperate': [
        {'priority': 'HIGH', 'action': 'Stadtbegrünung', 'timeline': '2026-2030', 'source': 'C40 Cities'},
        {'priority': 'HIGH', 'action': 'Hitzeschutzplan', 'timeline': 'Q2 2026', 'source': 'EU Adaptation'},
        {'priority': 'MEDIUM', 'action': 'Regenwasser-Management', 'timeline': '2026-2028', 'source': 'Local'}
    ],
    'cold': [
        {'priority': 'CRITICAL', 'action': 'Permafrost-Monitoring', 'timeline': '2026', 'source': 'Arctic Council'},
        {'priority': 'HIGH', 'action': 'Infrastruktur-Anpassung', 'timeline': '2026-2030', 'source': 'National'},
        {'priority': 'HIGH', 'action': 'Küstenschutz', 'timeline': '2026-2028', 'source': 'USACE'}
    ]
}


class AnalyzeRequest(BaseModel):
    location: str


async def geocode_city(city_name: str) -> dict:
    """Geokodierung mit Nominatim"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                'https://nominatim.openstreetmap.org/search',
                params={'q': city_name, 'format': 'json', 'limit': 1, 'addressdetails': 1},
                headers={'User-Agent': 'TERA-RiskIntelligence/2.3'}
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
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None


def estimate_elevation_coast(lat: float, lon: float) -> tuple:
    """Schätzt Höhe und Küstenabstand"""
    is_ocean = globe.is_ocean(lat, lon)
    if is_ocean:
        return 0, 0
    
    coast_dist = 100
    for r in [0.05, 0.1, 0.2, 0.5, 1.0]:
        for dlat, dlon in [(r,0), (-r,0), (0,r), (0,-r)]:
            try:
                if globe.is_ocean(lat + dlat, lon + dlon):
                    coast_dist = r * 111
                    break
            except:
                pass
        if coast_dist < 100:
            break
    
    elevation = 50
    if coast_dist < 5:
        elevation = 5
    elif coast_dist < 20:
        elevation = 20
    
    return elevation, coast_dist


def determine_risk_type(lat: float, lon: float, country: str, city: str) -> str:
    """Bestimmt Risikoprofil basierend auf Geo + Land"""
    country_lower = country.lower() if country else ''
    city_lower = city.lower() if city else ''
    
    # Konfliktgebiete (Namen in verschiedenen Sprachen + Koordinaten)
    conflict_keywords = ['ukraine', 'syria', 'سوريا', 'yemen', 'اليمن', 'sudan', 'سودان', 
                        'libya', 'ليبيا', 'palestine', 'فلسطين', 'israel', 'myanmar', 
                        'afghanistan', 'أفغانستان', 'somalia', 'الصومال', 'ethiopia', 'mali', 'niger',
                        'gaza', 'west bank', 'donbas', 'kharkiv', 'mariupol']
    if any(k in country_lower or k in city_lower for k in conflict_keywords):
        return 'conflict'
    
    # Koordinaten-basierte Konflikterkennung (2024/2025 Hotspots)
    conflict_zones = [
        (32, 38, 35, 42),   # Syrien
        (44, 52, 22, 40),   # Ukraine
        (12, 18, 42, 55),   # Jemen
        (8, 23, 21, 38),    # Sudan
        (25, 34, 10, 25),   # Libyen
        (31, 33, 34, 36),   # Gaza/Israel
        (0, 12, 35, 48),    # Somalia/Äthiopien
    ]
    for lat_min, lat_max, lon_min, lon_max in conflict_zones:
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return 'conflict'
    
    # Seismische Zonen
    seismic_check = [
        (30, 45, 120, 150),  # Japan
        (35, 42, 20, 30),    # Griechenland/Türkei
        (32, 42, -125, -115), # Kalifornien
        (-10, 10, 95, 130),  # Indonesien
        (28, 35, 75, 90),    # Nepal/Himalaya
        (-40, -30, -75, -70) # Chile
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
    
    coastal_kw = ['coast', 'beach', 'port', 'bay', 'island', 'miami', 'venice', 'mumbai', 'lagos', 'new york', 'shanghai', 'jakarta', 'dhaka']
    if any(k in city_lower for k in coastal_kw):
        return 'coastal'
    
    return 'temperate'


@router.post("/analyze")
@router.get("/analyze")
async def analyze_location(location: Optional[str] = None, request: Optional[AnalyzeRequest] = None):
    """
    Analysiert JEDEN Standort weltweit mit ECHTEN Daten
    
    Datenquellen:
    - USGS Earthquake Catalog (seismisches Risiko)
    - IPCC AR6 SSP2-4.5 (Klimaprojektionen)
    - ERA5 Climatology (Temperatur/Niederschlag)
    - Global Land Mask (Topografie)
    - Firecrawl (Echtzeit-News)
    """
    city_name = location or (request.location if request else None)
    if not city_name:
        raise HTTPException(status_code=400, detail="Location required")
    
    city_name = city_name.strip()
    geo = await geocode_city(city_name)
    if not geo:
        raise HTTPException(status_code=404, detail=f"Location not found: {city_name}")
    
    risk_type = determine_risk_type(geo['lat'], geo['lon'], geo['country'], city_name)
    elevation, coast_dist = estimate_elevation_coast(geo['lat'], geo['lon'])
    
    # ============================================================
    # ECHTE RISIKO-BERECHNUNG MIT USGS/IPCC
    # ============================================================
    try:
        engine = get_engine()
        assessment = await engine.assess_location(
            location=city_name,
            lat=geo['lat'],
            lon=geo['lon'],
            elevation_m=elevation,
            coast_dist_km=coast_dist,
            country=geo['country']
        )
        
        # Echte Werte aus RealRiskEngine
        risk_score = assessment.total_score
        climate_risk = assessment.climate_score
        conflict_risk = assessment.conflict_score
        projection_2026 = engine._format_projection(assessment)
        data_sources = assessment.data_sources
        
    except Exception as e:
        print(f"RealRiskEngine error (fallback): {e}")
        # Fallback auf statische Scores
        scores = {
            'coastal': (0.65, 0.75, 0.15),
            'seismic': (0.55, 0.50, 0.12),
            'arid': (0.50, 0.65, 0.20),
            'conflict': (0.80, 0.30, 0.90),
            'tropical': (0.58, 0.70, 0.15),
            'temperate': (0.32, 0.40, 0.10),
            'cold': (0.40, 0.45, 0.08)
        }
        risk_score, climate_risk, conflict_risk = scores.get(risk_type, (0.35, 0.40, 0.10))
        projection_2026 = PROJECTIONS_2026.get(risk_type, PROJECTIONS_2026['temperate'])
        data_sources = ['Fallback (statisch)']
    
    # ============================================================
    # REALTIME INTELLIGENCE (Firecrawl + Ollama LLM)
    # ============================================================
    realtime_data = {}
    try:
        realtime_data = await realtime_service.get_realtime_context(
            location=city_name,
            country=geo['country'],
            risk_type=risk_type,
            lat=geo['lat'],
            lon=geo['lon']
        )
        # Risiko-Anpassung basierend auf Echtzeit-Daten
        if realtime_data.get('risk_adjustment'):
            adjustment = float(realtime_data.get('risk_adjustment', 0))
            risk_score = min(1.0, max(0.0, risk_score + adjustment))
    except Exception as e:
        print(f"Realtime Intelligence error: {e}")
        realtime_data = {
            'realtime_assessment': 'Echtzeit-Analyse nicht verfügbar',
            'trend': 'unbekannt',
            'risk_adjustment': 0,
            'sources': [],
            'llm_model': 'unavailable'
        }
    
    # ============================================================
    # LLM PRECISION FORECAST
    # ============================================================
    precision_forecast = {}
    try:
        precision_forecast = await precision_engine.generate_precision_forecast(
            location=city_name,
            country=geo['country'],
            lat=geo['lat'],
            lon=geo['lon'],
            risk_type=risk_type,
            current_data={
                'conflict_risk': conflict_risk,
                'realtime_risk_adjustment': realtime_data.get('risk_adjustment', 0)
            }
        )
    except Exception as e:
        print(f"Precision Engine error: {e}")
        precision_forecast = {'error': str(e)}
    
    return {
        'location': city_name,
        'latitude': geo['lat'],
        'longitude': geo['lon'],
        'country': geo['country'],
        'bbox': geo.get('bbox'),
        'city_type': risk_type,
        
        # ECHTE Risiko-Scores
        'risk_score': round(risk_score, 3),
        'climate_risk': round(climate_risk, 3),
        'conflict_risk': round(conflict_risk, 3),
        
        # 2026 Projektion
        'projection_2026': projection_2026,
        
        # Empfehlungen
        'recommendations': RECOMMENDATIONS.get(risk_type, RECOMMENDATIONS['temperate']),
        
        # Transparenz
        'data_sources': data_sources,
        'methodology': 'IPCC AR6 SSP2-4.5 + USGS + ERA5',
        'forecast_year': 2026,
        
        # Realtime Intelligence
        'realtime_intelligence': realtime_data,
        
        # LLM Precision Forecast
        'precision_forecast': precision_forecast,
        
        # Zonen (werden durch Hexagon-Daten gefüllt)
        'zones': {}
    }


@router.get("/risk-map")
async def get_risk_map(city: str = Query(...), resolution: int = 8):
    """Hexagon-Risikokarte für JEDE Stadt"""
    from services.real_data_tessellation import EchteDatenTessellation
    
    geo = await geocode_city(city)
    if not geo:
        raise HTTPException(status_code=404, detail=f"City not found: {city}")
    
    risk_type = determine_risk_type(geo['lat'], geo['lon'], geo['country'], city)
    
    # Schnelle Tessellation ohne LLM (LLM nur für /analyze)
    tessellation = EchteDatenTessellation()
    features = await tessellation.generiere_risikokarte(
        lat=geo['lat'],
        lon=geo['lon'],
        stadt_typ=risk_type,
        aufloesung=resolution,
        radius_km=15.0
    )
    
    return {'type': 'FeatureCollection', 'features': features}


@router.get("/health")
async def health():
    return {
        "status": "healthy", 
        "version": "2.3.0-real-data",
        "data_sources": ["USGS", "IPCC AR6", "ERA5", "Firecrawl"],
        "forecast_year": 2026
    }


# ============================================================
# PHASE 1: PROFESSIONAL ANALYSIS ENDPOINT
# ============================================================

@router.get("/professional")
async def professional_analysis(city: str = Query(..., description="Stadt fuer professionelle Analyse")):
    from services.professional_analysis import professional_engine
    
    # Nutze existierende Geocoding-Funktion
    geo = await geocode_city(city)
    if not geo:
        raise HTTPException(status_code=404, detail=f"Stadt nicht gefunden: {city}")
    
    lat = geo["lat"]
    lon = geo["lon"]
    country = geo.get("country", "Unknown")
    location_type = determine_risk_type(lat, lon, country, city)
    
    # Professionelle Analyse durchfuehren
    result = await professional_engine.analyze_professional(
        city=city,
        country=country,
        lat=lat,
        lon=lon,
        location_type=location_type
    )
    
    return {
        "status": "success",
        "city": city,
        "analysis": {
            "location": result.location,
            "timestamp": result.timestamp.isoformat(),
            "total_risk": result.total_risk.to_dict(),
            "climate_risk": result.climate_risk.to_dict(),
            "conflict_risk": result.conflict_risk.to_dict(),
            "seismic_risk": result.seismic_risk.to_dict(),
            "web_intelligence": result.web_intelligence,
            "scenarios": result.scenarios,
            "recommendations": result.recommendations,
            "sources": [s for s in result.sources if s]
        }
    }
