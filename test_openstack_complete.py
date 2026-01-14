#!/usr/bin/env python3
"""
Vollständiger OpenStack Test - versucht alles bis es funktioniert
"""
import sys
import yaml
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def test_config_file():
    """Testet ob die Konfigurationsdatei existiert und gültig ist"""
    console.print("\n[bold cyan]1. Prüfe Konfigurationsdatei...[/bold cyan]")
    
    config_path = Path.home() / ".config" / "openstack" / "clouds.yaml"
    
    if not config_path.exists():
        console.print(f"[red]✗[/red] Konfiguration nicht gefunden: {config_path}")
        return None
    
    console.print(f"[green]✓[/green] Konfiguration gefunden: {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if not config or "clouds" not in config:
            console.print("[red]✗[/red] Ungültige Konfiguration")
            return None
        
        cloud_name = list(config["clouds"].keys())[0]
        cloud = config["clouds"][cloud_name]
        
        console.print(f"[green]✓[/green] Cloud Name: {cloud_name}")
        console.print(f"[green]✓[/green] Auth URL: {cloud.get('auth', {}).get('auth_url', 'N/A')}")
        console.print(f"[green]✓[/green] Region: {cloud.get('region_name', 'N/A')}")
        
        return config
    except Exception as e:
        console.print(f"[red]✗[/red] Fehler beim Laden: {e}")
        return None

def test_imports():
    """Testet ob alle benötigten Module verfügbar sind"""
    console.print("\n[bold cyan]2. Prüfe Python-Module...[/bold cyan]")
    
    try:
        from openstack import connection
        console.print("[green]✓[/green] openstacksdk installiert")
    except ImportError:
        console.print("[red]✗[/red] openstacksdk nicht installiert")
        console.print("[yellow]Installiere mit: pip install openstacksdk[/yellow]")
        return False
    
    try:
        from rich import console as rich_console
        console.print("[green]✓[/green] rich installiert")
    except ImportError:
        console.print("[yellow]⚠[/yellow] rich nicht installiert (optional)")
    
    return True

def test_connection_method1():
    """Test 1: Standard Connection"""
    console.print("\n[bold cyan]3. Teste Verbindung (Methode 1: Standard)...[/bold cyan]")
    
    try:
        from openstack import connection
        
        conn = connection.Connection(
            cloud='openstack',
            config_dir=str(Path.home() / ".config" / "openstack")
        )
        
        console.print("[yellow]Versuche Authorization...[/yellow]")
        conn.authorize()
        console.print("[green]✓[/green] Verbindung erfolgreich!")
        return conn
    except Exception as e:
        console.print(f"[red]✗[/red] Fehler: {str(e)[:100]}")
        return None

def test_connection_method2():
    """Test 2: Direkte Parameter"""
    console.print("\n[bold cyan]4. Teste Verbindung (Methode 2: Direkte Parameter)...[/bold cyan]")
    
    try:
        from openstack import connection
        
        # Lade Config
        config_path = Path.home() / ".config" / "openstack" / "clouds.yaml"
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        cloud = config["clouds"]["openstack"]
        auth = cloud["auth"]
        
        conn = connection.Connection(
            auth_url=auth["auth_url"],
            application_credential_id=auth["application_credential_id"],
            application_credential_secret=auth["application_credential_secret"],
            region_name=cloud["region_name"],
            interface=cloud["interface"],
            identity_api_version=cloud.get("identity_api_version", 3),
            auth_type=cloud.get("auth_type", "v3applicationcredential")
        )
        
        console.print("[yellow]Versuche Authorization...[/yellow]")
        conn.authorize()
        console.print("[green]✓[/green] Verbindung erfolgreich!")
        return conn
    except Exception as e:
        console.print(f"[red]✗[/red] Fehler: {str(e)[:100]}")
        return None

def test_services(conn):
    """Testet alle verfügbaren Services"""
    console.print("\n[bold cyan]5. Teste OpenStack Services...[/bold cyan]")
    
    results = {}
    
    # Compute Service
    try:
        servers = list(conn.compute.servers())
        results['compute'] = {'status': 'ok', 'count': len(servers)}
        console.print(f"[green]✓[/green] Compute Service: {len(servers)} Server")
    except Exception as e:
        results['compute'] = {'status': 'error', 'error': str(e)}
        console.print(f"[red]✗[/red] Compute Service: {str(e)[:50]}")
    
    # Image Service
    try:
        images = list(conn.compute.images())
        results['image'] = {'status': 'ok', 'count': len(images)}
        console.print(f"[green]✓[/green] Image Service: {len(images)} Images")
    except Exception as e:
        results['image'] = {'status': 'error', 'error': str(e)}
        console.print(f"[yellow]⚠[/yellow] Image Service: {str(e)[:50]}")
    
    # Network Service
    try:
        networks = list(conn.network.networks())
        results['network'] = {'status': 'ok', 'count': len(networks)}
        console.print(f"[green]✓[/green] Network Service: {len(networks)} Networks")
    except Exception as e:
        results['network'] = {'status': 'error', 'error': str(e)}
        console.print(f"[yellow]⚠[/yellow] Network Service: {str(e)[:50]}")
    
    # Flavors
    try:
        flavors = list(conn.compute.flavors())
        results['flavors'] = {'status': 'ok', 'count': len(flavors)}
        console.print(f"[green]✓[/green] Flavors: {len(flavors)} verfügbar")
    except Exception as e:
        results['flavors'] = {'status': 'error', 'error': str(e)}
        console.print(f"[yellow]⚠[/yellow] Flavors: {str(e)[:50]}")
    
    return results

def show_servers(conn):
    """Zeigt alle Server in einer Tabelle"""
    try:
        servers = list(conn.compute.servers())
        
        if not servers:
            console.print("\n[yellow]Keine Server gefunden[/yellow]")
            return
        
        table = Table(title="OpenStack Server")
        table.add_column("ID", style="cyan", no_wrap=False)
        table.add_column("Name", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("IP Address", style="magenta")
        
        for server in servers:
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
                server.id[:16] + "...",
                server.name,
                server.status,
                ip or "N/A"
            )
        
        console.print("\n")
        console.print(table)
    except Exception as e:
        console.print(f"[red]Fehler beim Anzeigen der Server: {e}[/red]")

def main():
    console.print(Panel.fit(
        "[bold cyan]OpenStack Vollständiger Verbindungstest[/bold cyan]\n"
        "Testet alle Methoden bis eine funktioniert",
        border_style="cyan"
    ))
    
    # Test 1: Config Datei
    config = test_config_file()
    if not config:
        console.print("\n[bold red]✗ Konfiguration fehlt oder ist ungültig![/bold red]")
        sys.exit(1)
    
    # Test 2: Imports
    if not test_imports():
        console.print("\n[bold red]✗ Benötigte Module fehlen![/bold red]")
        sys.exit(1)
    
    # Test 3: Verbindung Methode 1
    conn = test_connection_method1()
    
    # Test 4: Verbindung Methode 2 (falls Methode 1 fehlschlägt)
    if not conn:
        console.print("\n[yellow]Versuche alternative Methode...[/yellow]")
        conn = test_connection_method2()
    
    if not conn:
        console.print("\n[bold red]✗ Alle Verbindungsversuche fehlgeschlagen![/bold red]")
        console.print("\n[yellow]Mögliche Lösungen:[/yellow]")
        console.print("1. Prüfen Sie Ihre VPN-Verbindung")
        console.print("2. Prüfen Sie die Application Credentials")
        console.print("3. Prüfen Sie die Auth URL")
        sys.exit(1)
    
    # Test 5: Services
    results = test_services(conn)
    
    # Zeige Server
    show_servers(conn)
    
    # Zusammenfassung
    console.print("\n" + "=" * 60)
    console.print("[bold green]✓ Verbindungstest erfolgreich abgeschlossen![/bold green]")
    console.print("=" * 60)
    
    console.print("\n[bold]Zusammenfassung:[/bold]")
    for service, result in results.items():
        if result['status'] == 'ok':
            console.print(f"  [green]✓[/green] {service}: {result['count']} gefunden")
        else:
            console.print(f"  [red]✗[/red] {service}: {result.get('error', 'Fehler')[:50]}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Abgebrochen vom Benutzer[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Unerwarteter Fehler:[/bold red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

