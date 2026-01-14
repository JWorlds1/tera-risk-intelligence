# 🗺️ Weltkarten-Visualisierung - Anleitung

## Übersicht

Dieser Guide zeigt, wie Sie gefährdete Regionen durch Klimaerwärmung auf einer interaktiven Weltkarte visualisieren können.

## 🚀 Schnellstart

### Option 1: Vollständige Pipeline (Empfohlen)

```bash
cd backend
python run_full_pipeline.py
```

Dies führt automatisch aus:
1. ✅ Crawling (Extraktion von NASA, UN Press, World Bank)
2. ✅ Geocoding (Koordinaten hinzufügen)
3. ✅ Visualisierung (interaktive Karte erstellen)

### Option 2: Schritt für Schritt

```bash
# Schritt 1: Crawling
python run_pipeline.py

# Schritt 2: Geocoding (falls noch nicht vorhanden)
python geocode_existing_records.py

# Schritt 3: Visualisierung
python world_map_visualization.py
```

## 📊 Was wird visualisiert?

### Risiko-Level

Die Karte zeigt Records nach Risiko-Level:

- 🔴 **CRITICAL** - Kritische Gefährdung (Score ≥ 0.8)
- 🟠 **HIGH** - Hohe Gefährdung (Score ≥ 0.6)
- 🟡 **MEDIUM** - Mittlere Gefährdung (Score ≥ 0.4)
- 🔵 **LOW** - Niedrige Gefährdung (Score ≥ 0.2)
- ⚪ **MINIMAL** - Minimale Gefährdung (Score < 0.2)

### Risiko-Score Berechnung

Der Gesamt-Score wird berechnet aus:
- **Climate Risk** (40%) - Klima-Indikatoren (Drought, Flood, etc.)
- **Conflict Risk** (40%) - Konflikt-Indikatoren (War, Crisis, etc.)
- **Urgency** (20%) - Dringlichkeits-Indikatoren (Urgent, Critical, etc.)

### Marker auf der Karte

- **Größe**: Basierend auf Risiko-Score
- **Farbe**: Basierend auf Risiko-Level
- **Popup**: Details zu Record, Risiko-Scores, Indikatoren

## 🎨 Karten-Features

### Layer

1. **OpenStreetMap** (Standard)
2. **Light Map** (CartoDB Positron)
3. **Dark Map** (CartoDB Dark Matter)
4. **Heatmap** - Dichte-Visualisierung aller Records

### Interaktivität

- ✅ **Zoom** - In/Out für Details
- ✅ **Pan** - Karte verschieben
- ✅ **Popup** - Klick auf Marker für Details
- ✅ **Layer Control** - Layer ein/ausblenden
- ✅ **Tooltip** - Hover für Quick-Info

## 📁 Output

Die Karte wird gespeichert als:
```
./data/world_map.html
```

Öffnen Sie die Datei im Browser:
```bash
open ./data/world_map.html
# oder
python -m http.server 8000
# Dann Browser: http://localhost:8000/data/world_map.html
```

## 🔍 Daten prüfen

### Anzahl Records mit Koordinaten

```python
from database import DatabaseManager

db = DatabaseManager()
stats = db.get_statistics()
print(f"Records mit Koordinaten: {stats.get('records_with_coordinates', 0)}")
```

### Records nach Land

```sql
SELECT primary_country_code, COUNT(*) 
FROM records 
WHERE primary_country_code IS NOT NULL
GROUP BY primary_country_code
ORDER BY COUNT(*) DESC;
```

### Records nach Risiko-Level

```python
from database import DatabaseManager
from risk_scoring import RiskScorer

db = DatabaseManager()
scorer = RiskScorer()

records = db.get_records(limit=1000)
risk_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'MINIMAL': 0}

for record in records:
    risk = scorer.calculate_risk(record)
    level = scorer.get_risk_level(risk.score)
    risk_counts[level] += 1

print(risk_counts)
```

## 🎯 Gefährdete Regionen identifizieren

### Top gefährdete Regionen

Die Karte zeigt automatisch:
- Regionen mit vielen CRITICAL/HIGH Risk Records
- Heatmap für Dichte-Visualisierung
- Clustering nach geografischer Nähe

### Filter nach Region

```python
# Records für spezifische Region
records = db.get_records()
east_africa_records = [r for r in records if r.get('region') == 'East Africa']

# Visualisiere nur diese Region
# (Modifiziere world_map_visualization.py)
```

## 🛠️ Anpassungen

### Risiko-Score anpassen

Bearbeiten Sie `risk_scoring.py`:
- Gewichtungen ändern
- Indikatoren hinzufügen/entfernen
- Score-Berechnung anpassen

### Karten-Style anpassen

Bearbeiten Sie `world_map_visualization.py`:
- Farben ändern
- Marker-Größe anpassen
- Popup-Inhalt erweitern

### Weitere Visualisierungen

- **Timeline-Map**: Veränderung über Zeit
- **Choropleth**: Länder nach Risiko-Level einfärben
- **3D-Visualisierung**: Mit Plotly

## 📊 Beispiel-Output

Nach erfolgreicher Ausführung sehen Sie:

```
🌍 Erstelle Weltkarten-Visualisierung...
✅ Gefunden: 52 Records mit Koordinaten
✅ Karte gespeichert: ./data/world_map.html
📊 Statistiken:
   - CRITICAL: 5
   - HIGH: 12
   - MEDIUM: 18
   - LOW: 10
   - MINIMAL: 7
```

## ✅ Checkliste

- [ ] Pipeline ausgeführt (`run_full_pipeline.py`)
- [ ] Records haben Koordinaten (prüfe mit `test_extraction.py`)
- [ ] Karte erstellt (`world_map.html` existiert)
- [ ] Karte im Browser geöffnet
- [ ] Risiko-Level sichtbar
- [ ] Popups funktionieren
- [ ] Heatmap aktiviert

## 🐛 Troubleshooting

### Keine Koordinaten

```bash
# Geocode bestehende Records
python geocode_existing_records.py
```

### Karte zeigt keine Marker

- Prüfe ob Records Koordinaten haben
- Prüfe Browser-Konsole für Fehler
- Prüfe ob Folium installiert ist: `pip install folium`

### Risiko-Scores zu niedrig/hoch

- Passe Gewichtungen in `risk_scoring.py` an
- Prüfe ob Indikatoren im Text vorhanden sind

## 🎉 Nächste Schritte

1. ✅ **Karte erstellt** - Gefährdete Regionen sichtbar
2. 📊 **Daten analysieren** - Welche Regionen sind am gefährdetsten?
3. 🔄 **Regelmäßig aktualisieren** - Pipeline automatisiert laufen lassen
4. 📈 **Erweiterte Visualisierungen** - Timeline, Choropleth, etc.

