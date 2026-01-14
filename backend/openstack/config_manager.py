"""
OpenStack Konfigurations-Manager
Verwaltet clouds.yaml und OpenStack Client Konfiguration
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm
import getpass

console = Console()


class OpenStackConfigManager:
    """Verwaltet OpenStack Konfiguration"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialisiert den Config Manager
        
        Args:
            config_dir: Verzeichnis für clouds.yaml (default: ~/.config/openstack)
        """
        if config_dir is None:
            self.config_dir = Path.home() / ".config" / "openstack"
        else:
            self.config_dir = Path(config_dir)
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.clouds_yaml_path = self.config_dir / "clouds.yaml"
        self.secure_yaml_path = self.config_dir / "secure.yaml"
    
    def setup_interactive(self, cloud_name: str = "hda-cloud") -> Dict[str, any]:
        """
        Interaktive Einrichtung der OpenStack Konfiguration
        
        Args:
            cloud_name: Name der Cloud-Konfiguration
            
        Returns:
            Dict mit Konfigurationsdaten
        """
        console.print("\n[bold cyan]OpenStack Konfiguration Setup[/bold cyan]")
        console.print("=" * 60)
        
        # Basis-Authentifizierung
        console.print("\n[bold yellow]Authentifizierungs-Informationen:[/bold yellow]")
        auth_url = Prompt.ask(
            "OpenStack Identity URL (auth_url)",
            default="https://identity.hda-cloud.de:5000/v3"
        )
        
        project_name = Prompt.ask("Project Name", default="")
        project_domain_name = Prompt.ask("Project Domain Name", default="default")
        
        username = Prompt.ask("Username")
        user_domain_name = Prompt.ask("User Domain Name", default="default")
        
        # Passwort sicher abfragen
        password = getpass.getpass("Password (wird nicht angezeigt): ")
        
        # Region
        region_name = Prompt.ask("Region Name", default="RegionOne")
        
        # Optional: Interface
        interface = Prompt.ask(
            "Interface (public/internal/admin)",
            default="public",
            choices=["public", "internal", "admin"]
        )
        
        # Optional: Verify SSL
        verify_ssl = Confirm.ask("SSL Zertifikat verifizieren?", default=True)
        
        config = {
            "clouds": {
                cloud_name: {
                    "auth": {
                        "auth_url": auth_url,
                        "project_name": project_name,
                        "project_domain_name": project_domain_name,
                        "username": username,
                        "user_domain_name": user_domain_name,
                        "password": password,  # Wird in secure.yaml gespeichert
                    },
                    "region_name": region_name,
                    "interface": interface,
                    "verify": verify_ssl,
                }
            }
        }
        
        return config
    
    def save_config(self, config: Dict, save_password: bool = False) -> bool:
        """
        Speichert Konfiguration in clouds.yaml
        
        Args:
            config: Konfigurations-Dict
            save_password: Ob Passwort gespeichert werden soll (nicht empfohlen)
            
        Returns:
            True bei Erfolg
        """
        try:
            # Passwort aus clouds.yaml entfernen (gehört in secure.yaml)
            clouds_config = config.copy()
            password = None
            
            if "clouds" in clouds_config:
                for cloud_name, cloud_config in clouds_config["clouds"].items():
                    if "auth" in cloud_config and "password" in cloud_config["auth"]:
                        password = cloud_config["auth"].pop("password")
            
            # clouds.yaml speichern (ohne Passwort)
            with open(self.clouds_yaml_path, 'w') as f:
                yaml.dump(clouds_config, f, default_flow_style=False, sort_keys=False)
            
            console.print(f"[green]✓[/green] Konfiguration gespeichert: {self.clouds_yaml_path}")
            
            # secure.yaml für Passwort (optional)
            if password and save_password:
                secure_config = clouds_config.copy()
                for cloud_name in secure_config.get("clouds", {}):
                    if "auth" not in secure_config["clouds"][cloud_name]:
                        secure_config["clouds"][cloud_name]["auth"] = {}
                    secure_config["clouds"][cloud_name]["auth"]["password"] = password
                
                with open(self.secure_yaml_path, 'w') as f:
                    yaml.dump(secure_config, f, default_flow_style=False, sort_keys=False)
                
                # Sichere Berechtigungen setzen
                os.chmod(self.secure_yaml_path, 0o600)
                console.print(f"[green]✓[/green] Secure-Konfiguration gespeichert: {self.secure_yaml_path}")
            
            return True
            
        except Exception as e:
            console.print(f"[red]✗[/red] Fehler beim Speichern: {e}")
            return False
    
    def load_config(self) -> Optional[Dict]:
        """Lädt Konfiguration aus clouds.yaml"""
        try:
            if not self.clouds_yaml_path.exists():
                return None
            
            with open(self.clouds_yaml_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Lade secure.yaml falls vorhanden
            if self.secure_yaml_path.exists():
                with open(self.secure_yaml_path, 'r') as f:
                    secure_config = yaml.safe_load(f)
                    
                # Merge Passwörter
                if "clouds" in secure_config:
                    for cloud_name, cloud_config in secure_config["clouds"].items():
                        if cloud_name in config.get("clouds", {}):
                            if "auth" in cloud_config and "password" in cloud_config["auth"]:
                                if "auth" not in config["clouds"][cloud_name]:
                                    config["clouds"][cloud_name]["auth"] = {}
                                config["clouds"][cloud_name]["auth"]["password"] = \
                                    secure_config["clouds"][cloud_name]["auth"]["password"]
            
            return config
            
        except Exception as e:
            console.print(f"[red]✗[/red] Fehler beim Laden: {e}")
            return None
    
    def validate_config(self, config: Optional[Dict] = None) -> bool:
        """
        Validiert OpenStack Konfiguration
        
        Args:
            config: Optional Konfiguration (sonst wird geladen)
            
        Returns:
            True wenn gültig
        """
        if config is None:
            config = self.load_config()
        
        if config is None:
            console.print("[red]✗[/red] Keine Konfiguration gefunden")
            return False
        
        if "clouds" not in config:
            console.print("[red]✗[/red] 'clouds' Sektion fehlt")
            return False
        
        for cloud_name, cloud_config in config["clouds"].items():
            if "auth" not in cloud_config:
                console.print(f"[red]✗[/red] 'auth' fehlt für Cloud '{cloud_name}'")
                return False
            
            auth = cloud_config["auth"]
            required_fields = ["auth_url", "project_name", "username"]
            
            for field in required_fields:
                if field not in auth or not auth[field]:
                    console.print(f"[red]✗[/red] '{field}' fehlt für Cloud '{cloud_name}'")
                    return False
        
        console.print("[green]✓[/green] Konfiguration ist gültig")
        return True
    
    def get_cloud_config(self, cloud_name: str) -> Optional[Dict]:
        """Gibt Konfiguration für eine spezifische Cloud zurück"""
        config = self.load_config()
        if config and "clouds" in config:
            return config["clouds"].get(cloud_name)
        return None

