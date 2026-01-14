#!/usr/bin/env python3
"""
Liste OpenStack Ressourcen
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from openstack.client import OpenStackClient
from rich.console import Console
from rich.table import Table

console = Console()


def main():
    """Listet alle OpenStack Ressourcen auf"""
    cloud_name = sys.argv[1] if len(sys.argv) > 1 else "hda-cloud"
    
    client = OpenStackClient(cloud_name=cloud_name)
    
    if not client.connect():
        console.print("[red]✗[/red] Verbindung fehlgeschlagen!")
        sys.exit(1)
    
    # Server
    console.print("\n[bold cyan]Server[/bold cyan]")
    servers = client.list_servers(detailed=True)
    if servers:
        client.print_servers_table(servers)
    else:
        console.print("[yellow]Keine Server gefunden[/yellow]")
    
    # Images
    console.print("\n[bold cyan]Images[/bold cyan]")
    images = client.list_images()
    if images:
        table = Table()
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Status", style="yellow")
        for img in images:
            table.add_row(img["id"][:8] + "...", img["name"], img["status"])
        console.print(table)
    else:
        console.print("[yellow]Keine Images gefunden[/yellow]")
    
    # Flavors
    console.print("\n[bold cyan]Flavors[/bold cyan]")
    flavors = client.list_flavors()
    if flavors:
        table = Table()
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("vCPUs", style="yellow")
        table.add_column("RAM (MB)", style="magenta")
        table.add_column("Disk (GB)", style="blue")
        for flv in flavors:
            table.add_row(
                flv["id"][:8] + "...",
                flv["name"],
                str(flv["vcpus"]),
                str(flv["ram"]),
                str(flv["disk"])
            )
        console.print(table)
    else:
        console.print("[yellow]Keine Flavors gefunden[/yellow]")
    
    # Networks
    console.print("\n[bold cyan]Networks[/bold cyan]")
    networks = client.list_networks()
    if networks:
        table = Table()
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Status", style="yellow")
        for net in networks:
            table.add_row(net["id"][:8] + "...", net["name"], net["status"])
        console.print(table)
    else:
        console.print("[yellow]Keine Networks gefunden[/yellow]")
    
    # Security Groups
    console.print("\n[bold cyan]Security Groups[/bold cyan]")
    sec_groups = client.list_security_groups()
    if sec_groups:
        table = Table()
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Description", style="yellow")
        for sg in sec_groups:
            table.add_row(
                sg["id"][:8] + "...",
                sg["name"],
                sg.get("description", "")[:50]
            )
        console.print(table)
    else:
        console.print("[yellow]Keine Security Groups gefunden[/yellow]")


if __name__ == "__main__":
    main()

