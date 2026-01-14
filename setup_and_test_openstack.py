#!/usr/bin/env python3
"""
Setup und Test der OpenStack Verbindung
"""
import yaml
import os
from pathlib import Path
import sys

def create_config():
    """Erstellt die OpenStack Konfiguration"""
    config = {
        "clouds": {
            "openstack": {
                "auth": {
                    "auth_url": "https://h-da.cloud:13000",
                    "application_credential_id": "ba44dda4814e443faba80ae101d704a8",
                    "application_credential_secret": "Wesen"
                },
                "region_name": "eu-central",
                "interface": "public",
                "identity_api_version": 3,
                "auth_type": "v3applicationcredential"
            }
        }
    }
    
    config_dir = Path.home() / ".config" / "openstack"
    config_dir.mkdir(parents=True, exist_ok=True)
    clouds_yaml = config_dir / "clouds.yaml"
    
    with open(clouds_yaml, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"✓ Konfiguration erstellt: {clouds_yaml}")
    return True

def test_connection():
    """Testet die OpenStack Verbindung"""
    try:
        from openstack import connection
        from rich.console import Console
        from rich.table import Table
        
        console = Console()
        
        console.print("\n[bold cyan]OpenStack Verbindungstest[/bold cyan]")
        console.print("=" * 60)
        
        console.print("\n[yellow]Stelle Verbindung zu h-da.cloud her...[/yellow]")
        
        conn = connection.Connection(
            cloud='openstack',
            config_dir=str(Path.home() / ".config" / "openstack")
        )
        
        # Teste Verbindung
        conn.authorize()
        console.print("[green]✓[/green] Verbindung erfolgreich!")
        
        # Liste Server
        try:
            servers = list(conn.compute.servers())
            console.print(f"\n[bold]Server:[/bold] {len(servers)} gefunden")
            
            if servers:
                table = Table(title="Server")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="green")
                table.add_column("Status", style="yellow")
                table.add_column("IP", style="magenta")
                
                for server in servers[:20]:
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
        except Exception as e:
            console.print(f"[yellow]Server-Liste Fehler: {e}[/yellow]")
        
        # Liste Images
        try:
            images = list(conn.compute.images())
            console.print(f"\n[bold]Images:[/bold] {len(images)} gefunden")
        except Exception as e:
            console.print(f"[yellow]Images Fehler: {e}[/yellow]")
        
        # Liste Flavors
        try:
            flavors = list(conn.compute.flavors())
            console.print(f"\n[bold]Flavors:[/bold] {len(flavors)} gefunden")
            
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
            console.print(f"[yellow]Flavors Fehler: {e}[/yellow]")
        
        console.print("\n[bold green]✓ Verbindungstest erfolgreich![/bold green]")
        return True
        
    except ImportError:
        print("❌ openstacksdk nicht installiert. Installiere mit: pip install openstacksdk")
        return False
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("OpenStack Setup und Test")
    print("=" * 60)
    
    # Erstelle Konfiguration
    if create_config():
        print("\n" + "=" * 60)
        # Teste Verbindung
        if test_connection():
            print("\n[bold green]✓ Alles erfolgreich![/bold green]")
            sys.exit(0)
        else:
            print("\n[bold red]✗ Verbindungstest fehlgeschlagen[/bold red]")
            sys.exit(1)
    else:
        print("\n[bold red]✗ Konfiguration fehlgeschlagen[/bold red]")
        sys.exit(1)

