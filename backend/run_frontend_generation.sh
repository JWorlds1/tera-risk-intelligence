#!/bin/bash
# Generiere Frontend-Daten für alle kritischen Länder

echo "🌍 Generiere Frontend-Daten..."
echo "Output: data/frontend/"

# Aktiviere Python-Umgebung falls vorhanden
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Generiere Daten
python3 backend/generate_frontend_data.py

echo ""
echo "✅ Frontend-Daten generiert!"
echo ""
echo "📁 Verfügbare Dateien:"
echo "  - data/frontend/complete_data.json"
echo "  - data/frontend/map_data.geojson"
echo "  - data/frontend/early_warning.json"
echo "  - data/frontend/adaptation_recommendations.json"
echo "  - data/frontend/causal_relationships.json"



