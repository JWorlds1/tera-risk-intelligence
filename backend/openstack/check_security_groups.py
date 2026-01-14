#!/usr/bin/env python3
"""
Prüft Security Groups eines Servers
"""
import sys
from pathlib import Path
from openstack import connection
from rich.console import Console
from rich.table import Table

console = Console()

def check_security_groups(server_id):
    """Prüft Security Groups eines Servers"""
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
            console.print("\n[yellow]⚠[/yellow] Keine Security Groups zugewiesen")
        else:
            console.print(f"\n[bold]Security Groups:[/bold]")
            ssh_allowed_check = False
            
            for sg in sec_groups:
                sg_name = sg.get('name') if isinstance(sg, dict) else (sg.name if hasattr(sg, 'name') else 'Unknown')
                sg_id = sg.get('id') if isinstance(sg, dict) else (sg.id if hasattr(sg, 'id') else None)
                
                console.print(f"  - {sg_name}")
                
                # Hole Details der Security Group
                try:
                    if sg_id:
                        sg_obj = conn.network.get_security_group(sg_id)
                    else:
                        sg_obj = conn.network.find_security_group(sg_name)
                    
                    if sg_obj:
                        console.print(f"\n    [cyan]Security Group: {sg_obj.name}[/cyan]")
                        
                        # Hole Rules direkt
                        rules = list(conn.network.security_group_rules(security_group_id=sg_obj.id))
                        
                        if rules:
                            table = Table()
                            table.add_column("Direction", style="cyan")
                            table.add_column("Protocol", style="yellow")
                            table.add_column("Port", style="green")
                            table.add_column("Remote", style="magenta")
                            
                            for rule in rules:
                                direction = rule.direction
                                protocol = rule.protocol or "all"
                                port_range = ""
                                if rule.port_range_min is not None and rule.port_range_max is not None:
                                    if rule.port_range_min == rule.port_range_max:
                                        port_range = str(rule.port_range_min)
                                    else:
                                        port_range = f"{rule.port_range_min}-{rule.port_range_max}"
                                elif rule.port_range_min is not None:
                                    port_range = f"{rule.port_range_min}+"
                                
                                remote = rule.remote_ip_prefix or (rule.remote_group_id if rule.remote_group_id else "any")
                                
                                table.add_row(
                                    direction,
                                    protocol,
                                    port_range or "all",
                                    str(remote)
                                )
                                
                                # Prüfe SSH
                                if (direction == 'ingress' and 
                                    (protocol == 'tcp' or protocol is None) and
                                    (rule.port_range_min is None or rule.port_range_min <= 22) and
                                    (rule.port_range_max is None or rule.port_range_max >= 22)):
                                    ssh_allowed_check = True
                            
                            console.print(table)
                        else:
                            console.print("    [dim]Keine Rules definiert[/dim]")
                except Exception as e:
                    console.print(f"    [yellow]⚠[/yellow] Konnte Details nicht abrufen: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Setze ssh_allowed basierend auf Check
            ssh_allowed = ssh_allowed_check
        
        # Prüfe ob SSH (Port 22) erlaubt ist
        ssh_allowed = False
        for sg in sec_groups:
            try:
                sg_obj = conn.network.find_security_group(sg.get('id') or sg.get('name'))
                if sg_obj:
                    rules = sg_obj.security_group_rules or []
                    for rule in rules:
                        if (rule.direction == 'ingress' and 
                            (rule.protocol == 'tcp' or rule.protocol is None) and
                            (rule.port_range_min is None or rule.port_range_min <= 22) and
                            (rule.port_range_max is None or rule.port_range_max >= 22)):
                            ssh_allowed = True
                            break
            except:
                pass
        
        console.print(f"\n[bold]SSH-Zugriff (Port 22):[/bold]")
        if ssh_allowed:
            console.print("  [green]✓[/green] SSH sollte erlaubt sein")
        else:
            console.print("  [red]✗[/red] SSH könnte blockiert sein")
            console.print("  [yellow]Hinweis:[/yellow] Fügen Sie eine Security Group Rule hinzu:")
            console.print("    - Direction: ingress")
            console.print("    - Protocol: TCP")
            console.print("    - Port: 22")
            console.print("    - Remote: 0.0.0.0/0 (oder Ihr VPN-Subnetz)")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    server_id = "e73e74c7-4648-4c91-9811-2bcc7a748a88"
    if len(sys.argv) > 1:
        server_id = sys.argv[1]
    
    check_security_groups(server_id)

