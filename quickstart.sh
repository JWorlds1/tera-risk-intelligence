#!/bin/bash
# Quick-Start Script für Climate Conflict Pipeline

set -e

echo "🌍 Climate Conflict Pipeline - Quick Start"
echo "=========================================="
echo ""

# Prüfe ob Docker installiert ist
if ! command -v docker &> /dev/null; then
    echo "❌ Docker ist nicht installiert!"
    echo "Bitte installiere Docker: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose ist nicht installiert!"
    echo "Bitte installiere docker-compose"
    exit 1
fi

# Erstelle data-Verzeichnis falls nicht vorhanden
mkdir -p ./data

echo "✅ Docker gefunden"
echo ""

# Zeige Menü
echo "Was möchtest du tun?"
echo "1) Pipeline einmalig ausführen (Extraktion)"
echo "2) Dashboard starten (Daten anzeigen)"
echo "3) Test der Extraktion"
echo "4) Alles (Pipeline + Dashboard)"
echo "5) Automatisiertes Crawling starten (Scheduler)"
echo ""
read -p "Wähle Option (1-5): " option

case $option in
    1)
        echo "🚀 Starte Pipeline..."
        docker-compose -f docker-compose.pipeline.yml up --build pipeline
        ;;
    2)
        echo "📊 Starte Dashboard..."
        echo "Dashboard verfügbar unter: http://localhost:5000"
        docker-compose -f docker-compose.pipeline.yml up --build dashboard
        ;;
    3)
        echo "🧪 Teste Extraktion..."
        docker-compose -f docker-compose.pipeline.yml run --rm pipeline python test_extraction.py
        ;;
    4)
        echo "🚀 Starte Pipeline..."
        docker-compose -f docker-compose.pipeline.yml up --build -d pipeline
        echo "⏳ Warte 30 Sekunden..."
        sleep 30
        echo "📊 Starte Dashboard..."
        echo "Dashboard verfügbar unter: http://localhost:5000"
        docker-compose -f docker-compose.pipeline.yml up --build dashboard
        ;;
    5)
        echo "🔄 Starte automatisiertes Crawling..."
        echo "Pipeline läuft im Hintergrund (täglich 02:00, alle 6h)"
        docker-compose -f docker-compose.pipeline.yml up --build scheduler
        ;;
    *)
        echo "❌ Ungültige Option"
        exit 1
        ;;
esac

