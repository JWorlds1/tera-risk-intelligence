# 🕷️ Crawling-Strategie - Verbesserungen

## 🔍 Aktuelle Probleme

1. **Übersichtsseiten statt Artikel**: Die aktuellen URLs führen zu Übersichtsseiten, nicht zu einzelnen Artikeln
2. **Fehlende Artikel-Discovery**: Wir crawlen nicht die Links auf den Übersichtsseiten
3. **URL-Patterns ändern sich**: Webseiten-Strukturen ändern sich häufig

## ✅ Lösungsansätze

### Strategie 1: Artikel-Discovery (Implementiert)

**Wie es funktioniert:**
1. Crawle Übersichtsseiten
2. Finde alle Links die zu Artikeln führen
3. Crawle dann die einzelnen Artikel

**Vorteile:**
- Findet automatisch neue Artikel
- Funktioniert auch wenn URLs sich ändern
- Skalierbar

### Strategie 2: RSS Feeds nutzen

**Viele Webseiten haben RSS Feeds:**
- NASA: `https://earthobservatory.nasa.gov/feeds/earth.rss`
- UN Press: `https://press.un.org/en/rss.xml`
- World Bank: `https://www.worldbank.org/en/news/rss`

**Vorteile:**
- Strukturierte Daten
- Immer aktuelle Artikel
- Einfacher zu parsen

### Strategie 3: Sitemaps nutzen

**Viele Webseiten haben Sitemaps:**
- `https://earthobservatory.nasa.gov/sitemap.xml`
- `https://press.un.org/sitemap.xml`
- `https://www.worldbank.org/sitemap.xml`

**Vorteile:**
- Alle URLs auf einmal
- Strukturiert
- Offiziell unterstützt

## 🚀 Implementierung

### Schritt 1: Smart Crawler (✅ Erstellt)

```bash
python smart_crawler.py
```

- Findet Artikel-URLs automatisch
- Crawlt dann die Artikel
- Speichert in Datenbank

### Schritt 2: RSS Feeds (⏳ Nächster Schritt)

```python
# RSS Parser implementieren
- Parse RSS Feeds
- Extrahiere Artikel-URLs
- Crawle Artikel
```

### Schritt 3: Sitemaps (⏳ Optional)

```python
# Sitemap Parser
- Parse Sitemap XML
- Filter nach relevanten URLs
- Crawle Artikel
```

## 📊 Was wird aktuell gecrawlt?

### Aus den bestehenden Daten:

**NASA (2 Records):**
- Übersichtsseiten (Features, World of Change)
- Keine einzelnen Artikel

**UN Press (2 Records):**
- Übersichtsseiten
- Ein Security Council Meeting

**World Bank (1 Record):**
- Übersichtsseite

### Mit Smart Crawler:

**Erwartete Ergebnisse:**
- 20-50 Artikel pro Quelle
- Echte Inhalte mit Details
- Bessere Extraktion

## 🎯 Nächste Schritte

1. ✅ **Smart Crawler** erstellt
2. ⏳ **RSS Feeds** implementieren
3. ⏳ **Sitemaps** nutzen
4. ⏳ **Bessere Extraktion** für Artikel-Inhalte
5. ⏳ **Volltext-Extraktion** implementieren

## 🔧 Verbesserungen für Extraktion

### NASA:
- Extrahiere Bild-URLs mit Koordinaten
- Nutze Metadaten aus Bildern
- Extrahiere Datum-Ranges für "World of Change"

### UN Press:
- Extrahiere vollständigen Text von Press Releases
- Identifiziere Länder aus Text
- Extrahiere Zitate und Statements

### World Bank:
- Extrahiere Projekt-Details
- Nutze strukturierte Daten (JSON-LD)
- Extrahiere Finanzierungs-Beträge



