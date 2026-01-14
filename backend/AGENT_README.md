# 🌍 Climate Conflict Agent System

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
