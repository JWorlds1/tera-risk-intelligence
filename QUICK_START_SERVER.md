# 🚀 Quick Start: LLM-Crawling-Server erstellen

## ✅ Automatisches Script (EMPFOHLEN)

Das automatische Script behebt das Duplikat-Image-Problem:

```bash
python3 backend/openstack/create_server_auto.py
```

**Was es macht:**
- ✅ Findet automatisch das beste Ubuntu 22.04 Image (ACTIVE)
- ✅ Verwendet Image-ID direkt (vermeidet Duplikat-Problem)
- ✅ Erstellt Server mit `c1.8xlarge` (128 GB RAM)
- ✅ Konfiguriert alles automatisch
- ✅ Zeigt IP-Adresse und Zugriffsinformationen

## 📋 Konfiguration

Das Script verwendet automatisch:
- **Server-Name:** `geospatial-llm-crawler-01`
- **Image:** Ubuntu 22.04 LTS (erstes ACTIVE Image)
- **Flavor:** `c1.8xlarge` (64 vCPUs, 128 GB RAM)
- **Network:** `twm-projekt2-network`

## ⏱️ Dauer

- Server-Erstellung: ~2-3 Minuten
- Setup-Script: ~5-10 Minuten (LLM-Installation)
- **Gesamt:** ~10-15 Minuten

## 📝 Nach der Erstellung

Das Script zeigt Ihnen:
- ✅ Server-IP-Adresse
- ✅ SSH-Zugriff
- ✅ Datenbank-Zugangsdaten
- ✅ LLM-Service-Informationen
- ✅ Nächste Schritte

## 🔧 Falls Probleme auftreten

### Duplikat-Image-Problem (behoben):
Das automatische Script verwendet Image-IDs direkt, daher sollte dieses Problem nicht mehr auftreten.

### Manuelle Auswahl:
Falls Sie das interaktive Script verwenden möchten:
```bash
python3 backend/openstack/create_crawling_server.py
```
Wählen Sie dann:
- Image: **Nummer 1** (ACTIVE Status)
- Flavor: **c1.8xlarge** oder **5**
- Network: **twm-projekt2-network** oder **1**

## 🎯 Nächste Schritte nach Server-Erstellung

1. **SSH zum Server:**
   ```bash
   ssh ubuntu@<SERVER_IP>
   ```

2. **LLM-Modelle installieren:**
   ```bash
   ollama pull llama2:70b
   ollama pull mixtral:8x7b
   ```

3. **Projekt-Code hochladen:**
   ```bash
   scp -r backend/ ubuntu@<SERVER_IP>:/opt/geospatial-intelligence/
   ```

4. **Crawling starten:**
   ```bash
   cd /opt/geospatial-intelligence
   python3 run_pipeline.py
   ```

Viel Erfolg! 🚀

