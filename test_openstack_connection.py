#!/usr/bin/env python3
"""Testet OpenStack Verbindung mit korrekter Konfiguration"""
import sys
from pathlib import Path

try:
    from openstack import connection
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    console.print("\n[bold cyan]OpenStack Verbindungstest[/bold cyan]")
    console.print("=" * 60)
    
    # Verbindung herstellen
    console.print("\n[yellow]Stelle Verbindung zu h-da.cloud her...[/yellow]")
    
    conn = connection.Connection(
        cloud='openstack',  # Cloud Name aus clouds.yaml
        config_dir=str(Path.home() / ".config" / "openstack")
    )
    
    # Teste Verbindung durch Authorization
    conn.authorize()
    console.print("[green]✓[/green] Verbindung erfolgreich!")
    
    # Teste verschiedene Services
    console.print("\n[bold]Teste verfügbare Services...[/bold]")
    
    # Compute (Nova) - Server
    try:
        servers = list(conn.compute.servers())
        console.print(f"  [green]✓[/green] Compute Service: {len(servers)} Server gefunden")
        
        if servers:
            table = Table(title="Server")
            table.add_column("ID", style="cyan", no_wrap=False)
            table.add_column("Name", style="green")
            table.add_column("Status", style="yellow")
            table.add_column("IP", style="magenta")
            
            for server in servers[:20]:  # Zeige max 20
                # Extrahiere IP-Adresse
                ip = ""
                try:
                    addresses = server.addresses or {}
                    for network_name, addr_list in addresses.items():
                        if addr_list:
                            for addr in addr_list:
                                if addr.get("version") == 4:
                                    ip = addr.get("addr", "")
                                    break
                            if ip:
                                break
                except:
                    pass
                
                table.add_row(
                    server.id[:12] + "...",
                    server.name,
                    server.status,
                    ip or "N/A"
                )
            console.print(table)
        else:
            console.print("  [yellow]Keine Server vorhanden[/yellow]")
    except Exception as e:
        console.print(f"  [red]✗[/red] Compute Service Fehler: {e}")
    
    # Image (Glance)
    try:
        images = list(conn.compute.images())
        console.print(f"\n  [green]✓[/green] Image Service: {len(images)} Images gefunden")
        
        if images:
            table = Table(title="Images")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Status", style="yellow")
            
            for img in images[:10]:
                table.add_row(
                    img.id[:12] + "...",
                    img.name,
                    img.status
                )
            console.print(table)
    except Exception as e:
        console.print(f"  [red]✗[/red] Image Service Fehler: {e}")
    
    # Flavors
    try:
        flavors = list(conn.compute.flavors())
        console.print(f"\n  [green]✓[/green] Flavors: {len(flavors)} Flavors gefunden")
        
        if flavors:
            table = Table(title="Flavors")
            table.add_column("Name", style="green")
            table.add_column("vCPUs", style="yellow")
            table.add_column("RAM (MB)", style="magenta")
            table.add_column("Disk (GB)", style="blue")
            
            for flavor in flavors[:15]:
                table.add_row(
                    flavor.name,
                    str(flavor.vcpus),
                    str(flavor.ram),
                    str(flavor.disk)
                )
            console.print(table)
    except Exception as e:
        console.print(f"  [red]✗[/red] Flavors Fehler: {e}")
    
    # Network (Neutron)
    try:
        networks = list(conn.network.networks())
        console.print(f"\n  [green]✓[/green] Network Service: {len(networks)} Networks gefunden")
        
        if networks:
            table = Table(title="Networks")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Status", style="yellow")
            
            for net in networks[:10]:
                table.add_row(
                    net.id[:12] + "...",
                    net.name,
                    net.status
                )
            console.print(table)
    except Exception as e:
        console.print(f"  [red]✗[/red] Network Service Fehler: {e}")
    
    # Security Groups
    try:
        sec_groups = list(conn.network.security_groups())
        console.print(f"\n  [green]✓[/green] Security Groups: {len(sec_groups)} gefunden")
    except Exception as e:
        console.print(f"  [red]✗[/red] Security Groups Fehler: {e}")
    
    console.print("\n[bold green]✓ Verbindungstest erfolgreich abgeschlossen![/bold green]")
    console.print("\n[bold]Sie können jetzt OpenStack verwenden![/bold]")
    
except ImportError as e:
    print(f"❌ Import Fehler: {e}")
    print("Stelle sicher, dass openstacksdk installiert ist: pip install openstacksdk")
    sys.exit(1)
except Exception as e:
    print(f"❌ Fehler: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

