#!/usr/bin/env python3
"""Direkter Test der OpenStack Verbindung"""
import sys
from pathlib import Path

# Füge backend zum Pfad hinzu, aber importiere openstack SDK direkt
sys.path.insert(0, str(Path(__file__).parent))

try:
    from openstack import connection
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    console.print("\n[bold cyan]OpenStack Verbindungstest[/bold cyan]")
    console.print("=" * 60)
    
    # Verbindung herstellen
    console.print("\n[yellow]Stelle Verbindung her...[/yellow]")
    
    conn = connection.Connection(
        cloud='openstack',  # Cloud Name aus clouds.yaml
        config_dir=str(Path.home() / ".config" / "openstack")
    )
    
    # Teste Verbindung durch Authorization
    conn.authorize()
    console.print("[green]✓[/green] Verbindung erfolgreich!")
    
    # Teste verschiedene Services
    console.print("\n[bold]Teste verfügbare Services...[/bold]")
    
    # Compute (Nova)
    try:
        servers = list(conn.compute.servers())
        console.print(f"  [green]✓[/green] Compute Service: {len(servers)} Server gefunden")
        
        if servers:
            table = Table(title="Server")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Status", style="yellow")
            
            for server in servers[:10]:  # Zeige max 10
                table.add_row(
                    server.id[:8] + "...",
                    server.name,
                    server.status
                )
            console.print(table)
    except Exception as e:
        console.print(f"  [red]✗[/red] Compute Service Fehler: {e}")
    
    # Image (Glance)
    try:
        images = list(conn.compute.images())
        console.print(f"  [green]✓[/green] Image Service: {len(images)} Images gefunden")
    except Exception as e:
        console.print(f"  [red]✗[/red] Image Service Fehler: {e}")
    
    # Network (Neutron)
    try:
        networks = list(conn.network.networks())
        console.print(f"  [green]✓[/green] Network Service: {len(networks)} Networks gefunden")
    except Exception as e:
        console.print(f"  [red]✗[/red] Network Service Fehler: {e}")
    
    # Flavors
    try:
        flavors = list(conn.compute.flavors())
        console.print(f"  [green]✓[/green] Flavors: {len(flavors)} Flavors gefunden")
        
        if flavors:
            table = Table(title="Flavors")
            table.add_column("Name", style="green")
            table.add_column("vCPUs", style="yellow")
            table.add_column("RAM (MB)", style="magenta")
            table.add_column("Disk (GB)", style="blue")
            
            for flavor in flavors[:10]:
                table.add_row(
                    flavor.name,
                    str(flavor.vcpus),
                    str(flavor.ram),
                    str(flavor.disk)
                )
            console.print(table)
    except Exception as e:
        console.print(f"  [red]✗[/red] Flavors Fehler: {e}")
    
    console.print("\n[bold green]✓ Verbindungstest abgeschlossen![/bold green]")
    
except ImportError as e:
    print(f"❌ Import Fehler: {e}")
    print("Stelle sicher, dass openstacksdk installiert ist: pip install openstacksdk")
    sys.exit(1)
except Exception as e:
    print(f"❌ Fehler: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

