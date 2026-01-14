# ⚡ Quick Start - 5 Minuten Setup

## 1️⃣ Installation (2 Minuten)

```bash
# Repository clonen (falls noch nicht geschehen)
cd /Users/qed97/Geospatial_Intelligence

# Virtual Environment erstellen
python3 -m venv .venv
source .venv/bin/activate  # Mac/Linux
# Windows: .venv\Scripts\activate

# Dependencies installieren
cd backend
pip install -r requirements.txt

# Playwright Browser installieren
playwright install chromium
```

## 2️⃣ Ersten Test-Run (1 Minute)

```bash
# Einfacher Test mit NASA
python cli.py --source NASA
```

**Ausgabe:**
```
╔════════════════════════════════════════════════════════╗
║  🌍 Umweltfrieden Agenten-Scraper                     ║
║  Frühwarnsystem für klimabedingte Konflikte           ║
║  100% Kostenlos & Open Source                         ║
╚════════════════════════════════════════════════════════╝

🚀 Starte Batch-Scraping: 6 URLs für NASA
🌐 Fetching: https://earthobservatory.nasa.gov/images
✅ Erfolgreich extrahiert: Drought in East Africa
...
```

## 3️⃣ Daten prüfen (1 Minute)

```bash
# Ausgabe-Verzeichnis
ls -lh data/parquet/
ls -lh data/ndjson/
ls -lh data/csv/

# Schnelle Analyse mit Python
python3 << EOF
import pandas as pd
df = pd.read_parquet('data/parquet/nasa_*.parquet')
print(f"✅ {len(df)} Records extrahiert")
print(df[['title', 'region', 'publish_date']].head())
EOF
```

## 4️⃣ Alle Quellen scrapen (1 Minute)

```bash
# Alle 4 Quellen (NASA, UN, WFP, WorldBank)
python cli.py

# Dauert ca. 2-5 Minuten je nach Anzahl URLs
```

## 5️⃣ Docker (Optional)

```bash
# Aus Projektroot
cd ..
docker-compose up scraper

# Im Hintergrund
docker-compose up -d scraper

# Logs
docker-compose logs -f scraper

# Stoppen
docker-compose stop scraper
```

---

## 🎯 Nächste Schritte

### URLs erweitern

Bearbeite `backend/url_lists.py`:

```python
NASA_URLS = [
    'https://earthobservatory.nasa.gov/images',
    'https://earthobservatory.nasa.gov/images/12345/your-article',
    # Füge mehr hinzu...
]
```

### Daten analysieren

Siehe `backend/USAGE.md` für:
- Pandas-Analysen
- NLP-Beispiele
- Geo-Visualisierung

### Scheduler einrichten (Cron)

```bash
# Täglich um 6 Uhr morgens scrapen
0 6 * * * cd /path/to/project/backend && .venv/bin/python cli.py
```

---

## 🆘 Probleme?

**Import-Fehler?**
```bash
# Stelle sicher, dass du im backend/ Verzeichnis bist
cd backend
python cli.py
```

**Playwright-Fehler?**
```bash
playwright install chromium
```

**Keine Daten?**
```bash
# Debug-Modus
export LOG_LEVEL=DEBUG
python cli.py --source NASA
```

**Docker-Fehler?**
```bash
# Neu bauen
docker-compose build scraper
docker-compose up scraper
```

---

**Fertig! 🎉 Du hast jetzt einen funktionierenden Agenten-Scraper.**

Lies `README.md` für mehr Details und `backend/USAGE.md` für erweiterte Nutzung.

