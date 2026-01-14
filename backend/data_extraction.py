#!/usr/bin/env python3
"""
Data Extraction Module - Extrahiert strukturierte numerische Daten aus Text
"""
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import json


@dataclass
class ExtractedNumbers:
    """Strukturierte numerische Daten aus Text extrahiert"""
    # Klima-Daten
    temperatures: List[float]  # Temperaturen in Celsius
    precipitation: List[float]  # Niederschlag in mm
    population_numbers: List[int]  # Bevölkerungszahlen
    financial_amounts: List[float]  # Finanzbeträge (USD)
    percentages: List[float]  # Prozentsätze
    dates: List[str]  # Datumsangaben
    
    # Metriken
    affected_people: Optional[int] = None
    funding_amount: Optional[float] = None
    risk_score: Optional[float] = None
    
    # Kontextuelle Informationen
    units: Dict[str, str] = None  # Einheiten für die Zahlen
    locations: List[str] = None  # Erwähnte Orte
    
    def __post_init__(self):
        if self.units is None:
            self.units = {}
        if self.locations is None:
            self.locations = []


class NumberExtractor:
    """Extrahiert numerische Daten aus Text"""
    
    def __init__(self):
        # Patterns für verschiedene Datentypen
        self.temperature_patterns = [
            r'(-?\d+(?:\.\d+)?)\s*°?\s*[CcFf]',  # "25°C", "77F"
            r'(-?\d+(?:\.\d+)?)\s*(?:degrees?\s*)?(?:celsius|fahrenheit|centigrade)',  # "25 degrees celsius"
            r'temperature[:\s]+(-?\d+(?:\.\d+)?)',  # "temperature: 25"
        ]
        
        self.precipitation_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:mm|millimeters?|inches?|in)',  # "500mm", "20 inches"
            r'precipitation[:\s]+(\d+(?:\.\d+)?)',  # "precipitation: 500"
            r'rainfall[:\s]+(\d+(?:\.\d+)?)',  # "rainfall: 500"
        ]
        
        self.population_patterns = [
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:people|individuals|persons|population|residents|inhabitants)',  # "1,000,000 people"
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:million|billion|thousand)\s*(?:people|individuals|persons)?',  # "1 million people"
            r'population[:\s]+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',  # "population: 1000000"
        ]
        
        self.financial_patterns = [
            r'\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:million|billion|thousand|trillion)?\s*(?:USD|dollars?)?',  # "$1.5 billion"
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:million|billion|thousand|trillion)\s*(?:USD|dollars?|US\$)',  # "1.5 billion USD"
            r'funding[:\s]+\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',  # "funding: $500000"
        ]
        
        self.percentage_patterns = [
            r'(\d+(?:\.\d+)?)\s*%',  # "25%"
            r'(\d+(?:\.\d+)?)\s*percent',  # "25 percent"
            r'(\d+(?:\.\d+)?)\s*per\s*cent',  # "25 per cent"
        ]
        
        self.date_patterns = [
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',  # "01/15/2025"
            r'\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b',  # "2025-01-15"
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',  # "January 15, 2025"
        ]
    
    def extract_all(self, text: str) -> ExtractedNumbers:
        """Extrahiere alle numerischen Daten aus Text"""
        if not text:
            return ExtractedNumbers(
                temperatures=[],
                precipitation=[],
                population_numbers=[],
                financial_amounts=[],
                percentages=[],
                dates=[]
            )
        
        text_lower = text.lower()
        
        # Extrahiere Temperaturen
        temperatures = self._extract_temperatures(text)
        
        # Extrahiere Niederschlag
        precipitation = self._extract_precipitation(text)
        
        # Extrahiere Bevölkerungszahlen
        population_numbers = self._extract_population(text)
        
        # Extrahiere Finanzbeträge
        financial_amounts = self._extract_financial(text)
        
        # Extrahiere Prozentsätze
        percentages = self._extract_percentages(text)
        
        # Extrahiere Datumsangaben
        dates = self._extract_dates(text)
        
        # Extrahiere spezifische Metriken
        affected_people = self._extract_affected_people(text)
        funding_amount = self._extract_funding_amount(text)
        
        # Extrahiere Orte
        locations = self._extract_locations(text)
        
        return ExtractedNumbers(
            temperatures=temperatures,
            precipitation=precipitation,
            population_numbers=population_numbers,
            financial_amounts=financial_amounts,
            percentages=percentages,
            dates=dates,
            affected_people=affected_people,
            funding_amount=funding_amount,
            locations=locations
        )
    
    def _extract_temperatures(self, text: str) -> List[float]:
        """Extrahiere Temperaturen"""
        temperatures = []
        for pattern in self.temperature_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    temp = float(match)
                    # Konvertiere Fahrenheit zu Celsius wenn nötig
                    if 'f' in text.lower() and temp > 50:  # Heuristik: F > 50
                        temp = (temp - 32) * 5/9
                    temperatures.append(round(temp, 2))
                except ValueError:
                    continue
        return list(set(temperatures))  # Entferne Duplikate
    
    def _extract_precipitation(self, text: str) -> List[float]:
        """Extrahiere Niederschlagsmengen"""
        precipitation = []
        for pattern in self.precipitation_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    value = float(match.replace(',', ''))
                    # Konvertiere inches zu mm wenn nötig
                    if 'inch' in text.lower():
                        value = value * 25.4
                    precipitation.append(round(value, 2))
                except ValueError:
                    continue
        return list(set(precipitation))
    
    def _extract_population(self, text: str) -> List[int]:
        """Extrahiere Bevölkerungszahlen"""
        population = []
        for pattern in self.population_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Handle Millionen, Milliarden, etc.
                    num_str = match.replace(',', '')
                    multiplier = 1
                    
                    if 'million' in text.lower():
                        multiplier = 1_000_000
                    elif 'billion' in text.lower():
                        multiplier = 1_000_000_000
                    elif 'thousand' in text.lower():
                        multiplier = 1_000
                    
                    value = int(float(num_str) * multiplier)
                    population.append(value)
                except ValueError:
                    continue
        return list(set(population))
    
    def _extract_financial(self, text: str) -> List[float]:
        """Extrahiere Finanzbeträge"""
        amounts = []
        for pattern in self.financial_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    num_str = match.replace(',', '')
                    multiplier = 1
                    
                    # Handle Millionen, Milliarden, etc.
                    if 'billion' in text.lower():
                        multiplier = 1_000_000_000
                    elif 'million' in text.lower():
                        multiplier = 1_000_000
                    elif 'thousand' in text.lower():
                        multiplier = 1_000
                    elif 'trillion' in text.lower():
                        multiplier = 1_000_000_000_000
                    
                    value = float(num_str) * multiplier
                    amounts.append(round(value, 2))
                except ValueError:
                    continue
        return list(set(amounts))
    
    def _extract_percentages(self, text: str) -> List[float]:
        """Extrahiere Prozentsätze"""
        percentages = []
        for pattern in self.percentage_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    value = float(match)
                    if 0 <= value <= 100:  # Validiere Bereich
                        percentages.append(round(value, 2))
                except ValueError:
                    continue
        return list(set(percentages))
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extrahiere Datumsangaben"""
        dates = []
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        return list(set(dates))
    
    def _extract_affected_people(self, text: str) -> Optional[int]:
        """Extrahiere Anzahl betroffener Personen"""
        patterns = [
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:people|individuals|persons)\s*(?:affected|displaced|in\s+need)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:million|billion|thousand)\s*(?:people|individuals|persons)\s*(?:affected|displaced|in\s+need)?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    num_str = match.group(1).replace(',', '')
                    multiplier = 1
                    if 'million' in text.lower():
                        multiplier = 1_000_000
                    elif 'billion' in text.lower():
                        multiplier = 1_000_000_000
                    elif 'thousand' in text.lower():
                        multiplier = 1_000
                    return int(float(num_str) * multiplier)
                except ValueError:
                    continue
        return None
    
    def _extract_funding_amount(self, text: str) -> Optional[float]:
        """Extrahiere Finanzierungsbetrag"""
        patterns = [
            r'funding[:\s]+\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:million|billion|thousand)\s*(?:USD|dollars?)\s*(?:in\s+funding|funding)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    num_str = match.group(1).replace(',', '')
                    multiplier = 1
                    if 'billion' in text.lower():
                        multiplier = 1_000_000_000
                    elif 'million' in text.lower():
                        multiplier = 1_000_000
                    elif 'thousand' in text.lower():
                        multiplier = 1_000
                    return round(float(num_str) * multiplier, 2)
                except ValueError:
                    continue
        return None
    
    def _extract_locations(self, text: str) -> List[str]:
        """Extrahiere erwähnte Orte (einfache Heuristik)"""
        # Pattern für Länder/Regionen (kann erweitert werden)
        location_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:region|country|province|state|area)',
            r'in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        locations = []
        for pattern in location_patterns:
            matches = re.findall(pattern, text)
            locations.extend(matches)
        
        # Entferne häufige False Positives
        false_positives = {'The', 'This', 'That', 'These', 'Those', 'A', 'An'}
        locations = [loc for loc in locations if loc not in false_positives]
        
        return list(set(locations))


# Beispiel-Nutzung
if __name__ == "__main__":
    extractor = NumberExtractor()
    
    test_text = """
    The temperature in East Africa reached 35°C last week, with precipitation 
    of only 50mm. Over 2 million people are affected by the drought. 
    The UN has allocated $500 million USD in funding to address the crisis.
    The situation has worsened by 25% compared to last year.
    """
    
    extracted = extractor.extract_all(test_text)
    print(json.dumps(asdict(extracted), indent=2, default=str))

