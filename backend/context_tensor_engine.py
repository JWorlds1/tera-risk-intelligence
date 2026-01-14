"""
Context Tensor Engine - Generates multidimensional context tensors for H3 cells
Implements 6 dimensions: Climate, Geography, Socioeconomics, Infrastructure, Vulnerability, Unstructured Data
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import httpx
import structlog
# Forward reference - import only when needed to avoid circular dependency
# from h3_grid_engine import H3GridEngine, H3Cell

logger = structlog.get_logger(__name__)


@dataclass
class ClimateDimension:
    """Climate & Environment dimension"""
    temp_mean: float = 0.0
    temp_max: float = 0.0
    temp_min: float = 0.0
    precipitation: float = 0.0
    extreme_events_frequency: float = 0.0
    extreme_events_intensity: float = 0.0
    air_quality_pm25: float = 0.0
    air_quality_ozone: float = 0.0
    soil_moisture: float = 0.0


@dataclass
class GeographyDimension:
    """Geography & Land Use dimension"""
    elevation: float = 0.0
    slope: float = 0.0
    land_cover_class: str = 'Unknown'  # Forest, Agriculture, Urban, Water, etc.
    coastal_proximity: float = 0.0  # Distance to coast in km
    water_body: bool = False


@dataclass
class SocioeconomicDimension:
    """Socioeconomic dimension"""
    population_density: float = 0.0  # per km²
    gdp_per_capita: float = 0.0
    poverty_rate: float = 0.0
    education_level: float = 0.0
    unemployment_rate: float = 0.0


@dataclass
class InfrastructureDimension:
    """Infrastructure dimension"""
    road_density: float = 0.0  # km per km²
    hospital_proximity: float = 0.0  # km to nearest hospital
    energy_infrastructure: float = 0.0  # density score
    water_infrastructure: float = 0.0  # access score


@dataclass
class VulnerabilityDimension:
    """Adaptive Capacity & Vulnerability dimension"""
    social_vulnerability_index: float = 0.0
    governance_quality: float = 0.0
    financial_access: float = 0.0
    health_system_quality: float = 0.0


@dataclass
class UnstructuredDataDimension:
    """Unstructured data dimension"""
    news_articles: List[Dict[str, Any]] = field(default_factory=list)
    research_papers: List[Dict[str, Any]] = field(default_factory=list)
    satellite_images: List[Dict[str, Any]] = field(default_factory=list)
    social_media_posts: List[Dict[str, Any]] = field(default_factory=list)
    government_documents: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ContextTensor:
    """Complete context tensor for an H3 cell"""
    h3_index: str
    timestamp: datetime
    dimensions: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize dimensions"""
        if not self.dimensions:
            self.dimensions = {
                'climate': ClimateDimension(),
                'geography': GeographyDimension(),
                'socioeconomic': SocioeconomicDimension(),
                'infrastructure': InfrastructureDimension(),
                'vulnerability': VulnerabilityDimension(),
                'unstructured': UnstructuredDataDimension()
            }


class ContextTensorEngine:
    """Engine for generating context tensors for H3 cells"""
    
    def __init__(self, config=None):
        """
        Initialize the Context Tensor Engine
        
        Args:
            config: Configuration object (optional)
        """
        self.config = config
        # Lazy import to avoid circular dependency
        self.h3_engine = None
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # API endpoints (will be configured via environment variables)
        self.copernicus_api_key = None  # Set via config
        self.noaa_api_key = None
        self.world_bank_base_url = "https://api.worldbank.org/v2"
        self.osm_overpass_url = "https://overpass-api.de/api/interpreter"
        
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
    
    async def generate_tensor_for_cell(
        self,
        h3_cell: Any,  # H3Cell - using Any to avoid circular import
        year: Optional[int] = None
    ) -> ContextTensor:
        """
        Generate a complete context tensor for a single H3 cell
        
        Args:
            h3_cell: H3Cell object
            year: Year for temporal data (default: current year)
        
        Returns:
            ContextTensor object
        """
        if year is None:
            year = datetime.now().year
        
        tensor = ContextTensor(
            h3_index=h3_cell.h3_index,
            timestamp=datetime.now()
        )
        
        # Generate all dimensions in parallel
        tasks = [
            self._fetch_climate_data(h3_cell, year),
            self._fetch_geography_data(h3_cell),
            self._fetch_socioeconomic_data(h3_cell, year),
            self._fetch_infrastructure_data(h3_cell),
            self._fetch_vulnerability_data(h3_cell, year),
            self._fetch_unstructured_data(h3_cell)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Assign results to tensor dimensions
        tensor.dimensions['climate'] = results[0] if not isinstance(results[0], Exception) else ClimateDimension()
        tensor.dimensions['geography'] = results[1] if not isinstance(results[1], Exception) else GeographyDimension()
        tensor.dimensions['socioeconomic'] = results[2] if not isinstance(results[2], Exception) else SocioeconomicDimension()
        tensor.dimensions['infrastructure'] = results[3] if not isinstance(results[3], Exception) else InfrastructureDimension()
        tensor.dimensions['vulnerability'] = results[4] if not isinstance(results[4], Exception) else VulnerabilityDimension()
        tensor.dimensions['unstructured'] = results[5] if not isinstance(results[5], Exception) else UnstructuredDataDimension()
        
        # Log any errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Error fetching dimension {i}: {result}")
        
        return tensor
    
    async def _fetch_climate_data(
        self,
        h3_cell: Any,  # H3Cell - using Any to avoid circular import
        year: int
    ) -> ClimateDimension:
        """
        Fetch climate data from Copernicus, NOAA, etc.
        
        Args:
            h3_cell: H3Cell object
            year: Year for data
        
        Returns:
            ClimateDimension object
        """
        # TODO: Integrate with Copernicus Climate Data Store API
        # TODO: Integrate with NOAA Gridded Data API
        # For now, return mock data structure
        
        # Placeholder: In production, this would call:
        # - Copernicus ERA5 API for temperature, precipitation
        # - NOAA API for extreme events
        # - Open-Meteo API as fallback
        
        return ClimateDimension(
            temp_mean=20.0,
            temp_max=25.0,
            temp_min=15.0,
            precipitation=100.0,
            extreme_events_frequency=0.1,
            extreme_events_intensity=0.5,
            air_quality_pm25=15.0,
            air_quality_ozone=50.0,
            soil_moisture=0.5
        )
    
    async def _fetch_geography_data(self, h3_cell: Any) -> GeographyDimension:
        """
        Fetch geography and land use data
        
        Args:
            h3_cell: H3Cell object
        
        Returns:
            GeographyDimension object
        """
        # TODO: Integrate with:
        # - USGS ASTER/SRTM DEM for elevation
        # - ESA WorldCover for land cover
        # - Copernicus Global Land Service
        
        # Placeholder implementation
        return GeographyDimension(
            elevation=100.0,
            slope=5.0,
            land_cover_class='Urban',
            coastal_proximity=50.0,
            water_body=False
        )
    
    async def _fetch_socioeconomic_data(
        self,
        h3_cell: Any,  # H3Cell - using Any to avoid circular import
        year: int
    ) -> SocioeconomicDimension:
        """
        Fetch socioeconomic data from World Bank, GPW, etc.
        
        Args:
            h3_cell: H3Cell object
            year: Year for data
        
        Returns:
            SocioeconomicDimension object
        """
        # TODO: Integrate with:
        # - World Bank Open Data API
        # - Gridded Population of the World (GPW)
        # - Facebook Marketing API (for proxies)
        
        # Placeholder implementation
        return SocioeconomicDimension(
            population_density=1000.0,
            gdp_per_capita=50000.0,
            poverty_rate=10.0,
            education_level=80.0,
            unemployment_rate=5.0
        )
    
    async def _fetch_infrastructure_data(self, h3_cell: Any) -> InfrastructureDimension:
        """
        Fetch infrastructure data from OpenStreetMap, etc.
        
        Args:
            h3_cell: H3Cell object
        
        Returns:
            InfrastructureDimension object
        """
        # TODO: Integrate with:
        # - OpenStreetMap Overpass API for roads, hospitals
        # - Government inventories for energy infrastructure
        # - Global datasets for water infrastructure
        
        try:
            # Example Overpass API query for roads in H3 cell
            # This is a simplified version - full implementation would query OSM
            pass
        except Exception as e:
            logger.warning(f"Error fetching infrastructure data: {e}")
        
        # Placeholder implementation
        return InfrastructureDimension(
            road_density=5.0,
            hospital_proximity=10.0,
            energy_infrastructure=0.7,
            water_infrastructure=0.8
        )
    
    async def _fetch_vulnerability_data(
        self,
        h3_cell: Any,  # H3Cell - using Any to avoid circular import
        year: int
    ) -> VulnerabilityDimension:
        """
        Fetch vulnerability and adaptive capacity data
        
        Args:
            h3_cell: H3Cell object
            year: Year for data
        
        Returns:
            VulnerabilityDimension object
        """
        # TODO: Integrate with:
        # - World Bank GovData360
        # - Notre Dame Global Adaptation Initiative (ND-GAIN)
        # - Research datasets
        
        # Placeholder implementation
        return VulnerabilityDimension(
            social_vulnerability_index=0.5,
            governance_quality=0.7,
            financial_access=0.6,
            health_system_quality=0.75
        )
    
    async def _fetch_unstructured_data(self, h3_cell: Any) -> UnstructuredDataDimension:
        """
        Fetch unstructured data using Firecrawl, crawl4ai, etc.
        
        Args:
            h3_cell: H3Cell object
        
        Returns:
            UnstructuredDataDimension object
        """
        # TODO: Integrate with:
        # - Firecrawl for web scraping
        # - crawl4ai for intelligent crawling
        # - Google Scholar / ArXiv API for research papers
        # - Social Media APIs / GDELT Project
        
        # Placeholder implementation
        return UnstructuredDataDimension(
            news_articles=[],
            research_papers=[],
            satellite_images=[],
            social_media_posts=[],
            government_documents=[]
        )
    
    async def generate_tensors_for_grid(
        self,
        h3_grid: Any,  # H3Grid from h3_grid_engine - using Any to avoid circular import
        year: Optional[int] = None
    ) -> List[ContextTensor]:
        """
        Generate context tensors for all cells in a grid
        
        Args:
            h3_grid: H3Grid object
            year: Year for temporal data
        
        Returns:
            List of ContextTensor objects
        """
        tasks = [
            self.generate_tensor_for_cell(cell, year)
            for cell in h3_grid.cells
        ]
        
        # Process in batches to avoid overwhelming APIs
        batch_size = 10
        all_tensors = []
        
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            results = await asyncio.gather(*batch, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error generating tensor: {result}")
                else:
                    all_tensors.append(result)
            
            # Small delay between batches
            await asyncio.sleep(0.5)
        
        return all_tensors
    
    def aggregate_raster_data(
        self,
        raster_data: List[Tuple[float, float, float]],  # (lat, lng, value)
        h3_cell: Any  # H3Cell - using Any to avoid circular import
    ) -> float:
        """
        Aggregate raster data for an H3 cell (average, majority, etc.)
        
        Args:
            raster_data: List of (lat, lng, value) tuples
            h3_cell: H3Cell object
        
        Returns:
            Aggregated value (average)
        """
        # Get all points within H3 cell boundary
        cell_points = [
            (lat, lng, value)
            for lat, lng, value in raster_data
            if self._point_in_polygon(lat, lng, h3_cell.boundary)
        ]
        
        if not cell_points:
            return 0.0
        
        # Return average value
        return sum(value for _, _, value in cell_points) / len(cell_points)
    
    def _point_in_polygon(
        self,
        lat: float,
        lng: float,
        polygon: List[Tuple[float, float]]
    ) -> bool:
        """
        Check if a point is inside a polygon (ray casting algorithm)
        
        Args:
            lat: Latitude
            lng: Longitude
            polygon: List of (lat, lng) tuples
        
        Returns:
            True if point is inside polygon
        """
        n = len(polygon)
        inside = False
        
        p1_lat, p1_lng = polygon[0]
        for i in range(1, n + 1):
            p2_lat, p2_lng = polygon[i % n]
            if lng > min(p1_lng, p2_lng):
                if lng <= max(p1_lng, p2_lng):
                    if lat <= max(p1_lat, p2_lat):
                        if p1_lng != p2_lng:
                            xinters = (lng - p1_lng) * (p2_lat - p1_lat) / (p2_lng - p1_lng) + p1_lat
                        if p1_lat == p2_lat or lat <= xinters:
                            inside = not inside
            p1_lat, p1_lng = p2_lat, p2_lng
        
        return inside


# Example usage
if __name__ == '__main__':
    async def main():
        engine = ContextTensorEngine()
        
        # Create H3 grid
        h3_engine = H3GridEngine()
        grid = h3_engine.generate_grid(
            center_lat=-6.2088,
            center_lng=106.8456,
            scale='city',
            region_name='Jakarta'
        )
        
        # Generate tensor for first cell
        tensor = await engine.generate_tensor_for_cell(grid.cells[0])
        print(f"Generated tensor for H3 cell: {tensor.h3_index}")
        print(f"Climate temp_mean: {tensor.dimensions['climate'].temp_mean}")
        print(f"Geography elevation: {tensor.dimensions['geography'].elevation}")
        
        await engine.close()
    
    asyncio.run(main())

