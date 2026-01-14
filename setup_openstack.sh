#!/bin/bash
# OpenStack Setup Script - Erstellt Konfiguration und testet Verbindung

echo "=========================================="
echo "OpenStack Setup für H-DA Cloud"
echo "=========================================="
echo ""

# Erstelle Config-Verzeichnis
mkdir -p ~/.config/openstack

# Kopiere Template
if [ -f "backend/openstack/clouds.yaml.template" ]; then
    cp backend/openstack/clouds.yaml.template ~/.config/openstack/clouds.yaml
    echo "✓ Konfiguration erstellt: ~/.config/openstack/clouds.yaml"
else
    echo "Erstelle clouds.yaml..."
    cat > ~/.config/openstack/clouds.yaml << 'EOF'
clouds:
  openstack:
    auth:
      auth_url: https://h-da.cloud:13000
      application_credential_id: "ba44dda4814e443faba80ae101d704a8"
      application_credential_secret: "Wesen"
    region_name: "eu-central"
    interface: "public"
    identity_api_version: 3
    auth_type: "v3applicationcredential"
EOF
    echo "✓ Konfiguration erstellt"
fi

echo ""
echo "Teste Verbindung..."
echo ""

# Teste mit OpenStack CLI
if command -v openstack &> /dev/null; then
    echo "Teste mit OpenStack CLI:"
    openstack --os-cloud openstack server list 2>&1 | head -20
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✓ Verbindung erfolgreich!"
    else
        echo ""
        echo "⚠ Verbindungstest mit CLI fehlgeschlagen, versuche Python SDK..."
    fi
fi

# Teste mit Python SDK
echo ""
echo "Teste mit Python SDK:"
python3 test_openstack_connection.py 2>&1

echo ""
echo "=========================================="
echo "Setup abgeschlossen!"
echo ""
echo "Verwendung:"
echo "  openstack --os-cloud openstack server list"
echo "  python3 test_openstack_connection.py"
echo "=========================================="

