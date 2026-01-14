#!/usr/bin/env python3
"""
Ändert die OpenStack Konfiguration
Verwendung: python3 update_config.py [OPTIONEN]
"""
import yaml
import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()

def load_config():
    """Lädt die aktuelle Konfiguration"""
    config_path = Path.home() / ".config" / "openstack" / "clouds.yaml"
    if not config_path.exists():
        console.print("[red]✗[/red] Konfiguration nicht gefunden!")
        return None
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def save_config(config):
    """Speichert die Konfiguration"""
    config_path = Path.home() / ".config" / "openstack" / "clouds.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    console.print(f"[green]✓[/green] Konfiguration gespeichert: {config_path}")

def show_config(config):
    """Zeigt die aktuelle Konfiguration"""
    if not config or "clouds" not in config:
        console.print("[red]✗[/red] Keine gültige Konfiguration gefunden")
        return
    
    cloud_name = list(config["clouds"].keys())[0] if config["clouds"] else None
    if not cloud_name:
        console.print("[red]✗[/red] Keine Cloud-Konfiguration gefunden")
        return
    
    cloud = config["clouds"][cloud_name]
    auth = cloud.get("auth", {})
    
    console.print("\n[bold cyan]Aktuelle Konfiguration:[/bold cyan]")
    console.print(f"  Cloud Name: {cloud_name}")
    console.print(f"  Auth URL: {auth.get('auth_url', 'N/A')}")
    console.print(f"  Application Credential ID: {auth.get('application_credential_id', 'N/A')[:20]}...")
    console.print(f"  Region: {cloud.get('region_name', 'N/A')}")
    console.print(f"  Interface: {cloud.get('interface', 'N/A')}")
    console.print(f"  Auth Type: {cloud.get('auth_type', 'N/A')}")

def update_config_interactive():
    """Interaktive Konfigurationsänderung"""
    config = load_config()
    if not config:
        return False
    
    show_config(config)
    
    cloud_name = list(config["clouds"].keys())[0]
    cloud = config["clouds"][cloud_name]
    auth = cloud.get("auth", {})
    
    console.print("\n[bold yellow]Was möchten Sie ändern?[/bold yellow]")
    console.print("1. Auth URL")
    console.print("2. Application Credential ID")
    console.print("3. Application Credential Secret")
    console.print("4. Region")
    console.print("5. Interface")
    console.print("6. Alles")
    console.print("0. Abbrechen")
    
    choice = Prompt.ask("\nWahl", default="0")
    
    if choice == "0":
        console.print("[yellow]Abgebrochen[/yellow]")
        return False
    
    if choice == "1" or choice == "6":
        new_url = Prompt.ask("Neue Auth URL", default=auth.get("auth_url", ""))
        auth["auth_url"] = new_url
    
    if choice == "2" or choice == "6":
        new_id = Prompt.ask("Neue Application Credential ID", default=auth.get("application_credential_id", ""))
        auth["application_credential_id"] = new_id
    
    if choice == "3" or choice == "6":
        new_secret = Prompt.ask("Neue Application Credential Secret", default=auth.get("application_credential_secret", ""))
        auth["application_credential_secret"] = new_secret
    
    if choice == "4" or choice == "6":
        new_region = Prompt.ask("Neue Region", default=cloud.get("region_name", ""))
        cloud["region_name"] = new_region
    
    if choice == "5" or choice == "6":
        new_interface = Prompt.ask("Neue Interface (public/internal/admin)", default=cloud.get("interface", "public"))
        cloud["interface"] = new_interface
    
    cloud["auth"] = auth
    config["clouds"][cloud_name] = cloud
    
    if Confirm.ask("\nÄnderungen speichern?", default=True):
        save_config(config)
        show_config(config)
        return True
    else:
        console.print("[yellow]Änderungen verworfen[/yellow]")
        return False

def main():
    parser = argparse.ArgumentParser(description="OpenStack Konfiguration ändern")
    parser.add_argument("--show", action="store_true", help="Zeige aktuelle Konfiguration")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interaktive Änderung")
    
    args = parser.parse_args()
    
    if args.show:
        config = load_config()
        if config:
            show_config(config)
    elif args.interactive or len(sys.argv) == 1:
        update_config_interactive()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

