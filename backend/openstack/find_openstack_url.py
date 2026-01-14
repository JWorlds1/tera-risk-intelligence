#!/usr/bin/env python3
"""
Versucht verschiedene OpenStack Identity URLs zu finden
"""
import requests
import socket
from urllib.parse import urlparse
from rich.console import Console
from rich.table import Table

console = Console()

# Mögliche URLs zum Testen
POSSIBLE_URLS = [
    "https://identity.hda-cloud.de:5000/v3",
    "https://keystone.hda-cloud.de:5000/v3",
    "https://identity.h-da.de:5000/v3",
    "https://keystone.h-da.de:5000/v3",
    "https://openstack.hda-cloud.de:5000/v3",
    "https://cloud.h-da.de:5000/v3",
    "https://identity.h-da.de/v3",
    "https://keystone.h-da.de/v3",
]

# Mögliche IPs (falls bekannt)
POSSIBLE_IPS = []

def test_url(url):
    """Testet ob eine URL erreichbar ist"""
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or 443
        
        # Teste DNS-Auflösung
        try:
            ip = socket.gethostbyname(host)
            console.print(f"  [green]✓[/green] DNS: {host} -> {ip}")
        except socket.gaierror:
            console.print(f"  [red]✗[/red] DNS: {host} kann nicht aufgelöst werden")
            return False
        
        # Teste Verbindung
        try:
            response = requests.get(url, timeout=5, verify=False)
            console.print(f"  [green]✓[/green] HTTP: Status {response.status_code}")
            return True
        except requests.exceptions.RequestException as e:
            console.print(f"  [yellow]⚠[/yellow] HTTP: {str(e)[:50]}")
            # Auch wenn HTTP fehlschlägt, könnte die Domain existieren
            return True  # DNS funktioniert
        
    except Exception as e:
        console.print(f"  [red]✗[/red] Fehler: {e}")
        return False

def main():
    console.print("\n[bold cyan]Suche nach OpenStack Identity URL[/bold cyan]")
    console.print("=" * 60)
    
    table = Table(title="URL Tests")
    table.add_column("URL", style="cyan")
    table.add_column("DNS", style="yellow")
    table.add_column("Status", style="green")
    
    working_urls = []
    
    for url in POSSIBLE_URLS:
        console.print(f"\n[yellow]Teste:[/yellow] {url}")
        parsed = urlparse(url)
        host = parsed.hostname
        
        dns_ok = False
        try:
            ip = socket.gethostbyname(host)
            dns_ok = True
            dns_status = f"✓ {ip}"
        except socket.gaierror:
            dns_status = "✗ Nicht auflösbar"
        
        if dns_ok:
            try:
                response = requests.get(url, timeout=5, verify=False)
                status = f"✓ {response.status_code}"
                working_urls.append(url)
            except:
                status = "⚠ Verbindung fehlgeschlagen"
        else:
            status = "-"
        
        table.add_row(url, dns_status, status)
    
    console.print("\n")
    console.print(table)
    
    if working_urls:
        console.print(f"\n[bold green]✓ Gefundene URLs:[/bold green]")
        for url in working_urls:
            console.print(f"  {url}")
    else:
        console.print("\n[bold red]✗ Keine erreichbaren URLs gefunden[/bold red]")
        console.print("\n[yellow]Mögliche Lösungen:[/yellow]")
        console.print("1. Prüfen Sie die HDA Cloud Dokumentation")
        console.print("2. Fragen Sie Ihren Administrator nach der korrekten URL")
        console.print("3. Prüfen Sie das HDA Cloud Dashboard")
        console.print("4. Möglicherweise benötigen Sie eine IP-Adresse statt Domain")

if __name__ == "__main__":
    main()

