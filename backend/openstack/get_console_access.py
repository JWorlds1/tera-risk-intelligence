#!/usr/bin/env python3
"""
Versucht Console-Zugriff auf den Server zu bekommen
"""
import sys
from pathlib import Path
from openstack import connection
from rich.console import Console
from rich.panel import Panel

console = Console()

def get_console_access(server_id):
    """Versucht verschiedene Console-Zugriffs-Methoden"""
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
        console.print(f"\n[bold]Server:[/bold] {server.name}")
        
        # Versuche verschiedene Console-Typen
        console_types = ['novnc', 'xvpvnc', 'spice-html5', 'rdp-html5', 'serial']
        
        console.print("\n[yellow]Versuche Console-Zugriff...[/yellow]")
        
        for console_type in console_types:
            try:
                console_obj = conn.compute.create_server_console(
                    server.id,
                    type=console_type
                )
                if console_obj:
                    console_url = console_obj.url if hasattr(console_obj, 'url') else str(console_obj)
                    console.print(f"\n[green]✓[/green] Console-Zugriff verfügbar ({console_type}):")
                    console.print(f"  {console_url}")
                    return console_url
            except Exception as e:
                console.print(f"  [dim]{console_type}: Nicht verfügbar[/dim]")
                continue
        
        # Alternative: Versuche VNC-URL direkt
        try:
            # Hole Server-Details mit allen Attributen
            server_full = conn.compute.get_server(server_id)
            
            # Prüfe ob Console-Informationen im Server-Objekt sind
            if hasattr(server_full, 'console'):
                console.print(f"\n[green]✓[/green] Console-Info gefunden:")
                console.print(f"  {server_full.console}")
        except:
            pass
        
        console.print("\n[yellow]⚠[/yellow] Kein Console-Zugriff verfügbar")
        console.print("\n[bold cyan]Alternative Lösungen:[/bold cyan]")
        console.print("1. SSH-Key über user_data hinzufügen (benötigt Server-Neustart)")
        console.print("2. Passwort-Login aktivieren (benötigt Server-Neustart)")
        console.print("3. Server neu erstellen mit SSH-Key")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    server_id = "e73e74c7-4648-4c91-9811-2bcc7a748a88"
    if len(sys.argv) > 1:
        server_id = sys.argv[1]
    
    get_console_access(server_id)

