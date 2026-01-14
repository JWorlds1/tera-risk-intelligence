#!/usr/bin/env python3
"""
Beispiel: OpenStack Server für HPC-Berechnungen einrichten
"""
import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from openstack.client import OpenStackClient
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()


def create_hpc_server(client: OpenStackClient):
    """Erstellt einen HPC-Server für Geospatial Intelligence Berechnungen"""
    
    console.print("\n[bold cyan]HPC Server Setup[/bold cyan]")
    console.print("=" * 60)
    
    # Liste verfügbare Ressourcen
    console.print("\n[bold]Verfügbare Ressourcen:[/bold]")
    
    # Images
    images = client.list_images()
    console.print("\n[yellow]Images:[/yellow]")
    for i, img in enumerate(images[:10], 1):
        console.print(f"  {i}. {img['name']} ({img['id'][:8]}...)")
    
    image_choice = Prompt.ask("\nWähle Image (Name oder Nummer)", default=images[0]['name'] if images else "")
    
    # Flavors
    flavors = client.list_flavors()
    console.print("\n[yellow]Flavors:[/yellow]")
    for i, flv in enumerate(flavors[:10], 1):
        console.print(f"  {i}. {flv['name']} - {flv['vcpus']} vCPUs, {flv['ram']}MB RAM, {flv['disk']}GB Disk")
    
    flavor_choice = Prompt.ask("\nWähle Flavor (Name oder Nummer)", default=flavors[0]['name'] if flavors else "")
    
    # Networks
    networks = client.list_networks()
    console.print("\n[yellow]Networks:[/yellow]")
    for i, net in enumerate(networks[:10], 1):
        console.print(f"  {i}. {net['name']} ({net['id'][:8]}...)")
    
    network_choice = Prompt.ask("\nWähle Network (Name oder Nummer)", default=networks[0]['name'] if networks else "")
    
    # Server-Name
    server_name = Prompt.ask("\nServer-Name", default="geospatial-hpc-worker-01")
    
    # User Data Script für HPC-Setup
    user_data = """#!/bin/bash
# HPC Setup Script für Geospatial Intelligence

# System Update
apt-get update -y
apt-get upgrade -y

# Python und Basis-Tools
apt-get install -y python3-pip python3-dev build-essential
apt-get install -y git curl wget

# MPI für verteilte Berechnungen
apt-get install -y openmpi-bin openmpi-common libopenmpi-dev

# Python Pakete für HPC
pip3 install --upgrade pip
pip3 install mpi4py numpy pandas scipy scikit-learn

# Geospatial Libraries
pip3 install geopandas rasterio folium

# Projekt-Dependencies
pip3 install openai anthropic firecrawl-py

# Docker für Containerisierung (optional)
apt-get install -y docker.io
systemctl enable docker
systemctl start docker

# NFS Client für Shared Storage (falls benötigt)
apt-get install -y nfs-common

# Logging
echo "HPC Setup abgeschlossen: $(date)" >> /var/log/hpc-setup.log
"""
    
    # Security Groups
    sec_groups = client.list_security_groups()
    default_sec_group = [sg['name'] for sg in sec_groups if sg['name'] == 'default']
    
    # Erstelle Server
    console.print(f"\n[bold]Erstelle Server '{server_name}'...[/bold]")
    console.print(f"  Image: {image_choice}")
    console.print(f"  Flavor: {flavor_choice}")
    console.print(f"  Network: {network_choice}")
    
    if not Confirm.ask("\nFortfahren?", default=True):
        console.print("[yellow]Abgebrochen[/yellow]")
        return None
    
    server = client.create_server(
        name=server_name,
        image=image_choice,
        flavor=flavor_choice,
        network=network_choice,
        security_groups=default_sec_group,
        user_data=user_data
    )
    
    if server:
        console.print(f"\n[green]✓[/green] Server erstellt!")
        console.print(f"  ID: {server['id']}")
        console.print(f"  Name: {server['name']}")
        console.print(f"  Status: {server['status']}")
        
        # Warte auf aktive Status
        console.print("\n[yellow]Warte auf Server-Start...[/yellow]")
        max_wait = 300  # 5 Minuten
        waited = 0
        
        while waited < max_wait:
            time.sleep(10)
            waited += 10
            
            updated_server = client.get_server(server['id'])
            if updated_server:
                status = updated_server['status']
                console.print(f"  Status: {status} ({waited}s)")
                
                if status == 'ACTIVE':
                    console.print(f"\n[green]✓[/green] Server ist aktiv!")
                    console.print(f"  IP: {updated_server.get('ip', 'Wird zugewiesen...')}")
                    break
                elif status == 'ERROR':
                    console.print(f"\n[red]✗[/red] Server-Erstellung fehlgeschlagen!")
                    break
        
        return server
    else:
        console.print("\n[red]✗[/red] Server-Erstellung fehlgeschlagen!")
        return None


def main():
    """Hauptfunktion"""
    cloud_name = sys.argv[1] if len(sys.argv) > 1 else "hda-cloud"
    
    console.print(f"\n[bold]OpenStack HPC Server Setup[/bold]")
    console.print(f"Cloud: {cloud_name}\n")
    
    # Client initialisieren
    client = OpenStackClient(cloud_name=cloud_name)
    
    # Verbindung herstellen
    if not client.connect():
        console.print("\n[red]✗[/red] Verbindung fehlgeschlagen!")
        console.print("Führen Sie zuerst das Setup aus: python3 backend/openstack/setup.py")
        sys.exit(1)
    
    # HPC Server erstellen
    server = create_hpc_server(client)
    
    if server:
        console.print("\n[bold green]✓ Setup abgeschlossen![/bold green]")
        console.print("\n[bold]Nächste Schritte:[/bold]")
        console.print("1. SSH zum Server verbinden")
        console.print("2. Projekt-Code hochladen")
        console.print("3. HPC-Berechnungen starten")
    else:
        console.print("\n[bold red]✗ Setup fehlgeschlagen![/bold red]")


if __name__ == "__main__":
    main()

