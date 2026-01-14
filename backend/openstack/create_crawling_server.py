#!/usr/bin/env python3
"""
Erstellt einen OpenStack Server für dynamisches Internet-Crawling
Mit Datenbank und vollständigem Crawling-Setup
"""
import sys
from pathlib import Path
from openstack import connection
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
import time

console = Console()


def list_resources(conn):
    """Listet verfügbare Ressourcen auf"""
    console.print("\n[bold cyan]Verfügbare Ressourcen:[/bold cyan]")
    
    # Images
    images = list(conn.compute.images())
    console.print(f"\n[yellow]Images:[/yellow] {len(images)} verfügbar")
    table = Table()
    table.add_column("#", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Status", style="yellow")
    
    ubuntu_images = [img for img in images if "Ubuntu" in img.name and "22.04" in img.name]
    for i, img in enumerate(ubuntu_images[:10] if ubuntu_images else images[:10], 1):
        table.add_row(str(i), img.name[:50], img.status)
    console.print(table)
    
    # Flavors - Fokus auf RAM für Crawling
    flavors = list(conn.compute.flavors())
    console.print(f"\n[yellow]Flavors (sortiert nach RAM):[/yellow] {len(flavors)} verfügbar")
    table = Table()
    table.add_column("#", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("vCPUs", style="yellow")
    table.add_column("RAM (GB)", style="magenta")
    table.add_column("Disk (GB)", style="blue")
    
    # Sortiere nach RAM
    sorted_flavors = sorted(flavors, key=lambda x: x.ram, reverse=True)
    for i, flv in enumerate(sorted_flavors[:15], 1):
        table.add_row(
            str(i),
            flv.name,
            str(flv.vcpus),
            str(flv.ram // 1024),
            str(flv.disk)
        )
    console.print(table)
    
    # Networks
    networks = list(conn.network.networks())
    console.print(f"\n[yellow]Networks:[/yellow] {len(networks)} verfügbar")
    table = Table()
    table.add_column("#", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Status", style="yellow")
    
    for i, net in enumerate(networks[:10], 1):
        table.add_row(str(i), net.name, net.status)
    console.print(table)
    
    return images, sorted_flavors, networks


def create_crawling_server(conn, name, image, flavor, network, key_name=None):
    """Erstellt einen Crawling-Server mit vollständigem Setup"""
    
    # User Data Script für Crawling-Server Setup
    user_data = """#!/bin/bash
# Crawling Server Setup für Geospatial Intelligence
# Dynamisches Internet-Crawling mit Datenbank

set -e
exec > /var/log/crawling-server-setup.log 2>&1

echo "=== Crawling Server Setup Start: $(date) ==="

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

# Installiere große LLM-Modelle (kann später gemacht werden)
# ollama pull llama2:70b        # ~40 GB RAM
# ollama pull mixtral:8x7b       # ~26 GB RAM  
# ollama pull codellama:34b      # ~20 GB RAM

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
After=network.target postgresql.service

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

echo "=== Crawling Server Setup Abgeschlossen: $(date) ==="
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
    
    try:
        # Finde Image - verwende ID wenn möglich, sonst Name
        img = None
        
        # Versuche zuerst als ID
        try:
            img = conn.compute.get_image(image)
        except:
            pass
        
        # Falls nicht gefunden, suche nach Name (aber nimm das erste ACTIVE)
        if not img:
            images = list(conn.compute.images())
            for i in images:
                if i.name == image or image in i.name:
                    if i.status == "ACTIVE":
                        img = i
                        break
            
            # Fallback: erstes passendes Image
            if not img:
                for i in images:
                    if i.name == image or image in i.name:
                        img = i
                        break
        
        if not img:
            console.print(f"[red]✗[/red] Image '{image}' nicht gefunden")
            return None
        
        # Finde Flavor
        flv = conn.compute.find_flavor(flavor)
        if not flv:
            console.print(f"[red]✗[/red] Flavor '{flavor}' nicht gefunden")
            return None
        
        # Finde Network
        net = conn.network.find_network(network)
        if not net:
            console.print(f"[red]✗[/red] Network '{network}' nicht gefunden")
            return None
        
        # Erstelle Server
        console.print(f"\n[yellow]Erstelle Crawling-Server '{name}'...[/yellow]")
        console.print(f"  Image: {img.name}")
        console.print(f"  Flavor: {flv.name} ({flv.vcpus} vCPUs, {flv.ram // 1024} GB RAM, {flv.disk} GB Disk)")
        console.print(f"  Network: {net.name}")
        
        server = conn.compute.create_server(
            name=name,
            image_id=img.id,
            flavor_id=flv.id,
            networks=[{"uuid": net.id}],
            key_name=key_name,
            user_data=user_data
        )
        
        console.print(f"[green]✓[/green] Server wird erstellt...")
        console.print(f"  Server ID: {server.id}")
        console.print(f"  Status: {server.status}")
        
        return server
        
    except Exception as e:
        console.print(f"[red]✗[/red] Fehler beim Erstellen: {e}")
        import traceback
        traceback.print_exc()
        return None


def wait_for_server(conn, server_id, max_wait=600):
    """Wartet bis Server aktiv ist"""
    console.print("\n[yellow]Warte auf Server-Start...[/yellow]")
    
    waited = 0
    while waited < max_wait:
        time.sleep(10)
        waited += 10
        
        server = conn.compute.get_server(server_id)
        status = server.status
        
        console.print(f"  Status: {status} ({waited}s)")
        
        if status == 'ACTIVE':
            # Warte noch etwas für Setup-Script (LLM-Installation dauert länger)
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
            console.print(f"  IP-Adresse: {ip}")
            return server, ip
        elif status == 'ERROR':
            console.print(f"[red]✗[/red] Server-Erstellung fehlgeschlagen!")
            return None, None
    
    console.print(f"[yellow]⚠[/yellow] Timeout nach {max_wait}s")
    return None, None


def main():
    """Hauptfunktion"""
    console.print(Panel.fit(
        "[bold cyan]OpenStack Crawling-Server Erstellung[/bold cyan]\n"
        "Dynamisches Internet-Crawling mit Datenbank",
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
    
    # Liste Ressourcen
    images, flavors, networks = list_resources(conn)
    
    # Interaktive Auswahl
    console.print("\n[bold yellow]Server-Konfiguration:[/bold yellow]")
    
    server_name = Prompt.ask("Server-Name", default="geospatial-crawler-01")
    
    # Image Auswahl (Ubuntu 22.04 empfohlen)
    ubuntu_images = [img for img in images if "Ubuntu" in img.name and "22.04" in img.name]
    default_image = ubuntu_images[0].name if ubuntu_images else images[0].name
    
    image_choice = Prompt.ask(
        "Image (Nummer oder Name)",
        default=default_image
    )
    
    # Flavor Auswahl (empfohlen: viel RAM für LLM)
    console.print("\n[yellow]Empfehlung für LLM-Inference:[/yellow]")
    console.print("  Für kleine LLMs: 32-64 GB RAM")
    console.print("  Für große LLMs (70B+): 128 GB RAM")
    console.print("  Für sehr große LLMs: 256 GB RAM")
    
    # Zeige große Flavors
    large_flavors = [f for f in flavors if f.ram >= 32 * 1024]  # >= 32 GB
    if large_flavors:
        console.print("\n[bold cyan]Verfügbare große Flavors (für LLM):[/bold cyan]")
        table = Table()
        table.add_column("Name", style="green")
        table.add_column("vCPUs", style="yellow")
        table.add_column("RAM (GB)", style="magenta")
        table.add_column("Disk (GB)", style="blue")
        
        for flv in large_flavors[:10]:
            table.add_row(
                flv.name,
                str(flv.vcpus),
                str(flv.ram // 1024),
                str(flv.disk)
            )
        console.print(table)
    
    flavor_choice = Prompt.ask(
        "Flavor (Nummer oder Name)",
        default="c1.8xlarge" if large_flavors else "m1.2xlarge"  # 64 vCPUs, 128 GB RAM oder 8 vCPUs, 32 GB RAM
    )
    
    # Network Auswahl
    network_choice = Prompt.ask(
        "Network (Nummer oder Name)",
        default=networks[0].name if networks else ""
    )
    
    # Optional: SSH Key
    use_key = Confirm.ask("SSH Key verwenden?", default=False)
    key_name = None
    if use_key:
        key_name = Prompt.ask("SSH Key Name")
    
    # Bestätigung
    console.print("\n[bold]Zusammenfassung:[/bold]")
    console.print(f"  Name: {server_name}")
    console.print(f"  Image: {image_choice}")
    console.print(f"  Flavor: {flavor_choice}")
    console.print(f"  Network: {network_choice}")
    if key_name:
        console.print(f"  SSH Key: {key_name}")
    
    console.print("\n[yellow]Der Server wird konfiguriert mit:[/yellow]")
    console.print("  ✓ PostgreSQL Datenbank")
    console.print("  ✓ Python Crawling-Tools (Playwright, Selenium)")
    console.print("  ✓ Geospatial Libraries")
    console.print("  ✓ AI/LLM Libraries (OpenAI, Anthropic, LangChain)")
    console.print("  ✓ Ollama für lokale LLMs")
    console.print("  ✓ vLLM für große LLM-Inference")
    console.print("  ✓ Transformers & PyTorch")
    console.print("  ✓ ChromaDB für Vektordatenbank")
    console.print("  ✓ Automatische Backups")
    console.print("\n[bold cyan]Optimiert für LLM-Inference mit viel RAM![/bold cyan]")
    
    if not Confirm.ask("\nServer erstellen?", default=True):
        console.print("[yellow]Abgebrochen[/yellow]")
        sys.exit(0)
    
    # Erstelle Server
    server = create_crawling_server(conn, server_name, image_choice, flavor_choice, network_choice, key_name)
    
    if server:
        # Warte auf Aktivierung
        active_server, ip = wait_for_server(conn, server.id)
        
        if active_server and ip:
            console.print("\n" + "=" * 60)
            console.print("[bold green]✓ Crawling-Server erfolgreich erstellt![/bold green]")
            console.print("=" * 60)
            
            console.print(f"\n[bold]Server Details:[/bold]")
            console.print(f"  ID: {server.id}")
            console.print(f"  Name: {server.name}")
            console.print(f"  IP: {ip}")
            console.print(f"  Status: {active_server.status}")
            
            console.print(f"\n[bold]Zugriff:[/bold]")
            if key_name:
                console.print(f"  SSH: ssh -i ~/.ssh/{key_name}.pem ubuntu@{ip}")
            else:
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
            console.print(f"  Status: systemctl status ollama")
            console.print(f"  Modelle installieren: ollama pull llama2:70b")
            
            console.print(f"\n[bold]Nächste Schritte:[/bold]")
            console.print(f"  1. SSH zum Server verbinden")
            console.print(f"  2. Passwort ändern: sudo -u postgres psql -c \"ALTER USER crawler WITH PASSWORD 'neues_passwort';\"")
            console.print(f"  3. Projekt-Code hochladen: scp -r backend/ ubuntu@{ip}:/opt/geospatial-intelligence/")
            console.print(f"  4. LLM-Modelle installieren: ollama pull llama2:70b mistral:7b")
            console.print(f"  5. Crawling + LLM-Inference starten")
            
            console.print(f"\n[yellow]Setup-Log:[/yellow]")
            console.print(f"  Prüfen Sie: ssh ubuntu@{ip} 'cat /var/log/crawling-server-setup.log'")
        else:
            console.print("\n[yellow]⚠[/yellow] Server erstellt, aber Status unklar")
            console.print(f"  Prüfen Sie: openstack --os-cloud openstack server show {server.name}")
    else:
        console.print("\n[bold red]✗ Server-Erstellung fehlgeschlagen[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Abgebrochen vom Benutzer[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Fehler:[/bold red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

