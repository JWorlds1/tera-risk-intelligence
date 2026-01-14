#!/usr/bin/env python3
"""
Automatisches Script zum Erstellen des LLM-Crawling-Servers
Mit optimalen Einstellungen für 128 GB RAM
"""
import sys
from pathlib import Path
from openstack import connection
from rich.console import Console
from rich.panel import Panel
import time
import base64

console = Console()


def create_server_automated():
    """Erstellt Server automatisch mit optimalen Einstellungen"""
    
    console.print(Panel.fit(
        "[bold cyan]Automatische Server-Erstellung[/bold cyan]\n"
        "LLM-Crawling-Server mit 128 GB RAM",
        border_style="cyan"
    ))
    
    # Verbindung herstellen
    try:
        conn = connection.Connection(
            cloud='openstack',
            config_dir=str(Path.home() / ".config" / "openstack")
        )
        conn.authorize()
        console.print("[green]✓[/green] Verbindung zu OpenStack erfolgreich")
    except Exception as e:
        console.print(f"[red]✗[/red] Verbindungsfehler: {e}")
        sys.exit(1)
    
    # Konfiguration
    server_name = "geospatial-llm-crawler-01"
    image_name = "Ubuntu 22.04 LTS (Jammy Jellyfish) Cloud Image"
    flavor_name = "c1.8xlarge"  # 64 vCPUs, 128 GB RAM
    network_name = "twm-projekt2-network"  # Projekt-Netzwerk
    
    console.print("\n[bold yellow]Konfiguration:[/bold yellow]")
    console.print(f"  Server-Name: {server_name}")
    console.print(f"  Image: {image_name}")
    console.print(f"  Flavor: {flavor_name} (64 vCPUs, 128 GB RAM)")
    console.print(f"  Network: {network_name}")
    
    # Finde Ressourcen
    console.print("\n[yellow]Suche Ressourcen...[/yellow]")
    
    # Image finden - verwende Image-ID statt Name (wegen Duplikaten)
    images = list(conn.compute.images())
    image = None
    
    # Suche nach ACTIVE Ubuntu 22.04 Image
    for img in images:
        if "Ubuntu 22.04" in img.name and img.status == "ACTIVE":
            image = img
            break
    
    if not image:
        # Fallback: erstes Ubuntu 22.04 Image
        for img in images:
            if "Ubuntu 22.04" in img.name:
                image = img
                break
    
    if not image:
        console.print("[red]✗[/red] Ubuntu 22.04 Image nicht gefunden")
        sys.exit(1)
    
    console.print(f"  [green]✓[/green] Image gefunden: {image.name} (ID: {image.id[:16]}...)")
    
    # Flavor finden
    flavor = conn.compute.find_flavor(flavor_name)
    if not flavor:
        console.print(f"[red]✗[/red] Flavor '{flavor_name}' nicht gefunden")
        sys.exit(1)
    
    console.print(f"  [green]✓[/green] Flavor gefunden: {flavor.name} ({flavor.vcpus} vCPUs, {flavor.ram // 1024} GB RAM)")
    
    # Network finden
    networks = list(conn.network.networks())
    network = None
    
    # Versuche Projekt-Netzwerk zuerst
    for net in networks:
        if net.name == network_name:
            network = net
            break
    
    # Fallback: erstes ACTIVE Network
    if not network:
        for net in networks:
            if net.status == "ACTIVE":
                network = net
                break
    
    if not network:
        console.print("[red]✗[/red] Kein verfügbares Network gefunden")
        sys.exit(1)
    
    console.print(f"  [green]✓[/green] Network gefunden: {network.name}")
    
    # User Data Script (gleiches wie im anderen Script)
    user_data = """#!/bin/bash
# LLM-Crawling Server Setup für Geospatial Intelligence
# Optimiert für große LLMs (128 GB RAM)

set -e
exec > /var/log/crawling-server-setup.log 2>&1

echo "=== LLM-Crawling Server Setup Start: $(date) ==="

# System Update
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y

# Basis-Tools
apt-get install -y python3-pip python3-dev build-essential git curl wget vim htop
apt-get install -y sqlite3 postgresql-client

# PostgreSQL Server für Datenbank
apt-get install -y postgresql postgresql-contrib
systemctl enable postgresql
systemctl start postgresql

# Python-Pakete für Crawling
pip3 install --upgrade pip
pip3 install requests httpx aiohttp beautifulsoup4 lxml playwright selenium
pip3 install pandas pyarrow numpy sqlalchemy psycopg2-binary
pip3 install python-dotenv structlog rich

# Geospatial Libraries
pip3 install geopandas rasterio folium shapely fiona pyproj

# AI/LLM Libraries
pip3 install openai anthropic firecrawl-py langchain

# ChromaDB für Vektordatenbank
pip3 install chromadb

# LLM Inference Engines - Optimiert für große Modelle
pip3 install transformers accelerate bitsandbytes
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Ollama Installation für lokale LLMs (beste für große Modelle)
curl -fsSL https://ollama.com/install.sh | sh

# Ollama Konfiguration für große Modelle
mkdir -p /etc/systemd/system/ollama.service.d
cat > /etc/systemd/system/ollama.service.d/override.conf <<'OLLAMACONF'
[Service]
Environment="OLLAMA_NUM_PARALLEL=2"
Environment="OLLAMA_MAX_LOADED_MODELS=1"
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_KEEP_ALIVE=24h"
OLLAMACONF

systemctl daemon-reload
systemctl enable ollama
systemctl start ollama

# RAM-Optimierung für LLM-Inference
echo 'vm.swappiness=10' >> /etc/sysctl.conf
echo 'vm.nr_hugepages=1024' >> /etc/sysctl.conf
sysctl -p

# Node.js für Playwright Browser
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# Playwright Browser Installation
pip3 install playwright
python3 -m playwright install chromium firefox

# Docker für Containerisierung (optional)
apt-get install -y docker.io docker-compose
systemctl enable docker
systemctl start docker

# PostgreSQL Konfiguration
sudo -u postgres psql <<EOF
CREATE DATABASE geospatial_intelligence;
CREATE USER crawler WITH PASSWORD 'crawler_password_change_me';
GRANT ALL PRIVILEGES ON DATABASE geospatial_intelligence TO crawler;
\\c geospatial_intelligence
GRANT ALL ON SCHEMA public TO crawler;
EOF

# Erstelle Verzeichnisse
mkdir -p /opt/geospatial-intelligence
mkdir -p /opt/geospatial-intelligence/data
mkdir -p /opt/geospatial-intelligence/logs
mkdir -p /opt/geospatial-intelligence/backups
chmod 755 /opt/geospatial-intelligence

# Firewall (falls aktiv)
ufw allow 22/tcp
ufw allow 5432/tcp
ufw allow 11434/tcp
ufw --force enable || true

# Cron für automatische Backups
cat > /etc/cron.daily/geospatial-backup <<'CRONEOF'
#!/bin/bash
BACKUP_DIR="/opt/geospatial-intelligence/backups"
DATE=$(date +%Y%m%d_%H%M%S)
sudo -u postgres pg_dump geospatial_intelligence > "$BACKUP_DIR/db_backup_$DATE.sql"
find "$BACKUP_DIR" -name "db_backup_*.sql" -mtime +7 -delete
CRONEOF
chmod +x /etc/cron.daily/geospatial-backup

# Systemd Service für Crawling (Vorlage)
cat > /etc/systemd/system/geospatial-crawler.service <<'SERVICEEOF'
[Unit]
Description=Geospatial Intelligence Crawler
After=network.target postgresql.service ollama.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/geospatial-intelligence
ExecStart=/usr/bin/python3 /opt/geospatial-intelligence/crawler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICEEOF

echo "=== LLM-Crawling Server Setup Abgeschlossen: $(date) ==="
echo "PostgreSQL läuft auf Port 5432"
echo "Datenbank: geospatial_intelligence"
echo "Ollama läuft auf Port 11434"
echo "Verzeichnis: /opt/geospatial-intelligence"
echo ""
echo "Nächste Schritte:"
echo "1. Installiere LLM-Modelle: ollama pull llama2:70b"
echo "2. Teste LLM: ollama run llama2:70b 'Test'"
echo "3. Prüfe RAM: free -h"
"""
    
    # Erstelle Server
    console.print("\n[yellow]Erstelle Server...[/yellow]")
    console.print(f"  Verwende Image-ID: {image.id[:16]}... (vermeidet Duplikat-Problem)")
    
    # Kodiere user_data als Base64 (vermeidet Unicode-Probleme)
    user_data_encoded = base64.b64encode(user_data.encode('utf-8')).decode('utf-8')
    
    try:
        server = conn.compute.create_server(
            name=server_name,
            image_id=image.id,  # Verwende Image-ID direkt (vermeidet Duplikat-Problem)
            flavor_id=flavor.id,
            networks=[{"uuid": network.id}],
            user_data=user_data_encoded  # Base64-kodiert
        )
        
        console.print(f"[green]✓[/green] Server wird erstellt...")
        console.print(f"  Server ID: {server.id}")
        console.print(f"  Status: {server.status}")
        
        # Warte auf Aktivierung
        console.print("\n[yellow]Warte auf Server-Start...[/yellow]")
        console.print("  (Dies kann 5-10 Minuten dauern)")
        
        waited = 0
        max_wait = 600  # 10 Minuten
        
        while waited < max_wait:
            time.sleep(10)
            waited += 10
            
            try:
                server = conn.compute.get_server(server.id)
                status = server.status
                
                if waited % 30 == 0:  # Alle 30 Sekunden Status anzeigen
                    console.print(f"  Status: {status} ({waited}s)")
                
                if status == 'ACTIVE':
                    # Warte noch etwas für Setup-Script
                    console.print("  [yellow]Warte auf Setup-Abschluss (120s für LLM-Installation)...[/yellow]")
                    time.sleep(120)
                    
                    # Hole IP-Adresse
                    addresses = server.addresses or {}
                    ip = ""
                    for network_name, addr_list in addresses.items():
                        if addr_list:
                            for addr in addr_list:
                                if addr.get("version") == 4:
                                    ip = addr.get("addr", "")
                                    break
                            if ip:
                                break
                    
                    console.print(f"[green]✓[/green] Server ist aktiv!")
                    
                    # Zeige Zusammenfassung
                    console.print("\n" + "=" * 60)
                    console.print(Panel.fit(
                        "[bold green]✓ Server erfolgreich erstellt![/bold green]",
                        border_style="green"
                    ))
                    console.print("=" * 60)
                    
                    console.print(f"\n[bold]Server Details:[/bold]")
                    console.print(f"  ID: {server.id}")
                    console.print(f"  Name: {server.name}")
                    console.print(f"  IP: {ip}")
                    console.print(f"  Status: {server.status}")
                    console.print(f"  Flavor: {flavor.name} ({flavor.vcpus} vCPUs, {flavor.ram // 1024} GB RAM)")
                    
                    console.print(f"\n[bold]Zugriff:[/bold]")
                    console.print(f"  SSH: ssh ubuntu@{ip}")
                    
                    console.print(f"\n[bold]Datenbank:[/bold]")
                    console.print(f"  Host: {ip}")
                    console.print(f"  Port: 5432")
                    console.print(f"  Database: geospatial_intelligence")
                    console.print(f"  User: crawler")
                    console.print(f"  Password: crawler_password_change_me")
                    console.print(f"  [yellow]⚠ Bitte Passwort ändern![/yellow]")
                    
                    console.print(f"\n[bold]LLM-Services:[/bold]")
                    console.print(f"  Ollama: http://{ip}:11434")
                    console.print(f"  Status: ssh ubuntu@{ip} 'systemctl status ollama'")
                    console.print(f"  Modelle installieren: ssh ubuntu@{ip} 'ollama pull llama2:70b'")
                    
                    console.print(f"\n[bold]Nächste Schritte:[/bold]")
                    console.print(f"  1. SSH zum Server: ssh ubuntu@{ip}")
                    console.print(f"  2. Passwort ändern: sudo -u postgres psql -c \"ALTER USER crawler WITH PASSWORD 'neues_passwort';\"")
                    console.print(f"  3. LLM-Modelle installieren:")
                    console.print(f"     ollama pull llama2:70b")
                    console.print(f"     ollama pull mixtral:8x7b")
                    console.print(f"  4. Projekt-Code hochladen:")
                    console.print(f"     scp -r backend/ ubuntu@{ip}:/opt/geospatial-intelligence/")
                    console.print(f"  5. Crawling + LLM-Inference starten")
                    
                    console.print(f"\n[yellow]Setup-Log:[/yellow]")
                    console.print(f"  Prüfen Sie: ssh ubuntu@{ip} 'cat /var/log/crawling-server-setup.log'")
                    
                    return True
                    
                elif status == 'ERROR':
                    console.print(f"[red]✗[/red] Server-Erstellung fehlgeschlagen!")
                    console.print(f"  Prüfen Sie: openstack --os-cloud openstack server show {server.id}")
                    return False
                    
            except Exception as e:
                if waited % 60 == 0:  # Alle Minute Fehler zeigen
                    console.print(f"  [yellow]Warte... ({waited}s)[/yellow]")
        
        console.print(f"[yellow]⚠[/yellow] Timeout nach {max_wait}s")
        console.print(f"  Server wurde erstellt, aber Status unklar")
        console.print(f"  Prüfen Sie: openstack --os-cloud openstack server show {server.id}")
        return False
        
    except Exception as e:
        console.print(f"[red]✗[/red] Fehler beim Erstellen: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = create_server_automated()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Abgebrochen vom Benutzer[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Fehler:[/bold red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

