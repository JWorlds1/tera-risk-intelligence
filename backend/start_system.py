# start_system.py - Startet das komplette Real-time System
import asyncio
import subprocess
import sys
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

console = Console()

def check_dependencies():
    """Prüfe ob alle Dependencies installiert sind"""
    console.print("[bold blue]Checking dependencies...[/bold blue]")
    
    required_packages = [
        'fastapi', 'uvicorn', 'websockets', 'aiohttp', 
        'beautifulsoup4', 'playwright', 'pydantic',
        'structlog', 'rich', 'pandas', 'pyarrow'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        console.print(f"[red]Missing packages: {', '.join(missing_packages)}[/red]")
        console.print("[yellow]Run: pip install -r requirements.txt[/yellow]")
        return False
    
    console.print("[green]✅ All dependencies installed[/green]")
    return True

def check_playwright():
    """Prüfe ob Playwright installiert ist"""
    console.print("[bold blue]Checking Playwright...[/bold blue]")
    
    try:
        result = subprocess.run(['playwright', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            console.print("[green]✅ Playwright installed[/green]")
            return True
    except:
        pass
    
    console.print("[yellow]Installing Playwright browsers...[/yellow]")
    try:
        subprocess.run(['playwright', 'install', 'chromium'], 
                      check=True, timeout=300)
        console.print("[green]✅ Playwright browsers installed[/green]")
        return True
    except Exception as e:
        console.print(f"[red]❌ Playwright installation failed: {e}[/red]")
        return False

def check_ollama():
    """Prüfe ob Ollama läuft"""
    console.print("[bold blue]Checking Ollama...[/bold blue]")
    
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            if models:
                console.print(f"[green]✅ Ollama running with {len(models)} models[/green]")
                return True
            else:
                console.print("[yellow]⚠️ Ollama running but no models installed[/yellow]")
                console.print("[yellow]Run: ollama pull llama2:7b[/yellow]")
                return False
    except:
        pass
    
    console.print("[yellow]⚠️ Ollama not running[/yellow]")
    console.print("[yellow]Start Ollama: ollama serve[/yellow]")
    return False

def create_directories():
    """Erstelle benötigte Verzeichnisse"""
    console.print("[bold blue]Creating directories...[/bold blue]")
    
    directories = [
        'data',
        'data/json',
        'data/csv', 
        'data/parquet',
        'data/analytics',
        'templates',
        'logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    console.print("[green]✅ Directories created[/green]")

def start_services():
    """Starte alle Services"""
    console.print("[bold blue]Starting services...[/bold blue]")
    
    services = [
        {
            'name': 'Real-time Extractor API',
            'command': [sys.executable, 'real_time_extractor.py'],
            'port': 8001
        },
        {
            'name': 'Real-time Dashboard',
            'command': [sys.executable, 'real_time_dashboard.py'],
            'port': 8002
        }
    ]
    
    processes = []
    
    for service in services:
        console.print(f"Starting {service['name']} on port {service['port']}...")
        try:
            process = subprocess.Popen(service['command'])
            processes.append(process)
            time.sleep(2)  # Warte kurz zwischen Services
        except Exception as e:
            console.print(f"[red]❌ Failed to start {service['name']}: {e}[/red]")
    
    return processes

def run_tests():
    """Führe Tests aus"""
    console.print("[bold blue]Running tests...[/bold blue]")
    
    try:
        result = subprocess.run([sys.executable, 'test_real_time.py'], 
                              capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            console.print("[green]✅ Tests passed[/green]")
            return True
        else:
            console.print(f"[red]❌ Tests failed: {result.stderr}[/red]")
            return False
    except subprocess.TimeoutExpired:
        console.print("[red]❌ Tests timed out[/red]")
        return False
    except Exception as e:
        console.print(f"[red]❌ Test error: {e}[/red]")
        return False

def main():
    """Hauptfunktion"""
    console.print(Panel.fit(
        "🚀 Climate Conflict Real-time System Startup",
        subtitle="Garantierte Extraktion & Echtzeit-Monitoring",
        border_style="blue"
    ))
    
    # 1. Dependencies prüfen
    if not check_dependencies():
        return 1
    
    # 2. Playwright prüfen
    if not check_playwright():
        return 1
    
    # 3. Ollama prüfen (optional)
    ollama_available = check_ollama()
    
    # 4. Verzeichnisse erstellen
    create_directories()
    
    # 5. Tests ausführen
    console.print("\n[bold yellow]Do you want to run tests? (y/n):[/bold yellow]")
    run_tests_input = input().lower().strip()
    
    if run_tests_input == 'y':
        if not run_tests():
            console.print("[red]Tests failed. Continue anyway? (y/n):[/red]")
            if input().lower().strip() != 'y':
                return 1
    
    # 6. Services starten
    console.print("\n[bold green]Starting Real-time System...[/bold green]")
    processes = start_services()
    
    # 7. Status anzeigen
    console.print("\n[bold green]🎉 System started successfully![/bold green]")
    console.print("\n[bold cyan]Available Services:[/bold cyan]")
    console.print("• Real-time Extractor API: http://localhost:8001")
    console.print("• Real-time Dashboard: http://localhost:8002")
    console.print("• API Documentation: http://localhost:8001/docs")
    
    console.print("\n[bold cyan]Quick Start:[/bold cyan]")
    console.print("1. Open Dashboard: http://localhost:8002")
    console.print("2. Add Strategic URLs: Click 'Add Strategic URLs' button")
    console.print("3. Monitor Real-time: Watch jobs process in real-time")
    
    if not ollama_available:
        console.print("\n[bold yellow]⚠️ AI Features disabled (Ollama not running)[/bold yellow]")
        console.print("To enable AI features:")
        console.print("1. Start Ollama: ollama serve")
        console.print("2. Install models: ollama pull llama2:7b")
        console.print("3. Restart system")
    
    console.print("\n[bold cyan]Press Ctrl+C to stop all services[/bold cyan]")
    
    try:
        # Warte auf Interrupt
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Stopping services...[/bold yellow]")
        for process in processes:
            process.terminate()
        console.print("[green]✅ All services stopped[/green]")
        return 0

if __name__ == "__main__":
    sys.exit(main())
