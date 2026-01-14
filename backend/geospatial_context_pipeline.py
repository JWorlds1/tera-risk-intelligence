#!/usr/bin/env python3
"""
Geospatial Context Pipeline - Erstellt Kontexträume für jedes Land
Nutzt Firecrawl + Ollama für Datenextraktion und Analyse
"""
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import aiohttp
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
import time

from config import Config
from database import DatabaseManager
from firecrawl_enrichment import FirecrawlEnricher, CostTracker
from free_llm_extractor import FreeLLMExtractor
from geocoding import GeocodingService

console = Console()


@dataclass
class CountryContextSpace:
    """Kontextraum für ein Land"""
    country_code: str
    country_name: str
    latitude: float
    longitude: float
    risk_score: float
    risk_level: str
    climate_indicators: List[str]
    conflict_indicators: List[str]
    future_risks: List[Dict[str, Any]]
    context_summary: str
    data_sources: List[str]
    last_updated: datetime
    geojson: Optional[Dict] = None
    bbox: Optional[Dict] = None


class GeospatialContextPipeline:
    """Pipeline für Geospatial-Analyse mit Kontextraum-Erstellung"""
    
    def __init__(self):
        self.config = Config()
        self.db = DatabaseManager()
        self.geocoding = GeocodingService()
        self.cost_tracker = CostTracker()
        
        # Firecrawl Integration
        if self.config.FIRECRAWL_API_KEY:
            self.firecrawl = FirecrawlEnricher(
                api_key=self.config.FIRECRAWL_API_KEY,
                cost_tracker=self.cost_tracker
            )
        else:
            self.firecrawl = None
            console.print("[yellow]⚠️  Firecrawl API Key nicht gefunden[/yellow]")
        
        # Ollama Integration
        self.ollama_extractor = FreeLLMExtractor(
            ollama_host=self.config.OLLAMA_HOST,
            model=self.config.OLLAMA_MODEL
        )
        
        # Länder-Liste (ISO 3166-1 alpha-2)
        self.countries = self._load_country_list()
    
    def _load_country_list(self) -> List[Dict[str, str]]:
        """Lade Liste aller Länder"""
        # Top 50 kritische Länder für Klima-Konflikte
        critical_countries = [
            {"code": "IN", "name": "India"},
            {"code": "BD", "name": "Bangladesh"},
            {"code": "PK", "name": "Pakistan"},
            {"code": "PH", "name": "Philippines"},
            {"code": "VN", "name": "Vietnam"},
            {"code": "TH", "name": "Thailand"},
            {"code": "MM", "name": "Myanmar"},
            {"code": "ID", "name": "Indonesia"},
            {"code": "KE", "name": "Kenya"},
            {"code": "ET", "name": "Ethiopia"},
            {"code": "SO", "name": "Somalia"},
            {"code": "UG", "name": "Uganda"},
            {"code": "TZ", "name": "Tanzania"},
            {"code": "SD", "name": "Sudan"},
            {"code": "SS", "name": "South Sudan"},
            {"code": "CF", "name": "Central African Republic"},
            {"code": "TD", "name": "Chad"},
            {"code": "ML", "name": "Mali"},
            {"code": "NE", "name": "Niger"},
            {"code": "BF", "name": "Burkina Faso"},
            {"code": "NG", "name": "Nigeria"},
            {"code": "CM", "name": "Cameroon"},
            {"code": "HT", "name": "Haiti"},
            {"code": "DM", "name": "Dominica"},
            {"code": "HN", "name": "Honduras"},
            {"code": "GT", "name": "Guatemala"},
            {"code": "NI", "name": "Nicaragua"},
            {"code": "SY", "name": "Syria"},
            {"code": "IQ", "name": "Iraq"},
            {"code": "YE", "name": "Yemen"},
            {"code": "AF", "name": "Afghanistan"},
            {"code": "CN", "name": "China"},
            {"code": "BR", "name": "Brazil"},
            {"code": "MX", "name": "Mexico"},
            {"code": "CO", "name": "Colombia"},
            {"code": "PE", "name": "Peru"},
            {"code": "VE", "name": "Venezuela"},
            {"code": "EG", "name": "Egypt"},
            {"code": "LY", "name": "Libya"},
            {"code": "DZ", "name": "Algeria"},
            {"code": "MA", "name": "Morocco"},
            {"code": "TN", "name": "Tunisia"},
            {"code": "GH", "name": "Ghana"},
            {"code": "CI", "name": "Ivory Coast"},
            {"code": "SN", "name": "Senegal"},
            {"code": "MR", "name": "Mauritania"},
            {"code": "ZW", "name": "Zimbabwe"},
            {"code": "ZM", "name": "Zambia"},
            {"code": "MW", "name": "Malawi"},
            {"code": "MZ", "name": "Mozambique"},
        ]
        return critical_countries
    
    async def extract_country_data(
        self,
        country_code: str,
        country_name: str
    ) -> Dict[str, Any]:
        """Extrahiere Daten für ein Land mit Firecrawl + Ollama"""
        console.print(f"\n[bold cyan]🌍 Analysiere {country_name} ({country_code})[/bold cyan]")
        
        # 1. Hole bestehende Records aus Datenbank
        existing_records = self._get_country_records(country_code)
        
        # 2. Firecrawl Search für zusätzliche Daten
        firecrawl_data = []
        if self.firecrawl:
            try:
                keywords = [
                    f"{country_name} climate",
                    f"{country_name} conflict",
                    f"{country_name} drought",
                    f"{country_name} flood",
                    f"{country_name} risk"
                ]
                
                console.print(f"  [green]📡 Suche mit Firecrawl...[/green]")
                results, credits = self.firecrawl.enrich_with_search(
                    keywords=keywords[:3],  # Limit für Kosten
                    region=country_name,
                    limit=10,
                    scrape_content=True
                )
                firecrawl_data = results
                console.print(f"  ✅ {len(results)} Ergebnisse gefunden ({credits:.1f} Credits)")
            except Exception as e:
                console.print(f"  [yellow]⚠️  Firecrawl Fehler: {e}[/yellow]")
        
        # 3. Kombiniere alle Datenquellen
        all_text_data = []
        
        # Aus bestehenden Records
        for record in existing_records:
            if record.get('full_text'):
                all_text_data.append(record['full_text'][:2000])  # Limit für Performance
        
        # Aus Firecrawl
        for result in firecrawl_data:
            if isinstance(result, dict):
                content = result.get('markdown') or result.get('content', '')
                if content:
                    all_text_data.append(content[:2000])
        
        # 4. Ollama-Analyse für Kontextraum
        context_space = await self._analyze_with_ollama(
            country_code=country_code,
            country_name=country_name,
            text_data=all_text_data
        )
        
        return {
            'country_code': country_code,
            'country_name': country_name,
            'existing_records': len(existing_records),
            'firecrawl_results': len(firecrawl_data),
            'context_space': context_space
        }
    
    async def _analyze_with_ollama(
        self,
        country_code: str,
        country_name: str,
        text_data: List[str]
    ) -> Dict[str, Any]:
        """Analysiere Daten mit Ollama für Kontextraum-Erstellung"""
        if not text_data:
            return self._create_empty_context(country_code, country_name)
        
        # Kombiniere Text-Daten
        combined_text = "\n\n---\n\n".join(text_data[:5])  # Max 5 Quellen
        combined_text = combined_text[:5000]  # Limit für Ollama
        
        # Erstelle Analyse-Prompt
        prompt = self._create_analysis_prompt(country_name, combined_text)
        
        # Rufe Ollama auf mit Retry-Logik
        max_retries = 3
        retry_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                console.print(f"  [green]🤖 Analysiere mit Ollama ({self.config.OLLAMA_MODEL})...[/green]")
                
                timeout = aiohttp.ClientTimeout(total=120)  # 2 Minuten Timeout
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(
                        f"{self.config.OLLAMA_HOST}/api/generate",
                        json={
                            "model": self.config.OLLAMA_MODEL,
                            "prompt": prompt,
                            "stream": False,
                            "format": "json",
                            "options": {
                                "num_predict": 500,
                                "temperature": 0.7
                            }
                        }
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            extracted_text = result.get('response', '')
                            
                            if not extracted_text:
                                console.print(f"  [yellow]⚠️  Leere Antwort von Ollama[/yellow]")
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(retry_delay)
                                    continue
                                return self._create_empty_context(country_code, country_name)
                            
                            try:
                                analysis = json.loads(extracted_text)
                                # Validiere Analysis
                                analysis = self._validate_analysis(analysis, country_code, country_name)
                                console.print(f"  ✅ Analyse abgeschlossen")
                                return analysis
                            except json.JSONDecodeError:
                                # Fallback: Parse manuell
                                parsed = self._parse_ollama_response(extracted_text, country_code, country_name)
                                if parsed and parsed.get('risk_score', 0) > 0:
                                    return parsed
                                # Retry bei Parsing-Fehler
                                if attempt < max_retries - 1:
                                    console.print(f"  [yellow]⚠️  JSON-Parsing Fehler, Retry {attempt + 1}/{max_retries}[/yellow]")
                                    await asyncio.sleep(retry_delay)
                                    continue
                                return self._create_empty_context(country_code, country_name)
                        else:
                            error_text = await response.text()
                            console.print(f"  [yellow]⚠️  Ollama HTTP {response.status}: {error_text[:100]}[/yellow]")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_delay)
                                continue
                            return self._create_empty_context(country_code, country_name)
            
            except asyncio.TimeoutError:
                console.print(f"  [yellow]⚠️  Ollama Timeout (Versuch {attempt + 1}/{max_retries})[/yellow]")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                return self._create_empty_context(country_code, country_name)
            
            except aiohttp.ClientError as e:
                console.print(f"  [yellow]⚠️  Ollama Verbindungsfehler: {e}[/yellow]")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                return self._create_empty_context(country_code, country_name)
            
            except Exception as e:
                console.print(f"  [yellow]⚠️  Ollama Fehler: {e}[/yellow]")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                return self._create_empty_context(country_code, country_name)
        
        return self._create_empty_context(country_code, country_name)
    
    def _create_analysis_prompt(self, country_name: str, text: str) -> str:
        """Erstelle Prompt für Ollama-Analyse"""
        return f"""Analysiere die folgenden Daten für {country_name} und erstelle einen strukturierten Kontextraum.

Daten:
{text[:4000]}

Erstelle ein JSON-Objekt mit folgenden Feldern:
{{
  "risk_score": 0.0-1.0,  // Gesamt-Risiko-Score
  "risk_level": "CRITICAL|HIGH|MEDIUM|LOW|MINIMAL",
  "climate_indicators": ["drought", "flood", "heat_wave", ...],  // Liste von Klima-Indikatoren
  "conflict_indicators": ["war", "displacement", "resource_conflict", ...],  // Liste von Konflikt-Indikatoren
  "future_risks": [
    {{
      "type": "drought|flood|conflict|migration",
      "probability": 0.0-1.0,
      "timeframe": "short_term|medium_term|long_term",
      "severity": "low|medium|high|critical",
      "description": "Beschreibung des Risikos"
    }}
  ],
  "context_summary": "Zusammenfassung des Kontextraums (max 300 Wörter)",
  "data_sources": ["NASA", "UN", "World Bank", ...]  // Liste der Datenquellen
}}

Antworte NUR mit dem JSON-Objekt, keine zusätzlichen Erklärungen:
"""
    
    def _parse_ollama_response(
        self,
        response_text: str,
        country_code: str,
        country_name: str
    ) -> Dict[str, Any]:
        """Parse Ollama Response manuell falls JSON-Parsing fehlschlägt"""
        # Versuche JSON zu extrahieren
        json_match = None
        try:
            # Suche nach JSON-Objekt
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response_text[start:end]
                return json.loads(json_str)
        except:
            pass
        
        # Fallback: Erstelle aus Text
        return self._create_empty_context(country_code, country_name)
    
    def _validate_analysis(self, analysis: Dict[str, Any], country_code: str, country_name: str) -> Dict[str, Any]:
        """Validiere und normalisiere Analysis-Daten"""
        # Stelle sicher, dass alle erforderlichen Felder vorhanden sind
        validated = {
            "risk_score": float(analysis.get('risk_score', 0.0)),
            "risk_level": str(analysis.get('risk_level', 'MINIMAL')).upper(),
            "climate_indicators": list(analysis.get('climate_indicators', [])) if isinstance(analysis.get('climate_indicators'), list) else [],
            "conflict_indicators": list(analysis.get('conflict_indicators', [])) if isinstance(analysis.get('conflict_indicators'), list) else [],
            "future_risks": list(analysis.get('future_risks', [])) if isinstance(analysis.get('future_risks'), list) else [],
            "context_summary": str(analysis.get('context_summary', f'Keine Zusammenfassung verfügbar für {country_name}'))[:1000],  # Limit Länge
            "data_sources": list(analysis.get('data_sources', [])) if isinstance(analysis.get('data_sources'), list) else []
        }
        
        # Validiere risk_score
        validated['risk_score'] = max(0.0, min(1.0, validated['risk_score']))
        
        # Validiere risk_level
        valid_levels = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'MINIMAL']
        if validated['risk_level'] not in valid_levels:
            # Berechne aus risk_score
            if validated['risk_score'] >= 0.8:
                validated['risk_level'] = 'CRITICAL'
            elif validated['risk_score'] >= 0.6:
                validated['risk_level'] = 'HIGH'
            elif validated['risk_score'] >= 0.4:
                validated['risk_level'] = 'MEDIUM'
            elif validated['risk_score'] >= 0.2:
                validated['risk_level'] = 'LOW'
            else:
                validated['risk_level'] = 'MINIMAL'
        
        return validated
    
    def _create_empty_context(
        self,
        country_code: str,
        country_name: str
    ) -> Dict[str, Any]:
        """Erstelle leeren Kontextraum"""
        return {
            "risk_score": 0.0,
            "risk_level": "MINIMAL",
            "climate_indicators": [],
            "conflict_indicators": [],
            "future_risks": [],
            "context_summary": f"Keine Daten verfügbar für {country_name}",
            "data_sources": []
        }
    
    def _get_country_records(self, country_code: str) -> List[Dict]:
        """Hole alle Records für ein Land"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM records
                WHERE primary_country_code = ?
                ORDER BY fetched_at DESC
                LIMIT 100
            """, (country_code,))
            return [dict(row) for row in cursor.fetchall()]
    
    async def process_all_countries(self) -> List[CountryContextSpace]:
        """Verarbeite alle Länder und erstelle Kontexträume"""
        console.print(f"\n[bold green]🚀 Starte Geospatial-Analyse für {len(self.countries)} Länder[/bold green]")
        
        context_spaces = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task(
                "[cyan]Verarbeite Länder...",
                total=len(self.countries)
            )
            
            for country in self.countries:
                try:
                    # Extrahiere Daten
                    result = await self.extract_country_data(
                        country_code=country['code'],
                        country_name=country['name']
                    )
                    
                    # Hole Koordinaten (async-safe)
                    try:
                        # Nutze async geocode direkt
                        geo_result = await self.geocoding.geocode(country['name'], "country")
                        latitude = geo_result.latitude if geo_result and geo_result.latitude else 0.0
                        longitude = geo_result.longitude if geo_result and geo_result.longitude else 0.0
                    except Exception as e:
                        console.print(f"  [yellow]⚠️  Geocoding Fehler: {e}[/yellow]")
                        # Fallback: Versuche synchron
                        try:
                            geo_result = self.geocoding.geocode_country(country['code'])
                            latitude = geo_result.latitude if geo_result and geo_result.latitude else 0.0
                            longitude = geo_result.longitude if geo_result and geo_result.longitude else 0.0
                        except:
                            latitude = 0.0
                            longitude = 0.0
                    
                    # Erstelle Kontextraum
                    context_data = result['context_space']
                    
                    # Validiere context_data
                    if not isinstance(context_data, dict):
                        context_data = self._create_empty_context(country['code'], country['name'])
                    
                    context_space = CountryContextSpace(
                        country_code=country['code'],
                        country_name=country['name'],
                        latitude=latitude,
                        longitude=longitude,
                        risk_score=float(context_data.get('risk_score', 0.0)),
                        risk_level=str(context_data.get('risk_level', 'MINIMAL')).upper(),
                        climate_indicators=list(context_data.get('climate_indicators', [])) if isinstance(context_data.get('climate_indicators'), list) else [],
                        conflict_indicators=list(context_data.get('conflict_indicators', [])) if isinstance(context_data.get('conflict_indicators'), list) else [],
                        future_risks=list(context_data.get('future_risks', [])) if isinstance(context_data.get('future_risks'), list) else [],
                        context_summary=str(context_data.get('context_summary', ''))[:1000],  # Limit Länge
                        data_sources=list(context_data.get('data_sources', [])) if isinstance(context_data.get('data_sources'), list) else [],
                        last_updated=datetime.now()
                    )
                    
                    # Speichere in Datenbank
                    self._save_context_space(context_space)
                    
                    context_spaces.append(context_space)
                    
                except Exception as e:
                    console.print(f"  [red]❌ Fehler bei {country['name']}: {e}[/red]")
                    import traceback
                    console.print(f"  [dim]{traceback.format_exc()}[/dim]")
                    # Erstelle leeren Kontextraum bei Fehler
                    try:
                        empty_context = self._create_empty_context(country['code'], country['name'])
                        geo_result = self.geocoding.geocode_country(country['code'])
                        context_space = CountryContextSpace(
                            country_code=country['code'],
                            country_name=country['name'],
                            latitude=geo_result.latitude if geo_result else 0.0,
                            longitude=geo_result.longitude if geo_result else 0.0,
                            risk_score=empty_context['risk_score'],
                            risk_level=empty_context['risk_level'],
                            climate_indicators=empty_context['climate_indicators'],
                            conflict_indicators=empty_context['conflict_indicators'],
                            future_risks=empty_context['future_risks'],
                            context_summary=empty_context['context_summary'],
                            data_sources=empty_context['data_sources'],
                            last_updated=datetime.now()
                        )
                        self._save_context_space(context_space)
                        context_spaces.append(context_space)
                    except Exception as e2:
                        console.print(f"  [red]❌ Auch Fallback fehlgeschlagen: {e2}[/red]")
                
                progress.update(task, advance=1)
                
                # Rate Limiting zwischen Ländern
                await asyncio.sleep(0.5)
        
        # Kosten-Zusammenfassung
        cost_summary = self.cost_tracker.get_summary()
        console.print(f"\n[bold green]✅ Analyse abgeschlossen[/bold green]")
        console.print(f"  Firecrawl Credits: {cost_summary['firecrawl_credits_used']:.1f}")
        console.print(f"  Kontexträume erstellt: {len(context_spaces)}")
        
        return context_spaces
    
    def _save_context_space(self, context_space: CountryContextSpace):
        """Speichere Kontextraum in Datenbank"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Validiere Daten vor Speicherung
                if not context_space.country_code or not context_space.country_name:
                    console.print(f"  [yellow]⚠️  Ungültige Daten für {context_space.country_code}, überspringe Speicherung[/yellow]")
                    return
                
                # Erstelle oder aktualisiere Kontextraum
                cursor.execute("""
                    INSERT OR REPLACE INTO country_context_spaces (
                        country_code,
                        country_name,
                        latitude,
                        longitude,
                        risk_score,
                        risk_level,
                        climate_indicators,
                        conflict_indicators,
                        future_risks,
                        context_summary,
                        data_sources,
                        geojson,
                        bbox,
                        last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(context_space.country_code),
                    str(context_space.country_name),
                    float(context_space.latitude) if context_space.latitude else 0.0,
                    float(context_space.longitude) if context_space.longitude else 0.0,
                    float(context_space.risk_score),
                    str(context_space.risk_level),
                    json.dumps(context_space.climate_indicators) if context_space.climate_indicators else '[]',
                    json.dumps(context_space.conflict_indicators) if context_space.conflict_indicators else '[]',
                    json.dumps(context_space.future_risks) if context_space.future_risks else '[]',
                    str(context_space.context_summary)[:1000],  # Limit Länge
                    json.dumps(context_space.data_sources) if context_space.data_sources else '[]',
                    json.dumps(context_space.geojson) if context_space.geojson else None,
                    json.dumps(context_space.bbox) if context_space.bbox else None,
                    context_space.last_updated.isoformat() if isinstance(context_space.last_updated, datetime) else datetime.now().isoformat()
                ))
                
                conn.commit()
                console.print(f"  [dim]✅ {context_space.country_name} gespeichert[/dim]")
        except Exception as e:
            console.print(f"  [red]❌ Fehler beim Speichern von {context_space.country_name}: {e}[/red]")
            import traceback
            console.print(f"  [dim]{traceback.format_exc()}[/dim]")


async def main():
    """Hauptfunktion"""
    pipeline = GeospatialContextPipeline()
    context_spaces = await pipeline.process_all_countries()
    
    console.print(f"\n[bold green]✅ {len(context_spaces)} Kontexträume erstellt und gespeichert[/bold green]")
    
    return context_spaces


if __name__ == "__main__":
    asyncio.run(main())

