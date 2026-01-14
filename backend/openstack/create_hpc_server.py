#!/usr/bin/env python3
"""
Erstellt einen HPC-Server für Geospatial Intelligence Berechnungen
"""
import sys
from pathlib import Path
from openstack import connection
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel

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
    
    for i, img in enumerate(images[:15], 1):
        table.add_row(str(i), img.name[:50], img.status)
    console.print(table)
    
    # Flavors
    flavors = list(conn.compute.flavors())
    console.print(f"\n[yellow]Flavors:[/yellow] {len(flavors)} verfügbar")
    table = Table()
    table.add_column("#", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("vCPUs", style="yellow")
    table.add_column("RAM (GB)", style="magenta")
    table.add_column("Disk (GB)", style="blue")
    
    for i, flv in enumerate(flavors[:15], 1):
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
    
    return images, flavors, networks

def create_server(conn, name, image, flavor, network, key_name=None):
    """Erstellt einen neuen Server"""
    
    # User Data Script für HPC-Setup
    user_data = """#!/bin/bash
# HPC Setup Script für Geospatial Intelligence

set -e

echo "=== HPC Server Setup Start ===" | tee /var/log/hpc-setup.log

# System Update
apt-get update -y
apt-get upgrade -y

# Basis-Tools
apt-get install -y python3-pip python3-dev build-essential git curl wget vim

# MPI für verteilte Berechnungen
apt-get install -y openmpi-bin openmpi-common libopenmpi-dev

# Python Pakete für HPC
pip3 install --upgrade pip
pip3 install mpi4py numpy pandas scipy scikit-learn

# Geospatial Libraries
pip3 install geopandas rasterio folium shapely fiona pyproj

# Projekt-Dependencies
pip3 install openai anthropic firecrawl-py langchain

# Docker für Containerisierung (optional)
apt-get install -y docker.io
systemctl enable docker
systemctl start docker

# NFS Client für Shared Storage (falls benötigt)
apt-get install -y nfs-common

# SSH Key Setup (falls benötigt)
mkdir -p /root/.ssh
chmod 700 /root/.ssh

echo "=== HPC Server Setup Abgeschlossen: $(date) ===" | tee -a /var/log/hpc-setup.log
"""
    
    try:
        # Finde Image
        img = conn.compute.find_image(image)
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
        console.print(f"\n[yellow]Erstelle Server '{name}'...[/yellow]")
        console.print(f"  Image: {img.name}")
        console.print(f"  Flavor: {flv.name} ({flv.vcpus} vCPUs, {flv.ram // 1024} GB RAM)")
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

def main():
    console.print(Panel.fit(
        "[bold cyan]HPC Server Erstellung für Geospatial Intelligence[/bold cyan]",
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
    
    server_name = Prompt.ask("Server-Name", default="geospatial-hpc-01")
    
    # Image Auswahl
    image_choice = Prompt.ask(
        "Image (Nummer oder Name)",
        default="Ubuntu 22.04 LTS (Jammy Jellyfish) Cloud Image"
    )
    
    # Flavor Auswahl
    flavor_choice = Prompt.ask(
        "Flavor (Nummer oder Name)",
        default="m1.large"
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
    
    if not Confirm.ask("\nServer erstellen?", default=True):
        console.print("[yellow]Abgebrochen[/yellow]")
        sys.exit(0)
    
    # Erstelle Server
    server = create_server(conn, server_name, image_choice, flavor_choice, network_choice, key_name)
    
    if server:
        console.print("\n[bold green]✓ Server erfolgreich erstellt![/bold green]")
        console.print(f"\nServer Details:")
        console.print(f"  ID: {server.id}")
        console.print(f"  Name: {server.name}")
        console.print(f"  Status: {server.status}")
        console.print(f"\n[yellow]Hinweis:[/yellow] Der Server wird automatisch mit HPC-Tools konfiguriert.")
        console.print(f"  Prüfen Sie den Status mit: openstack --os-cloud openstack server show {server.name}")
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

