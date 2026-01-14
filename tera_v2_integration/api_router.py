"""
TERA V2: API Router
====================

Neue API-Endpunkte für:
- World State
- Kausale Ketten
- Vorhersagen
- Echtzeit-Alerts
"""

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import Optional, List
import asyncio
from datetime import datetime

# Importiere V2-Komponenten
from .realtime_global_monitor import GlobalMonitor
from .continuous_worker import ContinuousWorker
from .universal_causal_network import UniversalCausalNetwork
from .primary_drivers_catalog import PRIMARY_DRIVERS, get_all_effects, find_effect_chains
from .enhanced_tessellation import EnhancedTessellationEngine

router = APIRouter(prefix="/api/v2", tags=["TERA V2"])

# Initialisiere Engines (Singletons)
_causal_network: Optional[UniversalCausalNetwork] = None
_tessellation_engine: Optional[EnhancedTessellationEngine] = None
_worker: Optional[ContinuousWorker] = None

def get_causal_network() -> UniversalCausalNetwork:
    global _causal_network
    if _causal_network is None:
        _causal_network = UniversalCausalNetwork()
    return _causal_network

def get_tessellation_engine() -> EnhancedTessellationEngine:
    global _tessellation_engine
    if _tessellation_engine is None:
        _tessellation_engine = EnhancedTessellationEngine()
    return _tessellation_engine

def get_worker() -> ContinuousWorker:
    global _worker
    if _worker is None:
        _worker = ContinuousWorker()
    return _worker


# ═══════════════════════════════════════════════════════════════════════════════
# WORLD STATE ENDPUNKT
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/world-state")
async def get_world_state():
    """
    Hole den aktuellen Welt-Zustand.
    
    Enthält:
    - Aktive Klimaindizes (ENSO, AMO, IOD, NAO)
    - Erkannte Anomalien
    - Aktive Vorhersagen
    - Betroffene Regionen
    """
    worker = get_worker()
    
    # Führe einen Scan durch falls noch nicht geschehen
    if not worker.world_state:
        await worker.run_once()
    
    return JSONResponse(content={
        "status": "success",
        "data": {
            "world_state": worker.world_state.__dict__ if worker.world_state else None,
            "last_updated": datetime.now().isoformat(),
        }
    })


# ═══════════════════════════════════════════════════════════════════════════════
# KAUSALE KETTEN ENDPUNKTE
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/causal-chain/{driver_id}")
async def get_causal_chain(driver_id: str, max_depth: int = Query(default=3, ge=1, le=5)):
    """
    Hole die Kausalkette für einen bestimmten Treiber.
    
    Beispiel: /api/v2/causal-chain/volcanic_eruption
    """
    network = get_causal_network()
    
    if driver_id not in PRIMARY_DRIVERS:
        return JSONResponse(
            status_code=404,
            content={"error": f"Unbekannter Treiber: {driver_id}"}
        )
    
    # Visualisiere Kette
    chain_visualization = network.visualize_chain(driver_id, max_depth)
    
    # Hole Statistiken
    stats = network.get_network_stats()
    
    return JSONResponse(content={
        "status": "success",
        "driver": {
            "id": driver_id,
            "name": PRIMARY_DRIVERS[driver_id].name,
            "category": PRIMARY_DRIVERS[driver_id].category.value,
            "effects_count": len(PRIMARY_DRIVERS[driver_id].causal_effects),
        },
        "causal_chain": chain_visualization,
        "network_stats": stats,
    })


@router.get("/causal-chains/paths-to/{effect}")
async def get_paths_to_effect(effect: str):
    """
    Finde alle Kausalketten die zu einem bestimmten Effekt führen.
    
    Beispiel: /api/v2/causal-chains/paths-to/drought
    """
    network = get_causal_network()
    
    paths = network.get_all_paths_to(effect)
    
    # Formatiere Pfade
    formatted_paths = []
    for path in paths[:20]:  # Max 20 Pfade
        formatted = []
        for i, node in enumerate(path):
            node_data = network.graph.nodes.get(node, {})
            formatted.append({
                "id": node,
                "name": node_data.get("name", node),
                "type": node_data.get("type", "unknown"),
            })
            
            # Hole Kanten-Info
            if i < len(path) - 1:
                edge = network.graph.get_edge_data(node, path[i+1]) or {}
                formatted[-1]["edge_to_next"] = {
                    "probability": edge.get("probability"),
                    "delay": edge.get("delay"),
                }
        
        formatted_paths.append(formatted)
    
    return JSONResponse(content={
        "status": "success",
        "target_effect": effect,
        "paths_count": len(paths),
        "paths": formatted_paths,
    })


# ═══════════════════════════════════════════════════════════════════════════════
# PRIMÄRE TREIBER ENDPUNKTE
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/drivers")
async def list_drivers(category: Optional[str] = None):
    """
    Liste alle primären Treiber.
    
    Optional filtern nach Kategorie: tectonic, volcanic, solar, oceanic, atmospheric, cryospheric, anthropogenic
    """
    drivers = []
    
    for driver_id, driver in PRIMARY_DRIVERS.items():
        if category and driver.category.value.lower() != category.lower():
            continue
        
        drivers.append({
            "id": driver_id,
            "name": driver.name,
            "category": driver.category.value,
            "description": driver.description,
            "effects_count": len(driver.causal_effects),
            "data_sources_count": len(driver.data_sources),
            "threshold_warning": driver.threshold_warning,
            "threshold_critical": driver.threshold_critical,
        })
    
    return JSONResponse(content={
        "status": "success",
        "total": len(drivers),
        "drivers": drivers,
    })


@router.get("/drivers/{driver_id}")
async def get_driver_details(driver_id: str):
    """
    Hole Details zu einem bestimmten Treiber.
    """
    if driver_id not in PRIMARY_DRIVERS:
        return JSONResponse(
            status_code=404,
            content={"error": f"Unbekannter Treiber: {driver_id}"}
        )
    
    driver = PRIMARY_DRIVERS[driver_id]
    
    return JSONResponse(content={
        "status": "success",
        "driver": {
            "id": driver_id,
            "name": driver.name,
            "category": driver.category.value,
            "description": driver.description,
            "key_metrics": driver.key_metrics,
            "threshold_warning": driver.threshold_warning,
            "threshold_critical": driver.threshold_critical,
            "data_sources": [
                {
                    "name": ds.name,
                    "url": ds.url,
                    "update_frequency": ds.update_frequency,
                    "description": ds.description,
                }
                for ds in driver.data_sources
            ],
            "causal_effects": [
                {
                    "id": e.effect_id,
                    "name": e.name,
                    "probability": e.probability,
                    "delay": e.delay_range,
                    "regions": e.affected_regions,
                    "mechanism": e.mechanism,
                    "confidence": e.confidence,
                }
                for e in driver.causal_effects
            ],
            "teleconnections": driver.teleconnections,
        }
    })


# ═══════════════════════════════════════════════════════════════════════════════
# SIMULATION ENDPUNKT
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/simulate")
async def simulate_event(
    driver_id: str = Query(..., description="Treiber-ID"),
    magnitude: float = Query(..., description="Stärke des Ereignisses"),
    unit: str = Query(..., description="Einheit (z.B. M, VEI, °C)"),
    lat: float = Query(0, description="Breitengrad"),
    lon: float = Query(0, description="Längengrad"),
    location_name: str = Query("Unknown", description="Ortsname"),
):
    """
    Simuliere ein Ereignis und berechne alle Folgeeffekte.
    
    Beispiel: POST /api/v2/simulate?driver_id=volcanic_eruption&magnitude=5&unit=VEI&lat=-7.54&lon=110.44&location_name=Merapi
    """
    network = get_causal_network()
    
    if driver_id not in PRIMARY_DRIVERS:
        return JSONResponse(
            status_code=404,
            content={"error": f"Unbekannter Treiber: {driver_id}"}
        )
    
    # Bestimme Schweregrad
    driver = PRIMARY_DRIVERS[driver_id]
    # Vereinfachte Logik
    severity = "critical" if magnitude >= 5 else "warning"
    
    # Injiziere Ereignis
    event, predictions = network.inject_event(
        driver_id=driver_id,
        magnitude=magnitude,
        unit=unit,
        location={"lat": lat, "lon": lon, "name": location_name},
        severity=severity
    )
    
    # Formatiere Vorhersagen
    formatted_predictions = [
        {
            "effect": p.effect_name,
            "probability": p.probability,
            "confidence": p.confidence,
            "timing": p.expected_timing,
            "regions": p.expected_regions,
            "mechanism": p.mechanism,
        }
        for p in sorted(predictions, key=lambda x: -x.probability)[:20]
    ]
    
    return JSONResponse(content={
        "status": "success",
        "event": {
            "id": event.id,
            "driver": event.driver_name,
            "magnitude": f"{event.magnitude} {event.unit}",
            "location": event.location,
            "severity": event.severity,
            "timestamp": event.timestamp.isoformat(),
        },
        "predictions": {
            "total": len(predictions),
            "effects": formatted_predictions,
        },
        "message": f"Ereignis '{driver.name}' simuliert. {len(predictions)} Folgeeffekte berechnet."
    })


# ═══════════════════════════════════════════════════════════════════════════════
# ERWEITERTE TESSELLATION MIT KAUSALEM KONTEXT
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/tessellation/enhanced")
async def get_enhanced_tessellation(
    lat: float = Query(..., description="Breitengrad"),
    lon: float = Query(..., description="Längengrad"),
    radius_km: int = Query(15, ge=1, le=100, description="Radius in km"),
    resolution: int = Query(8, ge=5, le=10, description="H3 Auflösung"),
    year: int = Query(2026, ge=2024, le=2100, description="Projektionsjahr"),
    scenario: str = Query("SSP2-4.5", description="IPCC Szenario"),
):
    """
    Generiere erweiterte H3-Tessellation mit kausalem Kontext.
    
    Jede Zelle enthält:
    - Globalen Kontext (aktive Klimaindizes, Telekonnektion-Effekte)
    - Lokale Vulnerabilitäts-Faktoren
    - Kausale Ketten die diese Zelle betreffen
    - Zeitliche Projektion nach IPCC-Szenario
    """
    engine = get_tessellation_engine()
    
    # Demo-Klima (in Produktion von Live-API)
    climate = {
        'ONI': {'value': 1.8, 'phase': 'positive', 'strength': 'strong'},
        'IOD': {'value': 0.8, 'phase': 'positive', 'strength': 'moderate'},
        'AMO': {'value': 0.4, 'phase': 'neutral', 'strength': 'weak'},
    }
    
    result = engine.generate_hexagons(
        center_lat=lat,
        center_lon=lon,
        radius_km=radius_km,
        resolution=resolution,
        climate_state=climate,
        year=year,
        scenario=scenario
    )
    
    return JSONResponse(content={
        "status": "success",
        "parameters": {
            "center": {"lat": lat, "lon": lon},
            "radius_km": radius_km,
            "resolution": resolution,
            "year": year,
            "scenario": scenario,
        },
        "global_context": result.get("global_context"),
        "statistics": result.get("statistics"),
        "geojson": {
            "type": "FeatureCollection",
            "features": result.get("features", [])[:500],  # Limit
        },
        "metadata": result.get("metadata"),
    })


# ═══════════════════════════════════════════════════════════════════════════════
# WEBSOCKET FÜR ECHTZEIT-ALERTS
# ═══════════════════════════════════════════════════════════════════════════════

# Liste der verbundenen Clients
connected_clients: List[WebSocket] = []

@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    WebSocket für Echtzeit-Alerts.
    
    Clients erhalten Push-Benachrichtigungen bei:
    - Neuen Erdbeben M6+
    - Vulkanischen Ereignissen
    - Signifikanten Klima-Anomalien
    """
    await websocket.accept()
    connected_clients.append(websocket)
    
    try:
        # Sende initiale Nachricht
        await websocket.send_json({
            "type": "connection",
            "message": "TERA Real-Time Alerts verbunden",
            "timestamp": datetime.now().isoformat(),
        })
        
        # Halte Verbindung offen
        while True:
            # Warte auf Ping/Pong oder Client-Nachricht
            data = await websocket.receive_text()
            
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        connected_clients.remove(websocket)


async def broadcast_alert(alert: dict):
    """Sende Alert an alle verbundenen Clients."""
    for client in connected_clients:
        try:
            await client.send_json({
                "type": "alert",
                "data": alert,
                "timestamp": datetime.now().isoformat(),
            })
        except:
            # Client disconnected
            pass


# ═══════════════════════════════════════════════════════════════════════════════
# NETZWERK-STATISTIKEN
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/network/stats")
async def get_network_stats():
    """
    Hole Statistiken über das Kausale Netzwerk.
    """
    network = get_causal_network()
    stats = network.get_network_stats()
    
    # Zähle pro Kategorie
    from collections import Counter
    categories = Counter(d.category.value for d in PRIMARY_DRIVERS.values())
    
    return JSONResponse(content={
        "status": "success",
        "network": stats,
        "drivers_by_category": dict(categories),
        "total_effects": sum(len(d.causal_effects) for d in PRIMARY_DRIVERS.values()),
        "total_data_sources": sum(len(d.data_sources) for d in PRIMARY_DRIVERS.values()),
    })












