#!/bin/bash
# SSH Verbindung zum Geospatial Server
# Ausführen mit: ./connect.sh

cd "$(dirname "$0")"

SERVER_IP="141.100.238.104"
SSH_KEY="keys/geospatial-key.pem"
SSH_USER="ubuntu"

echo "🔌 Verbinde zu ${SERVER_IP}..."
echo ""

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "${SSH_USER}@${SERVER_IP}"

