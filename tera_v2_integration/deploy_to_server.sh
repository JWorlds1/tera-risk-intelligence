#!/bin/bash
# TERA V2 Integration - Deployment Script
# ========================================
# 
# Dieses Script deployed die neuen V2 Komponenten auf den TERA-Server
# und integriert sie mit dem bestehenden Backend.

set -e

# Konfiguration
SERVER_KEY="/Users/qed97/Geospatial_Intelligence/terraform/keys/geospatial-key.pem"
SERVER_USER="ubuntu"
SERVER_IP="141.100.238.104"
TERA_PATH="/data/tera"

echo "=============================================="
echo "TERA V2 Integration - Deployment"
echo "=============================================="

# 1. Dateien auf Server kopieren
echo ""
echo "📦 Kopiere V2 Module auf Server..."

scp -i $SERVER_KEY \
    climate_index_service.py \
    global_risk_engine.py \
    enhanced_tessellation.py \
    __init__.py \
    ${SERVER_USER}@${SERVER_IP}:${TERA_PATH}/backend/services/v2/

# 2. API Route erstellen
echo ""
echo "🔧 Erstelle API Route..."

ssh -i $SERVER_KEY ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
cat > /data/tera/backend/api/routes/causal.py << 'PYEOF'
"""
TERA V2: Causal Analysis API Routes
====================================
"""

from fastapi import APIRouter, Query
from typing import Optional
import sys
sys.path.insert(0, '/data/tera/backend/services/v2')

from enhanced_tessellation import EnhancedTessellationEngine
from global_risk_engine import GlobalRiskEngine
from climate_index_service import ClimateIndexService

router = APIRouter(prefix="/api/causal", tags=["causal"])

# Singletons
tessellation_engine = EnhancedTessellationEngine()
risk_engine = GlobalRiskEngine()
climate_service = ClimateIndexService()


@router.get("/risk-map")
async def get_causal_risk_map(
    city: str = Query(..., description="Stadt/Ort"),
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    resolution: int = Query(8, ge=7, le=10),
    radius_km: float = Query(20, ge=5, le=100),
    year: int = Query(2026, ge=2024, le=2100),
    scenario: str = Query("SSP2-4.5")
):
    """
    Generiere erweiterte Risiko-Tessellation mit kausalen Ketten.
    
    Kombiniert:
    - Aktuelle Klimaindizes (ENSO, AMO, IOD, etc.)
    - Telekonnektion-Effekte
    - Lokale Vulnerabilität
    - Zeitliche Projektion
    """
    # Koordinaten ermitteln (vereinfacht)
    if lat is None or lon is None:
        coords = {
            "sydney": (-33.87, 151.21),
            "miami": (25.76, -80.19),
            "lima": (-12.05, -77.04),
            "mumbai": (19.08, 72.88),
            "tokyo": (35.68, 139.69),
            "london": (51.51, -0.13),
            "berlin": (52.52, 13.40),
            "new york": (40.71, -74.01),
            "los angeles": (34.05, -118.24),
            "jakarta": (-6.21, 106.85),
        }
        lat, lon = coords.get(city.lower(), (0, 0))
    
    # Klimaindizes (Demo - in Produktion von NOAA)
    climate_indices = {
        "ONI": {"value": 1.8, "phase": "positive", "strength": "strong"},
        "AMO": {"value": 0.4, "phase": "neutral", "strength": "weak"},
        "IOD": {"value": 0.8, "phase": "positive", "strength": "moderate"},
        "NAO": {"value": -0.3, "phase": "neutral", "strength": "weak"},
    }
    
    # Generiere erweiterte Tessellation
    result = tessellation_engine.generate_hexagons(
        center_lat=lat,
        center_lon=lon,
        radius_km=radius_km,
        resolution=resolution,
        climate_indices=climate_indices,
        year=year,
        scenario=scenario
    )
    
    return {
        "status": "success",
        "city": city,
        "data": result
    }


@router.get("/climate-modes")
async def get_climate_modes():
    """Hole aktuelle Klimaindizes."""
    # Demo-Werte
    return {
        "status": "success",
        "modes": {
            "ONI": {"value": 1.8, "phase": "positive", "description": "El Niño (stark)"},
            "AMO": {"value": 0.4, "phase": "neutral", "description": "Atlantic neutral"},
            "IOD": {"value": 0.8, "phase": "positive", "description": "Indian Ocean Dipole positiv"},
            "NAO": {"value": -0.3, "phase": "neutral", "description": "North Atlantic neutral"},
        },
        "enso_status": "El Niño (stark): ONI = +1.8°C"
    }


@router.get("/effects")
async def get_teleconnection_effects(
    lat: float = Query(...),
    lon: float = Query(...)
):
    """Hole Telekonnektion-Effekte für einen Punkt."""
    climate_indices = {
        "ONI": {"value": 1.8, "phase": "positive", "strength": "strong"},
        "IOD": {"value": 0.8, "phase": "positive", "strength": "moderate"},
    }
    
    context = risk_engine.calculate_global_context(lat, lon, climate_indices)
    
    return {
        "status": "success",
        "location": {"lat": lat, "lon": lon},
        "region": context["region"],
        "effects": context["teleconnection_effects"],
        "hazard_risks": context["hazard_risks"],
        "causal_chains": context["causal_chains"]
    }
PYEOF

echo "API Route erstellt!"
ENDSSH

# 3. Router in main.py registrieren
echo ""
echo "🔗 Registriere Router in main.py..."

ssh -i $SERVER_KEY ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
# Prüfe ob causal router schon importiert
if ! grep -q "from api.routes.causal import router as causal_router" /data/tera/backend/main.py; then
    # Füge Import hinzu
    sed -i '/from api.routes.analysis import router as analysis_router/a from api.routes.causal import router as causal_router' /data/tera/backend/main.py
    
    # Füge include_router hinzu
    sed -i '/app.include_router(analysis_router)/a app.include_router(causal_router)' /data/tera/backend/main.py
    
    echo "Router registriert!"
else
    echo "Router bereits registriert."
fi
ENDSSH

# 4. Verzeichnis erstellen und Dependencies prüfen
echo ""
echo "📁 Erstelle Verzeichnis und prüfe Dependencies..."

ssh -i $SERVER_KEY ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
mkdir -p /data/tera/backend/services/v2
source /data/tera/venv/bin/activate
pip install h3 aiohttp --quiet
echo "Dependencies installiert!"
ENDSSH

# 5. Backend neustarten
echo ""
echo "🔄 Starte Backend neu..."

ssh -i $SERVER_KEY ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
pkill -f "uvicorn main:app" || true
sleep 2
cd /data/tera/backend
source /data/tera/venv/bin/activate
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8080 > /tmp/tera-backend.log 2>&1 &
sleep 3
echo "Backend gestartet!"

# Test
curl -s http://localhost:8080/ | head -c 100
ENDSSH

echo ""
echo "=============================================="
echo "✅ Deployment abgeschlossen!"
echo "=============================================="
echo ""
echo "Neue Endpoints verfügbar:"
echo "  GET /api/causal/risk-map?city=Sydney"
echo "  GET /api/causal/climate-modes"
echo "  GET /api/causal/effects?lat=-33.87&lon=151.21"
echo ""












