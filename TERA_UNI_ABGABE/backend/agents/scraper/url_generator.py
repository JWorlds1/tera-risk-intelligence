"""
Dynamic URL Generator for Context Data Sources
Generates relevant URLs for any location on Earth
"""
from typing import List, Dict, Any
from dataclasses import dataclass
from urllib.parse import urlencode
import h3


@dataclass
class GeneratedURL:
    source: str
    url: str
    type: str  # satellite, paper, news, data
    description: str


class URLGenerator:
    """Generate context-relevant URLs for any location"""
    
    # IPCC AR6 chapter mapping by topic
    IPCC_CHAPTERS = {
        "water": "https://www.ipcc.ch/report/ar6/wg2/chapter/chapter-4/",
        "food": "https://www.ipcc.ch/report/ar6/wg2/chapter/chapter-5/",
        "cities": "https://www.ipcc.ch/report/ar6/wg2/chapter/chapter-6/",
        "health": "https://www.ipcc.ch/report/ar6/wg2/chapter/chapter-7/",
        "poverty": "https://www.ipcc.ch/report/ar6/wg2/chapter/chapter-8/",
        "africa": "https://www.ipcc.ch/report/ar6/wg2/chapter/chapter-9/",
        "asia": "https://www.ipcc.ch/report/ar6/wg2/chapter/chapter-10/",
        "australasia": "https://www.ipcc.ch/report/ar6/wg2/chapter/chapter-11/",
        "central_south_america": "https://www.ipcc.ch/report/ar6/wg2/chapter/chapter-12/",
        "europe": "https://www.ipcc.ch/report/ar6/wg2/chapter/chapter-13/",
        "north_america": "https://www.ipcc.ch/report/ar6/wg2/chapter/chapter-14/",
        "small_islands": "https://www.ipcc.ch/report/ar6/wg2/chapter/chapter-15/",
        "polar": "https://www.ipcc.ch/report/ar6/wg2/chapter/chapter-16/",
    }
    
    # Continent mapping for IPCC
    CONTINENT_TO_IPCC = {
        "AF": "africa",
        "AS": "asia", 
        "EU": "europe",
        "NA": "north_america",
        "SA": "central_south_america",
        "OC": "australasia",
        "AN": "polar",
    }
    
    def __init__(self):
        pass
    
    def generate_nasa_worldview_url(self, lat: float, lon: float, date: str = None) -> GeneratedURL:
        """Generate NASA Worldview URL for satellite imagery"""
        # Calculate bounding box (approx 200km x 200km view)
        delta = 1.0
        bbox = f"{lon-delta},{lat-delta},{lon+delta},{lat+delta}"
        
        params = {
            "v": bbox,
            "l": "MODIS_Terra_CorrectedReflectance_TrueColor,Coastlines_15m",
            "t": date or "today",
        }
        
        url = f"https://worldview.earthdata.nasa.gov/?{urlencode(params)}"
        return GeneratedURL(
            source="NASA Worldview",
            url=url,
            type="satellite",
            description=f"Satellite imagery for ({lat:.2f}, {lon:.2f})"
        )
    
    def generate_nasa_firms_url(self, lat: float, lon: float) -> GeneratedURL:
        """Generate NASA FIRMS (Fire Information) URL"""
        url = f"https://firms.modaps.eosdis.nasa.gov/map/#t:adv;d:24hrs;l:fires_viirs_snpp,fires_modis_a,fires_modis_t;@{lon},{lat},8z"
        return GeneratedURL(
            source="NASA FIRMS",
            url=url,
            type="data",
            description="Active fire detection data"
        )
    
    def generate_copernicus_url(self, lat: float, lon: float) -> GeneratedURL:
        """Generate Copernicus Climate Data Store URL"""
        url = f"https://cds.climate.copernicus.eu/cdsapp#!/search?text=region&lat={lat}&lon={lon}"
        return GeneratedURL(
            source="Copernicus CDS",
            url=url,
            type="data",
            description="Climate data and reanalysis"
        )
    
    def generate_reliefweb_url(self, country: str) -> GeneratedURL:
        """Generate ReliefWeb humanitarian data URL"""
        url = f"https://reliefweb.int/country/{country.lower()}?search=disaster%20OR%20crisis"
        return GeneratedURL(
            source="ReliefWeb",
            url=url,
            type="news",
            description="Humanitarian situation reports"
        )
    
    def generate_gdelt_url(self, lat: float, lon: float) -> GeneratedURL:
        """Generate GDELT news monitoring URL"""
        url = f"https://api.gdeltproject.org/api/v2/geo/geo?query=conflict%20OR%20disaster&mode=artlist&format=json&maxrecords=50&sourcelang=eng&sourcelat={lat}&sourcelong={lon}&sourcedistance=100km"
        return GeneratedURL(
            source="GDELT",
            url=url,
            type="news",
            description="Global news events near location"
        )
    
    def generate_ipcc_url(self, continent: str = None, topic: str = None) -> GeneratedURL:
        """Generate relevant IPCC AR6 chapter URL"""
        chapter_key = None
        
        if continent and continent in self.CONTINENT_TO_IPCC:
            chapter_key = self.CONTINENT_TO_IPCC[continent]
        elif topic and topic.lower() in self.IPCC_CHAPTERS:
            chapter_key = topic.lower()
        else:
            chapter_key = "water"  # Default to water chapter
        
        url = self.IPCC_CHAPTERS.get(chapter_key, self.IPCC_CHAPTERS["water"])
        return GeneratedURL(
            source="IPCC AR6",
            url=url,
            type="paper",
            description=f"IPCC AR6 Chapter: {chapter_key}"
        )
    
    def generate_osm_url(self, lat: float, lon: float) -> GeneratedURL:
        """Generate OpenStreetMap URL"""
        url = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=12/{lat}/{lon}"
        return GeneratedURL(
            source="OpenStreetMap",
            url=url,
            type="map",
            description="OpenStreetMap view"
        )
    
    def generate_all_urls(
        self, 
        lat: float, 
        lon: float, 
        country_code: str = None,
        continent: str = None
    ) -> List[GeneratedURL]:
        """Generate all relevant URLs for a location"""
        urls = [
            self.generate_nasa_worldview_url(lat, lon),
            self.generate_nasa_firms_url(lat, lon),
            self.generate_copernicus_url(lat, lon),
            self.generate_gdelt_url(lat, lon),
            self.generate_osm_url(lat, lon),
        ]
        
        if country_code:
            urls.append(self.generate_reliefweb_url(country_code))
        
        urls.append(self.generate_ipcc_url(continent=continent))
        
        return urls
    
    def generate_for_h3_cell(self, h3_index: str, country_code: str = None, continent: str = None) -> List[GeneratedURL]:
        """Generate URLs for an H3 cell"""
        lat, lon = h3.h3_to_geo(h3_index)
        return self.generate_all_urls(lat, lon, country_code, continent)
