#!/usr/bin/env python3
"""
Praktische Storage-Lösung für gecrawlte Daten
Da Swift nicht verfügbar ist, verwenden wir eine Hybrid-Lösung
"""
from pathlib import Path
from openstack import connection
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import json
from datetime import datetime

console = Console()


class HybridStorageSolution:
    """
    Hybrid Storage-Lösung:
    - Lokaler Speicher für aktive Daten
    - OpenStack Block Storage für Backups
    - Automatische Synchronisation
    """
    
    def __init__(self):
        """Initialisiert Hybrid Storage"""
        try:
            self.conn = connection.Connection(
                cloud='openstack',
                config_dir=str(Path.home() / ".config" / "openstack")
            )
            self.conn.authorize()
            self.conn_available = True
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] OpenStack nicht verfügbar: {e}")
            self.conn_available = False
    
    def create_backup_volume(self, name: str, size_gb: int = 100) -> bool:
        """Erstellt ein Backup-Volume"""
        if not self.conn_available:
            return False
        
        try:
            # Prüfe ob Volume bereits existiert
            volumes = list(self.conn.block_storage.volumes())
            existing = [v for v in volumes if v.name == name]
            
            if existing:
                console.print(f"[yellow]⚠[/yellow] Volume '{name}' existiert bereits")
                return True
            
            console.print(f"[yellow]Erstelle Volume '{name}' ({size_gb} GB)...[/yellow]")
            
            volume = self.conn.block_storage.create_volume(
                name=name,
                size=size_gb,
                description=f"Backup Volume für {name}"
            )
            
            console.print(f"[green]✓[/green] Volume erstellt: {volume.id}")
            return True
            
        except Exception as e:
            console.print(f"[red]✗[/red] Fehler: {e}")
            return False
    
    def list_backup_volumes(self):
        """Listet Backup-Volumes auf"""
        if not self.conn_available:
            console.print("[yellow]⚠[/yellow] OpenStack nicht verfügbar")
            return
        
        volumes = list(self.conn.block_storage.volumes())
        
        if not volumes:
            console.print("[yellow]Keine Volumes gefunden[/yellow]")
            return
        
        table = Table(title="Backup Volumes")
        table.add_column("Name", style="green")
        table.add_column("Größe (GB)", style="yellow")
        table.add_column("Status", style="magenta")
        table.add_column("ID", style="cyan")
        
        for vol in volumes:
            table.add_row(
                vol.name or "N/A",
                str(vol.size),
                vol.status,
                vol.id[:16] + "..."
            )
        
        console.print("\n")
        console.print(table)
    
    def create_metadata_index(self, data_dir: Path) -> dict:
        """Erstellt Metadaten-Index für lokale Daten"""
        index = {
            "created_at": datetime.now().isoformat(),
            "directories": {},
            "total_files": 0,
            "total_size_bytes": 0
        }
        
        for item in data_dir.rglob("*"):
            if item.is_file():
                rel_path = str(item.relative_to(data_dir))
                size = item.stat().st_size
                
                # Gruppiere nach Verzeichnis
                dir_name = str(item.parent.relative_to(data_dir))
                if dir_name not in index["directories"]:
                    index["directories"][dir_name] = {
                        "files": [],
                        "total_size": 0
                    }
                
                index["directories"][dir_name]["files"].append({
                    "name": item.name,
                    "path": rel_path,
                    "size": size,
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                })
                
                index["directories"][dir_name]["total_size"] += size
                index["total_files"] += 1
                index["total_size_bytes"] += size
        
        return index
    
    def save_metadata(self, index: dict, output_path: Path):
        """Speichert Metadaten-Index"""
        with open(output_path, 'w') as f:
            json.dump(index, f, indent=2)
        
        console.print(f"[green]✓[/green] Metadaten gespeichert: {output_path}")
    
    def show_storage_summary(self, data_dir: Path = None):
        """Zeigt Storage-Zusammenfassung"""
        if data_dir is None:
            data_dir = Path("data")
        
        console.print(Panel.fit(
            "[bold cyan]Storage-Zusammenfassung[/bold cyan]",
            border_style="cyan"
        ))
        
        if not data_dir.exists():
            console.print(f"[yellow]⚠[/yellow] Verzeichnis nicht gefunden: {data_dir}")
            return
        
        # Erstelle Metadaten-Index
        console.print("\n[yellow]Analysiere lokale Daten...[/yellow]")
        index = self.create_metadata_index(data_dir)
        
        # Zeige Zusammenfassung
        table = Table(title="Lokale Daten")
        table.add_column("Verzeichnis", style="green")
        table.add_column("Dateien", style="yellow")
        table.add_column("Größe", style="magenta")
        
        for dir_name, dir_info in sorted(index["directories"].items(), 
                                         key=lambda x: x[1]["total_size"], 
                                         reverse=True)[:10]:
            table.add_row(
                dir_name[:50],
                str(len(dir_info["files"])),
                f"{dir_info['total_size'] / (1024**3):.2f} GB"
            )
        
        console.print("\n")
        console.print(table)
        
        console.print(f"\n[bold]Gesamt:[/bold]")
        console.print(f"  Dateien: {index['total_files']}")
        console.print(f"  Größe: {index['total_size_bytes'] / (1024**3):.2f} GB")
        
        # Speichere Metadaten
        metadata_file = data_dir / "storage_metadata.json"
        self.save_metadata(index, metadata_file)
        
        # Zeige OpenStack Status
        if self.conn_available:
            console.print("\n[bold cyan]OpenStack Status:[/bold cyan]")
            self.list_backup_volumes()


def main():
    """CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Hybrid Storage Solution")
    parser.add_argument("--summary", action="store_true", help="Zeige Storage-Zusammenfassung")
    parser.add_argument("--create-volume", type=str, help="Erstelle Backup-Volume (Name)")
    parser.add_argument("--volume-size", type=int, default=100, help="Volume-Größe in GB")
    parser.add_argument("--list-volumes", action="store_true", help="Liste Volumes")
    
    args = parser.parse_args()
    
    storage = HybridStorageSolution()
    
    if args.summary:
        storage.show_storage_summary()
    elif args.create_volume:
        storage.create_backup_volume(args.create_volume, args.volume_size)
    elif args.list_volumes:
        storage.list_backup_volumes()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

