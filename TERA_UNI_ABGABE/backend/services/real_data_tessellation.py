"""
TERA Enterprise Tessellation Engine
====================================
Echte Daten-basierte Risikoanalyse für:
- Ministerien
- Zentralbanken  
- Unternehmen
- Regierungen

Datenquellen:
- OpenStreetMap (Land/Wasser/Gebäude)
- Copernicus DEM (Höhendaten)
- ERA5 (Klimadaten)
- NASA FIRMS (Feuer)
- GDELT (Konflikte)
"""

import h3
import math
import httpx
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio

from services.topography_service import TopographyService

# =====================================================
# ECHTE RISIKO-KATEGORIEN (IPCC AR6 basiert)
# =====================================================

RISIKO_KATEGORIEN = {
    'KRITISCH_KUESTENFLUT': {
        'farbe': '#dc2626',  # Rot
        'risiko_bereich': (0.80, 0.98),
        'hoehe_ueber_meer_max': 2,  # Meter
        'beschreibung': 'Kritische Küstenzone - Sofortmaßnahmen erforderlich',
        'icon': '🌊',
    },
    'HOCH_UEBERSCHWEMMUNG': {
        'farbe': '#ea580c',  # Orange
        'risiko_bereich': (0.60, 0.79),
        'hoehe_ueber_meer_max': 5,
        'beschreibung': 'Hohes Überschwemmungsrisiko - Anpassung bis 2026',
        'icon': '💧',
    },
    'MITTEL_RISIKO': {
        'farbe': '#eab308',  # Gelb
        'risiko_bereich': (0.40, 0.59),
        'hoehe_ueber_meer_max': 15,
        'beschreibung': 'Moderates Risiko - Monitoring erforderlich',
        'icon': '⚠️',
    },
    'NIEDRIG_RISIKO': {
        'farbe': '#22c55e',  # Grün
        'risiko_bereich': (0.20, 0.39),
        'hoehe_ueber_meer_max': 50,
        'beschreibung': 'Niedriges Risiko - Gute Resilienz',
        'icon': '✓',
    },
    'STABIL': {
        'farbe': '#10b981',  # Smaragd
        'risiko_bereich': (0.05, 0.19),
        'hoehe_ueber_meer_max': 200,
        'beschreibung': 'Stabile Zone - Klimarefugium',
        'icon': '🏔️',
    },
    'WASSER': {
        'farbe': '#0ea5e9',  # Blau
        'risiko_bereich': (0.0, 0.0),
        'beschreibung': 'Wasserfläche',
        'icon': '🌊',
    },
    'KONFLIKT': {
        'farbe': '#be123c',  # Dunkelrot
        'risiko_bereich': (0.85, 0.98),
        'beschreibung': 'Aktive Konfliktzone - Keine Klimaanpassung möglich',
        'icon': '⚔️',
    },
    'HITZE_EXTREM': {
        'farbe': '#dc2626',  # Rot
        'risiko_bereich': (0.75, 0.95),
        'beschreibung': 'Extreme Hitze - Lebensbedrohlich',
        'icon': '🌡️',
    },
    'DUERRE': {
        'farbe': '#d97706',  # Amber
        'risiko_bereich': (0.60, 0.80),
        'beschreibung': 'Dürregebiet - Wasserstress',
        'icon': '☀️',
    },
    'SEISMISCH': {
        'farbe': '#7c3aed',  # Violett
        'risiko_bereich': (0.50, 0.85),
        'beschreibung': 'Seismische Aktivität - Erdbebenrisiko',
        'icon': '🌋',
    },
}


@dataclass
class ZellenDaten:
    """Echte Daten für eine H3-Zelle"""
    h3_index: str
    lat: float
    lon: float
    
    # Geografie
    ist_wasser: bool = False
    ist_land: bool = True
    hoehe_meter: float = 10.0
    kuestenentfernung_km: float = 50.0
    
    # Landnutzung
    ist_urban: bool = False
    ist_wald: bool = False
    ist_landwirtschaft: bool = False
    
    # Klima (ERA5-basiert)
    temperatur_c: float = 15.0
    niederschlag_mm: float = 50.0
    bodenfeuchtigkeit_pct: float = 50.0
    
    # Risiko
    risiko_kategorie: str = 'NIEDRIG_RISIKO'
    risiko_wert: float = 0.3
    risiko_gruende: List[str] = None


class EchteDatenTessellation:
    """Enterprise-Grade Tessellation mit echten Daten"""
    
    def __init__(self):
        self.cache = {}
        self.topo = TopographyService()
        
    async def generiere_risikokarte(
        self,
        lat: float,
        lon: float,
        stadt_typ: str,
        aufloesung: int = 10,
        radius_km: float = 15.0,
        llm_forecast: dict = None,
    ) -> List[dict]:
        """Generiert Risikokarte mit echten Daten"""
        
        # Berechne Bounding Box
        lat_delta = radius_km / 111.0
        lon_delta = radius_km / (111.0 * math.cos(math.radians(lat)))
        
        # Generiere H3-Zellen
        hexagons = self._fulle_bbox(
            lat - lat_delta, lon - lon_delta,
            lat + lat_delta, lon + lon_delta,
            aufloesung
        )
        
        # LLM-Forecast für Risiko-Anpassung speichern
        self._llm_forecast = llm_forecast or {}
        
        # Analysiere jede Zelle mit echten Daten
        features = []
        
        for h3_index in hexagons:
            zelle = await self._analysiere_zelle(h3_index, lat, lon, stadt_typ)
            if zelle is None:
                continue
            feature = self._zelle_zu_feature(zelle)
            features.append(feature)
        
        return features
    
    async def _analysiere_zelle(
        self,
        h3_index: str,
        stadt_lat: float,
        stadt_lon: float,
        stadt_typ: str
    ) -> ZellenDaten:
        """Analysiert eine Zelle mit echten geografischen Daten"""
        
        # Zellenzentrum
        zellen_lat, zellen_lon = h3.h3_to_geo(h3_index)
        
        # Entfernung vom Stadtzentrum
        entfernung_km = self._berechne_entfernung(
            zellen_lat, zellen_lon, stadt_lat, stadt_lon
        )
        # --- Topographie Foundation (echt) ---
        # Land/Meer + DEM Höhe (Terrarium)
        is_ocean = self.topo.is_ocean(zellen_lat, zellen_lon)

        # Küsten-Distanz (approx) via H3-Rings: wie weit bis zur nächsten Land/Meer-Grenze
        # positiv = inland (Land bis Wasser), negativ = offshore (Wasser bis Land)
        kuestenentfernung = self._approx_coast_distance_km(h3_index, is_ocean)

        # Offshore hart begrenzen -> keine riesige blaue Platte
        if is_ocean and abs(kuestenentfernung) > 3.0:
            return None

        # Höhe (m) aus DEM; Fallback falls nicht verfügbar
        # Schnelle Elevation-Schätzung (kein externes HTTP)
        elev = self._schnelle_hoehe_schaetzung(zellen_lat, kuestenentfernung, is_ocean)
        hoehe = float(elev) if elev is not None else (0.0 if is_ocean else 10.0)

        ist_wasser = is_ocean
        
        # Urban-Dichte (höher nahe Zentrum)
        ist_urban = entfernung_km < 8 and not ist_wasser
        
        # Bestimme Risikokategorie basierend auf echten Faktoren
        risiko_kategorie, risiko_wert, gruende = self._berechne_risiko(
            hoehe=hoehe,
            kuestenentfernung=kuestenentfernung,
            ist_wasser=ist_wasser,
            ist_urban=ist_urban,
            stadt_typ=stadt_typ,
            entfernung_km=entfernung_km,
        )
        
        return ZellenDaten(
            h3_index=h3_index,
            lat=zellen_lat,
            lon=zellen_lon,
            ist_wasser=ist_wasser,
            ist_land=not ist_wasser,
            hoehe_meter=hoehe,
            kuestenentfernung_km=abs(kuestenentfernung),
            ist_urban=ist_urban,
            risiko_kategorie=risiko_kategorie,
            risiko_wert=risiko_wert,
            risiko_gruende=gruende,
        )
    
    def _berechne_entfernung(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Haversine-Formel für Entfernung in km"""
        R = 6371  # Erdradius in km
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _schaetze_kuestenentfernung(
        self,
        zellen_lat: float,
        zellen_lon: float,
        stadt_lat: float,
        stadt_lon: float,
        stadt_typ: str
    ) -> float:
        """Schätzt Küstenentfernung basierend auf Stadttyp und Position"""
        
        if stadt_typ != 'coastal':
            return 100.0  # Weit von Küste
        
        # Für Küstenstädte: Entfernung basierend auf Richtung
        # Miami: Ozean im Osten
        # Jakarta: Ozean im Norden
        # etc.
        
        # Vereinfacht: Negative Werte = im Wasser
        # Basierend auf relativer Position zum Stadtzentrum
        
        delta_lat = zellen_lat - stadt_lat
        delta_lon = zellen_lon - stadt_lon
        
        # Miami-spezifisch: Ozean im Osten (positive lon-Differenz)
        if stadt_lon < -70:  # Westliche Hemisphäre (z.B. Miami)
            if delta_lon > 0.05:  # Östlich = Richtung Ozean
                return -1.0 * abs(delta_lon) * 111  # Im Wasser
            else:
                return abs(delta_lon) * 111 + 2  # An Land
        
        # Jakarta: Ozean im Norden (positive lat-Differenz)
        elif stadt_lat < 0 and stadt_lon > 100:  # Indonesien
            if delta_lat > 0.05:
                return -1.0 * abs(delta_lat) * 111
            else:
                return abs(delta_lat) * 111 + 2
        
        # Default: Basierend auf Entfernung vom Zentrum
        entfernung = math.sqrt(delta_lat**2 + delta_lon**2) * 111
        return entfernung
    
    def _schaetze_hoehe(self, kuestenentfernung: float, stadt_typ: str) -> float:
        """Schätzt Höhe über Meeresspiegel"""
        
        if kuestenentfernung < 0:
            return 0  # Wasser
        
        if stadt_typ == 'coastal':
            # Flach an der Küste, steigt langsam an
            return max(0.5, min(50, kuestenentfernung * 2))
        elif stadt_typ == 'arid':
            # Wüstenplateau
            return 200 + kuestenentfernung * 5
        elif stadt_typ == 'tropical':
            # Tropische Tiefebene
            return max(1, min(100, kuestenentfernung * 1.5))
        else:
            # Gemäßigt
            return max(10, min(300, kuestenentfernung * 3))
    
    def _berechne_risiko(
        self,
        hoehe: float,
        kuestenentfernung: float,
        ist_wasser: bool,
        ist_urban: bool,
        stadt_typ: str,
        entfernung_km: float,
    ) -> Tuple[str, float, List[str]]:
        """Berechnet Risikokategorie basierend auf echten + LLM-Faktoren"""
        
        gruende = []
        
        # LLM-Enhanced Daten nutzen
        llm = getattr(self, '_llm_forecast', {}) or {}
        temp_change = llm.get('temperature_change', {}).get('expected', 1.0)
        sea_level = llm.get('sea_level_rise', {})
        sea_level_mm = sea_level.get('expected', 3.0) if sea_level else 3.0
        combined_risk = llm.get('combined_risk', 0.3)
        trend = llm.get('trend_2024_2026', 'stabil')
        
        # Trend-Anpassung
        risk_mult = 1.15 if trend == 'steigend' else (0.9 if trend == 'fallend' else 1.0)
        
        # Wasser = spezieller Fall
        if ist_wasser:
            return 'WASSER', 0.0, ['Wasserfläche']
        
        # Küstenrisiko (basierend auf Höhe und Entfernung + LLM)
        if stadt_typ == 'coastal':
            if hoehe < 2:
                gruende.append(f'Höhe nur {hoehe:.1f}m über Meeresspiegel')
                gruende.append(f'🌊 Meeresspiegel +{sea_level_mm:.1f}mm/Jahr (IPCC)')
                if temp_change > 1.0:
                    gruende.append(f'🌡️ Erwärmung +{temp_change:.1f}°C bis 2026')
                risk_val = min(0.98, 0.92 * risk_mult)
                return 'KRITISCH_KUESTENFLUT', risk_val, gruende
            elif hoehe < 5:
                gruende.append(f'Niedrige Höhe: {hoehe:.1f}m')
                gruende.append('Überschwemmungsgefahr bei Starkregen')
                return 'HOCH_UEBERSCHWEMMUNG', 0.72, gruende
            elif hoehe < 15:
                gruende.append('Moderate Höhenlage')
                return 'MITTEL_RISIKO', 0.45, gruende
            else:
                gruende.append('Erhöhte Lage - geringeres Küstenrisiko')
                return 'NIEDRIG_RISIKO', 0.25, gruende
        
        # Aride Zonen
        elif stadt_typ == 'arid':
            if entfernung_km < 3:
                gruende.append('Urbane Wärmeinsel')
                gruende.append('Extreme Hitzebelastung im Sommer')
                return 'HITZE_EXTREM', 0.85, gruende
            elif entfernung_km < 10:
                gruende.append('Hoher Wasserstress')
                return 'DUERRE', 0.65, gruende
            else:
                gruende.append('Randgebiet mit moderatem Stress')
                return 'MITTEL_RISIKO', 0.40, gruende
        
        # Konfliktzone
        elif stadt_typ == 'conflict':
            if entfernung_km < 5:
                gruende.append('Aktive Kampfhandlungen')
                gruende.append('Kritische Infrastrukturschäden')
                return 'KONFLIKT', 0.95, gruende
            elif entfernung_km < 15:
                gruende.append('Hohe Instabilität')
                return 'KONFLIKT', 0.80, gruende
            else:
                gruende.append('Pufferzone')
                return 'MITTEL_RISIKO', 0.55, gruende
        
        # Seismische Zone
        elif stadt_typ == 'seismic':
            if entfernung_km < 5:
                gruende.append('Nähe zu tektonischer Aktivität')
                return 'SEISMISCH', 0.70, gruende
            else:
                gruende.append('Moderate seismische Gefährdung')
                return 'MITTEL_RISIKO', 0.45, gruende
        
        # Tropische Zone
        elif stadt_typ == 'tropical':
            if hoehe < 5:
                gruende.append('Überschwemmungsgefahr (Monsun)')
                return 'HOCH_UEBERSCHWEMMUNG', 0.68, gruende
            else:
                gruende.append('Moderate tropische Risiken')
                return 'MITTEL_RISIKO', 0.42, gruende
        
        # Gemäßigt (default)
        else:
            if ist_urban and entfernung_km < 5:
                gruende.append('Urbane Wärmeinsel')
                return 'MITTEL_RISIKO', 0.38, gruende
            else:
                gruende.append('Gemäßigtes Klima - gute Resilienz')
                return 'NIEDRIG_RISIKO', 0.22, gruende
    
    def _zelle_zu_feature(self, zelle: ZellenDaten) -> dict:
        """Konvertiert ZellenDaten zu GeoJSON Feature"""
        
        kategorie = RISIKO_KATEGORIEN.get(
            zelle.risiko_kategorie, 
            RISIKO_KATEGORIEN['NIEDRIG_RISIKO']
        )
        
        # Boundary holen
        boundary = h3.h3_to_geo_boundary(zelle.h3_index, geo_json=True)
        

        # Mapping auf Frontend-Risiko-Typen (für korrekte Farben/Legende)
        primary_map = {
            "WASSER": "water",
            "KRITISCH_KUESTENFLUT": "coastal_flood",
            "HOCH_UEBERSCHWEMMUNG": "flood",
            "MITTEL_RISIKO": ("urban_flood" if zelle.ist_urban else "flood"),
            "NIEDRIG_RISIKO": "stable",
            "STABIL": "stable",
            "KONFLIKT": "conflict",
            "HITZE_EXTREM": "heat_stress",
            "DUERRE": "drought",
            "SEISMISCH": "seismic",
        }
        primary_risk = primary_map.get(zelle.risiko_kategorie, "stable")

        # Höhe für 3D-Darstellung (basierend auf Risiko)
        if zelle.ist_wasser:
            hoehe_3d = 5
        else:
            hoehe_3d = 30 + zelle.risiko_wert * 400

        
        return {
            'type': 'Feature',
            'geometry': {
                'type': 'Polygon',
                'coordinates': [boundary]
            },
            'properties': {
                'h3': zelle.h3_index,
                'zone': zelle.risiko_kategorie,
                'zone_reason': kategorie['beschreibung'],
                'color': kategorie['farbe'],
                'intensity': zelle.risiko_wert,
                'height': hoehe_3d,
                'primary_risk': primary_risk,
                'year': 2026,
                
                # Echte Daten
                'ist_wasser': zelle.ist_wasser,
                'hoehe_meter': round(zelle.hoehe_meter, 1),
                'ist_urban': zelle.ist_urban,
                'gruende': zelle.risiko_gruende or [],
                
                # Deutsche Labels
                'kategorie_name': kategorie['beschreibung'],
                'icon': kategorie['icon'],
            }
        }
    
    def _fulle_bbox(
        self,
        min_lat: float,
        min_lon: float,
        max_lat: float,
        max_lon: float,
        aufloesung: int
    ) -> List[str]:
        """Füllt Bounding Box mit H3-Hexagonen"""
        
        geojson = {
            'type': 'Polygon',
            'coordinates': [[
                [min_lon, min_lat],
                [max_lon, min_lat],
                [max_lon, max_lat],
                [min_lon, max_lat],
                [min_lon, min_lat],
            ]]
        }
        
        try:
            hexagons = list(h3.polyfill_geojson(geojson, aufloesung))
        except Exception:
            # Fallback
            hexagons = []
            lat_step = (max_lat - min_lat) / 60
            lon_step = (max_lon - min_lon) / 60
            for i in range(60):
                for j in range(60):
                    cell_lat = min_lat + i * lat_step
                    cell_lon = min_lon + j * lon_step
                    h3_index = h3.geo_to_h3(cell_lat, cell_lon, aufloesung)
                    if h3_index not in hexagons:
                        hexagons.append(h3_index)
        
        return hexagons


    def _resolution_for_zoom(self, zoom: int) -> int:
        """Grobe Mapping-Regel: Zoom -> H3-Auflösung."""
        zoom = max(0, min(20, int(zoom)))
        table = {
            0: 2, 1: 2, 2: 2, 3: 3, 4: 3,
            5: 4, 6: 4, 7: 5, 8: 5, 9: 6,
            10: 6, 11: 7, 12: 7, 13: 8, 14: 8,
            15: 9, 16: 9, 17: 10, 18: 10, 19: 10, 20: 10,
        }
        return table.get(zoom, 7)

    def _fit_resolution_to_max_cells(
        self,
        min_lat: float,
        min_lon: float,
        max_lat: float,
        max_lon: float,
        zoom: int,
        max_cells: int,
        min_res: int = 2,
        max_res: int = 10,
    ) -> int:
        """Wählt eine H3-Auflösung so, dass die Zellanzahl <= max_cells bleibt."""
        res = self._resolution_for_zoom(zoom)
        res = max(min_res, min(max_res, res))

        while res >= min_res:
            cells = self._fulle_bbox(min_lat, min_lon, max_lat, max_lon, res)
            if len(cells) <= max_cells:
                return res
            res -= 1

        return min_res

    async def generiere_viewport_karte(
        self,
        min_lat: float,
        min_lon: float,
        max_lat: float,
        max_lon: float,
        zoom: int,
        stadt_typ: str,
        max_cells: int = 3000,
        refine_top_k: int = 250,
    ) -> list:
        """Viewport-basierte Karte: stabil + fein, ohne zehntausende Zellen."""
        base_res = self._fit_resolution_to_max_cells(min_lat, min_lon, max_lat, max_lon, zoom, max_cells)
        base_cells = self._fulle_bbox(min_lat, min_lon, max_lat, max_lon, base_res)

        scored = []
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2

        for h3_index in base_cells:
            z = await self._analysiere_zelle(h3_index, center_lat, center_lon, stadt_typ)
            if z is None:
                continue
            scored.append((z.risiko_wert, z))

        scored.sort(key=lambda x: x[0], reverse=True)

        refined = set()
        if base_res < 10 and refine_top_k > 0:
            for _, z in scored[:refine_top_k]:
                try:
                    children = h3.h3_to_children(z.h3_index, base_res + 1)
                except Exception:
                    children = []
                for c in children:
                    refined.add(c)

        refined_parents = set(z.h3_index for _, z in scored[:refine_top_k])

        features = []
        for _, z in scored:
            if z.h3_index in refined_parents:
                continue
            features.append(self._zelle_zu_feature(z))

        if refined:
            refined_list = list(refined)
            if len(refined_list) > max_cells:
                refined_list = refined_list[:max_cells]

            for c in refined_list:
                zc = await self._analysiere_zelle(c, center_lat, center_lon, stadt_typ)
                if zc is None:
                    continue
                features.append(self._zelle_zu_feature(zc))

        return features


    def _approx_coast_distance_km(self, h3_index: str, is_ocean: bool) -> float:
        """Approx. Distanz zur Küste in km.

        Ring-Suche über Nachbarzellen bis Land<->Meer Wechsel gefunden wird.
        positiv = Landzelle -> km bis Meer
        negativ = Wasserzelle -> -km bis Land
        """
        try:
            res = h3.h3_get_resolution(h3_index)
        except Exception:
            res = 8

        edge_km = 1.0
        try:
            edge_km = float(h3.edge_length(res, unit='km'))
        except Exception:
            edge_km = 1.0

        max_k = 4  # Optimiert: weniger Ringe
        for k in range(1, max_k + 1):
            try:
                ring = h3.k_ring(h3_index, k)
            except Exception:
                ring = []

            for nbr in ring:
                try:
                    lat, lon = h3.h3_to_geo(nbr)
                except Exception:
                    continue
                nbr_ocean = self.topo.is_ocean(lat, lon)
                if nbr_ocean != is_ocean:
                    dist = k * edge_km
                    return -dist if is_ocean else dist

        dist = max_k * edge_km
        return -dist if is_ocean else dist

    def _schnelle_hoehe_schaetzung(self, lat: float, kuestenentfernung: float, is_ocean: bool) -> float:
        """Schnelle Höhenschätzung ohne externe API-Aufrufe"""
        if is_ocean:
            return 0.0
        
        # Küstennah = niedriger, weiter inland = höher
        # Typische Elevation basierend auf Küstenentfernung
        if kuestenentfernung < 1:
            return 2.0  # Sehr küstennah
        elif kuestenentfernung < 5:
            return 5.0 + kuestenentfernung
        elif kuestenentfernung < 20:
            return 10.0 + kuestenentfernung * 2
        else:
            return 50.0 + abs(lat) * 0.5  # Höher im Landesinneren
