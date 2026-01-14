#!/usr/bin/env python3
"""
Löscht ALLE existierenden OpenStack Instanzen
WARNUNG: Dieses Skript löscht alle Server!
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import openstack
    from rich.console import Console
    from rich.prompt import Confirm
    from rich.table import Table
except ImportError:
    print("Bitte installiere die benötigten Pakete:")
    print("  pip install openstacksdk rich")
    sys.exit(1)

console = Console()


def main():
    console.print("[bold red]╔════════════════════════════════════════╗[/bold red]")
    console.print("[bold red]║  WARNUNG: Alle Server werden gelöscht  ║[/bold red]")
    console.print("[bold red]╚════════════════════════════════════════╝[/bold red]")
    console.print()
    
    # Verbindung herstellen
    try:
        conn = openstack.connect(cloud='openstack')
    except Exception as e:
        console.print(f"[red]Verbindungsfehler: {e}[/red]")
        sys.exit(1)
    
    # Server auflisten
    servers = list(conn.compute.servers())
    
    if not servers:
        console.print("[green]✓ Keine Server vorhanden - nichts zu löschen[/green]")
        return
    
    # Zeige was gelöscht wird
    console.print(f"\n[bold]Folgende {len(servers)} Server werden gelöscht:[/bold]\n")
    
    table = Table()
    table.add_column("ID", style="dim")
    table.add_column("Name", style="green")
    table.add_column("Status", style="yellow")
    
    for server in servers:
        table.add_row(server.id[:8] + "...", server.name, server.status)
    
    console.print(table)
    console.print()
    
    # Bestätigung
    if not Confirm.ask("[bold red]Alle oben genannten Server wirklich löschen?[/bold red]"):
        console.print("[yellow]Abgebrochen.[/yellow]")
        return
    
    # Löschen
    console.print("\n[bold]Lösche Server...[/bold]\n")
    
    deleted = 0
    failed = 0
    
    for server in servers:
        try:
            console.print(f"  Lösche [cyan]{server.name}[/cyan]...", end=" ")
            conn.compute.delete_server(server.id)
            conn.compute.wait_for_delete(server)
            console.print("[green]✓[/green]")
            deleted += 1
        except Exception as e:
            console.print(f"[red]✗ Fehler: {e}[/red]")
            failed += 1
    
    console.print()
    console.print(f"[bold green]✓ {deleted} Server gelöscht[/bold green]")
    if failed:
        console.print(f"[bold red]✗ {failed} Server konnten nicht gelöscht werden[/bold red]")
    
    console.print("\n[bold]Jetzt kannst du mit Terraform einen neuen Server erstellen:[/bold]")
    console.print("  cd terraform && make apply")


if __name__ == "__main__":
    main()

