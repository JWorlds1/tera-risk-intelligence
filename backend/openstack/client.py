"""
OpenStack Client Wrapper
Bietet einfache Schnittstelle für OpenStack-Operationen
"""
import os
from typing import List, Dict, Optional, Any
from openstack import connection
from openstack.exceptions import HttpException
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from .config_manager import OpenStackConfigManager

console = Console()


class OpenStackClient:
    """OpenStack Client Wrapper für einfache Operationen"""
    
    def __init__(self, cloud_name: str = "hda-cloud", config_dir: Optional[str] = None):
        """
        Initialisiert OpenStack Client
        
        Args:
            cloud_name: Name der Cloud-Konfiguration
            config_dir: Optional: Verzeichnis für clouds.yaml
        """
        self.cloud_name = cloud_name
        self.config_manager = OpenStackConfigManager(config_dir)
        self.conn = None
    
    def connect(self) -> bool:
        """
        Stellt Verbindung zu OpenStack her
        
        Returns:
            True bei Erfolg
        """
        try:
            # Lade Konfiguration
            config = self.config_manager.load_config()
            if not config:
                console.print("[red]✗[/red] Keine Konfiguration gefunden. Führe Setup aus.")
                return False
            
            # Stelle Verbindung her
            self.conn = connection.Connection(
                cloud=self.cloud_name,
                config_dir=str(self.config_manager.config_dir.parent)
            )
            
            # Teste Verbindung
            self.conn.authorize()
            console.print(f"[green]✓[/green] Verbindung zu OpenStack erfolgreich")
            return True
            
        except Exception as e:
            console.print(f"[red]✗[/red] Verbindungsfehler: {e}")
            return False
    
    def list_servers(self, detailed: bool = False) -> List[Dict]:
        """
        Listet alle Server auf
        
        Args:
            detailed: Ob detaillierte Informationen angezeigt werden sollen
            
        Returns:
            Liste von Server-Dicts
        """
        if not self.conn:
            if not self.connect():
                return []
        
        try:
            servers = list(self.conn.compute.servers())
            
            if detailed:
                return [self._server_to_dict(s) for s in servers]
            else:
                return [{"id": s.id, "name": s.name, "status": s.status} for s in servers]
                
        except Exception as e:
            console.print(f"[red]✗[/red] Fehler beim Auflisten der Server: {e}")
            return []
    
    def get_server(self, server_id: str) -> Optional[Dict]:
        """
        Holt Details eines Servers
        
        Args:
            server_id: Server ID oder Name
            
        Returns:
            Server-Dict oder None
        """
        if not self.conn:
            if not self.connect():
                return None
        
        try:
            server = self.conn.compute.find_server(server_id)
            if server:
                return self._server_to_dict(server)
            return None
            
        except Exception as e:
            console.print(f"[red]✗[/red] Fehler beim Abrufen des Servers: {e}")
            return None
    
    def create_server(
        self,
        name: str,
        image: str,
        flavor: str,
        network: str,
        key_name: Optional[str] = None,
        security_groups: Optional[List[str]] = None,
        user_data: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict]:
        """
        Erstellt einen neuen Server
        
        Args:
            name: Server-Name
            image: Image Name oder ID
            flavor: Flavor Name oder ID
            network: Network Name oder ID
            key_name: Optional: SSH Key Name
            security_groups: Optional: Liste von Security Group Namen
            user_data: Optional: User-Data Script
            **kwargs: Weitere Server-Parameter
            
        Returns:
            Server-Dict oder None
        """
        if not self.conn:
            if not self.connect():
                return None
        
        try:
            # Finde Image
            img = self.conn.compute.find_image(image)
            if not img:
                console.print(f"[red]✗[/red] Image '{image}' nicht gefunden")
                return None
            
            # Finde Flavor
            flv = self.conn.compute.find_flavor(flavor)
            if not flv:
                console.print(f"[red]✗[/red] Flavor '{flavor}' nicht gefunden")
                return None
            
            # Finde Network
            net = self.conn.network.find_network(network)
            if not net:
                console.print(f"[red]✗[/red] Network '{network}' nicht gefunden")
                return None
            
            # Erstelle Server
            server = self.conn.compute.create_server(
                name=name,
                image_id=img.id,
                flavor_id=flv.id,
                networks=[{"uuid": net.id}],
                key_name=key_name,
                security_groups=security_groups or [],
                user_data=user_data,
                **kwargs
            )
            
            console.print(f"[green]✓[/green] Server '{name}' wird erstellt...")
            return self._server_to_dict(server)
            
        except Exception as e:
            console.print(f"[red]✗[/red] Fehler beim Erstellen des Servers: {e}")
            return None
    
    def delete_server(self, server_id: str) -> bool:
        """
        Löscht einen Server
        
        Args:
            server_id: Server ID oder Name
            
        Returns:
            True bei Erfolg
        """
        if not self.conn:
            if not self.connect():
                return False
        
        try:
            server = self.conn.compute.find_server(server_id)
            if not server:
                console.print(f"[red]✗[/red] Server '{server_id}' nicht gefunden")
                return False
            
            self.conn.compute.delete_server(server)
            console.print(f"[green]✓[/green] Server '{server_id}' wird gelöscht...")
            return True
            
        except Exception as e:
            console.print(f"[red]✗[/red] Fehler beim Löschen des Servers: {e}")
            return False
    
    def list_images(self) -> List[Dict]:
        """Listet alle verfügbaren Images auf"""
        if not self.conn:
            if not self.connect():
                return []
        
        try:
            images = list(self.conn.compute.images())
            return [{"id": img.id, "name": img.name, "status": img.status} for img in images]
        except Exception as e:
            console.print(f"[red]✗[/red] Fehler beim Auflisten der Images: {e}")
            return []
    
    def list_flavors(self) -> List[Dict]:
        """Listet alle verfügbaren Flavors auf"""
        if not self.conn:
            if not self.connect():
                return []
        
        try:
            flavors = list(self.conn.compute.flavors())
            return [
                {
                    "id": flv.id,
                    "name": flv.name,
                    "vcpus": flv.vcpus,
                    "ram": flv.ram,
                    "disk": flv.disk
                }
                for flv in flavors
            ]
        except Exception as e:
            console.print(f"[red]✗[/red] Fehler beim Auflisten der Flavors: {e}")
            return []
    
    def list_networks(self) -> List[Dict]:
        """Listet alle verfügbaren Networks auf"""
        if not self.conn:
            if not self.connect():
                return []
        
        try:
            networks = list(self.conn.network.networks())
            return [{"id": net.id, "name": net.name, "status": net.status} for net in networks]
        except Exception as e:
            console.print(f"[red]✗[/red] Fehler beim Auflisten der Networks: {e}")
            return []
    
    def list_security_groups(self) -> List[Dict]:
        """Listet alle Security Groups auf"""
        if not self.conn:
            if not self.connect():
                return []
        
        try:
            sec_groups = list(self.conn.network.security_groups())
            return [{"id": sg.id, "name": sg.name, "description": sg.description} for sg in sec_groups]
        except Exception as e:
            console.print(f"[red]✗[/red] Fehler beim Auflisten der Security Groups: {e}")
            return []
    
    def print_servers_table(self, servers: Optional[List[Dict]] = None):
        """Zeigt Server in einer schönen Tabelle"""
        if servers is None:
            servers = self.list_servers(detailed=True)
        
        if not servers:
            console.print("[yellow]Keine Server gefunden[/yellow]")
            return
        
        table = Table(title="OpenStack Server")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Image", style="blue")
        table.add_column("Flavor", style="magenta")
        table.add_column("IP", style="red")
        
        for server in servers:
            table.add_row(
                server.get("id", "")[:8] + "...",
                server.get("name", ""),
                server.get("status", ""),
                server.get("image", {}).get("name", ""),
                server.get("flavor", {}).get("name", ""),
                server.get("ip", "")
            )
        
        console.print(table)
    
    def _server_to_dict(self, server) -> Dict:
        """Konvertiert Server-Objekt zu Dict"""
        return {
            "id": server.id,
            "name": server.name,
            "status": server.status,
            "created": server.created_at.isoformat() if server.created_at else None,
            "image": {"id": server.image.get("id", ""), "name": ""} if server.image else {},
            "flavor": {"id": server.flavor.get("id", ""), "name": ""} if server.flavor else {},
            "ip": self._get_server_ip(server),
            "metadata": server.metadata,
        }
    
    def _get_server_ip(self, server) -> str:
        """Extrahiert IP-Adresse aus Server"""
        try:
            addresses = server.addresses or {}
            for network_name, addr_list in addresses.items():
                if addr_list:
                    for addr in addr_list:
                        if addr.get("version") == 4:
                            return addr.get("addr", "")
        except:
            pass
        return ""

