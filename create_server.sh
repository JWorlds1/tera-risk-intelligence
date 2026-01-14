#!/bin/bash
# Einfaches Script zum Erstellen des LLM-Crawling-Servers

echo "=========================================="
echo "LLM-Crawling-Server Erstellung"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

echo "Starte automatische Server-Erstellung..."
echo ""

python3 backend/openstack/create_server_auto.py

echo ""
echo "=========================================="
echo "Fertig!"
echo "=========================================="

