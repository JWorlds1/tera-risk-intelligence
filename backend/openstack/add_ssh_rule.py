#!/usr/bin/env python3
"""
Fügt SSH-Zugriff (Port 22) zu einer Security Group hinzu
"""
import sys
from pathlib import Path
from openstack import connection
from rich.console import Console
from rich.panel import Panel

console = Console()

def add_ssh_rule(server_id, cidr="0.0.0.0/0"):
    """Fügt SSH-Rule zur Security Group des Servers hinzu"""
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
        
        # Hole Security Groups
        sec_groups = server.security_groups or []
        
        if not sec_groups:
            console.print("[red]✗[/red] Keine Security Groups gefunden")
            sys.exit(1)
        
        # Verwende die erste Security Group (normalerweise "default")
        sg_info = sec_groups[0]
        sg_name = sg_info.get('name') if isinstance(sg_info, dict) else (sg_info.name if hasattr(sg_info, 'name') else 'default')
        sg_id = sg_info.get('id') if isinstance(sg_info, dict) else (sg_info.id if hasattr(sg_info, 'id') else None)
        
        console.print(f"\n[yellow]Verwende Security Group:[/yellow] {sg_name}")
        
        # Hole Security Group Objekt
        if sg_id:
            sg = conn.network.get_security_group(sg_id)
        else:
            sg = conn.network.find_security_group(sg_name)
        
        if not sg:
            console.print(f"[red]✗[/red] Security Group '{sg_name}' nicht gefunden")
            sys.exit(1)
        
        # Prüfe ob SSH-Rule bereits existiert
        existing_rules = list(conn.network.security_group_rules(security_group_id=sg.id))
        ssh_exists = False
        
        for rule in existing_rules:
            if (rule.direction == 'ingress' and 
                rule.protocol == 'tcp' and
                rule.port_range_min == 22 and
                rule.port_range_max == 22):
                ssh_exists = True
                console.print(f"\n[yellow]⚠[/yellow] SSH-Rule existiert bereits:")
                console.print(f"  Remote: {rule.remote_ip_prefix or 'any'}")
                break
        
        if not ssh_exists:
            console.print(f"\n[yellow]Füge SSH-Rule hinzu...[/yellow]")
            console.print(f"  Direction: ingress")
            console.print(f"  Protocol: TCP")
            console.print(f"  Port: 22")
            console.print(f"  Remote: {cidr}")
            
            # Erstelle Rule
            rule = conn.network.create_security_group_rule(
                security_group_id=sg.id,
                direction='ingress',
                protocol='tcp',
                port_range_min=22,
                port_range_max=22,
                remote_ip_prefix=cidr
            )
            
            console.print(f"[green]✓[/green] SSH-Rule erfolgreich hinzugefügt!")
        else:
            console.print(f"\n[green]✓[/green] SSH-Rule existiert bereits")
        
        console.print("\n" + "=" * 60)
        console.print(Panel.fit(
            "[bold green]✓ Security Group aktualisiert![/bold green]\n"
            f"SSH-Zugriff von {cidr} ist jetzt erlaubt",
            border_style="green"
        ))
        console.print("=" * 60)
        
        console.print(f"\n[bold]Versuchen Sie jetzt:[/bold]")
        console.print(f"  ssh ubuntu@10.193.17.102")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    server_id = "e73e74c7-4648-4c91-9811-2bcc7a748a88"
    cidr = "0.0.0.0/0"  # Erlaubt Zugriff von überall
    
    if len(sys.argv) > 1:
        server_id = sys.argv[1]
    if len(sys.argv) > 2:
        cidr = sys.argv[2]
    
    add_ssh_rule(server_id, cidr)

