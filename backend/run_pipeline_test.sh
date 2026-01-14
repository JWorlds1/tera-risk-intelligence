#!/bin/bash
# Script zum Testen der Pipeline mit detailliertem Output

echo "🧪 Starte Pipeline-Test mit Validierung..."
echo "Testet Pipeline und zeigt Output für jedes Land"

# Aktiviere Python-Umgebung falls vorhanden
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Führe Test aus
python3 backend/test_global_pipeline.py

echo "✅ Pipeline-Test abgeschlossen!"



