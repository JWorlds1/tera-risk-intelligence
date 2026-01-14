#!/usr/bin/env python3
"""
Integriert OpenStack Storage in die Crawling-Pipeline
"""
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import json

# Füge backend zum Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent.parent))

from openstack.storage_manager import OpenStackStorageManager
from rich.console import Console
from rich.table import Table

console = Console()


class CrawlingStorageIntegration:
    """Integriert OpenStack Storage in Crawling-Pipeline"""
    
    def __init__(self):
        """Initialisiert Storage-Integration"""
        try:
            self.storage = OpenStackStorageManager()
            self.container_name = "crawled-data"
        except Exception as e:
            console.print(f"[red]✗[/red] Storage-Initialisierung fehlgeschlagen: {e}")
            self.storage = None
    
    def setup_containers(self):
        """Erstellt notwendige Container"""
        if not self.storage:
            return False
        
        containers = [
            "crawled-data",      # Gecrawlte Rohdaten (600 GB)
            "processed-data",    # Verarbeitete Daten (200 GB)
            "database-backups",  # Datenbank-Backups (50 GB)
            "embeddings"         # Vektor-Embeddings (50 GB)
        ]
        
        console.print("\n[bold cyan]Erstelle Storage-Container...[/bold cyan]")
        
        for container in containers:
            existing = self.storage.list_containers()
            if container not in existing:
                self.storage.create_container(container)
            else:
                console.print(f"[yellow]⚠[/yellow] Container '{container}' existiert bereits")
        
        return True
    
    def upload_crawled_data(
        self,
        source_name: str,
        data_dir: Optional[Path] = None
    ) -> bool:
        """
        Lädt gecrawlte Daten hoch
        
        Args:
            source_name: Name der Quelle (nasa, un_press, worldbank)
            data_dir: Optional: Verzeichnis mit Daten (sonst data/)
        """
        if not self.storage:
            console.print("[red]✗[/red] Storage nicht verfügbar")
            return False
        
        if data_dir is None:
            data_dir = Path("data")
        
        # Suche nach Daten-Verzeichnissen
        json_dir = data_dir / "json" / source_name
        csv_dir = data_dir / "csv" / source_name
        parquet_dir = data_dir / "parquet" / source_name
        
        results = {}
        
        # Upload JSON
        if json_dir.exists():
            console.print(f"\n[yellow]Lade JSON-Daten hoch ({source_name})...[/yellow]")
            json_results = self.storage.upload_directory(
                str(json_dir),
                self.container_name,
                prefix=f"raw/{source_name}/json"
            )
            results.update(json_results)
        
        # Upload CSV
        if csv_dir.exists():
            console.print(f"\n[yellow]Lade CSV-Daten hoch ({source_name})...[/yellow]")
            csv_results = self.storage.upload_directory(
                str(csv_dir),
                self.container_name,
                prefix=f"raw/{source_name}/csv"
            )
            results.update(csv_results)
        
        # Upload Parquet
        if parquet_dir.exists():
            console.print(f"\n[yellow]Lade Parquet-Daten hoch ({source_name})...[/yellow]")
            parquet_results = self.storage.upload_directory(
                str(parquet_dir),
                "processed-data",
                prefix=f"{source_name}/parquet"
            )
            results.update(parquet_results)
        
        successful = sum(1 for v in results.values() if v)
        console.print(f"\n[green]✓[/green] {successful}/{len(results)} Dateien hochgeladen")
        
        return successful > 0
    
    def backup_database(self, db_path: Optional[Path] = None) -> bool:
        """
        Erstellt Backup der Datenbank
        
        Args:
            db_path: Optional: Pfad zur Datenbank (sonst data/climate_conflict.db)
        """
        if not self.storage:
            console.print("[red]✗[/red] Storage nicht verfügbar")
            return False
        
        if db_path is None:
            db_path = Path("data/climate_conflict.db")
        
        if not db_path.exists():
            console.print(f"[red]✗[/red] Datenbank nicht gefunden: {db_path}")
            return False
        
        # Erstelle Backup-Name mit Datum
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"daily/{date_str}_climate_conflict.db"
        
        console.print(f"\n[yellow]Erstelle Datenbank-Backup...[/yellow]")
        
        success = self.storage.upload_file(
            str(db_path),
            "database-backups",
            backup_name
        )
        
        if success:
            console.print(f"[green]✓[/green] Backup erstellt: {backup_name}")
        
        return success
    
    def show_storage_status(self):
        """Zeigt Storage-Status"""
        if not self.storage:
            console.print("[red]✗[/red] Storage nicht verfügbar")
            return
        
        self.storage.show_storage_status()
        
        # Zeige Container-Inhalte
        containers = ["crawled-data", "processed-data", "database-backups", "embeddings"]
        
        console.print("\n[bold cyan]Container-Inhalte:[/bold cyan]")
        
        for container in containers:
            objects = self.storage.list_objects(container)
            if objects:
                total_size = sum(obj["size"] for obj in objects)
                console.print(f"\n[yellow]{container}:[/yellow]")
                console.print(f"  {len(objects)} Objekte")
                console.print(f"  {total_size / (1024**3):.2f} GB")
                
                # Zeige erste 5 Objekte
                for obj in objects[:5]:
                    console.print(f"    - {obj['name']} ({obj['size'] / (1024**2):.2f} MB)")


def main():
    """CLI für Storage-Integration"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenStack Storage Integration")
    parser.add_argument("--setup", action="store_true", help="Erstelle Container")
    parser.add_argument("--upload", type=str, help="Lade Daten hoch (nasa/un_press/worldbank)")
    parser.add_argument("--backup", action="store_true", help="Erstelle Datenbank-Backup")
    parser.add_argument("--status", action="store_true", help="Zeige Storage-Status")
    
    args = parser.parse_args()
    
    integration = CrawlingStorageIntegration()
    
    if args.setup:
        integration.setup_containers()
    elif args.upload:
        integration.upload_crawled_data(args.upload)
    elif args.backup:
        integration.backup_database()
    elif args.status:
        integration.show_storage_status()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

