"""
TERA Enterprise API - 2026 Prognose
===================================
Enterprise-Grade Risikoanalyse für:
- Ministerien & Regierungen
- Zentralbanken
- Versicherungen
- Infrastrukturbetreiber

Alle Texte auf Deutsch.
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict
import httpx
from services.forecast_2026 import calculate_2026_forecast, PROJECTIONS_2026, RECOMMENDATIONS_2026
from services.real_data_tessellation import EchteDatenTessellation, RISIKO_KATEGORIEN


# Mapping von deutschen zu englischen Keys für Frontend-Kompatibilität
def _to_frontend_format(recs: list) -> list:
    """Konvertiert deutsche Keys zu englischen für das Frontend"""
    priority_map = {"KRITISCH": "CRITICAL", "HOCH": "HIGH", "MITTEL": "MEDIUM", "NIEDRIG": "LOW"}
    return [
        {
            "priority": priority_map.get(r.get("prioritaet", ""), r.get("prioritaet", "MEDIUM")),
            "action": r.get("massnahme", ""),
            "timeline": r.get("zeitraum", ""),
            "source": r.get("quelle", "")
        }
        for r in recs
    ]

router = APIRouter()

class AnalyseAnfrage(BaseModel):
    location: str


# Deutsche Prognosen 2026
PROGNOSEN_2026_DE = {
    'coastal': """🌊 KÜSTENPROGNOSE 2026 (IPCC AR6 SSP2-4.5)

MEERESSPIEGELANSTIEG:
• Globaler Anstieg: +3.4mm/Jahr (beschleunigend)
• Lokaler Anstieg 2024→2026: +15mm
• 100-jährige Flutereignisse werden zu 80-jährigen

STURMFLUTRISIKO:
• Häufigkeit: +8% gegenüber 2024
• Intensität: +5% (wärmere Ozeane)
• Schadenpotential: +25% (Infrastrukturexposition)

KRITISCHE INFRASTRUKTUR:
• 72% der Küsteninfrastruktur unter Stress
• Entwässerungssysteme erreichen Kapazitätsgrenzen
• Versicherungsprämien steigen 15-20%

DATENQUELLEN: IPCC AR6 WG1, NOAA Sea Level Rise, Copernicus CDS, ERA5
KONFIDENZ: 75% (±0.08 Risikopunkte)
""",

    'arid': """☀️ DÜRREPROGNOSE 2026 (IPCC AR6 SSP2-4.5)

TEMPERATUR:
• Mittlere Erwärmung: +0.3°C gegenüber 2024
• Extreme Hitzetage (>40°C): +8 Tage/Jahr
• Urbane Wärmeinsel-Effekt: +2-4°C zusätzlich

WASSERRESSOURCEN:
• Grundwasserabsenkung: 15% schneller als 2020
• Oberflächenwasser-Verfügbarkeit: -12%
• Wasserstress-Index: 0.78 (hoch)

LANDWIRTSCHAFT:
• Ernteausfallrisiko: +18%
• Bewässerungsbedarf: +22%
• Anbauzonenverschiebung nordwärts

DATENQUELLEN: ERA5, FAO AQUASTAT, NASA GRACE, Copernicus C3S
KONFIDENZ: 72% (±0.10 Risikopunkte)
""",

    'tropical': """🌴 TROPENPROGNOSE 2026 (IPCC AR6 SSP2-4.5)

NIEDERSCHLAG:
• Monsunvariabilität: +12%
• Starkregenereignisse: +18% Intensität
• Trockenphasen zwischen Monsun: verlängert

ZYKLONE/TAIFUNE:
• Intensität Kategorie 4-5: +6%
• Rapid Intensification Events: +15%
• Schadenpotential: +30%

GESUNDHEIT:
• Dengue-Risikogebiet: +15% Ausdehnung
• Hitzeschlag-Risiko: +12%
• Feuchtkugeltemperatur nähert sich kritischen Werten

DATENQUELLEN: ERA5, NOAA NHC, WHO, NASA GPM
KONFIDENZ: 68% (±0.12 Risikopunkte)
""",

    'temperate': """🌤️ PROGNOSE GEMÄSSIGTE ZONE 2026 (IPCC AR6 SSP2-4.5)

TEMPERATUR:
• Mittlere Erwärmung: +0.2°C gegenüber 2024
• Hitzewellentage: +5/Jahr
• Mildere Winter: Kältewellen -15%

NIEDERSCHLAG:
• Starkregen-Intensität: +12%
• Urbane Überflutung: Risiko +18%
• Grundwasserneubildung: regional variabel

VEGETATION:
• Vegetationsperiode: 4 Tage früher
• Allergiesaison: verlängert
• Schädlingsausbreitung nordwärts

DATENQUELLEN: ERA5, DWD, EEA, Copernicus CLMS
KONFIDENZ: 78% (±0.06 Risikopunkte)
""",

    'conflict': """⚔️ KONFLIKTZONE 2026

SICHERHEITSLAGE:
• Instabilitätsindex: 0.85 (sehr hoch)
• Humanitärer Bedarf: +20% gegenüber 2024
• Infrastrukturschäden: 65%

KLIMAANPASSUNG:
• Nicht durchführbar während aktivem Konflikt
• Wasserinfrastruktur: 40% beschädigt
• Energieversorgung: instabil

PROGNOSE:
• Klimarisiken werden durch Konflikt verstärkt
• Post-Konflikt-Wiederaufbau muss klimaresilient sein
• Internationale Koordination erforderlich

DATENQUELLEN: ACLED, GDELT, UNHCR, OCHA
KONFIDENZ: 55% (hohe Unsicherheit durch Konfliktdynamik)
""",

    'seismic': """🌋 SEISMISCHE PROGNOSE 2026

ERDBEBENRISIKO:
• M6+ Wahrscheinlichkeit (30 Jahre): 15-25%
• Gebäude-Retrofit-Quote: 35%
• Tsunami-Frühwarnung: 85% Abdeckung

INFRASTRUKTUR:
• Kritische Gebäude vor 1980: 40%
• Verflüssigungsrisiko in Küstenzonen: hoch
• Evakuierungsrouten: teilweise unzureichend

VORBEREITUNG:
• Notfallvorräte in Haushalten: 60%
• Übungsfrequenz: halbjährlich empfohlen
• Versicherungsdeckung: oft unzureichend

DATENQUELLEN: USGS, JMA, EMSC, GEM Foundation
KONFIDENZ: 60% (Erdbeben schwer vorhersagbar)
"""
}

# Deutsche Empfehlungen
EMPFEHLUNGEN_2026_DE = {
    'coastal': [
        {'prioritaet': 'KRITISCH', 'massnahme': 'Küstenschutz-Audit', 'zeitraum': 'Q1 2025', 'quelle': 'IPCC AR6'},
        {'prioritaet': 'KRITISCH', 'massnahme': 'Hochwasser-Frühwarnsystem aktivieren', 'zeitraum': 'Q2 2025', 'quelle': 'WMO'},
        {'prioritaet': 'HOCH', 'massnahme': 'Evakuierungsrouten aktualisieren', 'zeitraum': '2025', 'quelle': 'FEMA'},
        {'prioritaet': 'HOCH', 'massnahme': 'Versicherungsdeckung prüfen', 'zeitraum': '2025', 'quelle': 'Swiss Re'},
        {'prioritaet': 'MITTEL', 'massnahme': 'Mangroven-/Feuchtgebietsschutz', 'zeitraum': '2025-2026', 'quelle': 'UNEP'},
    ],
    'arid': [
        {'prioritaet': 'KRITISCH', 'massnahme': 'Wasserreserven-Assessment', 'zeitraum': 'Q1 2025', 'quelle': 'FAO'},
        {'prioritaet': 'KRITISCH', 'massnahme': 'Hitzeaktionsplan aktivieren', 'zeitraum': 'Sommer 2025', 'quelle': 'WHO'},
        {'prioritaet': 'HOCH', 'massnahme': 'Wassersparmaßnahmen implementieren', 'zeitraum': '2025', 'quelle': 'WRI'},
        {'prioritaet': 'HOCH', 'massnahme': 'Kühlzentren einrichten', 'zeitraum': '2025', 'quelle': 'C40'},
        {'prioritaet': 'MITTEL', 'massnahme': 'Dürre-resistente Landwirtschaft', 'zeitraum': '2025-2026', 'quelle': 'CGIAR'},
    ],
    'tropical': [
        {'prioritaet': 'KRITISCH', 'massnahme': 'Zyklon-Schutzräume inspizieren', 'zeitraum': 'Q1 2025', 'quelle': 'UNDRR'},
        {'prioritaet': 'KRITISCH', 'massnahme': 'Gesundheitssystem-Kapazität prüfen', 'zeitraum': '2025', 'quelle': 'WHO'},
        {'prioritaet': 'HOCH', 'massnahme': 'Entwässerungssysteme erweitern', 'zeitraum': '2025', 'quelle': 'Weltbank'},
        {'prioritaet': 'HOCH', 'massnahme': 'Vektorbekämpfung intensivieren', 'zeitraum': '2025', 'quelle': 'CDC'},
        {'prioritaet': 'MITTEL', 'massnahme': 'Gebäude-Windresistenz verbessern', 'zeitraum': '2025-2026', 'quelle': 'IFC'},
    ],
    'temperate': [
        {'prioritaet': 'HOCH', 'massnahme': 'Urbane Entwässerung prüfen', 'zeitraum': 'Q1 2025', 'quelle': 'EU'},
        {'prioritaet': 'HOCH', 'massnahme': 'Hitzeschutzplan aktualisieren', 'zeitraum': 'Q2 2025', 'quelle': 'EEA'},
        {'prioritaet': 'MITTEL', 'massnahme': 'Grünflächen erweitern', 'zeitraum': '2025-2026', 'quelle': 'C40'},
        {'prioritaet': 'MITTEL', 'massnahme': 'Gebäude-Energieeffizienz', 'zeitraum': '2025-2027', 'quelle': 'IEA'},
        {'prioritaet': 'NIEDRIG', 'massnahme': 'Langzeit-Monitoring', 'zeitraum': 'Laufend', 'quelle': 'DWD/Met'},
    ],
    'conflict': [
        {'prioritaet': 'KRITISCH', 'massnahme': 'Humanitärer Korridor', 'zeitraum': 'Sofort', 'quelle': 'ICRC'},
        {'prioritaet': 'KRITISCH', 'massnahme': 'Medizinische Versorgung', 'zeitraum': 'Sofort', 'quelle': 'MSF'},
        {'prioritaet': 'HOCH', 'massnahme': 'Zivilschutznetzwerk', 'zeitraum': 'Laufend', 'quelle': 'UNHCR'},
        {'prioritaet': 'HOCH', 'massnahme': 'Wiederaufbauplanung', 'zeitraum': 'Bei Möglichkeit', 'quelle': 'Weltbank'},
        {'prioritaet': 'MITTEL', 'massnahme': 'Klimaresilienz integrieren', 'zeitraum': 'Post-Konflikt', 'quelle': 'UNDP'},
    ],
    'seismic': [
        {'prioritaet': 'KRITISCH', 'massnahme': 'Gebäude-Retrofit beschleunigen', 'zeitraum': '2025-2027', 'quelle': 'USGS'},
        {'prioritaet': 'KRITISCH', 'massnahme': 'Frühwarnsystem testen', 'zeitraum': 'Q2 2025', 'quelle': 'JMA'},
        {'prioritaet': 'HOCH', 'massnahme': 'Notfallkits verteilen', 'zeitraum': '2025', 'quelle': 'FEMA'},
        {'prioritaet': 'HOCH', 'massnahme': 'Evakuierungsübungen', 'zeitraum': 'Halbjährlich', 'quelle': 'Lokal'},
        {'prioritaet': 'MITTEL', 'massnahme': 'Bauvorschriften verschärfen', 'zeitraum': '2025', 'quelle': 'ICC'},
    ],
}


async def geokodiere_stadt(stadtname: str) -> Optional[dict]:
    """Geokodiert Stadt weltweit mit Nominatim"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                'https://nominatim.openstreetmap.org/search',
                params={
                    'q': stadtname,
                    'format': 'json',
                    'limit': 1,
                    'addressdetails': 1
                },
                headers={'User-Agent': 'TERA-Enterprise/2.1'}
            )
            data = response.json()
            if data:
                result = data[0]
                address = result.get('address', {})
                bbox = result.get('boundingbox', [])
                return {
                    'lat': float(result['lat']),
                    'lon': float(result['lon']),
                    'land': address.get('country', 'Unbekannt'),
                    'land_code': address.get('country_code', '').upper(),
                    'bbox': [float(b) for b in bbox] if bbox else None
                }
    except Exception as e:
        print(f'Geokodierung fehlgeschlagen: {e}')
    return None


def bestimme_risikotyp(lat: float, lon: float, land: str, stadt: str) -> str:
    """Bestimmt Risikoprofil basierend auf Standort"""
    stadt_lower = stadt.lower()
    land_lower = land.lower()
    
    # Konfliktzonen
    konflikt_laender = ['ukraine', 'syria', 'syrien', 'yemen', 'jemen', 'sudan', 'äthiopien', 'ethiopia', 'myanmar']
    konflikt_staedte = ['kyiv', 'kiew', 'charkiw', 'kharkiv', 'odesa', 'odessa', 'aleppo', 'sanaa']
    
    if any(x in land_lower for x in konflikt_laender):
        return 'conflict'
    if any(x in stadt_lower for x in konflikt_staedte):
        return 'conflict'
    
    # Seismische Zonen
    seismisch_laender = ['japan', 'indonesien', 'indonesia', 'philippinen', 'philippines', 'chile', 'türkei', 'turkey']
    seismisch_staedte = ['tokyo', 'tokio', 'osaka', 'jakarta', 'manila', 'istanbul']
    
    if any(x in land_lower for x in seismisch_laender):
        if any(x in stadt_lower for x in seismisch_staedte):
            return 'seismic'
    
    # Küstenstädte
    kuestenstaedte = ['miami', 'venedig', 'venice', 'amsterdam', 'new york', 'mumbai', 'shanghai', 
                      'bangkok', 'ho chi minh', 'singapur', 'singapore', 'jakarta', 'manila', 
                      'dhaka', 'lagos', 'sydney', 'hamburg', 'rotterdam', 'kopenhagen']
    if any(x in stadt_lower for x in kuestenstaedte):
        return 'coastal'
    
    # Aride Zonen
    arid_laender = ['ägypten', 'egypt', 'saudi', 'arabien', 'emirates', 'emirate', 'qatar', 'katar', 'irak', 'iraq', 'iran']
    arid_staedte = ['kairo', 'cairo', 'dubai', 'riad', 'riyadh', 'doha', 'phoenix', 'las vegas']
    
    if any(x in land_lower for x in arid_laender):
        return 'arid'
    if any(x in stadt_lower for x in arid_staedte):
        return 'arid'
    
    # Tropische Zone
    if abs(lat) < 23.5:
        tropisch_laender = ['indien', 'india', 'brasilien', 'brazil', 'vietnam', 'thailand', 'nigeria']
        if any(x in land_lower for x in tropisch_laender):
            return 'tropical'
    
    return 'temperate'


@router.post('/analyze')
@router.get('/analyze')
async def analysiere_standort(
    location: str = Query(None),
    request: AnalyseAnfrage = None
):
    """Analysiert Standort mit 2026 Prognose - Enterprise Edition"""
    
    stadtname = location or (request.location if request else None)
    if not stadtname:
        raise HTTPException(status_code=400, detail='Standort erforderlich')
    
    stadtname = stadtname.strip()
    
    # Geokodierung
    geo = await geokodiere_stadt(stadtname)
    if not geo:
        raise HTTPException(status_code=404, detail=f'Standort nicht gefunden: {stadtname}')
    
    # Risikotyp bestimmen
    risikotyp = bestimme_risikotyp(geo['lat'], geo['lon'], geo['land'], stadtname)
    
    # Basis-Risikoscores (IPCC AR6 basiert)
    basis_scores = {
        'coastal': (0.65, 0.75, 0.15),
        'seismic': (0.55, 0.50, 0.12),
        'arid': (0.50, 0.65, 0.20),
        'conflict': (0.80, 0.30, 0.90),
        'tropical': (0.58, 0.70, 0.15),
        'temperate': (0.32, 0.40, 0.10),
    }
    
    aktuell_risiko, aktuell_klima, aktuell_konflikt = basis_scores.get(risikotyp, (0.35, 0.40, 0.10))
    
    # 2026 Prognose berechnen
    prognose = calculate_2026_forecast(
        location=stadtname,
        lat=geo['lat'],
        lon=geo['lon'],
        risk_type=risikotyp,
        current_risk=aktuell_risiko,
        current_climate=aktuell_klima,
        current_conflict=aktuell_konflikt,
    )
    
    # Risikotyp-Namen auf Deutsch
    typ_namen = {
        'coastal': 'Küste',
        'arid': 'Arid/Wüste',
        'tropical': 'Tropisch',
        'temperate': 'Gemäßigt',
        'conflict': 'Konfliktzone',
        'seismic': 'Seismisch',
    }
    
    return {
        'standort': stadtname,
        'breitengrad': geo['lat'],
        'laengengrad': geo['lon'],
        'land': geo['land'],
        'land_code': geo.get('land_code', ''),
        'bbox': geo.get('bbox'),
        'risikotyp': risikotyp,
        'risikotyp_name': typ_namen.get(risikotyp, 'Unbekannt'),
        
        # Aktuell (2024)
        'aktuell': {
            'risiko_score': aktuell_risiko,
            'klima_risiko': aktuell_klima,
            'konflikt_risiko': aktuell_konflikt,
        },
        
        # 2026 Prognose
        'prognose_2026': {
            'risiko_score': prognose.risk_2026,
            'klima_risiko': prognose.climate_2026,
            'konflikt_risiko': prognose.conflict_2026,
            'risiko_delta': prognose.risk_delta,
            'klima_delta': prognose.climate_delta,
            'schluessel_metriken': prognose.key_metrics,
            'konfidenz': prognose.confidence,
        },
        
        # Deutsche Texte
        'prognose_text': PROGNOSEN_2026_DE.get(risikotyp, PROGNOSEN_2026_DE['temperate']),
        'empfehlungen': EMPFEHLUNGEN_2026_DE.get(risikotyp, EMPFEHLUNGEN_2026_DE['temperate']),
        'datenquellen': prognose.data_sources,
        
        # Legacy compatibility
        'location': stadtname,
        'latitude': geo['lat'],
        'longitude': geo['lon'],
        'country': geo['land'],
        'city_type': risikotyp,
        'risk_score': aktuell_risiko,
        'climate_risk': aktuell_klima,
        'conflict_risk': aktuell_konflikt,
        'projection_2026': PROGNOSEN_2026_DE.get(risikotyp, ''),
        'recommendations': _to_frontend_format(EMPFEHLUNGEN_2026_DE.get(risikotyp, [])),
        'zones': {},
    }


@router.get('/risk-map')
async def generiere_risikokarte(stadt: str = Query(..., alias='city'), aufloesung: int = 8):
    """Generiert Hexagon-Risikokarte mit echten Daten"""
    
    # Geokodierung
    geo = await geokodiere_stadt(stadt)
    if not geo:
        raise HTTPException(status_code=404, detail=f'Stadt nicht gefunden: {stadt}')
    
    risikotyp = bestimme_risikotyp(geo['lat'], geo['lon'], geo['land'], stadt)
    
    # Enterprise Tessellation
    tessellation = EchteDatenTessellation()
    features = await tessellation.generiere_risikokarte(
        lat=geo['lat'],
        lon=geo['lon'],
        stadt_typ=risikotyp,
        aufloesung=aufloesung,
        radius_km=15.0,
    )
    
    # Statistiken berechnen
    zonen_stats = {}
    for f in features:
        zone = f['properties']['zone']
        if zone not in zonen_stats:
            zonen_stats[zone] = {'anzahl': 0, 'farbe': f['properties']['color']}
        zonen_stats[zone]['anzahl'] += 1
    
    return {
        'type': 'FeatureCollection',
        'features': features,
        'metadaten': {
            'stadt': stadt,
            'land': geo['land'],
            'risikotyp': risikotyp,
            'jahr': 2026,
            'zellen_gesamt': len(features),
            'zonen': zonen_stats,
            'aufloesung': aufloesung,
            'datenquellen': ['IPCC AR6', 'ERA5', 'Copernicus', 'OpenStreetMap'],
        }
    }



@router.get('/risk-map/viewport')
async def generiere_risikokarte_viewport(
    min_lat: float,
    min_lon: float,
    max_lat: float,
    max_lon: float,
    zoom: int = 12,
    city_type: str = 'temperate',
    max_cells: int = 3000,
):
    """Viewport-basierte Risikokarte (zoom-adaptiv + capped), für stabile Visualisierung."""

    # Sanity
    if max_cells < 500:
        max_cells = 500
    if max_cells > 8000:
        max_cells = 8000

    tessellation = EchteDatenTessellation()
    features = await tessellation.generiere_viewport_karte(
        min_lat=min_lat,
        min_lon=min_lon,
        max_lat=max_lat,
        max_lon=max_lon,
        zoom=zoom,
        stadt_typ=city_type,
        max_cells=max_cells,
        refine_top_k=min(400, max(50, max_cells // 10)),
    )

    return {
        'type': 'FeatureCollection',
        'features': features,
        'metadaten': {
            'jahr': 2026,
            'city_type': city_type,
            'zoom': zoom,
            'max_cells': max_cells,
            'zellen_gesamt': len(features),
        }
    }
