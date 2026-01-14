#!/usr/bin/env python3
"""
OpenStack Ressourcen auflisten - für Terraform Konfiguration
Zeigt alle verfügbaren Images, Flavors, Networks etc.
"""

import sys
from pathlib import Path

# Backend-Pfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import openstack
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
except ImportError:
    print("Bitte installiere die benötigten Pakete:")
    print("  pip install openstacksdk rich")
    sys.exit(1)

console = Console()


def get_connection():
    """Erstellt OpenStack-Verbindung aus clouds.yaml"""
    try:
        conn = openstack.connect(cloud='openstack')
        return conn
    except Exception as e:
        console.print(f"[red]Fehler beim Verbinden: {e}[/red]")
        console.print("\nStelle sicher, dass ~/.config/openstack/clouds.yaml existiert")
        return None


def list_servers(conn):
    """Listet alle Server auf"""
    console.print("\n[bold cyan]═══ VORHANDENE SERVER (Instanzen) ═══[/bold cyan]\n")
    
    servers = list(conn.compute.servers())
    
    if not servers:
        console.print("[yellow]Keine Server gefunden[/yellow]")
        return
    
    table = Table(title="Aktuelle Server")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("IP", style="cyan")
    table.add_column("Flavor", style="magenta")
    
    for server in servers:
        # IP extrahieren
        ip = ""
        if server.addresses:
            for net, addrs in server.addresses.items():
                for addr in addrs:
                    if addr.get('version') == 4:
                        ip = addr.get('addr', '')
                        break
        
        table.add_row(
            server.id[:8] + "...",
            server.name,
            server.status,
            ip,
            server.flavor.get('original_name', '') if server.flavor else ''
        )
    
    console.print(table)
    console.print(f"\n[bold]Gesamt: {len(servers)} Server[/bold]")


def list_images(conn):
    """Listet alle verfügbaren Images auf"""
    console.print("\n[bold cyan]═══ VERFÜGBARE IMAGES ═══[/bold cyan]\n")
    
    images = list(conn.image.images())
    
    if not images:
        console.print("[yellow]Keine Images gefunden[/yellow]")
        return
    
    table = Table(title="Betriebssystem Images")
    table.add_column("Name", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Größe", style="cyan")
    table.add_column("ID", style="dim")
    
    for img in sorted(images, key=lambda x: x.name or ''):
        size_mb = f"{(img.size or 0) / 1024 / 1024:.0f} MB" if img.size else "N/A"
        table.add_row(
            img.name or '',
            img.status or '',
            size_mb,
            img.id[:12] + "..."
        )
    
    console.print(table)
    
    # Empfehlungen
    console.print("\n[bold green]✓ Empfohlene Images für Terraform:[/bold green]")
    for img in images:
        if img.name and 'ubuntu' in img.name.lower():
            console.print(f"  • image_name = \"{img.name}\"")


def list_flavors(conn):
    """Listet alle verfügbaren Flavors auf"""
    console.print("\n[bold cyan]═══ VERFÜGBARE FLAVORS (Server-Größen) ═══[/bold cyan]\n")
    
    flavors = list(conn.compute.flavors())
    
    if not flavors:
        console.print("[yellow]Keine Flavors gefunden[/yellow]")
        return
    
    table = Table(title="Server Konfigurationen")
    table.add_column("Name", style="green")
    table.add_column("vCPUs", style="cyan", justify="right")
    table.add_column("RAM", style="magenta", justify="right")
    table.add_column("Disk", style="yellow", justify="right")
    table.add_column("ID", style="dim")
    
    for flv in sorted(flavors, key=lambda x: (x.vcpus or 0, x.ram or 0)):
        ram_gb = f"{(flv.ram or 0) / 1024:.1f} GB" if flv.ram else "N/A"
        disk = f"{flv.disk or 0} GB"
        table.add_row(
            flv.name or '',
            str(flv.vcpus or 0),
            ram_gb,
            disk,
            flv.id[:12] + "..."
        )
    
    console.print(table)
    
    # Empfehlungen
    console.print("\n[bold green]✓ Empfohlene Flavors für Terraform:[/bold green]")
    for flv in flavors:
        if flv.name and 'small' in flv.name.lower():
            console.print(f"  • flavor_name = \"{flv.name}\" (Basis)")
        elif flv.name and 'medium' in flv.name.lower():
            console.print(f"  • flavor_name = \"{flv.name}\" (Standard)")
        elif flv.name and 'large' in flv.name.lower():
            console.print(f"  • flavor_name = \"{flv.name}\" (Leistung)")


def list_networks(conn):
    """Listet alle verfügbaren Networks auf"""
    console.print("\n[bold cyan]═══ VERFÜGBARE NETZWERKE ═══[/bold cyan]\n")
    
    networks = list(conn.network.networks())
    
    if not networks:
        console.print("[yellow]Keine Netzwerke gefunden[/yellow]")
        return
    
    table = Table(title="Netzwerke")
    table.add_column("Name", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Extern", style="cyan")
    table.add_column("Subnets", style="magenta")
    table.add_column("ID", style="dim")
    
    for net in networks:
        is_external = "✓" if net.is_router_external else ""
        subnets = len(net.subnet_ids) if net.subnet_ids else 0
        table.add_row(
            net.name or '',
            net.status or '',
            is_external,
            str(subnets),
            net.id[:12] + "..."
        )
    
    console.print(table)
    
    # Empfehlungen
    console.print("\n[bold green]✓ Empfohlene Netzwerke für Terraform:[/bold green]")
    for net in networks:
        if net.name and not net.is_router_external:
            console.print(f"  • network_name = \"{net.name}\" (privat)")
        if net.name and net.is_router_external:
            console.print(f"  • floating_ip_pool = \"{net.name}\" (für öffentliche IP)")


def list_keypairs(conn):
    """Listet alle SSH Keypairs auf"""
    console.print("\n[bold cyan]═══ SSH KEYPAIRS ═══[/bold cyan]\n")
    
    keypairs = list(conn.compute.keypairs())
    
    if not keypairs:
        console.print("[yellow]Keine Keypairs gefunden - Terraform wird einen neuen erstellen[/yellow]")
        return
    
    table = Table(title="SSH Schlüssel")
    table.add_column("Name", style="green")
    table.add_column("Fingerprint", style="cyan")
    
    for kp in keypairs:
        table.add_row(kp.name or '', kp.fingerprint or '')
    
    console.print(table)


def list_security_groups(conn):
    """Listet alle Security Groups auf"""
    console.print("\n[bold cyan]═══ SECURITY GROUPS ═══[/bold cyan]\n")
    
    sec_groups = list(conn.network.security_groups())
    
    if not sec_groups:
        console.print("[yellow]Keine Security Groups gefunden[/yellow]")
        return
    
    table = Table(title="Security Groups")
    table.add_column("Name", style="green")
    table.add_column("Beschreibung", style="yellow")
    table.add_column("Regeln", style="cyan", justify="right")
    
    for sg in sec_groups:
        rules_count = len(sg.security_group_rules) if sg.security_group_rules else 0
        table.add_row(
            sg.name or '',
            (sg.description or '')[:40],
            str(rules_count)
        )
    
    console.print(table)


def generate_terraform_config(conn):
    """Generiert Terraform Konfigurations-Empfehlungen"""
    console.print("\n[bold cyan]═══ TERRAFORM KONFIGURATION ═══[/bold cyan]\n")
    
    # Sammle Daten
    images = list(conn.image.images())
    flavors = list(conn.compute.flavors())
    networks = list(conn.network.networks())
    
    # Finde beste Optionen
    ubuntu_image = next((i for i in images if i.name and 'ubuntu' in i.name.lower() and '22' in i.name), None)
    small_flavor = next((f for f in flavors if f.name and 'small' in f.name.lower()), None)
    private_network = next((n for n in networks if n.name and not n.is_router_external), None)
    public_network = next((n for n in networks if n.name and n.is_router_external), None)
    
    config = f'''# Empfohlene terraform.tfvars Konfiguration:
# ==========================================

# Image
image_name = "{ubuntu_image.name if ubuntu_image else 'Ubuntu 22.04'}"

# Flavor (Server-Größe)
flavor_name = "{small_flavor.name if small_flavor else 'm1.small'}"

# Netzwerk
network_name = "{private_network.name if private_network else 'private-network'}"

# Floating IP Pool
floating_ip_pool = "{public_network.name if public_network else 'public'}"
'''
    
    panel = Panel(config, title="terraform.tfvars", border_style="green")
    console.print(panel)


def main():
    console.print(Panel.fit(
        "[bold]OpenStack Ressourcen Scanner[/bold]\n"
        "Für Terraform Konfiguration",
        border_style="cyan"
    ))
    
    conn = get_connection()
    if not conn:
        sys.exit(1)
    
    try:
        list_servers(conn)
        list_images(conn)
        list_flavors(conn)
        list_networks(conn)
        list_keypairs(conn)
        list_security_groups(conn)
        generate_terraform_config(conn)
        
        console.print("\n[bold green]✓ Scan abgeschlossen![/bold green]")
        console.print("\nNächste Schritte:")
        console.print("  1. Kopiere terraform.tfvars.example zu terraform.tfvars")
        console.print("  2. Passe die Werte basierend auf obigen Empfehlungen an")
        console.print("  3. Führe 'make apply' aus um den Server zu erstellen")
        
    except Exception as e:
        console.print(f"[red]Fehler: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()

