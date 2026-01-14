#!/usr/bin/env python3
"""
Systematische Geospatial-Extraktion
- Generiert 50 URLs systematisch
- Extrahiert mit Firecrawl + Ollama
- Erstellt Kontextraum für jedes Land
- Bereitet Daten für interaktive Risiko-Karte vor
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import requests

sys.path.append(str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from config import Config
from database import DatabaseManager
from firecrawl_enrichment import FirecrawlEnricher, CostTracker
from ipcc_context_engine import IPCCContextEngine
from schemas import PageRecord
from free_llm_extractor import FreeLLMExtractor
from risk_scoring import RiskScorer

console = Console()


class SystematicGeospatialExtractor:
    """Systematische Geospatial-Extraktion für Länder"""
    
    def __init__(self):
        self.config = Config()
        self.db = DatabaseManager()
        self.cost_tracker = CostTracker()
        self.firecrawl = FirecrawlEnricher(self.config.FIRECRAWL_API_KEY, self.cost_tracker)
        self.ipcc_engine = IPCCContextEngine()
        self.llm_extractor = FreeLLMExtractor(
            ollama_host=self.config.OLLAMA_HOST,
            model=self.config.OLLAMA_MODEL
        )
        self.risk_scorer = RiskScorer()
        
        # Länder für Geospatial-Analyse
        self.countries = {
            "DE": {"name": "Germany", "topics": ["flood", "drought", "heat wave"]},
            "FR": {"name": "France", "topics": ["heat wave", "drought", "wildfire"]},
            "IT": {"name": "Italy", "topics": ["flood", "drought", "heat wave"]},
            "ES": {"name": "Spain", "topics": ["drought", "wildfire", "heat wave"]},
            "GB": {"name": "United Kingdom", "topics": ["flood", "storm", "precipitation"]},
            "IN": {"name": "India", "topics": ["monsoon", "flood", "drought"]},
            "CN": {"name": "China", "topics": ["flood", "drought", "typhoon"]},
            "US": {"name": "United States", "topics": ["hurricane", "drought", "wildfire"]},
            "BR": {"name": "Brazil", "topics": ["drought", "flood", "deforestation"]},
            "AU": {"name": "Australia", "topics": ["drought", "wildfire", "heat wave"]},
        }
    
    def generate_urls_systematically(self, country_code: str, target_urls: int = 50) -> List[str]:
        """Generiere URLs systematisch für ein Land"""
        country_info = self.countries.get(country_code, {})
        country_name = country_info.get("name", country_code)
        topics = country_info.get("topics", [])
        
        console.print(f"\n[bold cyan]🌍 Generiere URLs für {country_name} ({country_code})...[/bold cyan]")
        
        urls = []
        
        # Strategie 1: Firecrawl Search mit verschiedenen Queries
        search_queries = []
        for topic in topics:
            search_queries.extend([
                f"{country_name} {topic} climate change",
                f"{country_name} {topic} IPCC",
                f"{country_name} {topic} extreme weather",
                f"{country_name} {topic} risk",
            ])
        
        # Strategie 2: Bekannte Quellen-URLs
        source_urls = {
            "DE": [
                "https://www.dwd.de/DE/klimaumwelt/klimawandel/klimawandel_node.html",
                "https://www.umweltbundesamt.de/themen/klima-energie/klimawandel",
                "https://www.pik-potsdam.de/de/aktuelles/nachrichten",
            ],
            "FR": [
                "https://www.ecologie.gouv.fr/climat",
                "https://www.meteofrance.fr/climat",
            ],
            "IT": [
                "https://www.isprambiente.gov.it/it/temi/cambiamenti-climatici",
            ],
            "ES": [
                "https://www.miteco.gob.es/es/cambio-climatico",
            ],
            "GB": [
                "https://www.gov.uk/government/collections/climate-change-explained",
                "https://www.metoffice.gov.uk/weather/climate",
            ],
            "IN": [
                "https://www.moef.gov.in/en/division/environment-division/climate-change",
            ],
            "CN": [
                "https://www.mee.gov.cn/ywgz/ydqhbh/wsqtkz/",
            ],
            "US": [
                "https://www.epa.gov/climatechange",
                "https://www.noaa.gov/climate",
            ],
            "BR": [
                "https://www.gov.br/mcti/pt-br/acompanhe-o-mcti/acoes-e-programas/mudanca-do-clima",
            ],
            "AU": [
                "https://www.dcceew.gov.au/climate-change",
            ],
        }
        
        urls.extend(source_urls.get(country_code, []))
        
        # Strategie 3: Generiere weitere URLs mit Ollama (falls verfügbar)
        if self.llm_extractor.ollama_available and len(urls) < target_urls:
            try:
                prompt = f"""Generiere 20 spezifische URLs oder Suchqueries für Klimadaten zu {country_name} ({country_code}).

Fokus auf:
- Offizielle Regierungs-Websites
- Wissenschaftliche Institutionen
- Klima-Organisationen
- IPCC-relevante Quellen

Antworte als JSON-Array:
["url oder query 1", "url oder query 2", ...]
"""
                response = requests.post(
                    f"{self.config.OLLAMA_HOST}/api/generate",
                    json={
                        "model": self.config.OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    generated = json.loads(result.get('response', '[]'))
                    if isinstance(generated, list):
                        urls.extend(generated[:20])
                        console.print(f"  [green]✅ {len(generated)} URLs/Queries mit LLM generiert[/green]")
            except:
                pass
        
        # Strategie 4: Firecrawl Search für fehlende URLs
        if len(urls) < target_urls:
            console.print(f"  [dim]Suche weitere URLs mit Firecrawl Search...[/dim]")
            for query in search_queries[:10]:  # Erste 10 Queries
                try:
                    response = requests.post(
                        "https://api.firecrawl.dev/v0/search",
                        headers={
                            "Authorization": f"Bearer {self.config.FIRECRAWL_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "query": query,
                            "limit": 5
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        results = data.get('data', {}).get('web', [])
                        for result in results:
                            url = result.get('url')
                            if url and url not in urls:
                                urls.append(url)
                                if len(urls) >= target_urls:
                                    break
                except:
                    continue
        
        console.print(f"  [green]✅ {len(urls)} URLs generiert[/green]")
        return urls[:target_urls]  # Limit auf target_urls
    
    async def extract_urls_with_firecrawl_ollama(
        self,
        urls: List[str],
        country_code: str
    ) -> List[Dict[str, Any]]:
        """Extrahiere URLs systematisch mit Firecrawl + Ollama"""
        console.print(f"\n[bold cyan]📊 Extrahiere {len(urls)} URLs...[/bold cyan]")
        
        records = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task(
                "[cyan]Extrahiere...",
                total=len(urls)
            )
            
            for url in urls:
                try:
                    # Schritt 1: Scrape mit Firecrawl
                    response = await asyncio.to_thread(
                        requests.post,
                        "https://api.firecrawl.dev/v0/scrape",
                        headers={
                            "Authorization": f"Bearer {self.config.FIRECRAWL_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "url": url,
                            "formats": ["markdown"],
                            "onlyMainContent": True
                        },
                        timeout=30
                    )
                    
                    if response.status_code != 200:
                        progress.update(task, advance=1)
                        continue
                    
                    scrape_data = response.json().get('data', {})
                    markdown = scrape_data.get('markdown', '')
                    metadata = scrape_data.get('metadata', {})
                    
                    if not markdown:
                        progress.update(task, advance=1)
                        continue
                    
                    # Schritt 2: Extrahiere mit Ollama (wenn verfügbar) oder Pattern-Matching
                    extracted_data = self.llm_extractor.extract_with_llm(
                        text=markdown[:2000],  # Erste 2000 Zeichen
                        schema=self._get_extraction_schema(),
                        use_llm=self.llm_extractor.ollama_available  # Nutze LLM wenn verfügbar
                    )
                    
                    # Schritt 3: Berechne Risiko-Score
                    record_dict = {
                        'url': url,
                        'source_domain': self._extract_domain(url),
                        'source_name': self._extract_source_name(url, country_code),
                        'fetched_at': datetime.now(),
                        'title': extracted_data.get('title') or metadata.get('title', ''),
                        'summary': extracted_data.get('summary') or metadata.get('description', ''),
                        'publish_date': extracted_data.get('publish_date') or metadata.get('publishedTime', ''),
                        'region': extracted_data.get('location') or self.countries.get(country_code, {}).get('name', ''),
                        'primary_country_code': country_code,
                        'topics': list(set(extracted_data.get('ipcc_risks', []))),
                        'content_type': 'research',
                        'full_text': markdown[:5000] if markdown else '',
                    }
                    
                    # Berechne Risiko
                    risk = self.risk_scorer.calculate_risk(record_dict)
                    record_dict['risk_score'] = risk.score
                    record_dict['risk_level'] = self.risk_scorer.get_risk_level(risk.score)
                    
                    records.append(record_dict)
                    progress.update(task, advance=1)
                    
                    llm_status = "🤖" if self.llm_extractor.ollama_available and self.llm_extractor.ollama_available else "📝"
                    console.print(f"    [dim]{llm_status} {record_dict.get('title', 'N/A')[:50]}... (Risk: {record_dict['risk_level']})[/dim]")
                
                except Exception as e:
                    console.print(f"    [yellow]⚠️  Fehler bei {url[:50]}...: {e}[/yellow]")
                    progress.update(task, advance=1)
                    continue
        
        return records
    
    def create_country_context_space(self, country_code: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Erstelle Kontextraum für ein Land"""
        console.print(f"\n[bold cyan]🧠 Erstelle Kontextraum für {country_code}...[/bold cyan]")
        
        country_info = self.countries.get(country_code, {})
        
        # Aggregiere Daten
        total_records = len(records)
        avg_risk_score = sum(r.get('risk_score', 0) for r in records) / total_records if records else 0
        
        risk_levels = {}
        for record in records:
            level = record.get('risk_level', 'UNKNOWN')
            risk_levels[level] = risk_levels.get(level, 0) + 1
        
        # Top Topics
        all_topics = []
        for record in records:
            all_topics.extend(record.get('topics', []))
        topic_counts = {}
        for topic in all_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # IPCC-Kontext
        ipcc_context = self.ipcc_engine.get_firecrawl_context({
            'region': country_info.get('name', ''),
            'title': f"Climate data for {country_info.get('name', '')}",
            'summary': f"Analysis of {total_records} records"
        })
        
        context_space = {
            'country_code': country_code,
            'country_name': country_info.get('name', ''),
            'total_records': total_records,
            'avg_risk_score': round(avg_risk_score, 3),
            'risk_distribution': risk_levels,
            'top_topics': [{'topic': t[0], 'count': t[1]} for t in top_topics],
            'ipcc_keywords': ipcc_context.get('keywords', [])[:10],
            'focus_areas': ipcc_context.get('focus_areas', []),
            'created_at': datetime.now().isoformat()
        }
        
        console.print(f"  [green]✅ Kontextraum erstellt: {total_records} Records, Avg Risk: {avg_risk_score:.2f}[/green]")
        return context_space
    
    def prepare_map_data(self, countries_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Bereite Daten für interaktive Risiko-Karte vor"""
        console.print(f"\n[bold cyan]🗺️  Bereite Karten-Daten vor...[/bold cyan]")
        
        features = []
        zones = []
        
        # Risiko-Farben
        risk_colors = {
            'CRITICAL': '#d32f2f',  # Rot
            'HIGH': '#f57c00',      # Orange
            'MEDIUM': '#fbc02d',    # Gelb
            'LOW': '#388e3c',       # Grün
            'MINIMAL': '#1976d2',   # Blau
        }
        
        for country_code, context in countries_data.items():
            # Erstelle GeoJSON Feature für jedes Land
            # TODO: Koordinaten aus Geocoding holen
            feature = {
                'type': 'Feature',
                'properties': {
                    'country_code': country_code,
                    'country_name': context.get('country_name', ''),
                    'risk_score': context.get('avg_risk_score', 0),
                    'risk_level': self._get_risk_level_from_score(context.get('avg_risk_score', 0)),
                    'total_records': context.get('total_records', 0),
                    'color': risk_colors.get(self._get_risk_level_from_score(context.get('avg_risk_score', 0)), '#999'),
                    'top_topics': [t['topic'] for t in context.get('top_topics', [])[:5]]
                },
                'geometry': {
                    'type': 'Point',
                    'coordinates': [0, 0]  # Wird durch Geocoding gefüllt
                }
            }
            features.append(feature)
            
            # Erstelle Risiko-Zone
            zone = {
                'country_code': country_code,
                'risk_level': feature['properties']['risk_level'],
                'risk_score': context.get('avg_risk_score', 0),
                'color': feature['properties']['color'],
                'opacity': min(context.get('avg_risk_score', 0) * 1.2, 0.8)
            }
            zones.append(zone)
        
        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }
        
        map_data = {
            'geojson': geojson,
            'zones': zones,
            'risk_colors': risk_colors,
            'metadata': {
                'total_countries': len(countries_data),
                'generated_at': datetime.now().isoformat()
            }
        }
        
        console.print(f"  [green]✅ Karten-Daten erstellt: {len(features)} Länder[/green]")
        return map_data
    
    def _get_risk_level_from_score(self, score: float) -> str:
        """Konvertiere Score zu Risk Level"""
        if score >= 0.8:
            return 'CRITICAL'
        elif score >= 0.6:
            return 'HIGH'
        elif score >= 0.4:
            return 'MEDIUM'
        elif score >= 0.2:
            return 'LOW'
        else:
            return 'MINIMAL'
    
    def _get_extraction_schema(self) -> Dict[str, Any]:
        """IPCC-Extraktionsschema"""
        return {
            "title": {"type": "string"},
            "summary": {"type": "string"},
            "publish_date": {"type": "string"},
            "location": {"type": "string"},
            "ipcc_risks": {"type": "array"},
            "temperature_data": {"type": "object"},
            "precipitation_data": {"type": "object"}
        }
    
    def _extract_domain(self, url: str) -> str:
        """Extrahiere Domain"""
        from urllib.parse import urlparse
        return urlparse(url).netloc
    
    def _extract_source_name(self, url: str, country_code: str) -> str:
        """Extrahiere Source-Name"""
        domain = self._extract_domain(url)
        country_name = self.countries.get(country_code, {}).get('name', '')
        
        if 'dwd.de' in domain:
            return 'DWD'
        elif 'umweltbundesamt.de' in domain:
            return 'Umweltbundesamt'
        elif 'gov.uk' in domain:
            return 'UK Government'
        elif 'epa.gov' in domain or 'noaa.gov' in domain:
            return 'US Government'
        elif 'ipcc' in domain.lower():
            return 'IPCC'
        else:
            return f'{country_name} Source'
    
    async def run_systematic_extraction(
        self,
        country_codes: List[str],
        urls_per_country: int = 50
    ) -> Dict[str, Any]:
        """Führe systematische Extraktion aus"""
        console.print(Panel.fit(
            "[bold green]🌍 Systematische Geospatial-Extraktion[/bold green]\n"
            f"[cyan]Länder: {len(country_codes)} | URLs pro Land: {urls_per_country}[/cyan]\n"
            f"[dim]Firecrawl + Ollama für intelligente Extraktion[/dim]",
            border_style="green"
        ))
        
        all_records = []
        countries_context = {}
        
        # Zeige aktuelle DB-Statistiken
        stats = self.db.get_statistics()
        initial_count = stats.get('total_records', 0)
        console.print(f"\n[bold blue]📊 Aktuelle Datenbank: {initial_count} Records[/bold blue]\n")
        
        # Für jedes Land
        for country_code in country_codes:
            console.print(f"\n{'='*60}")
            console.print(f"[bold yellow]🇺🇳 Land: {self.countries.get(country_code, {}).get('name', country_code)} ({country_code})[/bold yellow]")
            console.print(f"{'='*60}")
            
            # 1. Generiere URLs
            urls = self.generate_urls_systematically(country_code, urls_per_country)
            
            # 2. Extrahiere URLs
            records = await self.extract_urls_with_firecrawl_ollama(urls, country_code)
            
            # 3. Speichere Records
            if records:
                page_records = []
                for record_dict in records:
                    try:
                        page_record = PageRecord(**record_dict)
                        page_records.append(page_record)
                    except Exception as e:
                        continue
                
                db_result = self.db.insert_records_batch(page_records)
                console.print(f"\n  [green]💾 {db_result.get('new', 0)} neue Records gespeichert[/green]")
                
                all_records.extend(records)
                
                # 4. Erstelle Kontextraum
                context = self.create_country_context_space(country_code, records)
                countries_context[country_code] = context
        
        # 5. Bereite Karten-Daten vor
        map_data = self.prepare_map_data(countries_context)
        
        # Speichere Karten-Daten
        output_dir = Path("./data/frontend")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / "geospatial_map_data.json", 'w') as f:
            json.dump(map_data, f, indent=2, default=str)
        
        with open(output_dir / "countries_context.json", 'w') as f:
            json.dump(countries_context, f, indent=2, default=str)
        
        console.print(f"\n  [green]💾 Karten-Daten gespeichert: data/frontend/geospatial_map_data.json[/green]")
        
        # Finale Statistiken
        final_stats = self.db.get_statistics()
        final_count = final_stats.get('total_records', 0)
        
        console.print(f"\n[bold blue]📊 Finale Datenbank-Statistiken:[/bold blue]")
        console.print(f"  Gesamt Records: {final_count} (+{final_count - initial_count})")
        console.print(f"  Länder analysiert: {len(country_codes)}")
        console.print(f"  Kontexträume erstellt: {len(countries_context)}")
        
        # Kosten
        cost_summary = self.cost_tracker.get_summary()
        console.print(f"\n[bold yellow]💰 Kosten:[/bold yellow]")
        console.print(f"  Firecrawl Credits: {cost_summary['firecrawl_credits_used']:.1f}")
        console.print(f"  Verbleibend: {cost_summary['firecrawl_credits_remaining']:.1f}")
        
        return {
            'records_extracted': len(all_records),
            'countries_analyzed': len(country_codes),
            'context_spaces': countries_context,
            'map_data': map_data
        }


async def main():
    """Hauptfunktion"""
    extractor = SystematicGeospatialExtractor()
    
    # Länder für Analyse (kann erweitert werden)
    countries = ["DE", "FR", "IT", "ES", "GB"]  # Starte mit 5 Ländern
    
    results = await extractor.run_systematic_extraction(
        country_codes=countries,
        urls_per_country=50  # 50 URLs pro Land
    )
    
    console.print("\n[bold green]✅ Systematische Extraktion abgeschlossen![/bold green]")
    console.print("\n[bold blue]Nächste Schritte:[/bold blue]")
    console.print("  1. Geocoding: python geocode_existing_records.py")
    console.print("  2. Karte visualisieren: python web_app.py")
    console.print("  3. Risiko-Zonen prüfen: data/frontend/geospatial_map_data.json")


if __name__ == "__main__":
    asyncio.run(main())

