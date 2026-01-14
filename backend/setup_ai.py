# setup_ai.py - Setup Script für lokale LLMs und AI-Features
import subprocess
import sys
import os
from pathlib import Path
import structlog
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

logger = structlog.get_logger(__name__)
console = Console()


def check_docker():
    """Prüfe ob Docker installiert ist"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            console.print("✅ Docker ist installiert")
            return True
        else:
            console.print("❌ Docker nicht gefunden")
            return False
    except FileNotFoundError:
        console.print("❌ Docker nicht installiert")
        return False


def install_ollama():
    """Installiere Ollama für lokale LLMs"""
    console.print("\n[bold blue]Installing Ollama...[/bold blue]")
    
    try:
        # Prüfe ob Ollama bereits installiert ist
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            console.print("✅ Ollama bereits installiert")
            return True
    except FileNotFoundError:
        pass
    
    # Installiere Ollama
    if sys.platform == "darwin":  # macOS
        console.print("📥 Lade Ollama für macOS herunter...")
        subprocess.run([
            'curl', '-fsSL', 'https://ollama.ai/install.sh', '|', 'sh'
        ], shell=True)
    elif sys.platform == "linux":
        console.print("📥 Lade Ollama für Linux herunter...")
        subprocess.run([
            'curl', '-fsSL', 'https://ollama.ai/install.sh', '|', 'sh'
        ], shell=True)
    else:
        console.print("❌ Ollama Setup für Windows nicht automatisiert")
        console.print("Bitte installiere Ollama manuell: https://ollama.ai")
        return False
    
    return True


def download_models():
    """Lade kostenlose LLM-Modelle herunter"""
    console.print("\n[bold blue]Downloading AI Models...[/bold blue]")
    
    models = [
        "llama2:7b",
        "mistral:7b", 
        "codellama:7b"
    ]
    
    for model in models:
        console.print(f"📥 Lade {model} herunter...")
        try:
            result = subprocess.run(['ollama', 'pull', model], 
                                  capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                console.print(f"✅ {model} erfolgreich heruntergeladen")
            else:
                console.print(f"❌ Fehler beim Download von {model}: {result.stderr}")
        except subprocess.TimeoutExpired:
            console.print(f"⏰ Timeout beim Download von {model}")
        except Exception as e:
            console.print(f"❌ Fehler: {e}")


def setup_firecrawl():
    """Setup Firecrawl API"""
    console.print("\n[bold blue]Setting up Firecrawl...[/bold blue]")
    
    api_key = "fc-a0b3b8aa31244c10b0f15b4f2d570ac7"
    
    # Erstelle .env Datei
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, 'w') as f:
            f.write(f"FIRECRAWL_API_KEY={api_key}\n")
            f.write("ENABLE_AI_EXTRACTION=true\n")
            f.write("OLLAMA_HOST=http://localhost:11434\n")
            f.write("OLLAMA_MODEL=llama2:7b\n")
        
        console.print("✅ .env Datei erstellt")
    else:
        console.print("✅ .env Datei bereits vorhanden")
    
    console.print(f"🔑 Firecrawl API Key: {api_key}")
    console.print("💳 Du hast 20.000 kostenlose Credits!")


def test_ai_setup():
    """Teste AI-Setup"""
    console.print("\n[bold blue]Testing AI Setup...[/bold blue]")
    
    try:
        # Teste Ollama
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            console.print("✅ Ollama funktioniert")
            console.print(f"Verfügbare Modelle:\n{result.stdout}")
        else:
            console.print("❌ Ollama Test fehlgeschlagen")
        
        # Teste Python Imports
        try:
            import langchain
            import firecrawl
            console.print("✅ Python AI-Bibliotheken installiert")
        except ImportError as e:
            console.print(f"❌ Python AI-Bibliotheken fehlen: {e}")
        
    except Exception as e:
        console.print(f"❌ AI Setup Test fehlgeschlagen: {e}")


def create_docker_compose_ai():
    """Erstelle Docker Compose für AI-Services"""
    docker_compose_ai = """
version: "3.9"

services:
  ollama:
    image: ollama/ollama:latest
    container_name: geofin-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    networks:
      - geofin-net
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: geofin-redis
    ports:
      - "6379:6379"
    networks:
      - geofin-net
    restart: unless-stopped

volumes:
  ollama_data:
    driver: local

networks:
  geofin-net:
    driver: bridge
"""
    
    with open("docker-compose-ai.yml", "w") as f:
        f.write(docker_compose_ai)
    
    console.print("✅ Docker Compose für AI-Services erstellt")


def main():
    """Hauptfunktion für AI-Setup"""
    console.print(Panel.fit(
        "🤖 AI Setup für Climate Conflict Early Warning System",
        subtitle="LangChain + Ollama + Firecrawl Integration",
        border_style="blue"
    ))
    
    # 1. Docker prüfen
    if not check_docker():
        console.print("⚠️  Docker wird für optimale Performance empfohlen")
    
    # 2. Ollama installieren
    if install_ollama():
        # 3. Modelle herunterladen
        download_models()
    
    # 4. Firecrawl setup
    setup_firecrawl()
    
    # 5. Docker Compose erstellen
    create_docker_compose_ai()
    
    # 6. Test
    test_ai_setup()
    
    console.print("\n[bold green]🎉 AI Setup abgeschlossen![/bold green]")
    console.print("\n[bold cyan]Nächste Schritte:[/bold cyan]")
    console.print("1. Starte Ollama: ollama serve")
    console.print("2. Oder mit Docker: docker-compose -f docker-compose-ai.yml up -d")
    console.print("3. Teste das System: python test_ai.py")
    console.print("4. Starte Scraping: python cli.py --ai")


if __name__ == "__main__":
    main()
