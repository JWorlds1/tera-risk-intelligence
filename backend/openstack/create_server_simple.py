#!/usr/bin/env python3
"""
Vereinfachtes Script zum Erstellen des LLM-Crawling-Servers
Mit minimalem user_data Script (vermeidet Unicode-Probleme)
"""
import sys
from pathlib import Path
from openstack import connection
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import time
import base64

console = Console()


def wait_for_server_active(conn, server_id, flavor_name, max_wait=600):
    """Wartet bis Server aktiv ist und gibt Details zurück"""
    console.print("\n[yellow]Warte auf Server-Start...[/yellow]")
    console.print("  (Dies kann 5-10 Minuten dauern)")
    
    waited = 0
    while waited < max_wait:
        time.sleep(10)
        waited += 10
        
        try:
            server = conn.compute.get_server(server_id)
            status = server.status
            
            if waited % 30 == 0:
                console.print(f"  Status: {status} ({waited}s)")
            
            if status == 'ACTIVE':
                time.sleep(60)  # Warte auf Setup
                
                # Hole IP
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
                console.print(f"  Flavor: {flavor_name}")
                
                console.print(f"\n[bold]Zugriff:[/bold]")
                console.print(f"  SSH: ssh ubuntu@{ip}")
                
                console.print(f"\n[bold]Nächste Schritte:[/bold]")
                console.print(f"  1. SSH: ssh ubuntu@{ip}")
                console.print(f"  2. Setup-Log prüfen: cat /var/log/server-setup.log")
                console.print(f"  3. Weitere Pakete installieren falls nötig")
                console.print(f"  4. LLM-Modelle: ollama pull llama2:70b")
                
                return True, ip
            
            elif status == 'ERROR':
                console.print(f"[red]✗[/red] Server-Erstellung fehlgeschlagen!")
                return False, None
        
        except Exception as e:
            if waited % 60 == 0:
                console.print(f"  [yellow]Warte... ({waited}s)[/yellow]")
    
    console.print(f"[yellow]⚠[/yellow] Timeout nach {max_wait}s")
    return False, None


def create_server_simple():
    """Erstellt Server mit vereinfachtem Setup-Script"""
    
    console.print(Panel.fit(
        "[bold cyan]Vereinfachte Server-Erstellung[/bold cyan]\n"
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
    preferred_flavor_name = "c1.8xlarge"  # Bevorzugter Flavor
    network_name = "twm-projekt2-network"
    ssh_key_name = "hopp"  # SSH-Key Name
    
    console.print("\n[bold yellow]Konfiguration:[/bold yellow]")
    console.print(f"  Server-Name: {server_name}")
    console.print(f"  Bevorzugter Flavor: {preferred_flavor_name}")
    console.print(f"  Network: {network_name}")
    
    # Finde Ressourcen
    console.print("\n[yellow]Suche Ressourcen...[/yellow]")
    
    # Image finden
    images = list(conn.compute.images())
    image = None
    for img in images:
        if "Ubuntu 22.04" in img.name and img.status == "ACTIVE":
            image = img
            break
    
    if not image:
        for img in images:
            if "Ubuntu 22.04" in img.name:
                image = img
                break
    
    if not image:
        console.print("[red]✗[/red] Ubuntu 22.04 Image nicht gefunden")
        sys.exit(1)
    
    console.print(f"  [green]✓[/green] Image: {image.name[:50]}... (ID: {image.id[:16]}...)")
    
    # Prüfe Quota und finde passenden Flavor
    console.print("\n[yellow]Prüfe Quota und verfügbare Flavors...[/yellow]")
    
    quota_cores = None
    quota_ram = None
    available_cores = None
    available_ram = None
    
    try:
        # Versuche Quota-Informationen zu erhalten
        limits = conn.compute.get_limits()
        
        # Prüfe verschiedene mögliche Schlüsselnamen
        absolute = limits.absolute if hasattr(limits, 'absolute') else {}
        
        quota_cores = absolute.get('maxTotalCores') or absolute.get('maxTotalCoresUsed') or absolute.get('cores')
        quota_ram = absolute.get('maxTotalRAMSize') or absolute.get('maxTotalRAMUsed') or absolute.get('ram')
        used_cores = absolute.get('totalCoresUsed', 0) or absolute.get('coresUsed', 0)
        used_ram = absolute.get('totalRAMUsed', 0) or absolute.get('ramUsed', 0)
        
        if quota_cores and quota_ram:
            available_cores = quota_cores - used_cores
            available_ram = quota_ram - used_ram
            console.print(f"  Quota: {quota_cores} vCPUs, {quota_ram // 1024} GB RAM")
            console.print(f"  Verwendet: {used_cores} vCPUs, {used_ram // 1024} GB RAM")
            console.print(f"  Verfügbar: {available_cores} vCPUs, {available_ram // 1024} GB RAM")
        else:
            # Fallback: Versuche Quota aus absoluten Limits zu extrahieren
            if hasattr(limits, 'absolute'):
                for key, value in limits.absolute.items():
                    if 'core' in key.lower() and 'max' in key.lower():
                        quota_cores = value
                    elif 'ram' in key.lower() and 'max' in key.lower():
                        quota_ram = value
                
                if quota_cores and quota_ram:
                    available_cores = quota_cores - (absolute.get('totalCoresUsed', 0) or 0)
                    available_ram = quota_ram - (absolute.get('totalRAMUsed', 0) or 0)
                    console.print(f"  Quota: {quota_cores} vCPUs, {quota_ram // 1024} GB RAM")
                    console.print(f"  Verfügbar: {available_cores} vCPUs, {available_ram // 1024} GB RAM")
                else:
                    console.print("  [dim]Quota-Informationen nicht verfügbar (wird beim Erstellen geprüft)[/dim]")
            else:
                console.print("  [dim]Quota-Informationen nicht verfügbar (wird beim Erstellen geprüft)[/dim]")
    except Exception as e:
        console.print(f"  [dim]Quota-Informationen nicht verfügbar: {e}[/dim]")
        console.print("  [dim]Wird beim Erstellen geprüft[/dim]")
    
    # Finde alle Flavors und sortiere nach RAM
    all_flavors = list(conn.compute.flavors())
    sorted_flavors = sorted(all_flavors, key=lambda x: x.ram, reverse=True)
    
    # Versuche zuerst den bevorzugten Flavor
    flavor = conn.compute.find_flavor(preferred_flavor_name)
    
    if flavor:
        # Prüfe ob Flavor innerhalb der Quota liegt
        if quota_cores and flavor.vcpus > available_cores:
            console.print(f"  [yellow]⚠[/yellow] Flavor '{flavor.name}' benötigt {flavor.vcpus} vCPUs, aber nur {available_cores} verfügbar")
            flavor = None
        elif quota_ram and flavor.ram > available_ram:
            console.print(f"  [yellow]⚠[/yellow] Flavor '{flavor.name}' benötigt {flavor.ram // 1024} GB RAM, aber nur {available_ram // 1024} GB verfügbar")
            flavor = None
        else:
            console.print(f"  [green]✓[/green] Flavor '{flavor.name}' ist verfügbar ({flavor.vcpus} vCPUs, {flavor.ram // 1024} GB RAM)")
    
    # Falls bevorzugter Flavor nicht verfügbar, finde größten passenden Flavor
    if not flavor:
        console.print("\n[yellow]Suche größten verfügbaren Flavor innerhalb der Quota...[/yellow]")
        
        for flv in sorted_flavors:
            # Prüfe ob Flavor innerhalb der Quota liegt
            if quota_cores and flv.vcpus > available_cores:
                continue
            if quota_ram and flv.ram > available_ram:
                continue
            
            flavor = flv
            console.print(f"  [green]✓[/green] Gefundener Flavor: {flavor.name} ({flavor.vcpus} vCPUs, {flavor.ram // 1024} GB RAM)")
            break
        
        if not flavor:
            console.print("\n[red]✗[/red] Kein passender Flavor innerhalb der Quota gefunden!")
            if quota_cores and quota_ram:
                console.print(f"\n[yellow]Verfügbare Flavors innerhalb der Quota:[/yellow]")
                table = Table()
                table.add_column("Name", style="green")
                table.add_column("vCPUs", style="yellow")
                table.add_column("RAM (GB)", style="magenta")
                table.add_column("Disk (GB)", style="blue")
                
                for flv in sorted_flavors:
                    if (not quota_cores or flv.vcpus <= available_cores) and (not quota_ram or flv.ram <= available_ram):
                        table.add_row(
                            flv.name,
                            str(flv.vcpus),
                            str(flv.ram // 1024),
                            str(flv.disk)
                        )
                console.print(table)
            sys.exit(1)
    
    # Network finden
    networks = list(conn.network.networks())
    network = None
    
    for net in networks:
        if net.name == network_name:
            network = net
            break
    
    if not network:
        for net in networks:
            if net.status == "ACTIVE":
                network = net
                break
    
    if not network:
        console.print("[red]✗[/red] Kein verfügbares Network gefunden")
        sys.exit(1)
    
    console.print(f"  [green]✓[/green] Network: {network.name}")
    
    # Vereinfachtes User Data Script (minimal, nur ASCII, keine problematischen Zeichen)
    # Verwendet Base64-Kodierung um UnicodeDecodeError zu vermeiden
    user_data_script = """#!/bin/bash
# Verwende set +e für kritische Befehle, damit Script nicht bei Fehlern stoppt
set +e
exec > /var/log/server-setup.log 2>&1
echo "=== Server Setup Start: $(date) ==="
export DEBIAN_FRONTEND=noninteractive

# KRITISCH: Stelle sicher dass SSH läuft (SOFORT, bevor andere Pakete installiert werden!)
echo "=== Installing and starting SSH ==="
apt-get update -y || true
apt-get install -y openssh-server || true
systemctl enable ssh || true
systemctl start ssh || true

# Setze Passwort für ubuntu-User (für Console-Zugriff)
echo "=== Setting password for ubuntu user ==="
echo "ubuntu:ubuntu123" | chpasswd || true

# Aktiviere Passwort-Login in SSH
echo "=== Enabling password authentication ==="
sed -i 's/#PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config || true
sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config || true
systemctl restart ssh || true

echo "=== SSH should be running now ==="
systemctl status ssh || true

# Jetzt können andere Pakete installiert werden
set -e

# Basis-Tools
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
    
    # Base64-Kodierung um UnicodeDecodeError zu vermeiden
    # Einige OpenStack-Installationen erwarten Base64-kodiertes user_data
    user_data_encoded = base64.b64encode(user_data_script.encode('utf-8')).decode('ascii')
    
    console.print("\n[yellow]Erstelle Server...[/yellow]")
    console.print("  [dim]user_data wird Base64-kodiert uebertragen[/dim]")
    
    try:
        # Verwende Base64-kodiertes user_data um Unicode-Probleme zu vermeiden
        # Füge SSH-Key hinzu falls verfügbar
        server_params = {
            "name": server_name,
            "image_id": image.id,
            "flavor_id": flavor.id,
            "networks": [{"uuid": network.id}],
            "user_data": user_data_encoded
        }
        
        # Prüfe ob SSH-Key existiert und füge hinzu
        try:
            ssh_key = conn.compute.find_keypair(ssh_key_name)
            if ssh_key:
                server_params["key_name"] = ssh_key_name
                console.print(f"  [green]✓[/green] SSH-Key '{ssh_key_name}' wird verwendet")
            else:
                console.print(f"  [yellow]⚠[/yellow] SSH-Key '{ssh_key_name}' nicht gefunden - Server ohne Key")
        except Exception as e:
            console.print(f"  [yellow]⚠[/yellow] Konnte SSH-Key nicht prüfen: {e}")
        
        server = conn.compute.create_server(**server_params)
        
        console.print(f"[green]✓[/green] Server wird erstellt...")
        console.print(f"  Server ID: {server.id}")
        console.print(f"  Status: {server.status}")
        
        # Warte auf Aktivierung
        flavor_info = f"{flavor.name} ({flavor.vcpus} vCPUs, {flavor.ram // 1024} GB RAM)"
        success, ip = wait_for_server_active(conn, server.id, flavor_info)
        return success
        
    except Exception as e:
        error_msg = str(e)
        console.print(f"[red]✗[/red] Fehler beim Erstellen: {error_msg}")
        
        # Prüfe ob es ein Quota-Problem ist
        if "Quota exceeded" in error_msg or "quota" in error_msg.lower():
            console.print("\n[yellow]Quota-Problem erkannt![/yellow]")
            console.print("  Versuche einen kleineren Flavor zu finden...")
            
            # Versuche mit kleinerem Flavor
            try:
                # Finde größten verfügbaren Flavor
                all_flavors = list(conn.compute.flavors())
                sorted_flavors = sorted(all_flavors, key=lambda x: (x.ram, x.vcpus), reverse=True)
                
                # Extrahiere Quota aus Fehlermeldung falls möglich
                import re
                quota_match = re.search(r'of (\d+), (\d+)', error_msg)
                if quota_match:
                    max_cores = int(quota_match.group(1))
                    max_ram = int(quota_match.group(2))
                    
                    console.print(f"\n[yellow]Suche Flavor innerhalb der Quota ({max_cores} vCPUs, {max_ram // 1024} GB RAM)...[/yellow]")
                    
                    for flv in sorted_flavors:
                        if flv.vcpus <= max_cores and flv.ram <= max_ram:
                            console.print(f"\n[cyan]Versuche mit Flavor: {flv.name} ({flv.vcpus} vCPUs, {flv.ram // 1024} GB RAM)[/cyan]")
                            
                            server = conn.compute.create_server(
                                name=server_name,
                                image_id=image.id,
                                flavor_id=flv.id,
                                networks=[{"uuid": network.id}],
                                user_data=user_data_encoded
                            )
                            
                            console.print(f"[green]✓[/green] Server wird mit Flavor '{flv.name}' erstellt...")
                            console.print(f"  Server ID: {server.id}")
                            console.print(f"  Status: {server.status}")
                            
                            # Warte auf Aktivierung
                            flavor_info = f"{flv.name} ({flv.vcpus} vCPUs, {flv.ram // 1024} GB RAM)"
                            success, ip = wait_for_server_active(conn, server.id, flavor_info)
                            return success
                    
                    console.print("[red]✗[/red] Kein passender Flavor gefunden!")
            except Exception as retry_error:
                console.print(f"[red]✗[/red] Fehler beim Retry: {retry_error}")
        
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = create_server_simple()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Abgebrochen vom Benutzer[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Fehler:[/bold red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

