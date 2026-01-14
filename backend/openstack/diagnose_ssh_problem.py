#!/usr/bin/env python3
"""
Diagnostiziert SSH-Problem systematisch
"""
import sys
from pathlib import Path
from openstack import connection
from rich.console import Console
from rich.table import Table
import datetime

console = Console()

def diagnose_ssh_problem(server_id):
    """Systematische Diagnose des SSH-Problems"""
    
    try:
        conn = connection.Connection(
            cloud='openstack',
            config_dir=str(Path.home() / ".config" / "openstack")
        )
        conn.authorize()
        console.print("[green]✓[/green] Verbindung erfolgreich")
    except Exception as e:
        console.print(f"[red]✗[/red] Fehler: {e}")
        sys.exit(1)
    
    try:
        server = conn.compute.get_server(server_id)
        
        console.print("\n[bold cyan]=== SSH-Problem Diagnose ===[/bold cyan]\n")
        
        # 1. Server-Status
        console.print("[bold]1. Server-Status:[/bold]")
        created = datetime.datetime.fromisoformat(server.created_at.replace('Z', '+00:00'))
        now = datetime.datetime.now(datetime.timezone.utc)
        age = now - created
        
        table = Table()
        table.add_column("Eigenschaft", style="cyan")
        table.add_column("Wert", style="green")
        
        table.add_row("Name", server.name)
        table.add_row("Status", server.status)
        table.add_row("Power State", str(server.power_state))
        table.add_row("Alter", f"{int(age.total_seconds()/60)} Minuten")
        table.add_row("SSH-Key", getattr(server, 'key_name', 'None'))
        
        console.print(table)
        
        # 2. IP-Adressen
        console.print("\n[bold]2. Netzwerk-Konfiguration:[/bold]")
        addresses = server.addresses or {}
        for net_name, addr_list in addresses.items():
            for addr in addr_list:
                if addr.get("version") == 4:
                    ip = addr.get("addr")
                    console.print(f"  IP: {ip}")
                    console.print(f"  Network: {net_name}")
        
        # 3. Security Groups
        console.print("\n[bold]3. Security Groups:[/bold]")
        sec_groups = server.security_groups or []
        ssh_allowed = False
        
        for sg in sec_groups:
            sg_name = sg.get('name') if isinstance(sg, dict) else (sg.name if hasattr(sg, 'name') else 'Unknown')
            sg_id = sg.get('id') if isinstance(sg, dict) else (sg.id if hasattr(sg, 'id') else None)
            
            console.print(f"  - {sg_name}")
            
            try:
                if sg_id:
                    sg_obj = conn.network.get_security_group(sg_id)
                else:
                    sg_obj = conn.network.find_security_group(sg_name)
                
                if sg_obj:
                    rules = list(conn.network.security_group_rules(security_group_id=sg_obj.id))
                    for rule in rules:
                        if (rule.direction == 'ingress' and 
                            rule.protocol == 'tcp' and
                            rule.port_range_min == 22 and
                            rule.port_range_max == 22):
                            ssh_allowed = True
                            console.print(f"    [green]✓[/green] SSH (Port 22) erlaubt")
                            break
            except Exception as e:
                console.print(f"    [yellow]⚠[/yellow] Konnte Rules nicht prüfen")
        
        if not ssh_allowed:
            console.print("  [red]✗[/red] SSH könnte blockiert sein!")
        
        # 4. Mögliche Probleme
        console.print("\n[bold yellow]4. Mögliche Probleme:[/bold yellow]")
        
        problems = []
        
        if age.total_seconds() < 120:
            problems.append("Server ist sehr neu - SSH könnte noch starten")
        
        if not getattr(server, 'key_name', None):
            problems.append("Kein SSH-Key zugewiesen (aber Passwort sollte funktionieren)")
        
        if not ssh_allowed:
            problems.append("Security Group erlaubt SSH möglicherweise nicht")
        
        # Ubuntu Cloud Image spezifisch
        problems.append("Ubuntu Cloud Images starten SSH möglicherweise nicht automatisch")
        problems.append("cloud-init könnte SSH verzögert konfigurieren")
        problems.append("user_data Script könnte SSH nicht richtig starten")
        
        for i, problem in enumerate(problems, 1):
            console.print(f"  {i}. {problem}")
        
        # 5. Lösungsvorschläge
        console.print("\n[bold green]5. Lösungsvorschläge:[/bold green]")
        console.print("  A. Console-Login im Dashboard versuchen:")
        console.print("     - User: ubuntu")
        console.print("     - Passwort: ubuntu123")
        console.print("  B. Falls Login funktioniert:")
        console.print("     sudo systemctl status ssh")
        console.print("     sudo systemctl start ssh")
        console.print("  C. Prüfen Sie /var/log/server-setup.log")
        console.print("  D. Prüfen Sie cloud-init Logs:")
        console.print("     sudo cat /var/log/cloud-init.log")
        console.print("     sudo cat /var/log/cloud-init-output.log")
        
        # 6. Test-Connection
        console.print("\n[bold]6. Netzwerk-Test:[/bold]")
        if addresses:
            for net_name, addr_list in addresses.items():
                for addr in addr_list:
                    if addr.get("version") == 4:
                        ip = addr.get("addr")
                        console.print(f"  Teste Verbindung zu {ip}...")
                        import subprocess
                        result = subprocess.run(
                            ["nc", "-zv", "-w", "3", ip, "22"],
                            capture_output=True,
                            text=True
                        )
                        if result.returncode == 0:
                            console.print(f"  [green]✓[/green] Port 22 ist erreichbar!")
                        else:
                            console.print(f"  [red]✗[/red] Port 22 antwortet nicht (Connection refused)")
                            console.print(f"     Das bedeutet: Server erreicht, aber SSH läuft nicht")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    server_id = "125b18e3-b3c6-406c-9349-d5ee9f0b0b4f"  # Neuester Server
    if len(sys.argv) > 1:
        server_id = sys.argv[1]
    
    diagnose_ssh_problem(server_id)

