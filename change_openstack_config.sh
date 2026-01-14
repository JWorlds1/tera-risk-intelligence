#!/bin/bash
# Script zum Ändern der OpenStack Konfiguration

echo "=========================================="
echo "OpenStack Konfiguration ändern"
echo "=========================================="
echo ""

# Zeige aktuelle Konfiguration
echo "Aktuelle Konfiguration:"
python3 backend/openstack/update_config.py --show

echo ""
echo "Möchten Sie die Konfiguration ändern?"
read -p "Drücken Sie Enter für interaktive Änderung oder Ctrl+C zum Abbrechen..."

# Starte interaktive Änderung
python3 backend/openstack/update_config.py --interactive

echo ""
echo "=========================================="
echo "Fertig!"
echo "=========================================="

