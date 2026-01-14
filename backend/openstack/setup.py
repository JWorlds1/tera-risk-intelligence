#!/usr/bin/env python3
"""
OpenStack Setup Script
Interaktive Einrichtung der OpenStack Konfiguration
"""
import sys
from pathlib import Path

# Füge backend zum Python-Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent.parent))

from openstack.config_manager import OpenStackConfigManager
from rich.console import Console

console = Console()


def main():
    """Hauptfunktion für interaktives Setup"""
    console.print("\n[bold cyan]OpenStack Konfiguration Setup[/bold cyan]")
    console.print("=" * 60)
    
    # Cloud-Name abfragen
    cloud_name = console.input("\n[bold]Cloud-Name[/bold] (default: hda-cloud): ").strip() or "hda-cloud"
    
    # Config Manager initialisieren
    config_manager = OpenStackConfigManager()
    
    # Interaktive Konfiguration
    config = config_manager.setup_interactive(cloud_name=cloud_name)
    
    # Speichern?
    save_password = console.input(
        "\n[bold yellow]Passwort in secure.yaml speichern?[/bold yellow] (j/n, default: n): "
    ).strip().lower() == "j"
    
    # Konfiguration speichern
    if config_manager.save_config(config, save_password=save_password):
        console.print("\n[green]✓[/green] Konfiguration erfolgreich gespeichert!")
        
        # Validierung
        if config_manager.validate_config():
            console.print("\n[bold green]Setup abgeschlossen![/bold green]")
            console.print(f"\nKonfiguration gespeichert in: {config_manager.clouds_yaml_path}")
            if save_password:
                console.print(f"Passwort gespeichert in: {config_manager.secure_yaml_path}")
            
            console.print("\n[bold]Nächste Schritte:[/bold]")
            console.print("1. Teste die Verbindung: python -m backend.openstack.test_connection")
            console.print("2. Liste Server auf: python -m backend.openstack.list_resources")
        else:
            console.print("\n[yellow]⚠[/yellow] Konfiguration gespeichert, aber Validierung fehlgeschlagen.")
    else:
        console.print("\n[red]✗[/red] Setup fehlgeschlagen!")
        sys.exit(1)


if __name__ == "__main__":
    main()

