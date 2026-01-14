#!/usr/bin/env python3
"""
Löscht den aktuellen Server und erstellt ihn neu MIT SSH-Key
"""
import sys
from pathlib import Path
from openstack import connection
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
import time

console = Console()

def recreate_server_with_key(old_server_id):
    """Löscht Server und erstellt ihn neu mit SSH-Key"""
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
    
    try:
        # Hole alte Server-Informationen
        old_server = conn.compute.get_server(old_server_id)
        console.print(f"\n[bold]Alter Server:[/bold]")
        console.print(f"  Name: {old_server.name}")
        console.print(f"  ID: {old_server.id}")
        console.print(f"  Flavor: {old_server.flavor.get('original_name', 'Unknown')}")
        
        # Prüfe SSH-Key
        ssh_key_name = "hopp"
        ssh_key = conn.compute.find_keypair(ssh_key_name)
        if not ssh_key:
            console.print(f"[red]✗[/red] SSH-Key '{ssh_key_name}' nicht gefunden")
            sys.exit(1)
        
        console.print(f"\n[green]✓[/green] SSH-Key '{ssh_key_name}' gefunden")
        
        # Bestätigung
        if not Confirm.ask(f"\n[yellow]Möchten Sie den Server '{old_server.name}' löschen und neu erstellen?[/yellow]", default=False):
            console.print("[yellow]Abgebrochen[/yellow]")
            sys.exit(0)
        
        # Hole Netzwerk-Informationen
        addresses = old_server.addresses or {}
        network_name = None
        for net_name in addresses.keys():
            network_name = net_name
            break
        
        if not network_name:
            console.print("[red]✗[/red] Konnte Netzwerk nicht ermitteln")
            sys.exit(1)
        
        # Hole Image
        image_id = old_server.image.get('id') if old_server.image else None
        
        # Hole Flavor
        flavor_name = old_server.flavor.get('original_name')
        
        console.print(f"\n[yellow]Lösche alten Server...[/yellow]")
        conn.compute.delete_server(old_server_id)
        
        # Warte bis Server gelöscht ist
        console.print("  Warte auf Löschung...")
        for i in range(30):
            try:
                server = conn.compute.get_server(old_server_id)
                if server.status == 'DELETED':
                    break
            except:
                break
            time.sleep(2)
        
        console.print("[green]✓[/green] Server gelöscht")
        
        # Erstelle neuen Server mit SSH-Key
        console.print(f"\n[yellow]Erstelle neuen Server mit SSH-Key...[/yellow]")
        
        # Importiere create_server_simple Funktion
        sys.path.insert(0, str(Path(__file__).parent))
        from create_server_simple import create_server_simple
        
        console.print("\n[bold cyan]Hinweis:[/bold cyan]")
        console.print("  Das Script wird jetzt den Server neu erstellen.")
        console.print("  Bitte führen Sie 'python3 backend/openstack/create_server_simple.py' aus")
        console.print("  um den Server mit SSH-Key zu erstellen.")
        
        console.print("\n[yellow]Oder verwenden Sie dieses Script direkt...[/yellow]")
        
        # Erstelle Server direkt
        server_name = old_server.name
        network = conn.network.find_network(network_name)
        image = conn.compute.get_image(image_id) if image_id else None
        flavor = conn.compute.find_flavor(flavor_name)
        
        if not image:
            # Suche Ubuntu 22.04 Image
            images = list(conn.compute.images())
            for img in images:
                if "Ubuntu 22.04" in img.name and img.status == "ACTIVE":
                    image = img
                    break
        
        if not image or not flavor or not network:
            console.print("[red]✗[/red] Konnte Ressourcen nicht finden")
            sys.exit(1)
        
        # User Data Script (vereinfacht, Base64-kodiert)
        user_data_script = """#!/bin/bash
set -e
exec > /var/log/server-setup.log 2>&1
echo "Server Setup Start"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3-pip python3-dev git curl wget
apt-get install -y postgresql postgresql-contrib
systemctl enable postgresql
systemctl start postgresql
pip3 install --upgrade pip
pip3 install requests httpx aiohttp beautifulsoup4 playwright
pip3 install pandas numpy sqlalchemy psycopg2-binary
pip3 install openai anthropic langchain chromadb
curl -fsSL https://ollama.com/install.sh | sh
systemctl enable ollama
systemctl start ollama
mkdir -p /opt/geospatial-intelligence
sudo -u postgres psql -c "CREATE DATABASE geospatial_intelligence;"
sudo -u postgres psql -c "CREATE USER crawler WITH PASSWORD 'crawler123';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE geospatial_intelligence TO crawler;"
echo "Server Setup Complete"
"""
        
        import base64
        user_data_encoded = base64.b64encode(user_data_script.encode('utf-8')).decode('ascii')
        
        server = conn.compute.create_server(
            name=server_name,
            image_id=image.id,
            flavor_id=flavor.id,
            networks=[{"uuid": network.id}],
            key_name=ssh_key_name,
            user_data=user_data_encoded
        )
        
        console.print(f"[green]✓[/green] Server wird erstellt...")
        console.print(f"  Server ID: {server.id}")
        console.print(f"  SSH-Key: {ssh_key_name}")
        
        return server.id
        
    except Exception as e:
        console.print(f"[red]✗[/red] Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    server_id = "e73e74c7-4648-4c91-9811-2bcc7a748a88"
    if len(sys.argv) > 1:
        server_id = sys.argv[1]
    
    recreate_server_with_key(server_id)

