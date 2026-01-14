# 🔍 Dynamische Datensuche

## Übersicht

Die Pipeline nutzt jetzt **dynamische Suche**, die so lange verschiedene Strategien durchprobiert, bis echte Daten gefunden werden.

## Funktionsweise

### Wenn keine Daten gefunden werden:

1. **Verschiedene Keywords**: Probiert verschiedene Keyword-Kombinationen
2. **Verschiedene Datenquellen**: Durchsucht verschiedene URLs und APIs
3. **Verschiedene Kategorien**: Sucht in Research, GitHub, PDFs, etc.
4. **Datenbank-Durchsuchung**: Durchsucht lokale Datenbank
5. **Erweiterte Suche**: Nutzt alle verfügbaren Suchstrategien

### Suchstrategien

1. **Direkte Suche**: Standard Firecrawl-Suche
2. **Keyword-Variationen**: Verschiedene Kombinationen von Keywords
3. **Verwandte Begriffe**: Sucht nach verwandten Begriffen
4. **Regionale Suche**: Fokussiert auf Region
5. **Temporale Suche**: Sucht nach zeitlichen Daten
6. **Kategorie-Suche**: Sucht in spezifischen Kategorien

### Umfassende Suche

Wenn nach vielen Versuchen keine Daten gefunden werden:

- **Markierung**: `comprehensive_search: true`
- **Dokumentation**: Alle durchsuchten Quellen werden dokumentiert
- **Hinweis**: Klare Markierung dass umfassend gesucht wurde

## Output-Format

```json
{
  "found": true/false,
  "data": {
    "text_chunks": [...],
    "numerical_data": {...},
    "image_urls": [...],
    "records": [...]
  },
  "search_history": [
    {
      "iteration": 1,
      "strategy": "firecrawl_search",
      "keywords": [...],
      "results_count": 5
    }
  ],
  "sources_searched": [
    "firecrawl_search",
    "https://climate.nasa.gov",
    ...
  ],
  "total_searches": 15,
  "comprehensive_search": true,
  "data_summary": {
    "text_chunks": 10,
    "numerical_data_points": 5,
    "records": 8,
    "sources_count": 12
  }
}
```

## Verwendung

Die dynamische Suche wird automatisch verwendet, wenn keine Daten gefunden werden:

```python
from dynamic_data_search import DynamicDataSearcher

searcher = DynamicDataSearcher()

result = await searcher.search_until_found(
    location="Mumbai",
    country_code="IN",
    location_type="city",
    max_iterations=20,
    min_data_threshold=3
)

if result['found']:
    # Daten gefunden
    data = result['data']
else:
    # Umfassende Suche durchgeführt, keine Daten gefunden
    print(f"Umfassende Suche: {result['comprehensive_search']}")
    print(f"Quellen durchsucht: {result['sources_searched']}")
```

## Konfiguration

- **max_iterations**: Maximale Anzahl Suchversuche (Standard: 20)
- **min_data_threshold**: Mindestanzahl Datenpunkte (Standard: 3)
- **location_type**: 'city' oder 'country'

## Garantie

✅ **Echte Daten**: Nur echte, gefundene Daten werden verwendet  
✅ **Umfassende Suche**: Wenn keine Daten gefunden werden, wird markiert dass umfassend gesucht wurde  
✅ **Dokumentation**: Alle Suchversuche werden dokumentiert  
✅ **Keine Fallbacks**: Keine erfundenen Daten  



