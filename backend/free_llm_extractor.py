#!/usr/bin/env python3
"""
Kostenloser LLM-Extraktor mit Ollama für bessere Datenextraktion
Falls Ollama nicht verfügbar, verwendet es einfache Regex/Pattern-Matching
"""
import json
import re
from typing import Dict, Any, Optional, List
import requests
from rich.console import Console

console = Console()


class FreeLLMExtractor:
    """Kostenloser LLM-Extraktor mit Ollama-Fallback"""
    
    def __init__(self, ollama_host: str = "http://localhost:11434", model: str = "llama2:7b"):
        self.ollama_host = ollama_host
        self.model = model
        self.ollama_available = self._check_ollama()
    
    def _check_ollama(self) -> bool:
        """Prüfe ob Ollama verfügbar ist"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def extract_with_llm(self, text: str, schema: Dict[str, Any], use_llm: bool = False) -> Dict[str, Any]:
        """
        Extrahiere Daten mit LLM (Ollama) oder Fallback
        
        Args:
            text: Text zum Extrahieren
            schema: Extraktionsschema
            use_llm: Wenn True, versuche LLM (langsamer). Wenn False, verwende Pattern-Matching (schneller)
        """
        # Standard: Pattern-Matching (schnell und zuverlässig)
        # LLM nur wenn explizit gewünscht UND verfügbar
        if use_llm and self.ollama_available:
            try:
                # Versuche LLM mit kurzem Timeout
                return self._extract_with_ollama_fast(text, schema)
            except:
                # Fallback zu Pattern-Matching bei Fehler
                return self._extract_with_patterns(text, schema)
        else:
            return self._extract_with_patterns(text, schema)
    
    def _extract_with_ollama_fast(self, text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Schnellere Ollama-Extraktion mit kürzerem Timeout"""
        try:
            prompt = self._create_extraction_prompt(text[:1000], schema)  # Noch kürzer für Geschwindigkeit
            
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "num_predict": 200  # Begrenze Antwort-Länge für Geschwindigkeit
                    }
                },
                timeout=15  # Kürzerer Timeout für schnellere Fehlerbehandlung
            )
            
            if response.status_code == 200:
                result = response.json()
                extracted_text = result.get('response', '')
                try:
                    return json.loads(extracted_text)
                except:
                    return self._extract_with_patterns(text, schema)
            else:
                return self._extract_with_patterns(text, schema)
        except:
            return self._extract_with_patterns(text, schema)
    
    def _extract_with_ollama(self, text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extrahiere mit Ollama LLM"""
        try:
            # Erstelle Prompt für strukturierte Extraktion
            prompt = self._create_extraction_prompt(text, schema)
            
            # Rufe Ollama API auf (längerer Timeout für größere Modelle)
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=120  # 2 Minuten Timeout für größere Texte
            )
            
            if response.status_code == 200:
                result = response.json()
                extracted_text = result.get('response', '')
                
                # Parse JSON aus Response
                try:
                    extracted_data = json.loads(extracted_text)
                    return extracted_data
                except:
                    # Fallback zu Pattern-Matching wenn JSON-Parsing fehlschlägt
                    return self._extract_with_patterns(text, schema)
            else:
                console.print(f"  [yellow]⚠️  Ollama API Fehler: {response.status_code}[/yellow]")
                return self._extract_with_patterns(text, schema)
        
        except Exception as e:
            console.print(f"  [yellow]⚠️  Ollama Fehler: {e}[/yellow]")
            return self._extract_with_patterns(text, schema)
    
    def _create_extraction_prompt(self, text: str, schema: Dict[str, Any]) -> str:
        """Erstelle Prompt für LLM-Extraktion"""
        schema_description = json.dumps(schema, indent=2)
        
        # Kürze Text für schnellere Verarbeitung (Ollama ist langsamer)
        text_sample = text[:1500]  # Reduziert auf 1500 Zeichen für schnellere Antworten
        
        prompt = f"""Extrahiere strukturierte Daten aus dem folgenden Text im JSON-Format.

Schema:
{schema_description}

Text:
{text_sample}

Extrahiere die folgenden Felder:
- title: Titel des Artikels
- summary: Zusammenfassung (max 200 Wörter)
- publish_date: Veröffentlichungsdatum (falls vorhanden)
- location: Ort/Region (z.B. "Germany", "Deutschland", Stadtname)
- temperature_data: Temperatur-Daten falls vorhanden
- precipitation_data: Niederschlags-Daten falls vorhanden
- climate_event: Art des Klimaereignisses (flood, drought, heat wave, etc.)
- ipcc_risks: Liste von IPCC-identifizierten Risiken
- climate_indicators: Liste von Klima-Indikatoren

Antworte NUR mit einem gültigen JSON-Objekt, keine zusätzlichen Erklärungen:
"""
        return prompt
    
    def _extract_with_patterns(self, text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback: Extrahiere mit Pattern-Matching"""
        extracted = {}
        
        # Titel extrahieren (erste Zeile oder vor erstem Punkt)
        title_match = re.search(r'^([^\n\.]{10,200})', text.strip())
        if title_match:
            extracted['title'] = title_match.group(1).strip()
        
        # Zusammenfassung (erste 3 Sätze)
        sentences = re.split(r'[.!?]+\s+', text)
        if len(sentences) >= 3:
            extracted['summary'] = '. '.join(sentences[:3]).strip()[:500]
        else:
            extracted['summary'] = text[:500]
        
        # Datum extrahieren
        date_patterns = [
            r'(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})',
            r'(\d{4}[./-]\d{1,2}[./-]\d{1,2})',
            r'(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+\d{1,2},?\s+\d{4}',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                extracted['publish_date'] = match.group(1)
                break
        
        # Location/Region extrahieren
        location_keywords = ['Germany', 'Deutschland', 'Berlin', 'München', 'Hamburg', 'Köln', 
                           'Rhein', 'Elbe', 'Nordsee', 'Ostsee', 'Bavaria', 'Bayern']
        for keyword in location_keywords:
            if keyword.lower() in text.lower():
                extracted['location'] = keyword
                break
        
        # Temperatur-Daten
        temp_patterns = [
            r'(\d+\.?\d*)\s*°[CF]',
            r'(\d+\.?\d*)\s*Grad',
            r'Temperatur[:\s]+(\d+\.?\d*)',
        ]
        for pattern in temp_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    temp_value = float(match.group(1))
                    extracted['temperature_data'] = {'value': temp_value}
                    break
                except:
                    pass
        
        # Niederschlags-Daten
        precip_patterns = [
            r'(\d+\.?\d*)\s*mm',
            r'(\d+\.?\d*)\s*Liter',
            r'Niederschlag[:\s]+(\d+\.?\d*)',
        ]
        for pattern in precip_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    precip_value = float(match.group(1))
                    extracted['precipitation_data'] = {'value': precip_value}
                    break
                except:
                    pass
        
        # Klima-Ereignisse
        climate_events = []
        event_keywords = {
            'flood': ['flood', 'überschwemmung', 'hochwasser'],
            'drought': ['drought', 'dürre', 'trockenheit'],
            'heat wave': ['heat wave', 'hitzewelle', 'hitze'],
            'storm': ['storm', 'sturm', 'unwetter'],
            'snow': ['snow', 'schnee', 'schneefall']
        }
        for event_type, keywords in event_keywords.items():
            if any(kw.lower() in text.lower() for kw in keywords):
                climate_events.append(event_type)
        
        if climate_events:
            extracted['climate_event'] = climate_events[0]
            extracted['climate_indicators'] = climate_events
        
        # IPCC-Risiken
        ipcc_risks = []
        risk_keywords = {
            'Heavy precipitation': ['heavy rain', 'starker regen', 'niederschlag'],
            'Extreme heat events': ['extreme heat', 'extreme hitze', 'hitzewelle'],
            'Drought': ['drought', 'dürre'],
            'Flooding': ['flood', 'überschwemmung'],
            'Biodiversity loss': ['biodiversity', 'artenvielfalt']
        }
        for risk, keywords in risk_keywords.items():
            if any(kw.lower() in text.lower() for kw in keywords):
                ipcc_risks.append(risk)
        
        extracted['ipcc_risks'] = ipcc_risks[:5]  # Max 5
        
        return extracted

