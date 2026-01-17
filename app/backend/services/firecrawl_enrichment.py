"""
TERA FireCrawl Enrichment Service
Kombiniert Erddaten mit Web-Crawling für kontextuelle Risikobewertung

Workflow:
1. Erddaten (ERA5, Sentinel) → Numerische Anomalien erkennen
2. FireCrawl → Relevante Nachrichten crawlen
3. NLP → Themen und Orte extrahieren
4. H3 Mapping → Artikel mit Zellen verknüpfen
5. Enrichment → Risikobewertung anreichern
"""
import asyncio
import httpx
import h3
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from loguru import logger


# =====================================================
# DATA CLASSES
# =====================================================

@dataclass
class CrawledArticle:
    """Gecrawlter Artikel mit extrahierten Informationen"""
    url: str
    title: str
    content: str
    published_at: Optional[datetime] = None
    
    # Extrahierte Entitäten
    locations: List[Dict[str, Any]] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    sentiment: float = 0.0  # -1 (negativ) bis +1 (positiv)
    
    # H3 Mapping
    h3_indices: List[str] = field(default_factory=list)
    
    # Risiko-Signale
    risk_signals: List[str] = field(default_factory=list)
    urgency_score: float = 0.0


@dataclass
class EnrichedCell:
    """H3-Zelle mit angereicherten Daten"""
    h3_index: str
    lat: float
    lon: float
    
    # Numerische Daten (ERA5, Sentinel)
    temperature_c: float = 0.0
    temp_anomaly_c: float = 0.0
    precipitation_mm: float = 0.0
    precip_anomaly_pct: float = 0.0
    soil_moisture_pct: float = 50.0
    ndvi: float = 0.5
    
    # Crawled Context
    articles: List[CrawledArticle] = field(default_factory=list)
    article_count: int = 0
    dominant_topics: List[str] = field(default_factory=list)
    
    # Combined Risk
    numerical_risk: float = 0.0
    contextual_risk: float = 0.0
    combined_risk: float = 0.0
    risk_drivers: List[str] = field(default_factory=list)


# =====================================================
# TOPIC & ENTITY EXTRACTION
# =====================================================

class TopicExtractor:
    """Extrahiert Themen und Risiko-Signale aus Text"""
    
    # Risiko-relevante Themen
    RISK_TOPICS = {
        "drought": {
            "keywords": ["drought", "dürre", "dry", "trocken", "water shortage", "wassermangel"],
            "risk_weight": 0.8
        },
        "flood": {
            "keywords": ["flood", "überschwemmung", "hochwasser", "flooding", "deluge"],
            "risk_weight": 0.9
        },
        "heatwave": {
            "keywords": ["heatwave", "hitzewelle", "extreme heat", "rekordtemperatur", "heat record"],
            "risk_weight": 0.7
        },
        "wildfire": {
            "keywords": ["wildfire", "waldbrand", "forest fire", "bushfire", "feuer"],
            "risk_weight": 0.85
        },
        "storm": {
            "keywords": ["storm", "sturm", "hurricane", "cyclone", "typhoon", "orkan"],
            "risk_weight": 0.8
        },
        "crop_failure": {
            "keywords": ["crop failure", "ernteausfall", "harvest loss", "agricultural damage"],
            "risk_weight": 0.7
        },
        "conflict": {
            "keywords": ["conflict", "konflikt", "war", "krieg", "violence", "attack", "angriff"],
            "risk_weight": 0.9
        },
        "displacement": {
            "keywords": ["refugee", "flüchtling", "displacement", "vertreibung", "migration", "exodus"],
            "risk_weight": 0.75
        },
        "food_crisis": {
            "keywords": ["famine", "hungersnot", "food crisis", "nahrungskrise", "starvation"],
            "risk_weight": 0.9
        },
    }
    
    # Urgenz-Indikatoren
    URGENCY_KEYWORDS = [
        "emergency", "notfall", "urgent", "dringend", "critical", "kritisch",
        "immediate", "sofort", "warning", "warnung", "alert", "alarm",
        "evacuate", "evakuierung", "death toll", "todesopfer"
    ]
    
    def extract_topics(self, text: str) -> Tuple[List[str], float]:
        """Extrahiert Themen und berechnet Risiko-Gewicht"""
        text_lower = text.lower()
        
        found_topics = []
        total_weight = 0.0
        
        for topic, config in self.RISK_TOPICS.items():
            for keyword in config["keywords"]:
                if keyword in text_lower:
                    if topic not in found_topics:
                        found_topics.append(topic)
                        total_weight += config["risk_weight"]
                    break
        
        # Normalisieren
        if found_topics:
            avg_weight = total_weight / len(found_topics)
        else:
            avg_weight = 0.0
        
        return found_topics, avg_weight
    
    def calculate_urgency(self, text: str) -> float:
        """Berechnet Dringlichkeit basierend auf Keywords"""
        text_lower = text.lower()
        
        urgency_count = sum(1 for kw in self.URGENCY_KEYWORDS if kw in text_lower)
        
        # Normalisieren auf 0-1
        return min(1.0, urgency_count / 5)
    
    def analyze_sentiment(self, text: str) -> float:
        """Einfache Sentiment-Analyse (-1 bis +1)"""
        text_lower = text.lower()
        
        negative_words = [
            "crisis", "disaster", "death", "killed", "destroyed", "failed",
            "worst", "catastrophe", "emergency", "threat", "danger", "risk",
            "krise", "katastrophe", "tod", "zerstört", "gefahr"
        ]
        
        positive_words = [
            "recovery", "improvement", "success", "relief", "aid", "help",
            "solution", "progress", "safe", "stable", "erholung", "hilfe"
        ]
        
        neg_count = sum(1 for w in negative_words if w in text_lower)
        pos_count = sum(1 for w in positive_words if w in text_lower)
        
        total = neg_count + pos_count
        if total == 0:
            return 0.0
        
        return (pos_count - neg_count) / total


# =====================================================
# LOCATION EXTRACTION
# =====================================================

class LocationExtractor:
    """Extrahiert geografische Orte aus Text"""
    
    # Bekannte Orte mit Koordinaten
    KNOWN_LOCATIONS = {
        # Deutschland
        "berlin": (52.52, 13.41),
        "münchen": (48.14, 11.58),
        "hamburg": (53.55, 9.99),
        "frankfurt": (50.11, 8.68),
        "köln": (50.94, 6.96),
        "dresden": (51.05, 13.74),
        "brandenburg": (52.41, 13.08),
        
        # Europa
        "amsterdam": (52.37, 4.90),
        "rotterdam": (51.92, 4.48),
        "paris": (48.86, 2.35),
        "london": (51.51, -0.13),
        "madrid": (40.42, -3.70),
        "rom": (41.90, 12.50),
        "wien": (48.21, 16.37),
        
        # Krisenregionen
        "gaza": (31.50, 34.47),
        "ukraine": (48.38, 31.17),
        "kyiv": (50.45, 30.52),
        "sudan": (12.86, 30.22),
        "darfur": (13.50, 25.00),
        "yemen": (15.55, 48.52),
        "syria": (34.80, 39.00),
        "aleppo": (36.20, 37.16),
        
        # Klimahotspots
        "jakarta": (-6.21, 106.85),
        "miami": (25.76, -80.19),
        "mumbai": (19.08, 72.88),
        "dhaka": (23.81, 90.41),
        "lagos": (6.52, 3.38),
        "cairo": (30.04, 31.24),
    }
    
    def extract_locations(self, text: str) -> List[Dict[str, Any]]:
        """Extrahiert Orte aus Text und gibt H3-Indices zurück"""
        text_lower = text.lower()
        
        found_locations = []
        
        for name, (lat, lon) in self.KNOWN_LOCATIONS.items():
            if name in text_lower:
                h3_index = h3.latlng_to_cell(lat, lon, 7)
                found_locations.append({
                    "name": name.title(),
                    "lat": lat,
                    "lon": lon,
                    "h3_index": h3_index
                })
        
        return found_locations


# =====================================================
# FIRECRAWL SERVICE
# =====================================================

class FireCrawlEnrichmentService:
    """
    Kombiniert FireCrawl mit Erddaten für kontextuelle Anreicherung
    """
    
    # Priority-Quellen für Crawling
    PRIORITY_SOURCES = [
        {
            "name": "ReliefWeb",
            "url": "https://reliefweb.int/updates?search=disaster%20OR%20crisis",
            "type": "humanitarian",
            "priority": 10
        },
        {
            "name": "GDELT",
            "url": "https://api.gdeltproject.org/api/v2/doc/doc?query=climate%20disaster&mode=artlist&format=json",
            "type": "news",
            "priority": 9
        },
        {
            "name": "Carbon Brief",
            "url": "https://www.carbonbrief.org/",
            "type": "climate",
            "priority": 7
        },
        {
            "name": "Crisis Group",
            "url": "https://www.crisisgroup.org/",
            "type": "conflict",
            "priority": 8
        },
    ]
    
    def __init__(self, firecrawl_api_key: str = None):
        self.api_key = firecrawl_api_key
        self.topic_extractor = TopicExtractor()
        self.location_extractor = LocationExtractor()
    
    async def crawl_url(self, url: str) -> Optional[CrawledArticle]:
        """Crawlt eine URL und extrahiert Informationen"""
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Wenn FireCrawl API verfügbar
                if self.api_key:
                    response = await client.post(
                        "https://api.firecrawl.dev/v1/scrape",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "url": url,
                            "formats": ["markdown"],
                            "onlyMainContent": True
                        }
                    )
                    data = response.json().get("data", {})
                    content = data.get("markdown", "")
                    title = data.get("metadata", {}).get("title", "")
                else:
                    # Fallback: Einfacher HTTP-Abruf
                    response = await client.get(url, follow_redirects=True)
                    content = response.text[:10000]
                    
                    # Einfache Title-Extraktion
                    title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
                    title = title_match.group(1) if title_match else url
                    
                    # HTML-Tags entfernen für Content
                    content = re.sub(r'<[^>]+>', ' ', content)
                    content = re.sub(r'\s+', ' ', content).strip()
            
            # Themen extrahieren
            topics, risk_weight = self.topic_extractor.extract_topics(content)
            
            # Orte extrahieren
            locations = self.location_extractor.extract_locations(content)
            
            # Urgenz berechnen
            urgency = self.topic_extractor.calculate_urgency(content)
            
            # Sentiment analysieren
            sentiment = self.topic_extractor.analyze_sentiment(content)
            
            # H3 Indices aus Locations
            h3_indices = [loc["h3_index"] for loc in locations]
            
            return CrawledArticle(
                url=url,
                title=title,
                content=content[:5000],
                locations=locations,
                topics=topics,
                sentiment=sentiment,
                h3_indices=h3_indices,
                risk_signals=topics,
                urgency_score=urgency
            )
            
        except Exception as e:
            logger.error(f"Crawl error for {url}: {e}")
            return None
    
    async def enrich_h3_cell(
        self,
        h3_index: str,
        earth_data: Dict[str, float],
        crawled_articles: List[CrawledArticle]
    ) -> EnrichedCell:
        """
        Reichert eine H3-Zelle mit Crawling-Daten an
        
        Args:
            h3_index: H3-Index der Zelle
            earth_data: Numerische Erddaten (ERA5, Sentinel)
            crawled_articles: Gecrawlte Artikel für diese Region
        """
        lat, lon = h3.cell_to_latlng(h3_index)
        
        # Relevante Artikel filtern
        relevant_articles = [
            a for a in crawled_articles 
            if h3_index in a.h3_indices
        ]
        
        # Numerisches Risiko berechnen (aus Erddaten)
        numerical_risk = self._calculate_numerical_risk(earth_data)
        
        # Kontextuelles Risiko (aus Artikeln)
        contextual_risk = self._calculate_contextual_risk(relevant_articles)
        
        # Kombiniertes Risiko
        # Gewichtung: 60% numerisch, 40% kontextuell
        combined_risk = 0.6 * numerical_risk + 0.4 * contextual_risk
        
        # Dominante Themen
        all_topics = []
        for article in relevant_articles:
            all_topics.extend(article.topics)
        
        topic_counts = {}
        for topic in all_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        dominant_topics = sorted(topic_counts.keys(), key=lambda x: topic_counts[x], reverse=True)[:3]
        
        # Risiko-Treiber identifizieren
        risk_drivers = []
        
        if earth_data.get("temp_anomaly_c", 0) > 2:
            risk_drivers.append("temperature_anomaly")
        if earth_data.get("precip_anomaly_pct", 0) < -30:
            risk_drivers.append("precipitation_deficit")
        if earth_data.get("soil_moisture_pct", 50) < 20:
            risk_drivers.append("low_soil_moisture")
        if "drought" in dominant_topics:
            risk_drivers.append("drought_news")
        if "conflict" in dominant_topics:
            risk_drivers.append("conflict_news")
        if "flood" in dominant_topics:
            risk_drivers.append("flood_news")
        
        return EnrichedCell(
            h3_index=h3_index,
            lat=lat,
            lon=lon,
            temperature_c=earth_data.get("temperature_c", 0),
            temp_anomaly_c=earth_data.get("temp_anomaly_c", 0),
            precipitation_mm=earth_data.get("precipitation_mm", 0),
            precip_anomaly_pct=earth_data.get("precip_anomaly_pct", 0),
            soil_moisture_pct=earth_data.get("soil_moisture_pct", 50),
            ndvi=earth_data.get("ndvi", 0.5),
            articles=relevant_articles,
            article_count=len(relevant_articles),
            dominant_topics=dominant_topics,
            numerical_risk=numerical_risk,
            contextual_risk=contextual_risk,
            combined_risk=combined_risk,
            risk_drivers=risk_drivers
        )
    
    def _calculate_numerical_risk(self, earth_data: Dict[str, float]) -> float:
        """Berechnet Risiko aus numerischen Erddaten"""
        risk = 0.0
        
        # Temperatur-Anomalie
        temp_anom = abs(earth_data.get("temp_anomaly_c", 0))
        if temp_anom > 3:
            risk += 0.3
        elif temp_anom > 2:
            risk += 0.2
        elif temp_anom > 1:
            risk += 0.1
        
        # Niederschlags-Anomalie
        precip_anom = earth_data.get("precip_anomaly_pct", 0)
        if precip_anom < -50:  # Starke Dürre
            risk += 0.3
        elif precip_anom < -30:
            risk += 0.2
        elif precip_anom > 100:  # Starke Überschwemmung
            risk += 0.25
        
        # Bodenfeuchte
        soil = earth_data.get("soil_moisture_pct", 50)
        if soil < 15:
            risk += 0.2
        elif soil < 25:
            risk += 0.1
        
        # NDVI (Vegetation)
        ndvi = earth_data.get("ndvi", 0.5)
        if ndvi < 0.2:  # Wenig Vegetation / Dürre
            risk += 0.15
        
        return min(1.0, risk)
    
    def _calculate_contextual_risk(self, articles: List[CrawledArticle]) -> float:
        """Berechnet Risiko aus gecrawlten Artikeln"""
        if not articles:
            return 0.0
        
        # Durchschnittliche Urgenz
        avg_urgency = sum(a.urgency_score for a in articles) / len(articles)
        
        # Anzahl Risiko-Themen
        risk_topics = set()
        for article in articles:
            risk_topics.update(article.topics)
        
        topic_factor = min(1.0, len(risk_topics) / 5)
        
        # Negative Sentiment
        avg_sentiment = sum(a.sentiment for a in articles) / len(articles)
        sentiment_factor = max(0, -avg_sentiment)  # Nur negatives zählt
        
        # Artikel-Volumen (mehr Artikel = mehr Aufmerksamkeit)
        volume_factor = min(1.0, len(articles) / 10)
        
        # Kombinieren
        risk = (
            0.3 * avg_urgency +
            0.3 * topic_factor +
            0.2 * sentiment_factor +
            0.2 * volume_factor
        )
        
        return min(1.0, risk)
    
    async def run_enrichment_pipeline(
        self,
        target_locations: List[str] = None
    ) -> Dict[str, EnrichedCell]:
        """
        Führt die vollständige Anreicherungs-Pipeline aus
        
        1. Crawlt Priority-Quellen
        2. Extrahiert Orte und Themen
        3. Verknüpft mit H3-Zellen
        4. Berechnet kombiniertes Risiko
        """
        
        if target_locations is None:
            target_locations = ["berlin", "ukraine", "sudan", "jakarta"]
        
        logger.info(f"Starting enrichment pipeline for {len(target_locations)} locations")
        
        # 1. Crawl priority sources
        all_articles = []
        for source in self.PRIORITY_SOURCES[:3]:  # Limit für Demo
            logger.info(f"Crawling {source['name']}...")
            article = await self.crawl_url(source['url'])
            if article:
                all_articles.append(article)
        
        logger.info(f"Crawled {len(all_articles)} articles")
        
        # 2. Enrich cells
        enriched_cells = {}
        
        for location in target_locations:
            if location in self.location_extractor.KNOWN_LOCATIONS:
                lat, lon = self.location_extractor.KNOWN_LOCATIONS[location]
                h3_index = h3.latlng_to_cell(lat, lon, 7)
                
                # Mock earth data (in Produktion: ERA5/Sentinel)
                import random
                earth_data = {
                    "temperature_c": 15 + random.uniform(-10, 20),
                    "temp_anomaly_c": random.uniform(-1, 3),
                    "precipitation_mm": random.uniform(0, 50),
                    "precip_anomaly_pct": random.uniform(-50, 50),
                    "soil_moisture_pct": random.uniform(20, 80),
                    "ndvi": random.uniform(0.2, 0.8),
                }
                
                enriched = await self.enrich_h3_cell(
                    h3_index,
                    earth_data,
                    all_articles
                )
                
                enriched_cells[location] = enriched
        
        return enriched_cells


# =====================================================
# CONVENIENCE FUNCTIONS
# =====================================================

async def demo_enrichment():
    """Demo der FireCrawl-Anreicherung"""
    
    print("=" * 60)
    print("🔥 TERA FireCrawl Enrichment Demo")
    print("=" * 60)
    
    service = FireCrawlEnrichmentService()
    
    # Test-Locations
    locations = ["berlin", "ukraine", "jakarta", "miami"]
    
    enriched = await service.run_enrichment_pipeline(locations)
    
    print(f"\n📊 Ergebnisse für {len(enriched)} Standorte:\n")
    
    for location, cell in enriched.items():
        print(f"{'='*40}")
        print(f"📍 {location.upper()}")
        print(f"   H3: {cell.h3_index}")
        print(f"   Koordinaten: {cell.lat:.2f}, {cell.lon:.2f}")
        print(f"\n   🌡️  Numerische Daten:")
        print(f"      Temperatur: {cell.temperature_c:.1f}°C (Anomalie: {cell.temp_anomaly_c:+.1f}°C)")
        print(f"      Niederschlag: {cell.precipitation_mm:.1f}mm ({cell.precip_anomaly_pct:+.0f}%)")
        print(f"      Bodenfeuchte: {cell.soil_moisture_pct:.0f}%")
        print(f"      NDVI: {cell.ndvi:.2f}")
        print(f"\n   📰 Kontextuelle Daten:")
        print(f"      Artikel: {cell.article_count}")
        print(f"      Themen: {', '.join(cell.dominant_topics) if cell.dominant_topics else 'keine'}")
        print(f"\n   ⚠️  Risikobewertung:")
        print(f"      Numerisch: {cell.numerical_risk:.2f}")
        print(f"      Kontextuell: {cell.contextual_risk:.2f}")
        print(f"      KOMBINIERT: {cell.combined_risk:.2f}")
        if cell.risk_drivers:
            print(f"      Treiber: {', '.join(cell.risk_drivers)}")
    
    print(f"\n{'='*60}")
    print("✅ Enrichment Pipeline abgeschlossen!")


if __name__ == "__main__":
    asyncio.run(demo_enrichment())

