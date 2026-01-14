#!/usr/bin/env python3
"""
OpenStack Storage Manager für gecrawlte Daten
Verwaltet Object Storage (Swift) für große Datenmengen
"""
import sys
from pathlib import Path
from typing import Optional, List, Dict
from openstack import connection
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
import os

console = Console()


class OpenStackStorageManager:
    """Verwaltet OpenStack Object Storage für gecrawlte Daten"""
    
    def __init__(self, cloud_name: str = "openstack"):
        """Initialisiert den Storage Manager"""
        self.cloud_name = cloud_name
        self.conn = None
        self._connect()
    
    def _connect(self):
        """Stellt Verbindung zu OpenStack her"""
        try:
            self.conn = connection.Connection(
                cloud=self.cloud_name,
                config_dir=str(Path.home() / ".config" / "openstack")
            )
            self.conn.authorize()
            console.print("[green]✓[/green] Verbindung zu OpenStack erfolgreich")
        except Exception as e:
            console.print(f"[red]✗[/red] Verbindungsfehler: {e}")
            raise
    
    def list_containers(self) -> List[str]:
        """Listet alle Container auf"""
        try:
            containers = list(self.conn.object_store.containers())
            return [c.name for c in containers]
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Swift nicht verfügbar: {e}")
            return []
    
    def create_container(self, container_name: str, public: bool = False) -> bool:
        """Erstellt einen neuen Container"""
        try:
            self.conn.object_store.create_container(
                name=container_name,
                public=public
            )
            console.print(f"[green]✓[/green] Container '{container_name}' erstellt")
            return True
        except Exception as e:
            console.print(f"[red]✗[/red] Fehler beim Erstellen: {e}")
            return False
    
    def upload_file(
        self,
        local_path: str,
        container_name: str,
        object_name: Optional[str] = None,
        chunk_size: int = 1024 * 1024 * 100  # 100 MB chunks
    ) -> bool:
        """
        Lädt eine Datei hoch
        
        Args:
            local_path: Lokaler Dateipfad
            container_name: Container-Name
            object_name: Optional: Objekt-Name (sonst Dateiname)
            chunk_size: Chunk-Größe für große Dateien
        """
        local_file = Path(local_path)
        
        if not local_file.exists():
            console.print(f"[red]✗[/red] Datei nicht gefunden: {local_path}")
            return False
        
        if object_name is None:
            object_name = local_file.name
        
        try:
            file_size = local_file.stat().st_size
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console
            ) as progress:
                task = progress.add_task(
                    f"Lade hoch: {local_file.name}",
                    total=file_size
                )
                
                # Für große Dateien: Chunked Upload
                if file_size > chunk_size:
                    # Swift unterstützt große Objekte
                    with open(local_file, 'rb') as f:
                        self.conn.object_store.create_object(
                            container=container_name,
                            name=object_name,
                            data=f,
                            content_type='application/octet-stream'
                        )
                else:
                    # Normale Upload
                    with open(local_file, 'rb') as f:
                        self.conn.object_store.create_object(
                            container=container_name,
                            name=object_name,
                            data=f.read(),
                            content_type='application/octet-stream'
                        )
                
                progress.update(task, completed=file_size)
            
            console.print(f"[green]✓[/green] Datei hochgeladen: {object_name}")
            return True
            
        except Exception as e:
            console.print(f"[red]✗[/red] Upload-Fehler: {e}")
            return False
    
    def upload_directory(
        self,
        local_dir: str,
        container_name: str,
        prefix: str = "",
        extensions: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Lädt ein Verzeichnis hoch
        
        Args:
            local_dir: Lokales Verzeichnis
            container_name: Container-Name
            prefix: Optional: Präfix für Objekt-Namen
            extensions: Optional: Filter für Dateiendungen
        """
        local_path = Path(local_dir)
        
        if not local_path.is_dir():
            console.print(f"[red]✗[/red] Verzeichnis nicht gefunden: {local_dir}")
            return {}
        
        results = {}
        files = list(local_path.rglob("*"))
        files = [f for f in files if f.is_file()]
        
        if extensions:
            files = [f for f in files if f.suffix.lower() in extensions]
        
        console.print(f"\n[yellow]Lade {len(files)} Dateien hoch...[/yellow]")
        
        for file_path in files:
            relative_path = file_path.relative_to(local_path)
            object_name = f"{prefix}/{relative_path}" if prefix else str(relative_path)
            object_name = object_name.replace("\\", "/")  # Windows-Kompatibilität
            
            success = self.upload_file(str(file_path), container_name, object_name)
            results[str(relative_path)] = success
        
        successful = sum(1 for v in results.values() if v)
        console.print(f"\n[green]✓[/green] {successful}/{len(results)} Dateien erfolgreich hochgeladen")
        
        return results
    
    def download_file(
        self,
        container_name: str,
        object_name: str,
        local_path: str
    ) -> bool:
        """Lädt eine Datei herunter"""
        try:
            obj = self.conn.object_store.get_object(
                container=container_name,
                name=object_name
            )
            
            local_file = Path(local_path)
            local_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(local_file, 'wb') as f:
                f.write(obj.data)
            
            console.print(f"[green]✓[/green] Datei heruntergeladen: {local_path}")
            return True
            
        except Exception as e:
            console.print(f"[red]✗[/red] Download-Fehler: {e}")
            return False
    
    def list_objects(self, container_name: str, prefix: str = "") -> List[Dict]:
        """Listet Objekte in einem Container auf"""
        try:
            objects = list(self.conn.object_store.objects(
                container=container_name,
                prefix=prefix
            ))
            
            return [
                {
                    "name": obj.name,
                    "size": obj.bytes,
                    "content_type": obj.content_type,
                    "last_modified": obj.last_modified
                }
                for obj in objects
            ]
        except Exception as e:
            console.print(f"[red]✗[/red] Fehler: {e}")
            return []
    
    def get_storage_info(self) -> Dict:
        """Gibt Storage-Informationen zurück"""
        try:
            account = self.conn.object_store.get_account()
            return {
                "containers": account.container_count,
                "objects": account.object_count,
                "bytes": account.bytes_used
            }
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Storage-Info nicht verfügbar: {e}")
            return {}
    
    def show_storage_status(self):
        """Zeigt Storage-Status"""
        info = self.get_storage_info()
        containers = self.list_containers()
        
        table = Table(title="OpenStack Storage Status")
        table.add_column("Metrik", style="cyan")
        table.add_column("Wert", style="green")
        
        if info:
            table.add_row("Container", str(info.get("containers", 0)))
            table.add_row("Objekte", str(info.get("objects", 0)))
            bytes_used = info.get("bytes", 0)
            table.add_row("Speicher verwendet", f"{bytes_used / (1024**3):.2f} GB")
        
        console.print("\n")
        console.print(table)
        
        if containers:
            console.print(f"\n[yellow]Container:[/yellow] {', '.join(containers)}")


def main():
    """CLI für Storage Manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenStack Storage Manager")
    parser.add_argument("--list-containers", action="store_true", help="Liste Container")
    parser.add_argument("--create-container", type=str, help="Erstelle Container")
    parser.add_argument("--upload", type=str, help="Lade Datei/Verzeichnis hoch")
    parser.add_argument("--container", type=str, help="Container-Name")
    parser.add_argument("--status", action="store_true", help="Zeige Storage-Status")
    
    args = parser.parse_args()
    
    try:
        storage = OpenStackStorageManager()
        
        if args.status:
            storage.show_storage_status()
        elif args.list_containers:
            containers = storage.list_containers()
            console.print(f"\nContainer: {', '.join(containers) if containers else 'Keine'}")
        elif args.create_container:
            storage.create_container(args.create_container)
        elif args.upload and args.container:
            path = Path(args.upload)
            if path.is_file():
                storage.upload_file(args.upload, args.container)
            elif path.is_dir():
                storage.upload_directory(args.upload, args.container)
            else:
                console.print(f"[red]✗[/red] Pfad nicht gefunden: {args.upload}")
        else:
            parser.print_help()
            
    except Exception as e:
        console.print(f"[red]✗[/red] Fehler: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

