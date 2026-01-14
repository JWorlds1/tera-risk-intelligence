"""
TERA Pydantic Models
Strict type validation for all data structures
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


# =============================================================================
# Enums
# =============================================================================

class EventType(str, Enum):
    FLOOD = "flood"
    DROUGHT = "drought"
    CONFLICT = "conflict"
    HEATWAVE = "heatwave"
    STORM = "storm"
    WILDFIRE = "wildfire"
    EARTHQUAKE = "earthquake"
    FAMINE = "famine"


class Scenario(str, Enum):
    SSP1_26 = "SSP1-2.6"
    SSP2_45 = "SSP2-4.5"
    SSP3_70 = "SSP3-7.0"
    SSP5_85 = "SSP5-8.5"
    BASELINE = "baseline"


class AdminLevel(int, Enum):
    COUNTRY = 0
    STATE = 1
    CITY = 2


# =============================================================================
# Geometry Models
# =============================================================================

class Coordinates(BaseModel):
    """WGS84 coordinates"""
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class BoundingBox(BaseModel):
    """Geographic bounding box"""
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float


class GeoJSONPoint(BaseModel):
    """GeoJSON Point"""
    type: str = "Point"
    coordinates: List[float]  # [lon, lat]


class GeoJSONPolygon(BaseModel):
    """GeoJSON Polygon"""
    type: str = "Polygon"
    coordinates: List[List[List[float]]]


class GeoJSONFeature(BaseModel):
    """GeoJSON Feature"""
    type: str = "Feature"
    geometry: Dict[str, Any]
    properties: Dict[str, Any] = {}


class GeoJSONFeatureCollection(BaseModel):
    """GeoJSON FeatureCollection"""
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]


# =============================================================================
# Article & Extraction Models
# =============================================================================

class ArticleBase(BaseModel):
    """Base article model"""
    source: str
    url: str
    title: Optional[str] = None
    content: Optional[str] = None
    publish_date: Optional[datetime] = None


class ArticleCreate(ArticleBase):
    """Article creation model"""
    pass


class Article(ArticleBase):
    """Full article model"""
    id: UUID
    summary: Optional[str] = None
    scraped_at: datetime
    processed: bool = False
    metadata: Dict[str, Any] = {}

    class Config:
        from_attributes = True


class LLMExtractionRequest(BaseModel):
    """Request to LLM for entity extraction"""
    text: str = Field(..., min_length=10)
    max_entities: int = Field(default=10, ge=1, le=50)


class ExtractedEntity(BaseModel):
    """Entity extracted by LLM"""
    location: str
    coordinates: Optional[Coordinates] = None
    event_type: EventType
    severity: int = Field(..., ge=1, le=10)
    confidence: float = Field(..., ge=0, le=1)
    summary: Optional[str] = None


class LLMExtractionResponse(BaseModel):
    """Response from LLM extraction"""
    entities: List[ExtractedEntity]
    raw_response: Optional[str] = None
    processing_time_ms: int


# =============================================================================
# Risk Models
# =============================================================================

class RiskScores(BaseModel):
    """Risk score breakdown"""
    total_risk: float = Field(..., ge=0, le=100)
    hazard: float = Field(..., ge=0, le=100)
    exposure: float = Field(..., ge=0, le=100)
    vulnerability: float = Field(..., ge=0, le=100)


class ContextTensor(BaseModel):
    """Multidimensional context tensor for H3 cells"""
    
    class ClimateData(BaseModel):
        temperature_anomaly: float = 0
        precipitation_change: float = 0
        sea_level_rise: float = 0
        extreme_events_frequency: float = 0
    
    class GeographyData(BaseModel):
        elevation: float = 0
        land_use: str = "Unknown"
        water_body: bool = False
        coastal: bool = False
    
    class SocioEconData(BaseModel):
        population_density: float = 0
        gdp_per_capita: float = 0
        poverty_rate: float = 0
    
    class InfrastructureData(BaseModel):
        road_density: float = 0
        hospital_access: float = 0
        shelter_capacity: float = 0
    
    class VulnerabilityData(BaseModel):
        governance_index: float = 50
        adaptation_capacity: float = 50
        historical_events: int = 0
    
    climate: ClimateData = ClimateData()
    geography: GeographyData = GeographyData()
    socio: SocioEconData = SocioEconData()
    infrastructure: InfrastructureData = InfrastructureData()
    vulnerability: VulnerabilityData = VulnerabilityData()
    scores: RiskScores = RiskScores(total_risk=0, hazard=0, exposure=0, vulnerability=0)


class H3Cell(BaseModel):
    """H3 hexagonal cell with risk data"""
    h3_index: str
    resolution: int = Field(..., ge=0, le=15)
    centroid: Coordinates
    boundary: List[Coordinates]
    tensor: ContextTensor
    actions: List[Dict[str, Any]] = []


class RegionRisk(BaseModel):
    """Risk assessment for an administrative region"""
    region_id: UUID
    region_name: str
    admin_level: AdminLevel
    geometry: GeoJSONPolygon
    risk_scores: RiskScores
    scenario: Scenario
    year: int
    contributing_events: List[str] = []
    generated_image_url: Optional[str] = None


# =============================================================================
# API Request/Response Models
# =============================================================================

class AnalyzeRequest(BaseModel):
    """Request for context space analysis"""
    region_name: str
    year_offset: int = Field(default=0, ge=0, le=80)
    scenario: Scenario = Scenario.SSP2_45
    scale: str = Field(default="city", pattern="^(neighborhood|city|region)$")
    resolution: Optional[int] = None  # H3 resolution override


class AnalyzeResponse(BaseModel):
    """Response from context space analysis"""
    region_name: str
    year: int
    scenario: Scenario
    scale: str
    grid_center: Coordinates
    cells: List[H3Cell]
    global_stats: Dict[str, Any]


class ScrapingStatus(BaseModel):
    """Status of scraping task"""
    task_id: str
    status: str
    progress: float = Field(..., ge=0, le=100)
    articles_scraped: int = 0
    errors: List[str] = []


class HealthCheck(BaseModel):
    """System health check response"""
    status: str
    version: str
    services: Dict[str, bool]
    timestamp: datetime

