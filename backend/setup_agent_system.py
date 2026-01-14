#!/usr/bin/env python3
"""
Setup Script für Climate Conflict Agent System
Installiert alle Dependencies und konfiguriert das System
"""

import subprocess
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def install_dependencies():
    """Install required dependencies"""
    console.print("📦 [bold blue]Installing Dependencies...[/bold blue]")
    
    dependencies = [
        "httpx",
        "aiohttp", 
        "beautifulsoup4",
        "lxml",
        "firecrawl-py",
        "rich",
        "structlog",
        "numpy",
        "scikit-learn",
        "pandas",
        "sqlite3",
        "asyncio",
        "schedule"
    ]
    
    for dep in dependencies:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            console.print(f"  ✅ {dep}")
        except subprocess.CalledProcessError:
            console.print(f"  ❌ {dep} - Installation failed")
    
    console.print("✅ Dependencies installed!")

def create_config_file():
    """Create configuration file"""
    console.print("⚙️ [bold blue]Creating Configuration...[/bold blue]")
    
    config = {
        "FIRECRAWL_API_KEY": "fc-a0b3b8aa31244c10b0f15b4f2d570ac7",
        "ANALYSIS_INTERVAL": 1800,  # 30 minutes
        "MAX_CONCURRENT_REQUESTS": 5,
        "DATABASE_PATH": "./climate_agent_advanced.db",
        "MEMORY_PATH": "./agent_memory",
        "LOG_LEVEL": "INFO",
        "ENABLE_BROWSER_USE": True,
        "ENABLE_MEMORY_SYSTEM": True,
        "ENABLE_CONFLICT_ANALYSIS": True
    }
    
    config_path = Path("./agent_config.json")
    with open(config_path, 'w') as f:
        import json
        json.dump(config, f, indent=2)
    
    console.print(f"✅ Configuration saved to {config_path}")

def create_startup_scripts():
    """Create startup scripts"""
    console.print("🚀 [bold blue]Creating Startup Scripts...[/bold blue]")
    
    # Agent startup script
    agent_script = """#!/bin/bash
echo "🌍 Starting Climate Conflict Agent..."
cd "$(dirname "$0")"
python advanced_agent.py
"""
    
    with open("./start_agent.sh", "w") as f:
        f.write(agent_script)
    
    # Dashboard startup script
    dashboard_script = """#!/bin/bash
echo "📊 Starting Agent Dashboard..."
cd "$(dirname "$0")"
python agent_dashboard.py
"""
    
    with open("./start_dashboard.sh", "w") as f:
        f.write(dashboard_script)
    
    # Make scripts executable
    import os
    os.chmod("./start_agent.sh", 0o755)
    os.chmod("./start_dashboard.sh", 0o755)
    
    console.print("✅ Startup scripts created!")

def create_docker_setup():
    """Create Docker setup for 24/7 running"""
    console.print("🐳 [bold blue]Creating Docker Setup...[/bold blue]")
    
    dockerfile = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory
RUN mkdir -p /app/data /app/agent_memory

# Expose port
EXPOSE 8000

# Start command
CMD ["python", "advanced_agent.py"]
"""
    
    with open("./Dockerfile.agent", "w") as f:
        f.write(dockerfile)
    
    docker_compose = """version: '3.8'

services:
  climate-agent:
    build:
      context: .
      dockerfile: Dockerfile.agent
    container_name: climate-conflict-agent
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ./agent_memory:/app/agent_memory
      - ./climate_agent_advanced.db:/app/climate_agent_advanced.db
    environment:
      - FIRECRAWL_API_KEY=fc-a0b3b8aa31244c10b0f15b4f2d570ac7
      - ANALYSIS_INTERVAL=1800
    ports:
      - "8000:8000"
    
  agent-dashboard:
    build:
      context: .
      dockerfile: Dockerfile.agent
    container_name: climate-agent-dashboard
    restart: unless-stopped
    volumes:
      - ./climate_agent_advanced.db:/app/climate_agent_advanced.db
    ports:
      - "8001:8000"
    command: ["python", "agent_dashboard.py"]
"""
    
    with open("./docker-compose.agent.yml", "w") as f:
        f.write(docker_compose)
    
    console.print("✅ Docker setup created!")

def create_requirements():
    """Create requirements.txt for agent system"""
    console.print("📋 [bold blue]Creating Requirements...[/bold blue]")
    
    requirements = """# Climate Conflict Agent System Requirements

# Core dependencies
httpx==0.27.0
aiohttp==3.9.1
beautifulsoup4==4.12.3
lxml==5.1.0

# AI and ML
firecrawl-py==0.0.8
numpy>=1.21.0
scikit-learn>=1.0.0
pandas>=1.3.0

# Database
sqlite3

# Async and concurrency
asyncio
aiofiles==23.2.1
asyncio-throttle==1.0.2

# UI and logging
rich==13.7.0
structlog==23.2.0

# Scheduling
schedule==1.2.0

# Data processing
python-dateutil>=2.8.2
pytz>=2020.1

# HTTP and networking
requests>=2.31.0
urllib3>=1.26.0

# JSON and data formats
orjson>=3.9.0

# Environment
python-dotenv==1.0.0
"""
    
    with open("./requirements.agent.txt", "w") as f:
        f.write(requirements)
    
    console.print("✅ Requirements file created!")

def create_documentation():
    """Create documentation"""
    console.print("📚 [bold blue]Creating Documentation...[/bold blue]")
    
    readme = """# 🌍 Climate Conflict Agent System

Ein 24/7 autonomer Agent für die Überwachung klimabedingter Konflikte, inspiriert von Agent Zero.

## 🚀 Features

- **24/7 Monitoring**: Kontinuierliche Überwachung von NASA, UN Press, World Bank
- **AI-Powered Extraction**: Firecrawl API für intelligente Datenextraktion
- **Memory System**: Persistente Speicherung und Lernfähigkeit
- **Conflict Risk Analysis**: Automatische Risikobewertung
- **Real-time Dashboard**: Live-Monitoring und Visualisierung
- **Docker Support**: Containerisierte 24/7 Bereitstellung

## 📦 Installation

```bash
# Dependencies installieren
python setup_agent_system.py

# Oder manuell
pip install -r requirements.agent.txt
```

## 🚀 Verwendung

### Agent starten
```bash
python advanced_agent.py
# oder
./start_agent.sh
```

### Dashboard starten
```bash
python agent_dashboard.py
# oder
./start_dashboard.sh
```

### Docker (24/7)
```bash
docker-compose -f docker-compose.agent.yml up -d
```

## ⚙️ Konfiguration

Die Konfiguration erfolgt über `agent_config.json`:

```json
{
  "FIRECRAWL_API_KEY": "fc-a0b3b8aa31244c10b0f15b4f2d570ac7",
  "ANALYSIS_INTERVAL": 1800,
  "MAX_CONCURRENT_REQUESTS": 5,
  "ENABLE_MEMORY_SYSTEM": true,
  "ENABLE_CONFLICT_ANALYSIS": true
}
```

## 📊 Datenbank

Das System verwendet SQLite mit folgenden Tabellen:
- `extracted_data`: Extrahierte Daten
- `analysis_results`: Analyseergebnisse
- `conflict_events`: Konfliktereignisse
- `agent_memories`: Agent-Gedächtnis

## 🔧 API Integration

### Firecrawl API
- **Extract**: Strukturierte Datenextraktion
- **Search**: Intelligente Suche
- **Schema**: Anpassbare Extraktionsschemata

### Datenquellen
- **NASA Earth Observatory**: Klima-Monitoring
- **UN Press**: Geopolitische Ereignisse
- **World Bank**: Wirtschaftliche Auswirkungen

## 📈 Monitoring

Das Dashboard zeigt:
- Echtzeit-Statistiken
- Risikobewertungen
- Regionale Analysen
- Trend-Erkennung

## 🛠️ Entwicklung

```bash
# Tests ausführen
python -m pytest tests/

# Logs anzeigen
tail -f logs/agent.log

# Datenbank analysieren
sqlite3 climate_agent_advanced.db
```

## 📞 Support

Bei Problemen oder Fragen:
1. Logs überprüfen
2. Datenbank-Status prüfen
3. Firecrawl API-Status überprüfen
4. GitHub Issues erstellen

## 🔒 Sicherheit

- API-Keys in Umgebungsvariablen speichern
- Datenbank regelmäßig sichern
- Rate Limiting aktiviert
- Compliance mit robots.txt
"""
    
    with open("./AGENT_README.md", "w") as f:
        f.write(readme)
    
    console.print("✅ Documentation created!")

def main():
    """Main setup function"""
    console.print(Panel.fit(
        "🌍 Climate Conflict Agent System Setup\n"
        "Inspiriert von Agent Zero mit Memory, Browser-Use und Firecrawl",
        title="🚀 Setup",
        border_style="green"
    ))
    
    try:
        install_dependencies()
        create_config_file()
        create_startup_scripts()
        create_docker_setup()
        create_requirements()
        create_documentation()
        
        console.print("\n🎉 [bold green]Setup completed successfully![/bold green]")
        console.print("\n📋 [bold blue]Next Steps:[/bold blue]")
        console.print("1. Start Agent: python advanced_agent.py")
        console.print("2. Start Dashboard: python agent_dashboard.py")
        console.print("3. Docker 24/7: docker-compose -f docker-compose.agent.yml up -d")
        console.print("4. Read Documentation: AGENT_README.md")
        
    except Exception as e:
        console.print(f"❌ [red]Setup failed: {e}[/red]")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

