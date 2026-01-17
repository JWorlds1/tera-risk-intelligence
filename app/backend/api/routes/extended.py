from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger
import io

router = APIRouter(prefix='/api/extended', tags=['Extended'])

@router.get('/temporal')
async def temporal_projection(city: str, year: int = 2026, scenario: str = 'SSP2-4.5'):
    from services.geocoding import geocode_city
    from services.realtime_intelligence import realtime_service
    
    geo = await geocode_city(city)
    if not geo:
        raise HTTPException(status_code=404, detail=f'City not found: {city}')
    
    lat, lon = geo['lat'], geo['lon']
    country = geo['country']
    
    climate_risk = await realtime_service.get_climate_risk(lat, lon, year, scenario)
    seismic_risk = await realtime_service.get_seismic_risk(lat, lon, year)
    conflict_risk = await realtime_service.get_conflict_risk(lat, lon, country, year)
    
    total = climate_risk.value * 0.5 + conflict_risk.value * 0.3 + seismic_risk.value * 0.2
    
    return {
        'status': 'success',
        'city': city,
        'country': country,
        'year': year,
        'scenario': scenario,
        'risks': {
            'total': round(total, 3),
            'climate': {'value': round(climate_risk.value, 3), 'uncertainty': round(climate_risk.uncertainty, 3)},
            'conflict': {'value': round(conflict_risk.value, 3), 'uncertainty': round(conflict_risk.uncertainty, 3)},
            'seismic': {'value': round(seismic_risk.value, 3), 'uncertainty': round(seismic_risk.uncertainty, 3)}
        }
    }

@router.get('/ocean')
async def get_ocean_data(lat: float, lon: float):
    try:
        from services.noaa_ocean_service import noaa_service
        from services.copernicus_marine_service import copernicus_marine
        
        ocean_risk = await noaa_service.get_ocean_risk(lat, lon)
        marine_risk = await copernicus_marine.get_marine_risk(lat, lon)
        
        return {'status': 'success', 'ocean_risk': ocean_risk, 'marine_risk': marine_risk}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@router.get('/conflict')
async def get_conflict_data(lat: float, lon: float, country: str):
    try:
        from services.gdelt_service import gdelt_service
        intensity = await gdelt_service.get_conflict_intensity(lat, lon, country)
        return {'status': 'success', 'conflict': intensity}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@router.get('/export-pdf')
async def export_pdf(city: str, year: int = 2026, scenario: str = 'SSP2-4.5'):
    from services.geocoding import geocode_city
    from services.realtime_intelligence import realtime_service
    from services.pdf_export_service import pdf_service
    
    geo = await geocode_city(city)
    if not geo:
        raise HTTPException(status_code=404, detail=f'City not found: {city}')
    
    lat, lon = geo['lat'], geo['lon']
    country = geo['country']
    
    climate_risk = await realtime_service.get_climate_risk(lat, lon, year, scenario)
    seismic_risk = await realtime_service.get_seismic_risk(lat, lon, year)
    conflict_risk = await realtime_service.get_conflict_risk(lat, lon, country, year)
    
    total = climate_risk.value * 0.5 + conflict_risk.value * 0.3 + seismic_risk.value * 0.2
    
    analysis_data = {
        'total_risk': {'mean': total},
        'climate_risk': {'mean': climate_risk.value},
        'conflict_risk': {'mean': conflict_risk.value},
        'seismic_risk': {'mean': seismic_risk.value},
        'scenarios': {},
        'recommendations': []
    }
    
    try:
        pdf_bytes = await pdf_service.generate_report(city, country, analysis_data, year, scenario)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type='application/pdf',
            headers={'Content-Disposition': f'attachment; filename=TERA_{city}_{year}.pdf'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'PDF error: {str(e)}')
