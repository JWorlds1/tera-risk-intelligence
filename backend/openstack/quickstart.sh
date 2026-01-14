#!/bin/bash
# OpenStack Quick Start Script

echo "=========================================="
echo "OpenStack Integration Quick Start"
echo "=========================================="
echo ""

# Prüfe ob Python verfügbar ist
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 nicht gefunden. Bitte installieren Sie Python 3.8+"
    exit 1
fi

# Prüfe ob pip verfügbar ist
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 nicht gefunden. Bitte installieren Sie pip"
    exit 1
fi

echo "📦 Installiere OpenStack Client Abhängigkeiten..."
pip3 install -q python-openstackclient openstacksdk python-novaclient python-glanceclient python-neutronclient python-cinderclient python-keystoneclient PyYAML

if [ $? -ne 0 ]; then
    echo "❌ Installation fehlgeschlagen"
    exit 1
fi

echo "✅ Abhängigkeiten installiert"
echo ""

# Führe Setup aus
echo "🔧 Starte OpenStack Konfiguration..."
python3 backend/openstack/setup.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Setup abgeschlossen!"
    echo ""
    echo "📋 Nächste Schritte:"
    echo "   1. Teste die Verbindung:"
    echo "      python3 backend/openstack/test_connection.py"
    echo ""
    echo "   2. Liste verfügbare Ressourcen:"
    echo "      python3 backend/openstack/list_resources.py"
    echo ""
else
    echo "❌ Setup fehlgeschlagen"
    exit 1
fi

