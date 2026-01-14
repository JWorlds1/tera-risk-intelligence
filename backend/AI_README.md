# 🤖 AI-Powered Climate Conflict Early Warning System

## Übersicht

Dieses System kombiniert **traditionelle Web-Scraping-Techniken** mit **modernen AI-Technologien** für eine intelligente Extraktion und Analyse von Klima-Konflikt-Daten.

## 🚀 AI-Features

### 1. **LangChain-Agenten** (Kostenlos)
- **Intelligente Extraktion** mit strukturierter Datenanalyse
- **Pydantic-Integration** für robuste Datenvalidierung
- **Tool-basierte Architektur** für erweiterte Funktionalität

### 2. **Lokale LLMs** (100% Kostenlos)
- **Ollama** - Lokale LLM-Inferenz
- **LlamaCpp** - Optimierte Performance
- **Verfügbare Modelle**:
  - `llama2:7b` - Meta's Llama 2 (7B Parameter)
  - `mistral:7b` - Mistral 7B
  - `codellama:7b` - Code-spezialisiertes Modell
  - `llamacpp` - Lokale GGUF-Modelle

### 3. **Firecrawl API** (20.000 kostenlose Credits)
- **Strukturierte Extraktion** mit vordefinierten Schemas
- **Markdown + HTML** Ausgabe
- **Metadaten-Extraktion** (Titel, Datum, Regionen)
- **Dynamischer Content** Support

## 🛠️ Installation & Setup

### 1. **Basis-Installation**
```bash
# Dependencies installieren
pip install -r requirements.txt

# AI-Setup ausführen
python setup_ai.py
```

### 2. **Ollama installieren** (Lokale LLMs)
```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Modelle herunterladen
ollama pull llama2:7b
ollama pull mistral:7b
ollama pull codellama:7b

# Ollama starten
ollama serve
```

### 3. **Docker Setup** (Optional)
```bash
# AI-Services mit Docker starten
docker-compose -f docker-compose-ai.yml up -d
```

## 🎯 Verwendung

### **AI-unterstütztes Scraping**
```bash
# Mit AI-Extraktion
python cli.py --ai

# Spezifisches Modell
python cli.py --ai --model mistral

# Dry Run mit AI
python cli.py --ai --dry-run
```

### **Programmatische Verwendung**
```python
import asyncio
from ai_agents import ClimateConflictAgent, FirecrawlAgent

async def main():
    # Firecrawl Agent
    firecrawl = FirecrawlAgent("fc-a0b3b8aa31244c10b0f15b4f2d570ac7")
    result = await firecrawl.extract_page("https://example.com")
    
    # AI Agent
    ai_agent = ClimateConflictAgent(config, "fc-a0b3b8aa31244c10b0f15b4f2d570ac7")
    analysis = await ai_agent.analyze_text("Drought in East Africa...")
    
    print(f"Risk Level: {analysis.risk_level}")
    print(f"Affected Regions: {analysis.affected_regions}")

asyncio.run(main())
```

## 🧠 AI-Analyse-Features

### **Strukturierte Datenausgabe**
```python
class ClimateConflictAnalysis(BaseModel):
    climate_indicators: List[str]      # Dürre, Überschwemmung, etc.
    conflict_indicators: List[str]     # Gewalt, Vertreibung, etc.
    risk_level: str                    # niedrig, mittel, hoch, kritisch
    affected_regions: List[str]        # Betroffene Regionen
    urgency_score: int                 # 1-10 Dringlichkeit
    key_entities: List[str]            # Organisationen, Personen
    summary: str                       # Zusammenfassung
    recommendations: List[str]         # Handlungsempfehlungen
```

### **Intelligente Extraktion**
- **Klima-Indikatoren**: Dürre, Überschwemmung, Temperatur, NDVI
- **Konflikt-Indikatoren**: Gewalt, Vertreibung, Krise, Notfall
- **Geografische Analyse**: Regionen, Länder, Koordinaten
- **Risikobewertung**: Automatische Scoring-Algorithmen
- **Entitäts-Erkennung**: Organisationen, Personen, Orte

## 📊 Performance & Kosten

### **Kostenübersicht**
- **LangChain**: 100% kostenlos
- **Ollama**: 100% kostenlos (lokal)
- **Firecrawl**: 20.000 kostenlose Credits
- **Gesamtkosten**: 0€ (mit Studenten-Account)

### **Performance-Optimierungen**
- **Lokale Inferenz**: Keine API-Limits
- **Caching**: Intelligente Zwischenspeicherung
- **Batch-Processing**: Parallele Verarbeitung
- **Fallback-Strategien**: Traditionelle Extraktion als Backup

## 🔧 Konfiguration

### **Environment Variables**
```bash
# .env Datei
FIRECRAWL_API_KEY=fc-a0b3b8aa31244c10b0f15b4f2d570ac7
ENABLE_AI_EXTRACTION=true
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama2:7b
AI_CONFIDENCE_THRESHOLD=0.7
```

### **Model-Auswahl**
```python
# Verfügbare Modelle
models = [
    'llama2:7b',      # Beste Balance
    'mistral:7b',     # Schnell
    'codellama:7b',   # Code-spezialisiert
    'llamacpp'        # Lokale GGUF
]
```

## 🧪 Testing

### **AI-Features testen**
```bash
# Vollständiger AI-Test
python test_ai.py

# Einzelne Komponenten
python -c "from ai_agents import FirecrawlAgent; print('Firecrawl OK')"
python -c "from ai_agents import LocalLLMManager; print('LLM OK')"
```

### **System-Test**
```bash
# Komplettes System
python test_system.py

# Mit AI-Features
python cli.py --ai --dry-run
```

## 📈 Erweiterte Features

### **1. Multi-Model-Ensemble**
```python
# Mehrere Modelle kombinieren
models = ['llama2:7b', 'mistral:7b']
results = await ensemble_analysis(text, models)
```

### **2. Custom Prompts**
```python
# Spezifische Prompts für verschiedene Quellen
nasa_prompt = "Analysiere NASA-Daten auf Umweltstress..."
un_prompt = "Analysiere UN-Daten auf Sicherheitsrisiken..."
```

### **3. Real-time Monitoring**
```python
# AI-Performance überwachen
stats = ai_agent.get_stats()
print(f"Success Rate: {stats['ai_success_rate']}")
```

## 🚨 Troubleshooting

### **Häufige Probleme**

1. **Ollama nicht verfügbar**
   ```bash
   # Ollama starten
   ollama serve
   
   # Status prüfen
   ollama list
   ```

2. **Firecrawl API-Fehler**
   ```bash
   # API Key prüfen
   echo $FIRECRAWL_API_KEY
   
   # Credits prüfen
   curl -H "Authorization: Bearer $FIRECRAWL_API_KEY" \
        https://api.firecrawl.dev/v0/usage
   ```

3. **LangChain Import-Fehler**
   ```bash
   # Dependencies neu installieren
   pip install --upgrade langchain langchain-community
   ```

### **Performance-Optimierung**
- **GPU-Support**: CUDA für LlamaCpp
- **Memory-Management**: Batch-Größen anpassen
- **Caching**: Redis für häufige Anfragen

## 🎯 Nächste Schritte

1. **Setup ausführen**: `python setup_ai.py`
2. **AI testen**: `python test_ai.py`
3. **Scraping starten**: `python cli.py --ai`
4. **Modelle erweitern**: Weitere Ollama-Modelle
5. **Prompts optimieren**: Spezifische Prompts für Quellen

## 📚 Dokumentation

- **LangChain**: https://python.langchain.com/
- **Ollama**: https://ollama.ai/
- **Firecrawl**: https://docs.firecrawl.dev/
- **Pydantic**: https://docs.pydantic.dev/

---

**🎉 Mit diesem Setup hast du ein vollständig kostenloses, AI-gestütztes System für Klima-Konflikt-Frühwarnung!**
