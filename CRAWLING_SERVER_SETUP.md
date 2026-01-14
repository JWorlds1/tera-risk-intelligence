# 🕷️ Crawling-Server Setup auf OpenStack

## 🎯 Ziel

Einen OpenStack Server erstellen, der:
- ✅ Das gesamte Internet dynamisch crawlen kann
- ✅ Alle Daten in einer Datenbank speichert
- ✅ Für das Geospatial Intelligence Projekt optimiert ist
- ✅ Automatische Backups durchführt

## 🚀 Server erstellen

### Schritt 1: Server erstellen

```bash
python3 backend/openstack/create_crawling_server.py
```

Das Script führt Sie durch:
1. Image-Auswahl (Ubuntu 22.04 empfohlen)
2. Flavor-Auswahl (mindestens 8 GB RAM empfohlen)
3. Network-Auswahl
4. Optional: SSH Key

### Schritt 2: Warten auf Setup

Der Server wird automatisch konfiguriert mit:
- ✅ PostgreSQL Datenbank
- ✅ Python Crawling-Tools (Playwright, Selenium, httpx)
- ✅ Geospatial Libraries
- ✅ AI/LLM Libraries (OpenAI, Anthropic, LangChain)
- ✅ ChromaDB für Vektordatenbank
- ✅ Automatische Backups

**Setup-Zeit:** ~5-10 Minuten

## 📋 Server-Konfiguration

### Was wird installiert:

```
System:
├── Ubuntu 22.04 LTS
├── PostgreSQL 14+
├── Python 3.10+
├── Node.js 20+
└── Docker

Python-Pakete:
├── Crawling: requests, httpx, aiohttp, playwright, selenium
├── Datenbank: sqlalchemy, psycopg2-binary
├── Geospatial: geopandas, rasterio, folium
├── AI: openai, anthropic, langchain, chromadb
└── Utilities: pandas, numpy, rich, structlog

Services:
├── PostgreSQL (Port 5432)
├── Docker
└── Cron für Backups
```

### Datenbank-Konfiguration:

```
Database: geospatial_intelligence
User: crawler
Password: crawler_password_change_me (⚠ ÄNDERN!)
Port: 5432
```

## 🔧 Nach der Erstellung

### 1. SSH-Verbindung

```bash
# Mit SSH Key
ssh -i ~/.ssh/your-key.pem ubuntu@<SERVER_IP>

# Oder mit Passwort (falls konfiguriert)
ssh ubuntu@<SERVER_IP>
```

### 2. Passwort ändern

```bash
# PostgreSQL Passwort ändern
sudo -u postgres psql
ALTER USER crawler WITH PASSWORD 'Ihr_sicheres_Passwort';
\q
```

### 3. Projekt-Code hochladen

```bash
# Vom lokalen Rechner
scp -r backend/ ubuntu@<SERVER_IP>:/opt/geospatial-intelligence/
scp requirements.txt ubuntu@<SERVER_IP>:/opt/geospatial-intelligence/

# Auf dem Server
cd /opt/geospatial-intelligence
pip3 install -r requirements.txt
```

### 4. Datenbank-Schema erstellen

```bash
# Auf dem Server
cd /opt/geospatial-intelligence
python3 -c "from database import DatabaseManager; db = DatabaseManager(); db.init_database()"
```

### 5. Umgebungsvariablen konfigurieren

```bash
# Auf dem Server
nano /opt/geospatial-intelligence/.env
```

```env
# Datenbank
POSTGRESQL_HOST=localhost
POSTGRESQL_PORT=5432
POSTGRESQL_DB=geospatial_intelligence
POSTGRESQL_USER=crawler
POSTGRESQL_PASSWORD=Ihr_sicheres_Passwort

# APIs
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
FIRECRAWL_API_KEY=...
```

## 🕷️ Crawling starten

### Option 1: Manuell

```bash
# Auf dem Server
cd /opt/geospatial-intelligence
python3 run_pipeline.py
```

### Option 2: Als Service

```bash
# Service aktivieren
sudo systemctl enable geospatial-crawler
sudo systemctl start geospatial-crawler

# Status prüfen
sudo systemctl status geospatial-crawler

# Logs ansehen
sudo journalctl -u geospatial-crawler -f
```

### Option 3: Mit Screen/Tmux

```bash
# Screen Session starten
screen -S crawler
cd /opt/geospatial-intelligence
python3 run_pipeline.py

# Detach: Ctrl+A, dann D
# Reattach: screen -r crawler
```

## 📊 Monitoring

### Server-Status

```bash
# CPU/RAM
htop

# Disk-Space
df -h

# PostgreSQL Status
sudo systemctl status postgresql

# Datenbank-Größe
sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('geospatial_intelligence'));"
```

### Crawling-Logs

```bash
# Setup-Log
cat /var/log/crawling-server-setup.log

# Application-Logs
tail -f /opt/geospatial-intelligence/logs/*.log
```

## 💾 Backup-Strategie

### Automatische Backups

Tägliche Backups werden automatisch erstellt:
- Location: `/opt/geospatial-intelligence/backups/`
- Format: `db_backup_YYYYMMDD_HHMMSS.sql`
- Retention: 7 Tage

### Manuelles Backup

```bash
# Datenbank-Backup
sudo -u postgres pg_dump geospatial_intelligence > backup_$(date +%Y%m%d).sql

# Vollständiges Backup (inkl. Daten)
tar -czf backup_$(date +%Y%m%d).tar.gz /opt/geospatial-intelligence/data/
```

## 🔐 Sicherheit

### Firewall

```bash
# Nur SSH und PostgreSQL erlauben
sudo ufw allow 22/tcp
sudo ufw allow 5432/tcp
sudo ufw enable
```

### SSH Hardening

```bash
# SSH Key Authentication bevorzugen
sudo nano /etc/ssh/sshd_config
# PasswordAuthentication no
sudo systemctl restart sshd
```

## 📈 Skalierung

### Für mehr Performance:

1. **Größerer Flavor:**
   - Mehr RAM für größere Datenmengen
   - Mehr vCPUs für paralleles Crawling

2. **Mehrere Server:**
   - Crawler 1: NASA Daten
   - Crawler 2: UN Press Daten
   - Crawler 3: World Bank Daten

3. **Load Balancing:**
   - Verteile Crawling-Jobs auf mehrere Server
   - Zentrale Datenbank für alle Server

## 🎯 Empfohlene Flavor-Auswahl

### Für kleine Projekte:
- `m1.large` - 2 vCPUs, 8 GB RAM, 10 GB Disk

### Für mittlere Projekte:
- `m1.2xlarge` - 8 vCPUs, 32 GB RAM, 10 GB Disk

### Für große Projekte:
- `c1.3xlarge` - 24 vCPUs, 48 GB RAM, 10 GB Disk
- `c1.8xlarge` - 64 vCPUs, 128 GB RAM, 10 GB Disk

## 🚨 Troubleshooting

### Server startet nicht

```bash
# Prüfe Logs
openstack --os-cloud openstack server show <server-name>
openstack --os-cloud openstack console log show <server-name>
```

### PostgreSQL startet nicht

```bash
sudo systemctl status postgresql
sudo journalctl -u postgresql -n 50
```

### Crawling funktioniert nicht

```bash
# Prüfe Dependencies
pip3 list | grep playwright
python3 -m playwright install chromium

# Prüfe Logs
tail -f /opt/geospatial-intelligence/logs/*.log
```

## 📝 Nächste Schritte

1. ✅ Server erstellen
2. ✅ Projekt-Code hochladen
3. ✅ Datenbank konfigurieren
4. ✅ Crawling starten
5. ✅ Monitoring einrichten
6. ✅ Backups testen

Viel Erfolg mit Ihrem Crawling-Server! 🚀

