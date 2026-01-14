#!/usr/bin/env python3
"""
Setup Block Storage (Cinder) für gecrawlte Daten
Da Swift nicht verfügbar ist, verwenden wir Block Storage
"""
from pathlib import Path
from openstack import connection
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def setup_block_storage():
    """Erstellt Block Storage Volumes für gecrawlte Daten"""
    
    console.print(Panel.fit(
        "[bold cyan]Block Storage Setup für Geospatial Intelligence[/bold cyan]",
        border_style="cyan"
    ))
    
    try:
        conn = connection.Connection(
            cloud='openstack',
            config_dir=str(Path.home() / ".config" / "openstack")
        )
        conn.authorize()
        console.print("[green]✓[/green] Verbindung erfolgreich\n")
    except Exception as e:
        console.print(f"[red]✗[/red] Verbindungsfehler: {e}")
        return
    
    # Prüfe verfügbare Volumes
    volumes = list(conn.block_storage.volumes())
    console.print(f"[yellow]Aktuelle Volumes:[/yellow] {len(volumes)}")
    
    # Empfohlene Volume-Struktur
    volume_configs = [
        {
            "name": "geospatial-crawled-data",
            "size": 600,  # GB
            "description": "Gecrawlte Rohdaten (HTML, JSON, Bilder)"
        },
        {
            "name": "geospatial-processed-data",
            "size": 200,  # GB
            "description": "Verarbeitete Daten (Parquet, CSV, Analysen)"
        },
        {
            "name": "geospatial-database-backups",
            "size": 50,  # GB
            "description": "Datenbank-Backups"
        },
        {
            "name": "geospatial-embeddings",
            "size": 50,  # GB
            "description": "Vektor-Embeddings"
        }
    ]
    
    console.print("\n[bold cyan]Empfohlene Volume-Struktur:[/bold cyan]")
    table = Table()
    table.add_column("Name", style="green")
    table.add_column("Größe", style="yellow")
    table.add_column("Beschreibung", style="cyan")
    
    for config in volume_configs:
        # Prüfe ob Volume bereits existiert
        existing = [v for v in volumes if v.name == config["name"]]
        status = "[green]✓[/green] Existiert" if existing else "[yellow]Neu[/yellow]"
        
        table.add_row(
            config["name"],
            f"{config['size']} GB",
            config["description"]
        )
    
    console.print("\n")
    console.print(table)
    
    console.print("\n[yellow]Hinweis:[/yellow]")
    console.print("  Block Storage Volumes müssen an einen Server angehängt werden.")
    console.print("  Für reine Datenspeicherung ohne Server:")
    console.print("  1. Erstelle einen kleinen Server (z.B. m1.small)")
    console.print("  2. Erstelle Volumes")
    console.print("  3. Hänge Volumes an Server an")
    console.print("  4. Mounte Volumes als Dateisystem")
    
    console.print("\n[bold green]Alternative Lösung:[/bold green]")
    console.print("  Verwende lokalen Speicher + regelmäßige Backups zu OpenStack")
    console.print("  Oder verwende einen kleinen Server als Storage-Gateway")


def check_swift_permissions():
    """Prüft Swift-Berechtigungen"""
    console.print("\n[bold cyan]Prüfe Swift-Berechtigungen...[/bold cyan]")
    
    try:
        conn = connection.Connection(
            cloud='openstack',
            config_dir=str(Path.home() / ".config" / "openstack")
        )
        conn.authorize()
        
        # Versuche Swift-Endpoint zu finden
        try:
            # Prüfe ob Swift-Service verfügbar ist
            services = list(conn.identity.services())
            swift_service = [s for s in services if s.type == 'object-store']
            
            if swift_service:
                console.print(f"[green]✓[/green] Swift-Service gefunden: {swift_service[0].name}")
                console.print(f"[yellow]⚠[/yellow] Aber keine Berechtigung (401 Unauthorized)")
                console.print("\n[yellow]Mögliche Lösungen:[/yellow]")
                console.print("  1. Application Credentials haben keine Swift-Berechtigung")
                console.print("  2. Benötigen Sie zusätzliche Berechtigungen vom Administrator")
                console.print("  3. Verwenden Sie Block Storage (Cinder) stattdessen")
            else:
                console.print("[yellow]⚠[/yellow] Swift-Service nicht verfügbar")
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Swift-Prüfung: {e}")
            
    except Exception as e:
        console.print(f"[red]✗[/red] Fehler: {e}")


if __name__ == "__main__":
    check_swift_permissions()
    console.print("\n" + "=" * 60)
    setup_block_storage()

