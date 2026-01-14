# 🌍 Kritische Städte - Crawling Strategie

## ✅ Was funktioniert

### Crawl4AI Integration
- ✅ **Installiert und funktioniert**
- ✅ **Klima-Daten erfolgreich gecrawlt** (4 URLs für Athens, 3 für Rome)
- ✅ **191,000+ Zeichen extrahiert** aus Klima-Quellen

### Erreichte Ergebnisse
- **Athens**: 4 Klima-Datenquellen gecrawlt
- **Rome**: 3 Klima-Datenquellen gecrawlt
- **Vektor-Chunks erstellt** für jede Stadt
- **Daten gespeichert** in `data/critical_cities_data.json`

## ⚠️ Verbesserungen nötig

### Firecrawl-Suche
- **Problem**: IPCC/Conflict/Research-Suche gibt 0 Ergebnisse zurück
- **Ursache**: Möglicherweise zu generische Keywords oder API-Problem
- **Lösung**: Verbesserte Keywords + direkte URL-Crawling statt Suche

## 📋 Nächste Schritte

### Phase 1: WFP-Crawling reparieren ✅
```bash
python backend/crawl4ai_integration.py
```

### Phase 2: Kritische Städte crawlen ✅ (läuft)
```bash
python backend/critical_cities_crawler.py
```

### Phase 3: Firecrawl-Suche verbessern
- Direkte URLs statt Suche verwenden
- Bessere Keywords für IPCC/Conflict-Daten
- Mehr spezifische Quellen

### Phase 4: Vektorraum-Erstellung
- Embeddings generieren (OpenAI text-embedding-3-large)
- ChromaDB oder Qdrant für Vektor-DB
- Stadt-spezifische Chunks indizieren

### Phase 5: IPCC-Approximation
- IPCC-Daten für Städte approximieren
- Mit empirischen Daten abgleichen
- Confidence-Scores berechnen

## 🎯 Kritische Städte (Priorität)

### Hoch-Priorität
1. **Athens, GR** ✅ (gestartet)
2. **Rome, IT** ✅ (gestartet)
3. **Madrid, ES** (bereit)
4. **Istanbul, TR** (bereit)
5. **Berlin, DE** (bereit)

### URLs pro Stadt

#### Klima-Daten (Crawl4AI)
- EEA Urban Adaptation
- NASA Climate Effects
- World Bank Climate Portal
- World Weather Online

#### IPCC-Daten (Firecrawl Suche)
- IPCC Interactive Atlas
- Climate Knowledge Portal
- IPCC AR6 Reports

#### Konflikt-Daten (Firecrawl Suche)
- ACLED Data
- UNHCR Refugee Statistics
- IOM Migration Data

#### Forschungsdaten (Firecrawl Suche)
- Lancet Countdown
- Nature Climate Change
- EEA Publications

## 🔧 Technologie-Stack

- **Crawl4AI**: Für komplexe JavaScript-Seiten, Discovery
- **Firecrawl**: Für strukturierte Extraktion, API-Suche
- **Kombination**: Crawl4AI für Discovery → Firecrawl für strukturierte Daten

## 📊 Aktuelle Daten

- **Gesamt gecrawlt**: 2 Städte (Athens, Rome)
- **Klima-Daten**: 7 URLs erfolgreich
- **IPCC-Daten**: 0 (muss verbessert werden)
- **Konflikt-Daten**: 0 (muss verbessert werden)
- **Forschungsdaten**: 0 (muss verbessert werden)

## 💡 Empfehlungen

1. **Firecrawl-Suche verbessern**: Direkte URLs verwenden statt Suche
2. **Mehr Städte crawlen**: Alle 5 kritischen Städte
3. **Vektorraum aufbauen**: Nach erfolgreichem Crawling
4. **IPCC-Approximation**: Mit gecrawlten Daten



