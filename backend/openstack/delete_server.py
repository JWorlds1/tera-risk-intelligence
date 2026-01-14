#!/usr/bin/env python3
"""
Löscht einen OpenStack Server
"""
import sys
from pathlib import Path
from openstack import connection
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
import time

console = Console()

def delete_server(server_id):
    """Löscht einen Server"""
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
        
        console.print("\n[bold]Server-Informationen:[/bold]")
        console.print(f"  Name: {server.name}")
        console.print(f"  ID: {server.id}")
        console.print(f"  Status: {server.status}")
        
        # Zeige IP-Adressen
        addresses = server.addresses or {}
        if addresses:
            console.print(f"\n  IP-Adressen:")
            for net_name, addr_list in addresses.items():
                for addr in addr_list:
                    if addr.get("version") == 4:
                        console.print(f"    {net_name}: {addr.get('addr')}")
        
        # Warnung
        console.print("\n[bold red]⚠ WARNUNG:[/bold red]")
        console.print("  Dieser Server wird unwiderruflich gelöscht!")
        console.print("  Alle Daten auf dem Server gehen verloren!")
        
        # Prüfe ob --force Flag gesetzt ist
        force = "--force" in sys.argv or "-f" in sys.argv
        
        if not force:
            if not Confirm.ask("\n[yellow]Möchten Sie diesen Server wirklich löschen?[/yellow]", default=False):
                console.print("[yellow]Abgebrochen[/yellow]")
                sys.exit(0)
        else:
            console.print("\n[yellow]--force Flag gesetzt, lösche ohne weitere Bestätigung...[/yellow]")
        
        # Lösche Server
        console.print(f"\n[yellow]Lösche Server '{server.name}'...[/yellow]")
        conn.compute.delete_server(server_id)
        
        # Warte auf Löschung
        console.print("  Warte auf Löschung...")
        waited = 0
        max_wait = 120
        
        while waited < max_wait:
            time.sleep(2)
            waited += 2
            
            try:
                server = conn.compute.get_server(server_id)
                if waited % 10 == 0:
                    console.print(f"  Status: {server.status} ({waited}s)")
            except:
                # Server nicht mehr gefunden = gelöscht
                console.print(f"[green]✓[/green] Server erfolgreich gelöscht!")
                console.print(f"  Gelöscht nach {waited} Sekunden")
                
                console.print("\n" + "=" * 60)
                console.print(Panel.fit(
                    "[bold green]✓ Server gelöscht![/bold green]\n"
                    "Sie können jetzt einen neuen Server mit SSH-Key erstellen.",
                    border_style="green"
                ))
                console.print("=" * 60)
                
                console.print("\n[bold]Nächste Schritte:[/bold]")
                console.print("  python3 backend/openstack/create_server_simple.py")
                console.print("  (Das Script verwendet jetzt automatisch den SSH-Key 'hopp')")
                
                return True
        
        console.print(f"[yellow]⚠[/yellow] Timeout nach {max_wait}s - Server könnte noch gelöscht werden")
        return False
        
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg or "not found" in error_msg.lower():
            console.print("[yellow]⚠[/yellow] Server nicht gefunden (bereits gelöscht?)")
            return True
        else:
            console.print(f"[red]✗[/red] Fehler: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    server_id = "e73e74c7-4648-4c91-9811-2bcc7a748a88"
    
    # Parse Arguments
    args = [arg for arg in sys.argv[1:] if not arg.startswith("--") and not arg.startswith("-")]
    flags = [arg for arg in sys.argv[1:] if arg.startswith("--") or arg.startswith("-")]
    
    if args:
        server_id = args[0]
    else:
        console.print("[yellow]Verwende Standard-Server-ID[/yellow]")
        console.print(f"  {server_id}")
        console.print("\n[yellow]Hinweis:[/yellow] Sie können eine andere Server-ID als Argument übergeben")
        console.print("  Beispiel: python3 delete_server.py <server-id> [--force]")
    
    # Füge Flags zu sys.argv hinzu für delete_server Funktion
    sys.argv = [sys.argv[0], server_id] + flags
    
    delete_server(server_id)

