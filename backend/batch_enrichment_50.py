#!/usr/bin/env python3
"""
Batch-Enrichment: 50 Artikel mit 20 Datenpunkten anreichern
Iteriert durch ursprüngliche Webseiten und reichert jeden Artikel an
"""
import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import time
import json

sys.path.append(str(Path(__file__).parent))

from database import DatabaseManager
from config import Config
from fetchers import HTTPFetcher
from compliance import ComplianceAgent
from extractors import ExtractorFactory
from validators import ValidationAgent
from ipcc_context_engine import IPCCContextEngine
from firecrawl_enrichment import FirecrawlEnricher, CostTracker
from data_extraction import NumberExtractor
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel

console = Console()

# API Keys
FIRECRAWL_API_KEY = "fc-a0b3b8aa31244c10b0f15b4f2d570ac7"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY_HERE"

os.environ["FIRECRAWL_API_KEY"] = FIRECRAWL_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


class BatchEnrichmentPipeline:
    """Batch-Pipeline für 50 Artikel mit 20 Datenpunkten"""
    
    def __init__(self):
        self.config = Config()
        self.compliance = ComplianceAgent(self.config)
        self.db = DatabaseManager()
        self.ipcc_engine = IPCCContextEngine()
        self.cost_tracker = CostTracker()
        self.firecrawl_enricher = FirecrawlEnricher(FIRECRAWL_API_KEY, self.cost_tracker)
        self.number_extractor = NumberExtractor()
        
        # URLs der ursprünglichen Quellen - Verbesserte URLs die zu Artikellisten führen
        self.source_urls = {
            "NASA": [
                "https://earthobservatory.nasa.gov/images",
                "https://earthobservatory.nasa.gov/images/events",
                "https://earthobservatory.nasa.gov/features",
                "https://earthobservatory.nasa.gov/world-of-change",
                "https://earthobservatory.nasa.gov/global-maps"
            ],
            "UN Press": [
                "https://press.un.org/en/content/press-releases",
                "https://press.un.org/en/content/meetings-coverage",
                "https://press.un.org/en/content/statements",
                "https://press.un.org/en/content/briefings"
            ],
            "WFP": [
                "https://www.wfp.org/news",
                "https://www.wfp.org/stories",
                "https://www.wfp.org/news/latest",
                "https://www.wfp.org/publications"
            ],
            "World Bank": [
                "https://www.worldbank.org/en/news/all",
                "https://www.worldbank.org/en/news",
                "https://www.worldbank.org/en/news/press-release",
                "https://www.worldbank.org/en/news/feature"
            ]
        }
    
    async def discover_article_urls(self, source_name: str, start_urls: List[str], target_count: int = 50) -> List[str]:
        """Entdecke Artikel-URLs durch Iteration"""
        console.print(f"\n[cyan]Entdecke Artikel-URLs für {source_name}...[/cyan]")
        
        article_urls = set()
        visited_urls = set()
        to_visit = list(start_urls)
        
        fetcher = HTTPFetcher(self.config, self.compliance)
        await fetcher.__aenter__()
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                task = progress.add_task(f"Suche Artikel...", total=target_count)
                
                max_iterations = 20  # Begrenze Iterationen um Endlosschleifen zu vermeiden
                iteration = 0
                
                while len(article_urls) < target_count and to_visit and iteration < max_iterations:
                    current_url = to_visit.pop(0)
                    iteration += 1
                    
                    if current_url in visited_urls:
                        continue
                    
                    visited_urls.add(current_url)
                    
                    try:
                        # Fetch URL
                        result = await fetcher.fetch(current_url)
                        
                        if result.success and result.content:
                            # Finde Artikel-Links
                            found_urls = self._find_article_links(
                                result.content,
                                current_url,
                                source_name
                            )
                            
                            # Füge neue URLs hinzu
                            new_urls_added = 0
                            for url in found_urls:
                                if url not in article_urls and url not in visited_urls:
                                    article_urls.add(url)
                                    new_urls_added += 1
                                    
                                    # Füge auch zu to_visit hinzu für weitere Discovery (nur wenn noch Platz)
                                    if len(article_urls) < target_count and url not in to_visit:
                                        to_visit.append(url)
                            
                            if new_urls_added > 0:
                                console.print(f"  ✅ {current_url}: {new_urls_added} neue Artikel gefunden (Gesamt: {len(article_urls)})")
                            
                            progress.update(task, completed=len(article_urls))
                            
                            # Pause um Rate Limits zu vermeiden
                            await asyncio.sleep(1)
                        else:
                            console.print(f"  ⚠️  {current_url}: Kein Content erhalten")
                    
                    except Exception as e:
                        console.print(f"[red]Fehler bei {current_url}: {e}[/red]")
                        continue
                
                if iteration >= max_iterations:
                    console.print(f"[yellow]⚠️  Max Iterationen erreicht. Gefunden: {len(article_urls)} Artikel[/yellow]")
                
                await fetcher.__aexit__(None, None, None)
        
        except Exception as e:
            console.print(f"[red]Fehler: {e}[/red]")
            await fetcher.__aexit__(None, None, None)
        
        return list(article_urls)[:target_count]
    
    def _find_article_links(self, html: str, base_url: str, source: str) -> Set[str]:
        """Finde Artikel-Links auf einer Seite - Verbesserte Logik"""
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin, urlparse
        import re
        
        soup = BeautifulSoup(html, 'lxml')
        article_urls = set()
        
        if 'nasa' in base_url.lower():
            # NASA: Suche nach Links die zu einzelnen Artikeln führen
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_url, href)
                
                # Nur earthobservatory.nasa.gov URLs
                if 'earthobservatory.nasa.gov' not in full_url:
                    continue
                
                # Filtere Übersichtsseiten aus
                if any(x in full_url for x in ['/images', '/features', '/world-of-change', '/global-maps']):
                    # Aber nur wenn es ein spezifischer Artikel ist (mehrere Pfadsegmente)
                    parsed = urlparse(full_url)
                    path_parts = [p for p in parsed.path.split('/') if p]
                    
                    # Artikel haben meist mindestens 3 Pfadsegmente nach dem Domain-Teil
                    if len(path_parts) >= 2:
                        # Vermeide Übersichtsseiten (nur /images, /features etc.)
                        if len(path_parts) >= 3 or any(x in full_url for x in ['/images/', '/features/']):
                            # Vermeide Pagination und Filter
                            if not any(x in full_url for x in ['?page=', '?filter=', '?sort=']):
                                article_urls.add(full_url)
        
        elif 'press.un.org' in base_url.lower():
            # UN Press: Suche nach Press Release Links
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_url, href)
                
                # Nur press.un.org URLs
                if 'press.un.org' not in full_url:
                    continue
                
                # Suche nach /en/content/ mit spezifischen Patterns
                if '/en/content/' in full_url:
                    # Vermeide Übersichtsseiten
                    if not any(x in full_url for x in ['/content/press-releases', '/content/meetings-coverage', '/content/statements', '/content/briefings']):
                        # Artikel haben meist ein Datum oder eine ID im Pfad
                        # Pattern: /en/content/press-release/YYYY/MM/DD oder /en/content/statement/...
                        if re.search(r'/\d{4}/|/\d{2}/|/[a-z-]+/[a-z-]+', full_url):
                            # Mindestens 4 Pfadsegmente nach /en/content/
                            path_parts = [p for p in full_url.split('/en/content/')[1].split('/') if p] if '/en/content/' in full_url else []
                            if len(path_parts) >= 2:
                                article_urls.add(full_url)
        
        elif 'wfp.org' in base_url.lower():
            # WFP: Suche nach News-Artikel Links - Verbesserte Logik
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_url, href)
                
                # Nur wfp.org URLs
                if 'wfp.org' not in full_url:
                    continue
                
                # Filtere aus: Übersichtsseiten, Filter, Pagination, etc.
                exclude_patterns = [
                    '/news/all', '/news/press-release', '/news/feature',
                    '/news/speech', '/news/opinion', '/news/archive',
                    '?page=', '?filter=', '?sort=', '#', 'javascript:',
                    '/about', '/contact', '/donate', '/get-involved'
                ]
                
                if any(pattern in full_url for pattern in exclude_patterns):
                    continue
                
                # Suche nach verschiedenen WFP-URL-Patterns
                # Pattern 1: /news/YYYY/MM/DD/title-slug
                if re.search(r'/news/\d{4}/\d{2}/\d{2}/[a-z0-9-]+', full_url, re.I):
                    article_urls.add(full_url)
                    continue
                
                # Pattern 2: /stories/title-slug oder /news/title-slug
                if '/stories/' in full_url or '/news/' in full_url:
                    path_parts = []
                    if '/news/' in full_url:
                        path_parts = [p for p in full_url.split('/news/')[1].split('/') if p]
                    elif '/stories/' in full_url:
                        path_parts = [p for p in full_url.split('/stories/')[1].split('/') if p]
                    
                    # Mindestens 1 Pfadsegment (Titel-Slug), nicht nur Zahlen
                    if len(path_parts) >= 1 and path_parts[0] and not path_parts[0].isdigit():
                        # Prüfe ob es wie ein Artikel-Slug aussieht (enthält Buchstaben)
                        if re.search(r'[a-z]', path_parts[0], re.I):
                            article_urls.add(full_url)
                            continue
                
                # Pattern 3: /publications/ oder /resources/ mit Titel-Slug
                if '/publications/' in full_url or '/resources/' in full_url:
                    path_parts = [p for p in full_url.split('/') if p]
                    # Mindestens 5 Pfadsegmente (domain/news/title)
                    if len(path_parts) >= 5:
                        article_urls.add(full_url)
                        continue
                
                # Pattern 4: Suche nach Links mit class="article" oder ähnlich
                link_classes = link.get('class', [])
                if any('article' in str(cls).lower() or 'story' in str(cls).lower() or 'news' in str(cls).lower() for cls in link_classes):
                    if '/news/' in full_url or '/stories/' in full_url:
                        article_urls.add(full_url)
        
        elif 'worldbank.org' in base_url.lower():
            # World Bank: Suche nach News-Artikel Links
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_url, href)
                
                # Nur worldbank.org URLs
                if 'worldbank.org' not in full_url:
                    continue
                
                # Suche nach /en/news/ mit Datum-Pattern
                if '/en/news/' in full_url:
                    # Vermeide Übersichtsseiten
                    if not any(x in full_url for x in ['/news/all', '/news/press-release', '/news/feature', '/news/speech']):
                        # Artikel haben meist Datum im Pfad: /en/news/YYYY/MM/DD/...
                        if re.search(r'/\d{4}/\d{2}/\d{2}/', full_url):
                            article_urls.add(full_url)
                        # Oder haben einen Titel-Slug nach /news/
                        elif '/news/' in full_url:
                            path_parts = [p for p in full_url.split('/en/news/')[1].split('/') if p] if '/en/news/' in full_url else []
                            # Mindestens 1 Pfadsegment (Titel-Slug)
                            if len(path_parts) >= 1 and path_parts[0] and not path_parts[0].isdigit():
                                article_urls.add(full_url)
        
        return article_urls
    
    async def crawl_and_extract_article(self, url: str, source_name: str) -> Optional[Dict]:
        """Crawle einen Artikel und extrahiere Daten"""
        try:
            fetcher = HTTPFetcher(self.config, self.compliance)
            await fetcher.__aenter__()
            
            result = await fetcher.fetch(url)
            await fetcher.__aexit__(None, None, None)
            
            if not result.success or not result.content:
                return None
            
            # Extrahiere mit Extractor
            extractor_factory = ExtractorFactory(self.config)
            extractor = extractor_factory.get_extractor(url)
            
            if not extractor:
                return None
            
            record = extractor.extract(result)
            
            if record:
                return {
                    'url': url,
                    'source_name': source_name,
                    'record': record
                }
        
        except Exception as e:
            console.print(f"[red]Fehler beim Crawlen von {url}: {e}[/red]")
            return None
    
    def enrich_with_20_datapoints(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Reichere Record mit 20 Datenpunkten an (IPCC-basiert)"""
        enrichment = {
            'datapoints': {},
            'ipcc_metrics': {},
            'extracted_numbers': {},
            'firecrawl_data': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # 1. IPCC-Kontext erstellen
        ipcc_context = self.ipcc_engine.get_firecrawl_context(record)
        
        # 2. Firecrawl-Suche (IPCC-basiert)
        try:
            # Sicherstelle dass keywords eine Liste von Strings ist
            keywords = ipcc_context.get('keywords', [])
            if keywords:
                # Filtere None-Werte heraus
                keywords = [k for k in keywords[:5] if k and isinstance(k, str)]
            
            # KEINE Fallback-Keywords - nur echte Keywords verwenden
            # Wenn keine Keywords vorhanden, verwende nur Region falls vorhanden
            if not keywords and record.get('region'):
                keywords = [record.get('region')]
            
            if keywords:
                search_results, _ = self.firecrawl_enricher.enrich_with_search(
                    keywords=keywords,
                    region=record.get('region'),
                    limit=5,
                    scrape_content=True,
                    ipcc_context=ipcc_context
                )
                enrichment['firecrawl_data']['search_results'] = search_results
        except Exception as e:
            console.print(f"[yellow]Search-Fehler: {e}[/yellow]")
            enrichment['firecrawl_data']['search_results'] = []
        
        # 3. Extrahiere Zahlen aus Record + Search-Results
        text_content = f"{record.get('title', '')} {record.get('summary', '')} {record.get('full_text', '')}"
        
        # Füge Search-Results-Text hinzu
        for result in enrichment['firecrawl_data'].get('search_results', []):
            text_content += f" {result.get('title', '')} {result.get('description', '')}"
            if result.get('markdown'):
                text_content += f" {result.get('markdown', '')[:500]}"
        
        extracted = self.number_extractor.extract_all(text_content)
        
        # 4. Extrahiere NUR echte Datenpunkte - KEINE Fallback-Daten
        datapoints = {}
        
        # Temperatur-Datenpunkte (NUR wenn vorhanden)
        if extracted.temperatures:
            for i, temp in enumerate(extracted.temperatures[:3], 1):
                datapoints[f"temperature_{i}"] = temp
        
        # Niederschlags-Datenpunkte (NUR wenn vorhanden)
        if extracted.precipitation:
            for i, precip in enumerate(extracted.precipitation[:3], 1):
                datapoints[f"precipitation_{i}"] = precip
        
        # Bevölkerungs-Datenpunkte (NUR wenn vorhanden)
        if extracted.population_numbers:
            for i, pop in enumerate(extracted.population_numbers[:3], 1):
                datapoints[f"population_{i}"] = pop
        
        # Finanz-Datenpunkte (NUR wenn vorhanden)
        if extracted.financial_amounts:
            for i, amount in enumerate(extracted.financial_amounts[:3], 1):
                datapoints[f"financial_{i}"] = amount
        
        # Spezifische Metriken (NUR wenn vorhanden)
        if extracted.affected_people:
            datapoints["affected_people"] = extracted.affected_people
        
        if extracted.funding_amount:
            datapoints["funding_amount"] = extracted.funding_amount
        
        # IPCC-Metriken (NUR wenn echte Temperatur-Daten vorhanden)
        if extracted.temperatures and len(extracted.temperatures) > 0:
            avg_temp = sum(extracted.temperatures) / len(extracted.temperatures)
            anomaly = avg_temp - 13.5  # IPCC Baseline
            datapoints["temperature_anomaly"] = round(anomaly, 2)
        
        # IPCC-Metriken (NUR wenn echte Niederschlags-Daten vorhanden)
        if extracted.precipitation and len(extracted.precipitation) > 0:
            avg_precip = sum(extracted.precipitation) / len(extracted.precipitation)
            anomaly_percent = ((avg_precip - 100) / 100) * 100  # Normal = 100mm
            datapoints["precipitation_anomaly"] = round(anomaly_percent, 2)
        
        # Prozentsätze (NUR wenn vorhanden)
        if extracted.percentages:
            for i, pct in enumerate(extracted.percentages[:2], 1):
                datapoints[f"percentage_{i}"] = pct
        
        # Datumsangaben (NUR wenn vorhanden)
        if extracted.dates and len(extracted.dates) > 0:
            datapoints["dates_count"] = len(extracted.dates)
        
        # Orte (NUR wenn vorhanden)
        if extracted.locations and len(extracted.locations) > 0:
            datapoints["locations_count"] = len(extracted.locations)
            datapoints["locations"] = extracted.locations[:5]
        
        # Risk Scores (berechnen) - IMMER vorhanden, da aus echten Daten berechnet
        from risk_scoring import RiskScorer
        scorer = RiskScorer()
        risk = scorer.calculate_risk(record)
        datapoints["risk_score"] = risk.score
        datapoints["climate_risk"] = risk.climate_risk
        datapoints["conflict_risk"] = risk.conflict_risk
        datapoints["urgency"] = risk.urgency
        
        # Metadaten - IMMER vorhanden, da aus echten Record-Daten
        if record.get('title'):
            datapoints["has_title"] = 1
            datapoints["title_length"] = len(record.get('title', ''))
        
        if record.get('summary'):
            datapoints["has_summary"] = 1
            datapoints["summary_length"] = len(record.get('summary', ''))
        
        # Weitere Metadaten (NUR wenn vorhanden)
        if record.get('region'):
            datapoints["has_region"] = 1
        
        if record.get('topics') and len(record.get('topics', [])) > 0:
            datapoints["has_topics"] = len(record.get('topics', []))
        
        if record.get('full_text'):
            datapoints["has_full_text"] = 1
        
        if record.get('source_name'):
            datapoints["source_type"] = record.get('source_name')
        
        enrichment['datapoints'] = datapoints
        enrichment['extracted_numbers'] = {
            'temperatures': extracted.temperatures,
            'precipitation': extracted.precipitation,
            'population_numbers': extracted.population_numbers,
            'financial_amounts': extracted.financial_amounts,
            'affected_people': extracted.affected_people,
            'funding_amount': extracted.funding_amount
        }
        enrichment['ipcc_metrics'] = {
            'baseline_period': ipcc_context.get('ipcc_context', {}).get('baseline_period'),
            'current_anomaly': ipcc_context.get('ipcc_context', {}).get('current_anomaly'),
            'focus_areas': ipcc_context.get('focus_areas', [])
        }
        
        return enrichment
    
    def save_enriched_record(self, record: Dict, enrichment: Dict) -> int:
        """Speichere angereicherten Record in DB"""
        # Speichere Record zuerst
        from schemas import PageRecord
        
        page_record = PageRecord(
            url=record.get('url', ''),
            source_domain=record.get('source_domain', ''),
            source_name=record.get('source_name', ''),
            fetched_at=datetime.now(),
            title=record.get('title'),
            summary=record.get('summary'),
            publish_date=record.get('publish_date'),
            region=record.get('region'),
            topics=record.get('topics', []),
            content_type=record.get('content_type'),
            language=record.get('language', 'en'),
            full_text=record.get('full_text')
        )
        
        result = self.db.insert_record(page_record)
        
        if result:
            record_id, is_new = result
            
            # Speichere Anreicherungsdaten
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Erstelle Tabelle für Batch-Anreicherung
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS batch_enrichment (
                        record_id INTEGER PRIMARY KEY,
                        datapoints TEXT,
                        ipcc_metrics TEXT,
                        extracted_numbers TEXT,
                        firecrawl_data TEXT,
                        enrichment_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (record_id) REFERENCES records(id) ON DELETE CASCADE
                    )
                """)
                
                # Speichere Anreicherung
                cursor.execute("""
                    INSERT OR REPLACE INTO batch_enrichment (
                        record_id, datapoints, ipcc_metrics,
                        extracted_numbers, firecrawl_data
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    record_id,
                    json.dumps(enrichment.get('datapoints', {})),
                    json.dumps(enrichment.get('ipcc_metrics', {})),
                    json.dumps(enrichment.get('extracted_numbers', {})),
                    json.dumps(enrichment.get('firecrawl_data', {}))
                ))
            
            return record_id
        
        return None
    
    async def run_batch_50(self) -> Dict[str, Any]:
        """Führe Batch-Enrichment für 50 Artikel durch"""
        console.print(Panel.fit(
            "[bold green]🚀 Batch-Enrichment: 50 Artikel mit 20 Datenpunkten[/bold green]",
            border_style="green"
        ))
        
        all_enriched_records = []
        total_articles = 0
        target_count = 50
        
        # Iteriere durch alle Quellen
        for source_name, start_urls in self.source_urls.items():
            if total_articles >= target_count:
                break
            
            remaining = target_count - total_articles
            console.print(f"\n[bold cyan]📡 Verarbeite {source_name}[/bold cyan]")
            
            # Entdecke Artikel-URLs
            article_urls = await self.discover_article_urls(
                source_name,
                start_urls,
                target_count=min(remaining, 20)  # Max 20 pro Quelle
            )
            
            console.print(f"[green]Gefunden: {len(article_urls)} Artikel[/green]")
            
            # Verarbeite jeden Artikel
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                task = progress.add_task(
                    f"Verarbeite {source_name} Artikel...",
                    total=len(article_urls)
                )
                
                for url in article_urls:
                    if total_articles >= target_count:
                        break
                    
                    try:
                        # 1. Crawle Artikel
                        article_data = await self.crawl_and_extract_article(url, source_name)
                        
                        if not article_data:
                            progress.update(task, advance=1)
                            continue
                        
                        record = article_data['record']
                        record_dict = {
                            'url': url,
                            'source_name': source_name,
                            'title': record.title if hasattr(record, 'title') else None,
                            'summary': record.summary if hasattr(record, 'summary') else None,
                            'region': record.region if hasattr(record, 'region') else None,
                            'publish_date': record.publish_date if hasattr(record, 'publish_date') else None,
                            'topics': record.topics if hasattr(record, 'topics') else [],
                            'full_text': getattr(record, 'full_text', None)
                        }
                        
                        # 2. Reichere mit 20 Datenpunkten an
                        enrichment = self.enrich_with_20_datapoints(record_dict)
                        
                        # 3. Speichere in DB
                        record_id = self.save_enriched_record(record_dict, enrichment)
                        
                        if record_id:
                            all_enriched_records.append({
                                'record_id': record_id,
                                'url': url,
                                'source': source_name,
                                'datapoints_count': len(enrichment.get('datapoints', {})),
                                'enrichment': enrichment
                            })
                            total_articles += 1
                        
                        progress.update(task, advance=1)
                        
                        # Pause zwischen Requests
                        await asyncio.sleep(2)
                    
                    except Exception as e:
                        console.print(f"[red]Fehler bei {url}: {e}[/red]")
                        progress.update(task, advance=1)
                        continue
        
        # Zusammenfassung
        summary = {
            'total_articles': total_articles,
            'enriched_records': all_enriched_records,
            'costs': self.cost_tracker.get_summary(),
            'datapoints_summary': self._analyze_datapoints(all_enriched_records)
        }
        
        return summary
    
    def _analyze_datapoints(self, records: List[Dict]) -> Dict[str, Any]:
        """Analysiere extrahierte Datenpunkte"""
        analysis = {
            'total_datapoints': 0,
            'datapoint_types': {},
            'regions': set(),
            'sources': {}
        }
        
        for record in records:
            enrichment = record.get('enrichment', {})
            datapoints = enrichment.get('datapoints', {})
            
            analysis['total_datapoints'] += len(datapoints)
            
            for key in datapoints.keys():
                datapoint_type = key.split('_')[0] if '_' in key else key
                analysis['datapoint_types'][datapoint_type] = analysis['datapoint_types'].get(datapoint_type, 0) + 1
            
            source = record.get('source')
            if source:
                analysis['sources'][source] = analysis['sources'].get(source, 0) + 1
        
        analysis['datapoint_types'] = dict(sorted(analysis['datapoint_types'].items(), key=lambda x: x[1], reverse=True))
        analysis['regions'] = list(analysis['regions'])
        
        return analysis
    
    def show_stored_data(self, limit: int = 10):
        """Zeige was in der Datenbank gespeichert wurde"""
        console.print("\n[bold cyan]📊 Gespeicherte Daten:[/bold cyan]\n")
        
        # Hole Records
        records = self.db.get_records(limit=limit)
        
        if not records:
            console.print("[yellow]Keine Records gefunden[/yellow]")
            return
        
        # Zeige Records
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan")
        table.add_column("Titel", style="green")
        table.add_column("Quelle", style="yellow")
        table.add_column("Region", style="blue")
        table.add_column("Datum", style="white")
        
        for record in records:
            table.add_row(
                str(record.get('id', 'N/A')),
                (record.get('title', 'N/A') or 'N/A')[:40],
                record.get('source_name', 'N/A'),
                record.get('region', 'N/A') or 'N/A',
                record.get('publish_date', 'N/A') or 'N/A'
            )
        
        console.print(table)
        
        # Zeige Anreicherungsdaten
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Prüfe ob Tabelle existiert
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='batch_enrichment'
            """)
            
            if cursor.fetchone():
                cursor.execute("""
                    SELECT record_id, datapoints, enrichment_timestamp
                    FROM batch_enrichment
                    ORDER BY enrichment_timestamp DESC
                    LIMIT ?
                """, (limit,))
                
                enrichments = cursor.fetchall()
                
                if enrichments:
                    console.print(f"\n[bold cyan]📈 Anreicherungsdaten ({len(enrichments)}):[/bold cyan]\n")
                    
                    enrich_table = Table(show_header=True, header_style="bold magenta")
                    enrich_table.add_column("Record ID", style="cyan")
                    enrich_table.add_column("Datenpunkte", style="green")
                    enrich_table.add_column("Zeitstempel", style="yellow")
                    
                    for enrich in enrichments:
                        datapoints = json.loads(enrich[1])
                        enrich_table.add_row(
                            str(enrich[0]),
                            str(len(datapoints)),
                            enrich[2][:19] if enrich[2] else 'N/A'
                        )
                    
                    console.print(enrich_table)
        
        # Zeige Datenbank-Schema
        console.print("\n[bold cyan]🗄️  Datenbank-Schema:[/bold cyan]\n")
        
        schema_table = Table(show_header=True, header_style="bold magenta")
        schema_table.add_column("Tabelle", style="cyan")
        schema_table.add_column("Zweck", style="green")
        
        schema_table.add_row("records", "Haupttabelle: Alle gecrawlten Artikel")
        schema_table.add_row("record_topics", "Topics/Tags pro Record")
        schema_table.add_row("record_links", "Links pro Record")
        schema_table.add_row("record_images", "Bilder pro Record")
        schema_table.add_row("nasa_records", "NASA-spezifische Daten")
        schema_table.add_row("un_press_records", "UN Press-spezifische Daten")
        schema_table.add_row("worldbank_records", "World Bank-spezifische Daten")
        schema_table.add_row("extracted_numbers", "Extrahierte Zahlen")
        schema_table.add_row("risk_scores", "Berechnete Risk Scores")
        schema_table.add_row("llm_predictions", "LLM-basierte Predictions")
        schema_table.add_row("batch_enrichment", "Batch-Anreicherung (20 Datenpunkte)")
        schema_table.add_row("enriched_data", "Angereicherte Daten")
        schema_table.add_row("trend_predictions", "Zeitreihenvorhersagen")
        
        console.print(schema_table)


async def main():
    """Hauptfunktion"""
    pipeline = BatchEnrichmentPipeline()
    
    # Zeige aktuell gespeicherte Daten
    console.print("\n[bold yellow]1. Aktuell gespeicherte Daten:[/bold yellow]")
    pipeline.show_stored_data(limit=5)
    
    # Frage ob Batch ausgeführt werden soll
    console.print("\n[bold yellow]2. Batch-Enrichment starten?[/bold yellow]")
    console.print("[cyan]Dies wird durch die ursprünglichen Webseiten iterieren[/cyan]")
    console.print("[cyan]und 50 Artikel mit je 20 Datenpunkten anreichern...[/cyan]")
    
    # Starte Batch
    console.print("\n[bold green]🚀 Starte Batch-Enrichment...[/bold green]\n")
    
    summary = await pipeline.run_batch_50()
    
    # Zeige Ergebnisse
    console.print("\n[bold green]✅ Batch-Enrichment abgeschlossen![/bold green]\n")
    
    console.print(f"[cyan]Verarbeitet:[/cyan] {summary['total_articles']} Artikel")
    console.print(f"[cyan]Datenpunkte gesamt:[/cyan] {summary['datapoints_summary']['total_datapoints']}")
    
    # Datapoint-Typen
    console.print(f"\n[cyan]Datenpunkt-Typen:[/cyan]")
    for dtype, count in list(summary['datapoints_summary']['datapoint_types'].items())[:10]:
        console.print(f"  {dtype}: {count}")
    
    # Quellen-Verteilung
    console.print(f"\n[cyan]Quellen-Verteilung:[/cyan]")
    for source, count in summary['datapoints_summary']['sources'].items():
        console.print(f"  {source}: {count} Artikel")
    
    # Kosten
    costs = summary['costs']
    console.print(f"\n[bold yellow]💰 Kosten:[/bold yellow]")
    console.print(f"  Firecrawl Credits: {costs.get('firecrawl_credits_used', 0):.1f}")
    console.print(f"  Verbleibend: {costs.get('firecrawl_credits_remaining', 20000):,.0f}")
    console.print(f"  OpenAI Kosten: ${costs.get('openai_cost_usd', 0):.4f}")
    
    # Zeige gespeicherte Daten
    console.print("\n[bold yellow]3. Gespeicherte Daten nach Batch:[/bold yellow]")
    pipeline.show_stored_data(limit=10)


if __name__ == "__main__":
    asyncio.run(main())

