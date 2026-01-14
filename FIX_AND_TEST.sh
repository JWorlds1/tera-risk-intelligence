#!/bin/bash
# Script zum Beheben aller Probleme und vollständigen Test

cd "$(dirname "$0")/backend"

echo "🔧 SYSTEM-FIX & TEST"
echo "===================="
echo ""

echo "1️⃣  Geocoding durchführen..."
python geocode_existing_records.py

echo ""
echo "2️⃣  Integrationstest..."
python test_integration.py

echo ""
echo "3️⃣  Prüfe Datenbank-Status..."
python -c "
from database import DatabaseManager
db = DatabaseManager()
stats = db.get_statistics()
print(f'✅ Records: {stats[\"total_records\"]}')
print(f'✅ Mit Koordinaten: {stats[\"records_with_coordinates\"]}')
print(f'✅ Quellen: {len(stats[\"records_by_source\"])}')
"

echo ""
echo "4️⃣  Starte Frontend..."
echo "   Öffne im Browser: http://localhost:PORT"
echo ""
python web_app.py

