"""
TERA V2: Climate Index Service
===============================

Lädt Echtzeit-Klimaindizes von NOAA und anderen Quellen.
Diese Indizes definieren den aktuellen globalen Klimazustand.
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Optional
from dataclasses import dataclass
import re


@dataclass
class ClimateIndex:
    """Ein Klimaindex mit aktuellem Wert."""
    name: str
    full_name: str
    value: float
    phase: str  # "positive", "negative", "neutral"
    strength: str  # "weak", "moderate", "strong", "extreme"
    trend: str  # "rising", "falling", "stable"
    updated: datetime
    source: str
    
    @classmethod
    def from_value(cls, name: str, full_name: str, value: float, source: str):
        """Erstelle Index aus Rohwert."""
        # Phase bestimmen
        if value > 0.5:
            phase = "positive"
        elif value < -0.5:
            phase = "negative"
        else:
            phase = "neutral"
        
        # Stärke bestimmen
        abs_val = abs(value)
        if abs_val >= 2.0:
            strength = "extreme"
        elif abs_val >= 1.5:
            strength = "strong"
        elif abs_val >= 0.5:
            strength = "moderate"
        else:
            strength = "weak"
        
        return cls(
            name=name,
            full_name=full_name,
            value=value,
            phase=phase,
            strength=strength,
            trend="stable",  # Würde aus Zeitreihe berechnet
            updated=datetime.now(),
            source=source
        )


class ClimateIndexService:
    """Service zum Abrufen aktueller Klimaindizes."""
    
    # Bekannte Klima-Indizes und ihre Quellen
    INDICES = {
        "ONI": {
            "full_name": "Oceanic Niño Index",
            "url": "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",
            "description": "3-Monats-Mittel SST-Anomalie in Niño 3.4 Region"
        },
        "MEI": {
            "full_name": "Multivariate ENSO Index v2",
            "url": "https://psl.noaa.gov/enso/mei/data/meiv2.data",
            "description": "Kombiniert SST, SLP, Oberflächenwind, OLR"
        },
        "SOI": {
            "full_name": "Southern Oscillation Index",
            "url": "https://www.cpc.ncep.noaa.gov/data/indices/soi",
            "description": "Tahiti - Darwin Druckdifferenz"
        },
        "AMO": {
            "full_name": "Atlantic Multidecadal Oscillation",
            "url": "https://psl.noaa.gov/data/correlation/amon.us.data",
            "description": "Nordatlantik SST-Anomalie"
        },
        "PDO": {
            "full_name": "Pacific Decadal Oscillation",
            "url": "https://psl.noaa.gov/pdo/",
            "description": "Nordpazifik SST-Muster"
        },
        "NAO": {
            "full_name": "North Atlantic Oscillation",
            "url": "https://www.cpc.ncep.noaa.gov/products/precip/CWlink/pna/nao.shtml",
            "description": "Island - Azoren Druckdifferenz"
        },
        "AO": {
            "full_name": "Arctic Oscillation",
            "url": "https://www.cpc.ncep.noaa.gov/products/precip/CWlink/daily_ao_index/ao.shtml",
            "description": "Arktischer Druckmodus"
        },
        "IOD": {
            "full_name": "Indian Ocean Dipole",
            "url": "https://psl.noaa.gov/gcos_wgsp/Timeseries/DMI/",
            "description": "West-Ost Temperaturgradient im Indischen Ozean"
        }
    }
    
    def __init__(self):
        self.cache: Dict[str, ClimateIndex] = {}
        self.cache_duration = timedelta(hours=6)
        self.last_update: Optional[datetime] = None
    
    async def fetch_oni(self) -> Optional[float]:
        """Hole aktuellen ONI (El Niño Index) von NOAA."""
        try:
            async with aiohttp.ClientSession() as session:
                url = self.INDICES["ONI"]["url"]
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        # Parse die letzte Zeile
                        lines = [l.strip() for l in text.split('\n') if l.strip() and not l.startswith('#')]
                        if lines:
                            last_line = lines[-1]
                            values = last_line.split()
                            if len(values) >= 13:
                                # Letzter Nicht-Null-Wert
                                for v in reversed(values[1:]):
                                    try:
                                        val = float(v)
                                        if val != -99.9:
                                            return val
                                    except:
                                        continue
        except Exception as e:
            print(f"Fehler beim Abrufen von ONI: {e}")
        return None
    
    async def fetch_soi(self) -> Optional[float]:
        """Hole aktuellen SOI von NOAA."""
        try:
            async with aiohttp.ClientSession() as session:
                url = self.INDICES["SOI"]["url"]
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        lines = [l.strip() for l in text.split('\n') if l.strip() and not l.startswith('#')]
                        if lines:
                            last_line = lines[-1]
                            values = last_line.split()
                            if len(values) >= 2:
                                try:
                                    return float(values[-1])
                                except:
                                    pass
        except Exception as e:
            print(f"Fehler beim Abrufen von SOI: {e}")
        return None
    
    async def get_all_indices(self, use_cache: bool = True) -> Dict[str, ClimateIndex]:
        """
        Hole alle verfügbaren Klimaindizes.
        
        Returns:
            Dict mit Index-Namen als Keys und ClimateIndex Objekten als Values
        """
        # Cache prüfen
        if use_cache and self.last_update:
            if datetime.now() - self.last_update < self.cache_duration:
                return self.cache
        
        indices = {}
        
        # ONI versuchen
        oni_value = await self.fetch_oni()
        if oni_value is not None:
            indices["ONI"] = ClimateIndex.from_value(
                "ONI", "Oceanic Niño Index", oni_value, "NOAA CPC"
            )
        
        # SOI versuchen
        soi_value = await self.fetch_soi()
        if soi_value is not None:
            # SOI ist invertiert: negativ = El Niño
            indices["SOI"] = ClimateIndex.from_value(
                "SOI", "Southern Oscillation Index", soi_value, "NOAA CPC"
            )
        
        # Fallback: Simulierte Werte für Demo (in Produktion durch echte APIs ersetzen)
        if "ONI" not in indices:
            indices["ONI"] = ClimateIndex.from_value("ONI", "Oceanic Niño Index", 1.8, "Demo")
        
        if "AMO" not in indices:
            indices["AMO"] = ClimateIndex.from_value("AMO", "Atlantic Multidecadal Oscillation", 0.4, "Demo")
        
        if "IOD" not in indices:
            indices["IOD"] = ClimateIndex.from_value("IOD", "Indian Ocean Dipole", 0.8, "Demo")
        
        if "NAO" not in indices:
            indices["NAO"] = ClimateIndex.from_value("NAO", "North Atlantic Oscillation", -0.3, "Demo")
        
        if "PDO" not in indices:
            indices["PDO"] = ClimateIndex.from_value("PDO", "Pacific Decadal Oscillation", -0.2, "Demo")
        
        if "AO" not in indices:
            indices["AO"] = ClimateIndex.from_value("AO", "Arctic Oscillation", 0.5, "Demo")
        
        self.cache = indices
        self.last_update = datetime.now()
        
        return indices
    
    def get_enso_state(self, indices: Dict[str, ClimateIndex]) -> Dict:
        """Bestimme den ENSO-Zustand aus ONI."""
        oni = indices.get("ONI")
        if not oni:
            return {"state": "unknown", "strength": "unknown"}
        
        if oni.value >= 0.5:
            state = "El Niño"
        elif oni.value <= -0.5:
            state = "La Niña"
        else:
            state = "Neutral"
        
        return {
            "state": state,
            "strength": oni.strength,
            "value": oni.value,
            "description": f"{state} ({oni.strength}): ONI = {oni.value:+.1f}°C"
        }
    
    def to_dict(self, indices: Dict[str, ClimateIndex]) -> Dict:
        """Konvertiere für API-Response."""
        result = {}
        for name, idx in indices.items():
            result[name] = {
                "name": idx.name,
                "full_name": idx.full_name,
                "value": idx.value,
                "phase": idx.phase,
                "strength": idx.strength,
                "trend": idx.trend,
                "updated": idx.updated.isoformat(),
                "source": idx.source
            }
        return result


# Singleton
climate_service = ClimateIndexService()


async def main():
    """Test-Funktion."""
    print("=" * 60)
    print("TERA Climate Index Service - Test")
    print("=" * 60)
    
    indices = await climate_service.get_all_indices()
    
    print(f"\n📡 {len(indices)} Klimaindizes geladen:\n")
    
    for name, idx in indices.items():
        emoji = "🔴" if idx.phase == "positive" else "🔵" if idx.phase == "negative" else "⚪"
        print(f"  {emoji} {name:5s}: {idx.value:+.2f} ({idx.phase}, {idx.strength})")
        print(f"         {idx.full_name}")
    
    print("\n" + "-" * 60)
    enso = climate_service.get_enso_state(indices)
    print(f"🌊 ENSO Status: {enso['description']}")


if __name__ == "__main__":
    asyncio.run(main())












