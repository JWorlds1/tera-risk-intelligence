#!/usr/bin/env python3
"""
Prüft Server-Status und IP-Adressen
"""
import sys
from pathlib import Path
from openstack import connection
from rich.console import Console
from rich.table import Table

console = Console()

def check_server(server_id):
    """Prüft Server-Status und zeigt alle IP-Adressen"""
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
        server = conn.compute.get_server(server_id)
        
        console.print(f"\n[bold]Server Details:[/bold]")
        console.print(f"  ID: {server.id}")
        console.print(f"  Name: {server.name}")
        console.print(f"  Status: {server.status}")
        console.print(f"  Power State: {server.power_state}")
        
        # Zeige alle IP-Adressen
        console.print(f"\n[bold]IP-Adressen:[/bold]")
        addresses = server.addresses or {}
        
        table = Table()
        table.add_column("Network", style="cyan")
        table.add_column("IP-Adresse", style="green")
        table.add_column("Version", style="yellow")
        table.add_column("Type", style="magenta")
        
        floating_ips = []
        private_ips = []
        
        for network_name, addr_list in addresses.items():
            for addr in addr_list:
                ip = addr.get("addr", "")
                version = addr.get("version", "?")
                addr_type = addr.get("OS-EXT-IPS:type", "fixed")
                
                table.add_row(
                    network_name,
                    ip,
                    f"IPv{version}",
                    addr_type
                )
                
                if addr_type == "floating":
                    floating_ips.append(ip)
                elif version == 4:
                    private_ips.append(ip)
        
        console.print(table)
        
        # Prüfe Floating IPs
        console.print(f"\n[bold]Floating IPs:[/bold]")
        try:
            floating_ip_list = list(conn.network.ips(floating_ip=True))
            server_floating_ips = [ip for ip in floating_ip_list if ip.port_id]
            
            if server_floating_ips:
                for fip in server_floating_ips:
                    console.print(f"  [green]✓[/green] {fip.floating_ip_address} (Port: {fip.port_id})")
            else:
                console.print("  [yellow]⚠[/yellow] Keine Floating IP zugewiesen")
                console.print("  [dim]Hinweis: Private IPs sind nur innerhalb des Netzwerks erreichbar[/dim]")
        except Exception as e:
            console.print(f"  [yellow]⚠[/yellow] Konnte Floating IPs nicht abrufen: {e}")
        
        # Zeige verfügbare Floating IP Pools
        console.print(f"\n[bold]Verfügbare Floating IP Pools:[/bold]")
        try:
            pools = list(conn.network.ip_availability_groups())
            if pools:
                for pool in pools[:5]:
                    console.print(f"  - {pool.name if hasattr(pool, 'name') else pool.id}")
        except:
            try:
                # Alternative Methode
                pools = list(conn.network.networks(router_external=True))
                if pools:
                    for pool in pools[:5]:
                        console.print(f"  - {pool.name}")
            except Exception as e:
                console.print(f"  [dim]Konnte Pools nicht abrufen: {e}[/dim]")
        
        # SSH-Zugriff
        console.print(f"\n[bold]SSH-Zugriff:[/bold]")
        if floating_ips:
            console.print(f"  [green]Public IP verfügbar:[/green]")
            for fip in floating_ips:
                console.print(f"    ssh ubuntu@{fip}")
        elif private_ips:
            console.print(f"  [yellow]Nur private IP verfügbar:[/yellow]")
            for ip in private_ips:
                console.print(f"    ssh ubuntu@{ip}  [dim](nur innerhalb des Netzwerks)[/dim]")
            console.print(f"\n  [cyan]Hinweis:[/cyan] Für externen Zugriff benötigen Sie:")
            console.print(f"    1. Eine Floating IP zuweisen")
            console.print(f"    2. Oder Zugriff über VPN/Jump-Host")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    server_id = "e73e74c7-4648-4c91-9811-2bcc7a748a88"
    if len(sys.argv) > 1:
        server_id = sys.argv[1]
    
    check_server(server_id)

