"""
TERA V2: API Router für Server-Integration
============================================

Neue API-Endpunkte unter /api/v2/ ohne das bestehende System zu berühren.
"""

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict
from datetime import datetime
import asyncio
import aiohttp

router = APIRouter(prefix="/api/v2", tags=["TERA V2 - Causal Intelligence"])


# ═══════════════════════════════════════════════════════════════════════════════
# PRIMÄRE TREIBER KATALOG (inline für einfaches Deployment)
# ═══════════════════════════════════════════════════════════════════════════════

PRIMARY_DRIVERS = {
    "earthquake": {
        "name": "Erdbeben",
        "category": "Tektonisch",
        "description": "Tektonische Aktivität an Plattengrenzen",
        "threshold_warning": "M≥6.0",
        "threshold_critical": "M≥7.0",
        "effects": [
            {"id": "tsunami", "name": "Tsunami", "probability": 0.70, "delay": "0.5-2h", "regions": ["coastal"]},
            {"id": "landslide", "name": "Erdrutsch", "probability": 0.50, "delay": "0-24h", "regions": ["mountainous"]},
            {"id": "aftershocks", "name": "Nachbeben", "probability": 0.95, "delay": "0-30 Tage", "regions": ["local"]},
        ],
        "data_sources": ["USGS Earthquake Hazards", "EMSC"]
    },
    "volcanic_eruption": {
        "name": "Vulkanausbruch",
        "category": "Vulkanisch", 
        "description": "Explosive oder effusive Aktivität",
        "threshold_warning": "VEI≥3",
        "threshold_critical": "VEI≥4",
        "effects": [
            {"id": "ashfall", "name": "Aschefall", "probability": 0.90, "delay": "1-48h", "regions": ["downwind"]},
            {"id": "lahars", "name": "Lahare", "probability": 0.40, "delay": "Stunden-Tage", "regions": ["valleys"]},
            {"id": "regional_cooling", "name": "Regionale Abkühlung", "probability": 0.60, "delay": "1-12 Monate", "regions": ["hemisphere"]},
            {"id": "sst_anomaly", "name": "SST-Anomalie", "probability": 0.40, "delay": "3-12 Monate", "regions": ["global"]},
            {"id": "monsoon_disruption", "name": "Monsun-Störung", "probability": 0.50, "delay": "3-12 Monate", "regions": ["tropical"]},
        ],
        "data_sources": ["Smithsonian GVP", "VAAC", "OMI SO2"]
    },
    "enso": {
        "name": "ENSO (El Niño/La Niña)",
        "category": "Ozeanisch",
        "description": "El Niño Southern Oscillation",
        "threshold_warning": "ONI ±0.5",
        "threshold_critical": "ONI ±1.5",
        "effects": [
            {"id": "australia_drought", "name": "Australien Dürre", "probability": 0.75, "delay": "3-9 Monate", "regions": ["australia"]},
            {"id": "peru_flood", "name": "Peru Flut", "probability": 0.80, "delay": "3-12 Monate", "regions": ["south_america"]},
            {"id": "indonesia_drought", "name": "Indonesien Dürre", "probability": 0.65, "delay": "2-6 Monate", "regions": ["se_asia"]},
            {"id": "california_rain", "name": "Kalifornien Regen", "probability": 0.55, "delay": "Winter", "regions": ["na_west"]},
        ],
        "data_sources": ["NOAA ONI", "NOAA CPC"]
    },
    "atmospheric_blocking": {
        "name": "Atmosphärisches Blocking",
        "category": "Atmosphärisch",
        "description": "Persistente Hochdruckgebiete",
        "threshold_warning": "5+ Tage",
        "threshold_critical": "10+ Tage",
        "effects": [
            {"id": "extreme_heat", "name": "Extremhitze", "probability": 0.75, "delay": "3-14 Tage", "regions": ["blocking_region"]},
            {"id": "drought_blocking", "name": "Dürre", "probability": 0.65, "delay": "1-4 Wochen", "regions": ["blocking_region"]},
        ],
        "data_sources": ["NOAA Blocking Index", "GFS/ECMWF"]
    },
    "arctic_sea_ice": {
        "name": "Arktisches Meereis",
        "category": "Kryosphärisch",
        "description": "Meereis-Ausdehnung und -Dicke",
        "threshold_warning": "<10% unter Mittel",
        "threshold_critical": "<20% unter Mittel",
        "effects": [
            {"id": "arctic_amplification", "name": "Arktische Verstärkung", "probability": 0.80, "delay": "Monate", "regions": ["arctic"]},
            {"id": "jet_waviness", "name": "Jetstream Mäandrierung", "probability": 0.50, "delay": "Monate", "regions": ["mid_latitudes"]},
        ],
        "data_sources": ["NSIDC Sea Ice Index"]
    },
    "greenhouse_gas": {
        "name": "Treibhausgase",
        "category": "Anthropogen",
        "description": "CO2, CH4, N2O Konzentrationen",
        "threshold_warning": "CO2 >420ppm",
        "threshold_critical": "CO2 >450ppm",
        "effects": [
            {"id": "global_warming", "name": "Globale Erwärmung", "probability": 0.95, "delay": "Jahrzehnte", "regions": ["global"]},
            {"id": "sea_level_rise", "name": "Meeresspiegel", "probability": 0.90, "delay": "Jahrzehnte", "regions": ["coastal"]},
        ],
        "data_sources": ["NOAA GML", "Mauna Loa"]
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# KAUSALE VERBINDUNGEN
# ═══════════════════════════════════════════════════════════════════════════════

CAUSAL_CHAINS = {
    "volcanic_eruption → sst_anomaly": {"probability": 0.6, "delay": "3-12 Monate", "mechanism": "Aerosole blockieren Sonne → Ozean kühlt ab"},
    "sst_anomaly → enso": {"probability": 0.9, "delay": "1-3 Monate", "mechanism": "Warmes Wasser → Walker-Zirkulation ändert sich"},
    "enso → australia_drought": {"probability": 0.75, "delay": "3-9 Monate", "mechanism": "El Niño → absinkende Luft → Trockenheit"},
    "enso → peru_flood": {"probability": 0.80, "delay": "3-12 Monate", "mechanism": "Warmes Wasser vor Peru → extreme Niederschläge"},
    "arctic_sea_ice → jet_stream": {"probability": 0.5, "delay": "Wochen-Monate", "mechanism": "Weniger Eis → schwächerer Temperaturgradient"},
    "jet_stream → blocking": {"probability": 0.6, "delay": "Tage", "mechanism": "Wellen verstärken sich zu Blocks"},
    "blocking → heat_wave": {"probability": 0.75, "delay": "3-14 Tage", "mechanism": "Absinkende Luft → Kompression → Erwärmung"},
    "greenhouse_gas → global_warming": {"probability": 0.95, "delay": "Jahrzehnte", "mechanism": "Verstärkter Treibhauseffekt"},
}


# ═══════════════════════════════════════════════════════════════════════════════
# LIVE DATEN ABRUF
# ═══════════════════════════════════════════════════════════════════════════════

async def fetch_usgs_earthquakes() -> List[Dict]:
    """Hole aktuelle Erdbeben von USGS."""
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    earthquakes = []
                    for f in data.get("features", [])[:20]:
                        props = f.get("properties", {})
                        coords = f.get("geometry", {}).get("coordinates", [0, 0])
                        eq = {
                            "id": f.get("id"),
                            "magnitude": props.get("mag"),
                            "location": props.get("place"),
                            "time": datetime.fromtimestamp(props.get("time", 0)/1000).isoformat(),
                            "coordinates": {"lon": coords[0], "lat": coords[1], "depth": coords[2] if len(coords) > 2 else 0},
                            "severity": "critical" if props.get("mag", 0) >= 7 else "warning" if props.get("mag", 0) >= 6 else "info"
                        }
                        earthquakes.append(eq)
                    return earthquakes
    except Exception as e:
        return [{"error": str(e)}]
    return []


# ═══════════════════════════════════════════════════════════════════════════════
# API ENDPUNKTE
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/")
async def v2_info():
    """TERA V2 API Information."""
    return {
        "name": "TERA V2 - Causal Earth Intelligence",
        "version": "2.0.0",
        "description": "Kausale Analyse primärer Treiber für Erdsystem-Vorhersagen",
        "endpoints": {
            "drivers": "/api/v2/drivers - Alle primären Treiber",
            "driver_detail": "/api/v2/drivers/{id} - Details zu einem Treiber",
            "causal_chains": "/api/v2/causal-chains - Alle kausalen Verbindungen",
            "simulate": "/api/v2/simulate - Ereignis simulieren",
            "world_state": "/api/v2/world-state - Aktueller Erd-Zustand",
            "live_earthquakes": "/api/v2/live/earthquakes - USGS Echtzeit",
        }
    }


@router.get("/drivers")
async def list_drivers(category: Optional[str] = None):
    """Liste alle primären Treiber."""
    drivers = []
    for driver_id, driver in PRIMARY_DRIVERS.items():
        if category and driver["category"].lower() != category.lower():
            continue
        drivers.append({
            "id": driver_id,
            "name": driver["name"],
            "category": driver["category"],
            "description": driver["description"],
            "effects_count": len(driver["effects"]),
        })
    return {"status": "success", "total": len(drivers), "drivers": drivers}


@router.get("/drivers/{driver_id}")
async def get_driver(driver_id: str):
    """Details zu einem Treiber."""
    if driver_id not in PRIMARY_DRIVERS:
        return JSONResponse(status_code=404, content={"error": f"Treiber '{driver_id}' nicht gefunden"})
    
    driver = PRIMARY_DRIVERS[driver_id]
    return {
        "status": "success",
        "driver": {
            "id": driver_id,
            **driver
        }
    }


@router.get("/causal-chains")
async def get_causal_chains():
    """Alle kausalen Verbindungen."""
    chains = []
    for chain_name, chain_data in CAUSAL_CHAINS.items():
        parts = chain_name.split(" → ")
        chains.append({
            "source": parts[0],
            "target": parts[1] if len(parts) > 1 else "unknown",
            "probability": chain_data["probability"],
            "delay": chain_data["delay"],
            "mechanism": chain_data["mechanism"],
        })
    return {"status": "success", "total": len(chains), "chains": chains}


@router.get("/causal-chains/{driver_id}")
async def get_chains_for_driver(driver_id: str, depth: int = Query(default=3, ge=1, le=5)):
    """Kausalketten für einen bestimmten Treiber."""
    if driver_id not in PRIMARY_DRIVERS:
        return JSONResponse(status_code=404, content={"error": f"Treiber '{driver_id}' nicht gefunden"})
    
    driver = PRIMARY_DRIVERS[driver_id]
    
    # Direkte Effekte
    direct_effects = driver["effects"]
    
    # Ketten die von diesem Treiber ausgehen
    outgoing_chains = []
    for chain_name, chain_data in CAUSAL_CHAINS.items():
        if chain_name.startswith(driver_id):
            parts = chain_name.split(" → ")
            outgoing_chains.append({
                "target": parts[1] if len(parts) > 1 else "unknown",
                **chain_data
            })
    
    return {
        "status": "success",
        "driver": {"id": driver_id, "name": driver["name"]},
        "direct_effects": direct_effects,
        "outgoing_chains": outgoing_chains,
        "visualization": f"🔴 {driver['name']}\n" + "\n".join([
            f"    └── {e['name']} ({e['probability']:.0%})" for e in direct_effects[:5]
        ])
    }


@router.post("/simulate")
async def simulate_event(
    driver_id: str = Query(..., description="Treiber-ID"),
    magnitude: float = Query(..., description="Stärke"),
    location_name: str = Query("Unknown", description="Ort"),
):
    """Simuliere ein Ereignis und berechne Folgeeffekte."""
    if driver_id not in PRIMARY_DRIVERS:
        return JSONResponse(status_code=404, content={"error": f"Treiber '{driver_id}' nicht gefunden"})
    
    driver = PRIMARY_DRIVERS[driver_id]
    
    # Berechne Effekte
    predictions = []
    for effect in driver["effects"]:
        # Skaliere Wahrscheinlichkeit mit Magnitude (vereinfacht)
        scaled_prob = min(1.0, effect["probability"] * (magnitude / 5))
        predictions.append({
            "effect": effect["name"],
            "probability": round(scaled_prob, 2),
            "timing": effect["delay"],
            "regions": effect["regions"],
        })
    
    # Suche Ketten die weitergehen
    secondary_effects = []
    for chain_name, chain_data in CAUSAL_CHAINS.items():
        if chain_name.startswith(driver_id):
            parts = chain_name.split(" → ")
            target = parts[1] if len(parts) > 1 else None
            if target and target in PRIMARY_DRIVERS:
                for sub_effect in PRIMARY_DRIVERS[target]["effects"][:2]:
                    combined_prob = chain_data["probability"] * sub_effect["probability"]
                    secondary_effects.append({
                        "chain": f"{driver['name']} → {PRIMARY_DRIVERS[target]['name']} → {sub_effect['name']}",
                        "probability": round(combined_prob, 2),
                        "timing": f"{chain_data['delay']} + {sub_effect['delay']}",
                    })
    
    return {
        "status": "success",
        "event": {
            "driver": driver["name"],
            "magnitude": magnitude,
            "location": location_name,
            "timestamp": datetime.now().isoformat(),
        },
        "direct_effects": sorted(predictions, key=lambda x: -x["probability"]),
        "secondary_effects": sorted(secondary_effects, key=lambda x: -x["probability"])[:10],
        "total_effects": len(predictions) + len(secondary_effects),
    }


@router.get("/world-state")
async def get_world_state():
    """Aktueller Zustand der Erde."""
    # Hole Echtzeit-Daten
    earthquakes = await fetch_usgs_earthquakes()
    
    # Aktueller Klima-Status (Demo)
    climate_state = {
        "ENSO": {"value": 1.8, "phase": "El Niño", "strength": "stark"},
        "IOD": {"value": 0.8, "phase": "positiv", "strength": "moderat"},
        "AMO": {"value": 0.4, "phase": "neutral", "strength": "schwach"},
        "NAO": {"value": -0.3, "phase": "negativ", "strength": "schwach"},
    }
    
    # Aktive Alerts
    alerts = []
    critical_eq = [eq for eq in earthquakes if eq.get("severity") == "critical"]
    warning_eq = [eq for eq in earthquakes if eq.get("severity") == "warning"]
    
    if critical_eq:
        alerts.append({
            "type": "earthquake",
            "severity": "critical",
            "count": len(critical_eq),
            "message": f"{len(critical_eq)} kritische Erdbeben M7+ in den letzten 24h"
        })
    
    if climate_state["ENSO"]["strength"] == "stark":
        alerts.append({
            "type": "climate",
            "severity": "warning",
            "message": f"Starker {climate_state['ENSO']['phase']} aktiv - globale Auswirkungen erwartet"
        })
    
    # Vorhersagen basierend auf aktivem Zustand
    predictions = []
    if climate_state["ENSO"]["phase"] == "El Niño":
        predictions.extend([
            {"effect": "Australien Dürre", "probability": 0.75, "timing": "3-9 Monate"},
            {"effect": "Peru Überschwemmung", "probability": 0.80, "timing": "3-12 Monate"},
            {"effect": "Indonesien Dürre", "probability": 0.65, "timing": "2-6 Monate"},
        ])
    
    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "earthquakes_24h": len(earthquakes),
            "critical_events": len(critical_eq),
            "active_alerts": len(alerts),
        },
        "climate_state": climate_state,
        "recent_earthquakes": earthquakes[:10],
        "alerts": alerts,
        "predictions": predictions,
    }


@router.get("/live/earthquakes")
async def get_live_earthquakes():
    """Live Erdbeben von USGS."""
    earthquakes = await fetch_usgs_earthquakes()
    return {
        "status": "success",
        "source": "USGS Earthquake Hazards Program",
        "timestamp": datetime.now().isoformat(),
        "count": len(earthquakes),
        "earthquakes": earthquakes,
    }


@router.get("/paths-to/{effect}")
async def get_paths_to_effect(effect: str):
    """Finde alle kausalen Pfade zu einem bestimmten Effekt."""
    paths = []
    
    # Suche in allen Treibern nach diesem Effekt
    for driver_id, driver in PRIMARY_DRIVERS.items():
        for eff in driver["effects"]:
            if effect.lower() in eff["id"].lower() or effect.lower() in eff["name"].lower():
                paths.append({
                    "path": [driver["name"], eff["name"]],
                    "probability": eff["probability"],
                    "mechanism": f"{driver['name']} → {eff['name']}"
                })
    
    # Suche in Kausalketten
    for chain_name, chain_data in CAUSAL_CHAINS.items():
        if effect.lower() in chain_name.lower():
            parts = chain_name.split(" → ")
            source_name = PRIMARY_DRIVERS.get(parts[0], {}).get("name", parts[0])
            paths.append({
                "path": parts,
                "probability": chain_data["probability"],
                "mechanism": chain_data["mechanism"]
            })
    
    return {
        "status": "success",
        "target_effect": effect,
        "paths_found": len(paths),
        "paths": sorted(paths, key=lambda x: -x["probability"])
    }

