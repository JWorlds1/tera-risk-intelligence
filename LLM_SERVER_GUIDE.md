# 🤖 LLM-Server Setup Guide (64-128 GB RAM)

## 🎯 Optimiert für große LLM-Inference

Dieser Server ist speziell konfiguriert für:
- ✅ **Lokale LLM-Inference** mit Ollama
- ✅ **Große Modelle** (70B+ Parameter)
- ✅ **Dynamisches Internet-Crawling**
- ✅ **Geospatial Intelligence** Analysen

## 💾 RAM-Anforderungen

### Verfügbare Flavors für LLM:

| Flavor | vCPUs | RAM | Empfohlen für |
|--------|-------|-----|---------------|
| `c1.8xlarge` | 64 | 128 GB | ✅ **Llama2-70B, Mixtral-8x7B** |
| `c1.16xlarge` | 128 | 256 GB | Sehr große Modelle |
| `m1.8xlarge` | 32 | 128 GB | Alternative zu c1.8xlarge |
| `c1.3xlarge` | 24 | 48 GB | Llama2-34B, CodeLlama-34B |
| `m1.2xlarge` | 8 | 32 GB | Llama2-7B, Mistral-7B |

### RAM-Verteilung (128 GB Server):

```
┌─────────────────────────────────────┐
│  Gesamt: 128 GB RAM                 │
├─────────────────────────────────────┤
│  Llama2-70B:        ~40 GB          │
│  PostgreSQL:        ~8 GB           │
│  Crawling:          ~20 GB          │
│  System:            ~10 GB           │
│  Reserve:           ~50 GB           │
└─────────────────────────────────────┘
```

## 🚀 Server erstellen

```bash
python3 backend/openstack/create_crawling_server.py
```

**Empfohlene Auswahl:**
- **Image:** Ubuntu 22.04 LTS
- **Flavor:** `c1.8xlarge` (64 vCPUs, 128 GB RAM) ✅
- **Network:** Standard-Network

## 📦 Was wird installiert

### LLM-Tools:
- ✅ **Ollama** - Lokale LLM-Inference
- ✅ **Transformers** - Hugging Face Modelle
- ✅ **PyTorch** - Deep Learning Framework
- ✅ **vLLM** - Optimierte Inference (optional)

### Crawling-Tools:
- ✅ Playwright, Selenium
- ✅ httpx, aiohttp
- ✅ BeautifulSoup4, lxml

### Datenbank:
- ✅ PostgreSQL 14+
- ✅ Automatische Backups

## 🔧 Nach Server-Erstellung

### 1. SSH-Verbindung

```bash
ssh ubuntu@<SERVER_IP>
```

### 2. Ollama-Status prüfen

```bash
systemctl status ollama
curl http://localhost:11434/api/tags  # Liste Modelle
```

### 3. Große LLM-Modelle installieren

```bash
# Llama2-70B (~40 GB RAM, ~40 GB Disk)
ollama pull llama2:70b

# Mixtral-8x7B (~26 GB RAM, ~26 GB Disk) - Sehr gut!
ollama pull mixtral:8x7b

# CodeLlama-34B (~20 GB RAM)
ollama pull codellama:34b

# Llama2-34B (~20 GB RAM)
ollama pull llama2:34b

# Liste installierte Modelle
ollama list
```

### 4. LLM testen

```bash
# Interaktiver Test
ollama run llama2:70b "Was ist Geospatial Intelligence?"

# API-Test
curl http://localhost:11434/api/generate -d '{
  "model": "llama2:70b",
  "prompt": "Analysiere Klimarisiken für Ostafrika",
  "stream": false
}'
```

### 5. Python-Integration

```python
import requests

def query_llm(prompt, model="llama2:70b"):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]

# Beispiel
result = query_llm("Analysiere Klimarisiken für Somalia")
print(result)
```

## 🎯 Für Ihr Geospatial Intelligence Projekt

### Workflow:

```
1. Crawling → PostgreSQL Datenbank
   └─ Gecrawlte Daten (NASA, UN, World Bank)

2. Datenbank → LLM-Context
   └─ Extrahiere relevante Informationen

3. LLM-Inference → Analyse
   └─ Llama2-70B analysiert Daten
   └─ Erstellt Risiko-Vorhersagen

4. Ergebnisse → Datenbank zurück
   └─ Speichere Vorhersagen
   └─ Update Visualisierungen
```

### Beispiel-Integration:

```python
from backend.database import DatabaseManager
import requests

db = DatabaseManager()

# Hole gecrawlte Daten
records = db.get_records_by_region("East Africa")

# Erstelle LLM-Prompt
context = "\n".join([r.summary for r in records[:10]])
prompt = f"""
Analysiere diese Klima- und Konfliktdaten für Ostafrika:
{context}

Erstelle eine Risiko-Vorhersage basierend auf:
1. Klimarisiken
2. Konfliktpotential
3. Wirtschaftliche Faktoren
"""

# LLM-Inference
response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama2:70b",
        "prompt": prompt,
        "stream": False
    }
)

prediction = response.json()["response"]

# Speichere Vorhersage
db.save_prediction("East Africa", prediction)
```

## 📊 Monitoring

### RAM-Nutzung prüfen

```bash
# Gesamt-RAM
free -h

# Prozess-spezifisch
ps aux --sort=-%mem | head -10

# Ollama RAM
ps aux | grep ollama | awk '{sum+=$6} END {print sum/1024 " MB"}'
```

### LLM-Performance

```bash
# Ollama Logs
journalctl -u ollama -f

# Test-Geschwindigkeit
time ollama run llama2:70b "Test"
```

## 🔐 Optimierungen

### RAM-Optimierung

```bash
# Swappiness reduzieren
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Huge Pages aktivieren
echo 'vm.nr_hugepages=1024' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### Ollama-Konfiguration

```bash
# Konfiguration anpassen
sudo nano /etc/systemd/system/ollama.service.d/override.conf
```

```ini
[Service]
Environment="OLLAMA_NUM_PARALLEL=2"      # Parallele Requests
Environment="OLLAMA_MAX_LOADED_MODELS=1"  # Max gleichzeitige Modelle
Environment="OLLAMA_HOST=0.0.0.0:11434"   # Externer Zugriff
Environment="OLLAMA_KEEP_ALIVE=24h"      # Modelle im RAM behalten
```

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

## 🚨 Troubleshooting

### Out of Memory

```bash
# Prüfe verfügbaren RAM
free -h

# Verwende quantisierte Modelle
ollama pull llama2:70b-q4_0  # Weniger RAM
```

### Langsame Inference

```bash
# Prüfe CPU-Auslastung
htop

# Verwende kleinere Modelle für Tests
ollama run mistral:7b  # Schneller
```

## 📝 Zusammenfassung

**Für 128 GB RAM Server:**
- ✅ **Llama2-70B** läuft perfekt (~40 GB RAM)
- ✅ **Mixtral-8x7B** läuft perfekt (~26 GB RAM)
- ✅ Mehrere kleine Modelle parallel möglich
- ✅ Optimiert für Geospatial Intelligence

**Nächste Schritte:**
1. Server erstellen mit `c1.8xlarge` (128 GB RAM)
2. Ollama-Modelle installieren
3. Projekt-Code hochladen
4. Crawling + LLM-Inference starten

Viel Erfolg! 🚀

