#!/usr/bin/env python3
"""
Erstellt einen MINIMALEN Server NUR mit SSH - zum Testen
"""
import sys
from pathlib import Path
from openstack import connection
from rich.console import Console
from rich.panel import Panel
import time
import base64

console = Console()

def create_minimal_server():
    """Erstellt einen minimalen Server NUR mit SSH"""
    
    console.print(Panel.fit(
        "[bold cyan]Minimaler Server-Test[/bold cyan]\n"
        "NUR SSH - keine anderen Pakete",
        border_style="cyan"
    ))
    
    # Verbindung
    try:
        conn = connection.Connection(
            cloud='openstack',
            config_dir=str(Path.home() / ".config" / "openstack")
        )
        conn.authorize()
        console.print("[green]✓[/green] Verbindung erfolgreich")
    except Exception as e:
        console.print(f"[red]✗[/red] Fehler: {e}")
        sys.exit(1)
    
    # Minimales user_data - NUR SSH
    user_data_script = """#!/bin/bash
# MINIMALES Script - NUR SSH
exec > /var/log/minimal-setup.log 2>&1
echo "=== Minimal Setup Start: $(date) ==="

# SSH installieren und starten (OHNE set -e, damit es nicht stoppt)
apt-get update -y 2>&1
apt-get install -y openssh-server 2>&1
systemctl enable ssh 2>&1
systemctl start ssh 2>&1

# Passwort setzen
echo "ubuntu:ubuntu123" | chpasswd 2>&1

# SSH Config anpassen
sed -i 's/#PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config 2>&1
sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config 2>&1
systemctl restart ssh 2>&1

# Status prüfen
echo "=== SSH Status ==="
systemctl status ssh 2>&1 || true
netstat -tlnp | grep :22 || true
echo "=== Setup Complete: $(date) ==="
"""
    
    user_data_encoded = base64.b64encode(user_data_script.encode('utf-8')).decode('ascii')
    
    # Finde Ressourcen
    images = list(conn.compute.images())
    image = None
    for img in images:
        if "Ubuntu 22.04" in img.name and img.status == "ACTIVE":
            image = img
            break
    
    if not image:
        console.print("[red]✗[/red] Ubuntu 22.04 Image nicht gefunden")
        sys.exit(1)
    
    flavor = conn.compute.find_flavor("m1.small") or conn.compute.find_flavor("m1.tiny")
    if not flavor:
        flavors = list(conn.compute.flavors())
        flavor = flavors[0] if flavors else None
    
    if not flavor:
        console.print("[red]✗[/red] Kein Flavor gefunden")
        sys.exit(1)
    
    network = conn.network.find_network("twm-projekt2-network")
    if not network:
        networks = list(conn.network.networks())
        network = networks[0] if networks else None
    
    if not network:
        console.print("[red]✗[/red] Kein Network gefunden")
        sys.exit(1)
    
    ssh_key = conn.compute.find_keypair("hopp")
    
    console.print(f"\n[yellow]Erstelle minimalen Test-Server...[/yellow]")
    console.print(f"  Image: {image.name[:50]}")
    console.print(f"  Flavor: {flavor.name}")
    console.print(f"  Network: {network.name}")
    console.print(f"  SSH-Key: {'hopp' if ssh_key else 'None'}")
    
    server = conn.compute.create_server(
        name="test-minimal-ssh",
        image_id=image.id,
        flavor_id=flavor.id,
        networks=[{"uuid": network.id}],
        key_name="hopp" if ssh_key else None,
        user_data=user_data_encoded
    )
    
    console.print(f"[green]✓[/green] Server erstellt: {server.id}")
    console.print(f"\n[yellow]Warte auf Aktivierung...[/yellow]")
    
    # Warte auf ACTIVE
    for i in range(30):
        time.sleep(2)
        server = conn.compute.get_server(server.id)
        if server.status == 'ACTIVE':
            break
    
    if server.status != 'ACTIVE':
        console.print(f"[yellow]⚠[/yellow] Server Status: {server.status}")
        return
    
    # Hole IP
    addresses = server.addresses or {}
    ip = ""
    for net_name, addr_list in addresses.items():
        for addr in addr_list:
            if addr.get("version") == 4:
                ip = addr.get("addr", "")
                break
        if ip:
            break
    
    console.print(f"[green]✓[/green] Server aktiv!")
    console.print(f"\n[bold]Server Details:[/bold]")
    console.print(f"  IP: {ip}")
    console.print(f"  User: ubuntu")
    console.print(f"  Passwort: ubuntu123")
    console.print(f"\n[yellow]Warte 60 Sekunden für SSH-Setup...[/yellow]")
    
    time.sleep(60)
    
    console.print(f"\n[bold]Teste SSH-Zugriff:[/bold]")
    console.print(f"  ssh ubuntu@{ip}")
    console.print(f"  Passwort: ubuntu123")

if __name__ == "__main__":
    create_minimal_server()

