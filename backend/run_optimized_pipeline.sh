#!/bin/bash
# Script zum Ausführen der optimierten Pipeline

echo "🚀 Starte optimierte Crawling & Enrichment Pipeline..."

# Aktiviere Python-Umgebung falls vorhanden
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Führe optimierte Pipeline aus
python3 backend/optimized_pipeline.py

echo "✅ Pipeline abgeschlossen!"



