# 🤖 LLM-Server Konfiguration (64-128 GB RAM)

## 🎯 Optimiert für große LLM-Inference

Dieser Server ist konfiguriert für:
- ✅ Lokale LLM-Inference (Ollama)
- ✅ Große Modelle (70B+ Parameter)
- ✅ vLLM für optimierte Inference
- ✅ Transformers für Custom-Modelle

## 💾 RAM-Anforderungen für verschiedene Modelle

### Kleine Modelle (7B-13B Parameter):
- **RAM:** 16-32 GB
- **Beispiele:** Llama2-7B, Mistral-7B, CodeLlama-7B

### Mittlere Modelle (30B-40B Parameter):
- **RAM:** 64-80 GB
- **Beispiele:** Llama2-34B, CodeLlama-34B

### Große Modelle (70B+ Parameter):
- **RAM:** 128-256 GB
- **Beispiele:** Llama2-70B, Llama3-70B, Mixtral-8x7B

## 🚀 Empfohlene Flavor-Auswahl

### Für 70B Modelle:
```
c1.8xlarge  - 64 vCPUs, 128 GB RAM  ✅ EMPFOHLEN
c1.16xlarge - 128 vCPUs, 256 GB RAM (für sehr große Modelle)
```

### Für 34B Modelle:
```
c1.3xlarge  - 24 vCPUs, 48 GB RAM
m1.8xlarge  - 32 vCPUs, 128 GB RAM  ✅ GUT
```

### Für 7B-13B Modelle:
```
m1.2xlarge  - 8 vCPUs, 32 GB RAM
c1.xlarge   - 8 vCPUs, 16 GB RAM
```

## 📦 Installierte LLM-Tools

### 1. Ollama (Lokale LLMs)
```bash
# Status prüfen
systemctl status ollama

# Modelle installieren
ollama pull llama2:70b        # 70B Parameter, ~40 GB
ollama pull mistral:7b         # 7B Parameter, ~4 GB
ollama pull codellama:34b      # 34B Parameter, ~20 GB
ollama pull mixtral:8x7b       # 47B Parameter, ~26 GB

# Liste installierte Modelle
ollama list

# LLM testen
ollama run llama2:70b "Was ist Geospatial Intelligence?"
```

### 2. vLLM (Optimierte Inference)
```bash
# Für große Modelle mit optimierter Performance
python3 -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-70b-chat-hf \
    --tensor-parallel-size 1
```

### 3. Transformers (Custom-Modelle)
```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "meta-llama/Llama-2-70b-chat-hf"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True
)
```

## 🔧 Konfiguration nach Server-Erstellung

### 1. Ollama konfigurieren

```bash
# Ollama Config
nano /etc/systemd/system/ollama.service.d/override.conf
```

```ini
[Service]
Environment="OLLAMA_NUM_PARALLEL=4"
Environment="OLLAMA_MAX_LOADED_MODELS=2"
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### 2. RAM-Optimierung

```bash
# Swappiness reduzieren (weniger Swap-Nutzung)
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Huge Pages für bessere Performance
echo 'vm.nr_hugepages=1024' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### 3. Modelle installieren

```bash
# Große Modelle (benötigen viel RAM)
ollama pull llama2:70b        # ~40 GB RAM benötigt
ollama pull mixtral:8x7b      # ~26 GB RAM benötigt

# Mittlere Modelle
ollama pull codellama:34b     # ~20 GB RAM benötigt
ollama pull llama2:34b        # ~20 GB RAM benötigt

# Kleine Modelle (schnell)
ollama pull mistral:7b        # ~4 GB RAM benötigt
ollama pull llama2:7b         # ~4 GB RAM benötigt
```

## 🧪 LLM-Test

### Test-Script erstellen

```bash
cat > /opt/geospatial-intelligence/test_llm.py <<'EOF'
#!/usr/bin/env python3
"""Test LLM-Inference"""
import requests
import json

# Test Ollama
def test_ollama():
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "llama2:70b",
        "prompt": "Was ist Geospatial Intelligence?",
        "stream": False
    }
    
    response = requests.post(url, json=data)
    result = response.json()
    print("Ollama Response:")
    print(result.get("response", ""))

if __name__ == "__main__":
    test_ollama()
EOF

python3 /opt/geospatial-intelligence/test_llm.py
```

## 📊 Monitoring

### RAM-Nutzung prüfen

```bash
# Aktuelle RAM-Nutzung
free -h

# Prozess-spezifische RAM-Nutzung
ps aux --sort=-%mem | head -10

# Ollama RAM-Nutzung
ps aux | grep ollama
```

### LLM-Performance

```bash
# Ollama Logs
journalctl -u ollama -f

# vLLM Logs
tail -f /opt/geospatial-intelligence/logs/vllm.log
```

## 🎯 Empfohlene Konfiguration für Ihr Projekt

### Für Geospatial Intelligence mit LLM:

1. **Server:** c1.8xlarge (64 vCPUs, 128 GB RAM)
2. **LLM:** Llama2-70B oder Mixtral-8x7B
3. **Verwendung:**
   - Crawling: 20 GB RAM
   - PostgreSQL: 8 GB RAM
   - LLM-Inference: 80-100 GB RAM
   - Reserve: 20 GB

### Workflow:

```
1. Crawling → Datenbank (PostgreSQL)
2. Datenbank → LLM-Context
3. LLM-Inference → Analyse & Vorhersagen
4. Ergebnisse → Datenbank zurück
```

## 🚨 Troubleshooting

### Out of Memory

```bash
# Prüfe verfügbaren RAM
free -h

# Reduziere Modell-Größe oder verwende Quantisierung
ollama pull llama2:70b-q4_0  # Quantisiert, weniger RAM
```

### Langsame Inference

```bash
# Prüfe CPU-Auslastung
htop

# Verwende vLLM für bessere Performance
pip3 install vllm
```

### Ollama startet nicht

```bash
# Prüfe Logs
journalctl -u ollama -n 50

# Prüfe Port
netstat -tulpn | grep 11434
```

## 📝 Zusammenfassung

**Für 128 GB RAM Server:**
- ✅ Llama2-70B: ~40 GB RAM
- ✅ Mixtral-8x7B: ~26 GB RAM
- ✅ Mehrere kleine Modelle parallel möglich
- ✅ Optimiert für Geospatial Intelligence Workloads

Viel Erfolg mit Ihrem LLM-Server! 🚀

