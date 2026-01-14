#!/usr/bin/env python3
"""Testet verschiedene Ports für cloud.h-da.de"""
import requests
import socket
from rich.console import Console

console = Console()

base_host = "cloud.h-da.de"
ports_to_test = [5000, 443, 80, 8443, 35357, 9292]

console.print(f"\n[bold cyan]Teste Ports für {base_host}[/bold cyan]")
console.print("=" * 60)

try:
    ip = socket.gethostbyname(base_host)
    console.print(f"✓ IP-Adresse: {ip}\n")
except:
    console.print("✗ DNS-Auflösung fehlgeschlagen")
    exit(1)

for port in ports_to_test:
    for path in ["/v3", "/v3/auth/tokens", "/", "/identity/v3"]:
        url = f"https://{base_host}:{port}{path}"
        try:
            response = requests.get(url, timeout=3, verify=False, allow_redirects=False)
            console.print(f"[green]✓[/green] {url} - Status: {response.status_code}")
            if response.status_code in [200, 300, 301, 302, 401, 403]:
                console.print(f"  [bold green]→ Mögliche OpenStack URL![/bold green]")
        except requests.exceptions.SSLError:
            # SSL Fehler bedeutet, dass der Port erreichbar ist
            console.print(f"[yellow]⚠[/yellow] {url} - SSL Fehler (Port erreichbar)")
        except requests.exceptions.ConnectionError:
            pass  # Port nicht erreichbar
        except Exception as e:
            pass

console.print("\n[yellow]Hinweis:[/yellow] Prüfen Sie auch:")
console.print("  - HDA Cloud Dashboard für die korrekte URL")
console.print("  - Dokumentation oder Anleitungen von HDA")
console.print("  - Möglicherweise ist es eine interne IP-Adresse")

