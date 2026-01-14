#!/bin/bash
# Script zum Ausführen der globalen Klima-Analyse für alle 195 Länder

echo "🌍 Starte globale Klima-Analyse für alle 195 Länder..."
echo "Fokus auf am stärksten betroffene Länder weltweit"

# Aktiviere Python-Umgebung falls vorhanden
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Führe globale Analyse aus
python3 backend/global_climate_analysis.py

echo "✅ Globale Analyse abgeschlossen!"



