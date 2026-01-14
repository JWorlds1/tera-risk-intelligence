#!/usr/bin/env python3
"""
Fügt einen SSH-Key zu einem bestehenden Server hinzu
Hinweis: OpenStack erlaubt normalerweise keine nachträgliche Key-Zuweisung.
Der Server muss mit dem Key erstellt werden.
"""
import sys
from pathlib import Path
from openstack import connection
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def check_server_key(server_id):
    """Prüft ob Server einen SSH-Key hat"""
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
        
        key_name = getattr(server, 'key_name', None)
        if key_name:
            console.print(f"[green]✓[/green] Server hat SSH-Key: {key_name}")
        else:
            console.print(f"[yellow]⚠[/yellow] Server hat keinen SSH-Key zugewiesen")
            console.print("\n[yellow]Problem:[/yellow]")
            console.print("  OpenStack erlaubt keine nachträgliche SSH-Key-Zuweisung.")
            console.print("  Der Server muss mit dem Key erstellt werden.")
            
            console.print("\n[yellow]Verfügbare SSH-Keys:[/yellow]")
            try:
                keys = list(conn.compute.keypairs())
                if keys:
                    table = Table()
                    table.add_column("Name", style="green")
                    table.add_column("Fingerprint", style="yellow")
                    
                    for key in keys:
                        table.add_row(
                            key.name,
                            key.fingerprint[:40] + "..." if len(key.fingerprint) > 40 else key.fingerprint
                        )
                    console.print(table)
                else:
                    console.print("  Keine Keys gefunden")
            except Exception as e:
                console.print(f"  Konnte Keys nicht abrufen: {e}")
            
            console.print("\n[bold cyan]Lösung:[/bold cyan]")
            console.print("  1. Server löschen und neu erstellen MIT SSH-Key")
            console.print("  2. Oder: SSH-Key manuell auf dem Server hinzufügen")
            console.print("     (benötigt Console-Zugriff oder andere Authentifizierung)")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    server_id = "e73e74c7-4648-4c91-9811-2bcc7a748a88"
    if len(sys.argv) > 1:
        server_id = sys.argv[1]
    
    check_server_key(server_id)

