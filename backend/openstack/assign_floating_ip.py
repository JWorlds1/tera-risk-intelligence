#!/usr/bin/env python3
"""
Weist eine Floating IP einem Server zu
"""
import sys
from pathlib import Path
from openstack import connection
from rich.console import Console
from rich.panel import Panel

console = Console()

def assign_floating_ip(server_id, pool_name=None):
    """Weist eine Floating IP dem Server zu"""
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
        # Hole Server-Informationen
        server = conn.compute.get_server(server_id)
        console.print(f"\n[bold]Server:[/bold] {server.name} ({server.id})")
        
        # Prüfe ob bereits eine Floating IP zugewiesen ist
        addresses = server.addresses or {}
        existing_floating_ip = None
        
        for network_name, addr_list in addresses.items():
            for addr in addr_list:
                if addr.get("OS-EXT-IPS:type") == "floating":
                    existing_floating_ip = addr.get("addr")
                    break
            if existing_floating_ip:
                break
        
        if existing_floating_ip:
            console.print(f"[green]✓[/green] Server hat bereits eine Floating IP: {existing_floating_ip}")
            return existing_floating_ip
        
        # Finde verfügbare Floating IPs
        console.print("\n[yellow]Suche verfügbare Floating IPs...[/yellow]")
        
        floating_ips = list(conn.network.ips(floating_ip=True))
        available_fip = None
        
        for fip in floating_ips:
            if not fip.port_id:  # Nicht zugewiesen
                available_fip = fip
                console.print(f"  [green]✓[/green] Gefunden: {fip.floating_ip_address}")
                break
        
        # Falls keine verfügbar, erstelle eine neue
        if not available_fip:
            console.print("  [yellow]Keine verfügbare Floating IP gefunden, erstelle neue...[/yellow]")
            
            # Finde externes Netzwerk
            all_networks = list(conn.network.networks())
            external_networks = []
            
            for net in all_networks:
                # Prüfe ob Netzwerk extern ist (router:external=True)
                if hasattr(net, 'router_external') and net.router_external:
                    external_networks.append(net)
                # Oder prüfe nach bekannten externen Netzwerk-Namen
                elif net.name and ('public' in net.name.lower() or 'external' in net.name.lower()):
                    external_networks.append(net)
            
            if not external_networks:
                console.print("[yellow]⚠[/yellow] Kein explizit externes Netzwerk gefunden")
                console.print("  Versuche mit 'public' Netzwerken...")
                # Versuche mit Netzwerken die "public" im Namen haben
                for net in all_networks:
                    if net.name and 'public' in net.name.lower():
                        external_networks.append(net)
            
            if not external_networks:
                console.print("[red]✗[/red] Kein externes Netzwerk gefunden")
                console.print("\n[yellow]Verfügbare Netzwerke:[/yellow]")
                for net in all_networks[:10]:
                    external_flag = "EXTERNAL" if (hasattr(net, 'router_external') and net.router_external) else ""
                    console.print(f"  - {net.name} {external_flag}")
                sys.exit(1)
            
            # Verwende das erste externe Netzwerk oder das angegebene Pool
            external_net = None
            if pool_name:
                for net in external_networks:
                    if pool_name.lower() in net.name.lower():
                        external_net = net
                        break
            
            if not external_net:
                # Bevorzuge Netzwerke mit "public" im Namen
                for net in external_networks:
                    if 'public' in net.name.lower():
                        external_net = net
                        break
                if not external_net:
                    external_net = external_networks[0]
            
            console.print(f"  Verwende Netzwerk: {external_net.name} (ID: {external_net.id[:16]}...)")
            
            # Erstelle Floating IP
            fip = conn.network.create_ip(
                floating_network_id=external_net.id
            )
            available_fip = fip
            console.print(f"  [green]✓[/green] Neue Floating IP erstellt: {fip.floating_ip_address}")
        
        # Finde Port des Servers
        console.print("\n[yellow]Suche Server-Port...[/yellow]")
        
        # Hole alle Ports des Servers
        ports = list(conn.network.ports(device_id=server.id))
        
        if not ports:
            console.print("[red]✗[/red] Kein Port für Server gefunden")
            sys.exit(1)
        
        # Verwende den ersten Port mit IPv4
        server_port = None
        for port in ports:
            fixed_ips = port.fixed_ips or []
            for fixed_ip in fixed_ips:
                if fixed_ip.get('ip_version') == 4 or ':' not in fixed_ip.get('ip_address', ''):
                    server_port = port
                    break
            if server_port:
                break
        
        if not server_port:
            server_port = ports[0]
        
        console.print(f"  [green]✓[/green] Port gefunden: {server_port.id}")
        
        # Weise Floating IP zu
        console.print(f"\n[yellow]Weise Floating IP zu...[/yellow]")
        console.print(f"  Floating IP: {available_fip.floating_ip_address}")
        console.print(f"  Port: {server_port.id}")
        
        conn.network.update_ip(
            available_fip.id,
            port_id=server_port.id
        )
        
        console.print(f"[green]✓[/green] Floating IP erfolgreich zugewiesen!")
        
        # Warte kurz und hole aktualisierte Server-Informationen
        import time
        time.sleep(2)
        
        server = conn.compute.get_server(server_id)
        addresses = server.addresses or {}
        
        floating_ip = None
        for network_name, addr_list in addresses.items():
            for addr in addr_list:
                if addr.get("OS-EXT-IPS:type") == "floating":
                    floating_ip = addr.get("addr")
                    break
            if floating_ip:
                break
        
        console.print("\n" + "=" * 60)
        console.print(Panel.fit(
            f"[bold green]✓ Floating IP zugewiesen![/bold green]\n"
            f"Public IP: {floating_ip}",
            border_style="green"
        ))
        console.print("=" * 60)
        
        console.print(f"\n[bold]SSH-Zugriff:[/bold]")
        console.print(f"  ssh ubuntu@{floating_ip}")
        
        return floating_ip
        
    except Exception as e:
        console.print(f"[red]✗[/red] Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    server_id = "e73e74c7-4648-4c91-9811-2bcc7a748a88"
    pool_name = None
    
    if len(sys.argv) > 1:
        server_id = sys.argv[1]
    if len(sys.argv) > 2:
        pool_name = sys.argv[2]
    
    assign_floating_ip(server_id, pool_name)

