#!/usr/bin/env python3
"""
Test OpenStack Verbindung
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from openstack.client import OpenStackClient
from rich.console import Console

console = Console()


def main():
    """Testet OpenStack Verbindung"""
    console.print("\n[bold cyan]OpenStack Verbindungstest[/bold cyan]")
    console.print("=" * 60)
    
    cloud_name = sys.argv[1] if len(sys.argv) > 1 else "hda-cloud"
    
    client = OpenStackClient(cloud_name=cloud_name)
    
    if client.connect():
        console.print("\n[bold green]✓ Verbindung erfolgreich![/bold green]")
        
        # Teste verschiedene Operationen
        console.print("\n[bold]Teste verfügbare Ressourcen...[/bold]")
        
        # Images
        images = client.list_images()
        console.print(f"  Images: {len(images)} gefunden")
        
        # Flavors
        flavors = client.list_flavors()
        console.print(f"  Flavors: {len(flavors)} gefunden")
        
        # Networks
        networks = client.list_networks()
        console.print(f"  Networks: {len(networks)} gefunden")
        
        # Security Groups
        sec_groups = client.list_security_groups()
        console.print(f"  Security Groups: {len(sec_groups)} gefunden")
        
        # Server
        servers = client.list_servers()
        console.print(f"  Server: {len(servers)} gefunden")
        
        if servers:
            console.print("\n[bold]Aktuelle Server:[/bold]")
            client.print_servers_table()
        
    else:
        console.print("\n[bold red]✗ Verbindung fehlgeschlagen![/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main()

