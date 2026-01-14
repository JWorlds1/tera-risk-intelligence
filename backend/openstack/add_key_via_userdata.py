#!/usr/bin/env python3
"""
Fügt SSH-Key über user_data hinzu (benötigt Server-Neustart)
"""
import sys
from pathlib import Path
from openstack import connection
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
import base64

console = Console()

def add_key_via_userdata(server_id, ssh_key_name="hopp"):
    """Fügt SSH-Key über user_data hinzu und startet Server neu"""
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
        
        # Hole SSH-Key
        ssh_key = conn.compute.find_keypair(ssh_key_name)
        if not ssh_key:
            console.print(f"[red]✗[/red] SSH-Key '{ssh_key_name}' nicht gefunden")
            sys.exit(1)
        
        # Hole öffentlichen Key
        public_key = ssh_key.public_key
        
        console.print(f"\n[green]✓[/green] SSH-Key gefunden: {ssh_key_name}")
        console.print(f"  Fingerprint: {ssh_key.fingerprint}")
        
        console.print("\n[yellow]⚠[/yellow] Hinweis:")
        console.print("  Diese Methode fügt den SSH-Key über user_data hinzu.")
        console.print("  Der Server muss neu gestartet werden, damit die Änderung wirksam wird.")
        
        if not Confirm.ask("\n[yellow]Möchten Sie fortfahren?[/yellow]", default=False):
            console.print("[yellow]Abgebrochen[/yellow]")
            sys.exit(0)
        
        # Erstelle user_data Script das den Key hinzufügt
        user_data_script = f"""#!/bin/bash
set -e
exec > /var/log/add-ssh-key.log 2>&1
echo "Adding SSH Key: $(date)"

# Erstelle .ssh Verzeichnis für ubuntu User
mkdir -p /home/ubuntu/.ssh
chmod 700 /home/ubuntu/.ssh

# Füge öffentlichen Key hinzu
echo "{public_key}" >> /home/ubuntu/.ssh/authorized_keys
chmod 600 /home/ubuntu/.ssh/authorized_keys
chown -R ubuntu:ubuntu /home/ubuntu/.ssh

# Stelle sicher dass SSH läuft
systemctl enable ssh
systemctl start ssh

echo "SSH Key added successfully: $(date)"
"""
        
        user_data_encoded = base64.b64encode(user_data_script.encode('utf-8')).decode('ascii')
        
        # OpenStack erlaubt keine direkte user_data-Änderung nach Erstellung
        # Wir müssen den Server neu erstellen ODER über Console zugreifen
        
        console.print("\n[red]✗[/red] OpenStack erlaubt keine user_data-Änderung nach Server-Erstellung")
        console.print("\n[bold cyan]Verfügbare Optionen:[/bold cyan]")
        console.print("\n1. [yellow]Console-Zugriff[/yellow] (falls verfügbar):")
        console.print("   - Öffnen Sie das OpenStack Dashboard")
        console.print("   - Gehen Sie zu Compute > Instances")
        console.print("   - Klicken Sie auf 'Console' für den Server")
        console.print("   - Fügen Sie den Key manuell hinzu:")
        console.print(f"     mkdir -p ~/.ssh")
        console.print(f"     echo '{public_key}' >> ~/.ssh/authorized_keys")
        console.print(f"     chmod 600 ~/.ssh/authorized_keys")
        
        console.print("\n2. [yellow]Server neu erstellen[/yellow] (mit SSH-Key):")
        console.print("   python3 backend/openstack/create_server_simple.py")
        console.print("   (Das Script wurde aktualisiert und verwendet jetzt automatisch den Key)")
        
        console.print("\n3. [yellow]Passwort-Login aktivieren[/yellow] (über Console):")
        console.print("   sudo passwd ubuntu")
        console.print("   sudo sed -i 's/#PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config")
        console.print("   sudo systemctl restart sshd")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    server_id = "e73e74c7-4648-4c91-9811-2bcc7a748a88"
    ssh_key_name = "hopp"
    
    if len(sys.argv) > 1:
        server_id = sys.argv[1]
    if len(sys.argv) > 2:
        ssh_key_name = sys.argv[2]
    
    add_key_via_userdata(server_id, ssh_key_name)

