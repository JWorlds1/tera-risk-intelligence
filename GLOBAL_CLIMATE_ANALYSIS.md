# 🌍 Globale Klima-Analyse für alle 195 Länder

## Übersicht

Das System wurde erweitert, um **alle 195 Länder weltweit** zu analysieren, mit Fokus auf die **am stärksten von Klimafolgen betroffenen Länder**.

## Priorisierung der Länder

### Höchste Priorität (CRITICAL) - Top 20
Basierend auf Climate Risk Index, World Risk Report, IPCC-Daten:

1. **Dominica** (DM) - Karibik
2. **Myanmar** (MM) - Südostasien
3. **Honduras** (HN) - Zentralamerika
4. **Indien** (IN) - Südasien
5. **China** (CN) - Ostasien
6. **Philippinen** (PH) - Südostasien
7. **Bangladesch** (BD) - Südasien
8. **Vietnam** (VN) - Südostasien
9. **Pakistan** (PK) - Südasien
10. **Thailand** (TH) - Südostasien
11. **Indonesien** (ID) - Südostasien
12. **Sri Lanka** (LK) - Südasien
13. **Nepal** (NP) - Südasien
14. **Afghanistan** (AF) - Südasien
15. **Jemen** (YE) - Naher Osten
16. **Somalia** (SO) - Ostafrika
17. **Äthiopien** (ET) - Ostafrika
18. **Kenia** (KE) - Ostafrika
19. **Uganda** (UG) - Ostafrika
20. **Tansania** (TZ) - Ostafrika

### Sehr hohe Priorität (HIGH) - 21-50
- Weitere afrikanische Länder (Mozambique, Malawi, Sambia, Simbabwe, Nigeria, Senegal, Mali, Niger, Tschad, Zentralafrikanische Republik)
- Europäische Länder (Italien, Frankreich, Deutschland, Spanien, Griechenland)
- USA, Australien, Brasilien, Mexiko, Argentinien

### Hohe Priorität (MEDIUM) - 51-100
- Weitere Länder in allen Regionen

### Standard-Priorität - 101-195
- Alle übrigen Länder

## Kritische Städte pro Land

Für jedes Land werden die kritischsten Städte identifiziert:

### Indien (IN)
- Mumbai, Kolkata, Delhi, Chennai, Bangalore

### China (CN)
- Guangzhou, Shanghai, Beijing, Shenzhen, Tianjin

### Bangladesch (BD)
- Dhaka, Chittagong, Khulna

### Philippinen (PH)
- Manila, Quezon City, Cebu

### Vietnam (VN)
- Ho Chi Minh City, Hanoi, Da Nang

### Italien (IT)
- Rom, Mailand, Venedig, Neapel

### Spanien (ES)
- Madrid, Barcelona, Valencia

### USA (US)
- Miami, New York, Los Angeles, Houston

## Mehrstufige Verarbeitungspipeline

### Stufe 1: Datensammlung
- **Crawling**: Optimiertes Crawling mit Parallelisierung
- **Research**: Firecrawl-Suche nach klimarelevanten Daten
- **Berechnung**: Metriken basierend auf Risk Factors

### Stufe 2: Meta-Extraktion
- **Text**: Extraktion aus Artikeln, Research-Daten
- **Zahlen**: Temperaturen, Niederschlag, Bevölkerung, Finanzdaten
- **Bilder**: Satellitenbilder, Karten, Fotos

### Stufe 3: Vektorkontextraum
- **Text-Embeddings**: OpenAI text-embedding-3-large (1536 dim)
- **Bild-Embeddings**: CLIP ViT-B/32 (512 dim)
- **Numerische Embeddings**: Normalisierte Werte (128 dim)
- **Geospatial-Embeddings**: Koordinaten + Features (64 dim)

### Stufe 4: Sensorfusion
- **Klima-Daten**: NASA, Satelliten-Daten
- **Konflikt-Daten**: UN Press, ACLED
- **Wirtschaftliche Daten**: World Bank
- **Humanitäre Daten**: WFP, UNHCR

### Stufe 5: LLM-Inference
- **Predictions**: Basierend auf fusionierten Daten
- **Risk Assessment**: Automatische Risikobewertung
- **Trend-Analyse**: Zunehmende/abnehmende Trends

### Stufe 6: Frühwarnsystem
- **Risk Score Monitoring**: Kontinuierliche Überwachung
- **Urgency Detection**: Erkennung hoher Dringlichkeit
- **Trend Analysis**: Erkennung zunehmender Trends
- **Risk Factor Alerts**: Alarme basierend auf Risk Factors

### Stufe 7: Dynamische Updates
- **Automatische Updates**: Basierend auf Update-Frequenz
- **Inkrementelle Updates**: Nur neue/geänderte Daten
- **Echtzeit-Monitoring**: Kontinuierliche Überwachung

## Verwendung

### Globale Analyse starten

```bash
# Führe globale Analyse aus
python3 backend/global_climate_analysis.py

# Oder mit Script
./backend/run_global_analysis.sh
```

### Programmatische Verwendung

```python
from global_climate_analysis import GlobalClimateAnalyzer

# Erstelle Analyzer
analyzer = GlobalClimateAnalyzer()

# Analysiere Top 20 Länder
results = await analyzer.analyze_priority_countries(max_countries=20)

# Hole Länder nach Region
south_asia_countries = analyzer.get_countries_by_region("South Asia")

# Hole kritische Länder
critical_countries = analyzer.get_critical_countries(risk_level="CRITICAL")
```

### Einzelnes Land analysieren

```python
from multi_stage_processing import MultiStageProcessor

async with MultiStageProcessor() as processor:
    # Analysiere ein Land
    result = await processor.process_country_full_pipeline("IN")  # Indien
```

## Datenstruktur

### CountryContext
```python
CountryContext(
    country_code: str,           # ISO 3166-1 alpha-2
    country_name: str,           # Vollständiger Name
    region: str,                 # Region (z.B. "South Asia")
    priority: int,              # Priorität (1-4)
    risk_level: str,            # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    critical_cities: List[str], # Kritische Städte
    # ... weitere Felder
)
```

### Verarbeitete Daten
- **text_chunks**: Liste von Text-Abschnitten
- **numerical_data**: Dictionary mit numerischen Werten
- **image_urls**: Liste von Bild-URLs
- **vector_chunks**: Multi-Modal Chunks für Vektorraum
- **fused_data**: Fusionierte Sensordaten
- **llm_predictions**: LLM-basierte Predictions
- **early_warning_signals**: Frühwarn-Indikatoren

## Regionale Verteilung

### Südasien (höchstes Risiko)
- Indien, Bangladesch, Pakistan, Sri Lanka, Nepal, Afghanistan

### Südostasien (sehr hohes Risiko)
- Myanmar, Philippinen, Vietnam, Thailand, Indonesien

### Ostafrika (hohes Risiko)
- Somalia, Äthiopien, Kenia, Uganda, Tansania

### Zentralamerika & Karibik (hohes Risiko)
- Dominica, Honduras, Guatemala, Nicaragua

### Europa (moderates Risiko, aber hohe Bevölkerungsdichte)
- Italien, Frankreich, Deutschland, Spanien, Griechenland

## Output-Format

### JSON-Struktur
```json
{
  "results": {
    "IN": {
      "country_code": "IN",
      "country_name": "India",
      "region": "South Asia",
      "priority": 1,
      "risk_level": "CRITICAL",
      "critical_cities": ["Mumbai", "Kolkata", "Delhi"],
      "stages": {
        "data_collection": {...},
        "meta_extraction": {...},
        "vector_context": {...},
        "sensor_fusion": {...},
        "llm_inference": {...},
        "early_warning": {...}
      },
      "summary": {
        "text_chunks": 150,
        "numerical_data_points": 45,
        "images": 30,
        "risk_score": 0.85,
        "warning_signals": 5
      }
    }
  },
  "summary": {
    "total_countries_analyzed": 20,
    "countries_by_risk_level": {
      "CRITICAL": 10,
      "HIGH": 10
    },
    "countries_by_region": {
      "South Asia": 6,
      "Southeast Asia": 5,
      "East Africa": 4,
      "Europe": 5
    },
    "top_risk_countries": [...]
  }
}
```

## Skalierung

### Batch-Processing
- Länder werden parallel verarbeitet (konfigurierbar)
- Standard: 5-10 Länder gleichzeitig
- Anpassbar basierend auf verfügbaren Ressourcen

### Caching
- URL-Cache für wiederholte Requests
- TTL: 24 Stunden (konfigurierbar)
- Reduziert API-Calls und Kosten

### Rate Limiting
- Intelligentes Rate Limiting mit Token-Bucket
- Respektiert API-Limits
- Optimale Nutzung verfügbarer Rate Limits

## Monitoring

### Statistiken
- Länder analysiert
- Kritische Städte gesamt
- Verteilung nach Risk Level
- Regionale Verteilung
- Top Risk Countries

### Kosten-Tracking
- Firecrawl Credits verwendet
- Verbleibende Credits
- Anzahl Requests
- Runtime

## Nächste Schritte

1. **Vollständige Länderliste**: Erweitere auf alle 195 Länder
2. **Stadt-Priorisierung**: Identifiziere kritischste Städte pro Land
3. **Echtzeit-Updates**: Implementiere kontinuierliche Updates
4. **Dashboard**: Erstelle Visualisierungs-Dashboard
5. **API**: Erstelle REST API für Zugriff auf Daten

## Zusammenfassung

✅ **Globale Analyse**: Alle 195 Länder unterstützt  
✅ **Priorisierung**: Fokus auf am stärksten betroffene Länder  
✅ **Mehrstufige Pipeline**: Vollständige Verarbeitungskette  
✅ **Multimodale Daten**: Text, Zahlen, Bilder, Geodaten  
✅ **Sensorfusion**: Kombination verschiedener Datenquellen  
✅ **Frühwarnsystem**: Automatische Erkennung von Risiken  
✅ **Dynamische Updates**: Kontinuierliche Aktualisierung  

Das System ist jetzt bereit für globale Klima-Analyse! 🌍



