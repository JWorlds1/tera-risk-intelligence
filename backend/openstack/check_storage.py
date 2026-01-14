#!/usr/bin/env python3
"""
Prüft verfügbare Storage-Optionen in OpenStack
"""
from pathlib import Path
from openstack import connection
from rich.console import Console
from rich.table import Table

console = Console()

def check_storage_options():
    """Prüft verfügbare Storage-Optionen"""
    console.print("\n[bold cyan]OpenStack Storage-Optionen[/bold cyan]")
    console.print("=" * 60)
    
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
    
    # Prüfe Object Storage (Swift)
    console.print("[bold yellow]1. Object Storage (Swift)[/bold yellow]")
    try:
        containers = list(conn.object_store.containers())
        console.print(f"  [green]✓[/green] Swift verfügbar: {len(containers)} Container")
        
        account = conn.object_store.get_account()
        console.print(f"  [green]✓[/green] Account Info:")
        console.print(f"    - Container: {account.container_count}")
        console.print(f"    - Objekte: {account.object_count}")
        console.print(f"    - Speicher verwendet: {account.bytes_used / (1024**3):.2f} GB")
        
        if containers:
            table = Table(title="Container")
            table.add_column("Name", style="green")
            table.add_column("Objekte", style="yellow")
            table.add_column("Größe", style="magenta")
            
            for container in containers[:10]:
                try:
                    objects = list(conn.object_store.objects(container=container.name))
                    total_size = sum(obj.bytes for obj in objects)
                    table.add_row(
                        container.name,
                        str(len(objects)),
                        f"{total_size / (1024**3):.2f} GB"
                    )
                except:
                    table.add_row(container.name, "N/A", "N/A")
            
            console.print("\n")
            console.print(table)
        
    except Exception as e:
        console.print(f"  [red]✗[/red] Swift nicht verfügbar: {e}")
    
    # Prüfe Block Storage (Cinder)
    console.print("\n[bold yellow]2. Block Storage (Cinder)[/bold yellow]")
    try:
        volumes = list(conn.block_storage.volumes())
        console.print(f"  [green]✓[/green] Cinder verfügbar: {len(volumes)} Volumes")
        
        if volumes:
            table = Table(title="Volumes")
            table.add_column("Name", style="green")
            table.add_column("Größe (GB)", style="yellow")
            table.add_column("Status", style="magenta")
            
            for vol in volumes[:10]:
                table.add_row(
                    vol.name or vol.id[:12],
                    str(vol.size),
                    vol.status
                )
            
            console.print("\n")
            console.print(table)
        
        # Verfügbarer Speicher
        total_size = sum(v.size for v in volumes)
        console.print(f"\n  [green]✓[/green] Gesamt Volumes: {total_size} GB")
        
    except Exception as e:
        console.print(f"  [red]✗[/red] Cinder nicht verfügbar: {e}")
    
    # Empfehlung
    console.print("\n" + "=" * 60)
    console.print("[bold cyan]Empfehlung für Ihr Projekt:[/bold cyan]")
    console.print("=" * 60)
    console.print("\n[yellow]Für gecrawlte Daten (900 GB verfügbar):[/yellow]")
    console.print("  ✓ Object Storage (Swift) - Beste Wahl für große Datenmengen")
    console.print("    - Skalierbar bis zu mehreren TB")
    console.print("    - Geeignet für viele kleine Dateien")
    console.print("    - Automatische Replikation")
    console.print("    - Günstig für Archivierung")
    console.print("\n  Alternative: Block Storage (Cinder)")
    console.print("    - Für strukturierte Datenbanken")
    console.print("    - Höhere Performance")
    console.print("    - Aber weniger flexibel")
    
    console.print("\n[bold green]Nächste Schritte:[/bold green]")
    console.print("  1. Erstelle Container für gecrawlte Daten")
    console.print("  2. Integriere Storage in Crawling-Pipeline")
    console.print("  3. Automatischer Upload nach dem Crawling")


if __name__ == "__main__":
    check_storage_options()

