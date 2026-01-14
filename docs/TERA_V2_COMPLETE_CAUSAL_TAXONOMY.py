"""
TERA V2: Vollständige Kausal-Taxonomie
========================================

Dieses Modul definiert ALLE bekannten primären Treiber, die zu 
Extremwetterereignissen führen können, und ihre kausalen Verbindungen.

Struktur:
---------
1. PRIMÄRE TREIBER (Externe Antriebe / Root Causes)
   └── Tektonisch, Solar, Orbital, Anthropogen

2. SYSTEM-KOMPONENTEN (Was wird beeinflusst)
   └── Atmosphäre, Ozean, Kryosphäre, Biosphäre, Lithosphäre

3. ÜBERTRAGUNGSMECHANISMEN (Wie werden Effekte weitergegeben)
   └── Strahlung, Advektion, Konvektion, Rückkopplungen

4. KLIMA-MODI (Emergente Muster)
   └── ENSO, AMO, PDO, NAO, IOD, MJO, ...

5. REGIONALE EFFEKTE (Telekonnektion)
   └── Was passiert wo als Folge?

6. EXTREMEREIGNISSE (Finale Outputs)
   └── Flut, Dürre, Sturm, Feuer, Hitze, Kälte, ...

Ziel: Für JEDES Extremereignis den vollständigen kausalen Graphen
von der Wurzel bis zum Ereignis nachvollziehbar machen.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple
from enum import Enum, auto
import json


# ═══════════════════════════════════════════════════════════════════════════════
# TEIL 1: PRIMÄRE TREIBER (Root Causes / Externe Antriebe)
# ═══════════════════════════════════════════════════════════════════════════════

class PrimaryDriverCategory(Enum):
    """Kategorien von primären Treibern."""
    TECTONIC = "tectonic"           # Plattentektonik
    SOLAR = "solar"                 # Sonnenaktivität
    ORBITAL = "orbital"             # Erdbahnparameter
    VOLCANIC = "volcanic"           # Vulkanismus
    OCEANIC = "oceanic"             # Ozeandynamik
    ATMOSPHERIC = "atmospheric"     # Atmosphärendynamik
    ANTHROPOGENIC = "anthropogenic" # Menschlicher Einfluss
    BIOSPHERIC = "biospheric"       # Biosphäre
    CRYOSPHERIC = "cryospheric"     # Eisschilde/Gletscher
    EXTRATERRESTRIAL = "extraterrestrial"  # Kosmische Einflüsse


@dataclass
class PrimaryDriver:
    """Ein primärer Treiber im Klimasystem."""
    id: str
    name: str
    category: PrimaryDriverCategory
    description: str
    timescale: str  # "seconds", "hours", "days", "months", "years", "decades", "millennia"
    predictability: float  # 0-1 wie gut vorhersagbar
    data_sources: List[str]
    current_state_indicators: List[str]
    
    def __hash__(self):
        return hash(self.id)


# Alle bekannten primären Treiber
PRIMARY_DRIVERS = {
    # ═══════════════════════════════════════════════════════════════════════
    # TEKTONISCHE TREIBER
    # ═══════════════════════════════════════════════════════════════════════
    
    "PLATE_TECTONICS": PrimaryDriver(
        id="PLATE_TECTONICS",
        name="Plattentektonik",
        category=PrimaryDriverCategory.TECTONIC,
        description="Bewegung der tektonischen Platten, verursacht Erdbeben und Gebirgsbildung",
        timescale="millennia",
        predictability=0.1,
        data_sources=["USGS", "GeoFon", "IRIS"],
        current_state_indicators=["earthquake_rate", "plate_velocity", "stress_accumulation"]
    ),
    
    "EARTHQUAKE": PrimaryDriver(
        id="EARTHQUAKE",
        name="Erdbeben",
        category=PrimaryDriverCategory.TECTONIC,
        description="Plötzliche Freisetzung tektonischer Spannung",
        timescale="seconds",
        predictability=0.05,
        data_sources=["USGS Earthquake Catalog", "GeoFon", "EMSC"],
        current_state_indicators=["magnitude", "depth", "epicenter", "aftershock_sequence"]
    ),
    
    "SEAFLOOR_SPREADING": PrimaryDriver(
        id="SEAFLOOR_SPREADING",
        name="Ozeanbodenspreizung",
        category=PrimaryDriverCategory.TECTONIC,
        description="Ausbreitung des Meeresbodens an mittelozeanischen Rücken",
        timescale="millennia",
        predictability=0.2,
        data_sources=["NOAA Ocean Explorer", "Research Vessels"],
        current_state_indicators=["spreading_rate", "hydrothermal_activity"]
    ),
    
    # ═══════════════════════════════════════════════════════════════════════
    # VULKANISCHE TREIBER
    # ═══════════════════════════════════════════════════════════════════════
    
    "VOLCANIC_ERUPTION": PrimaryDriver(
        id="VOLCANIC_ERUPTION",
        name="Vulkanausbruch",
        category=PrimaryDriverCategory.VOLCANIC,
        description="Eruption von Magma, Asche und Gasen",
        timescale="hours",
        predictability=0.3,
        data_sources=["Smithsonian GVP", "USGS Volcano Hazards", "VAAC"],
        current_state_indicators=["VEI", "SO2_emission", "ash_column_height", "lava_volume"]
    ),
    
    "VOLCANIC_DEGASSING": PrimaryDriver(
        id="VOLCANIC_DEGASSING",
        name="Vulkanische Entgasung",
        category=PrimaryDriverCategory.VOLCANIC,
        description="Kontinuierliche Freisetzung von Gasen (CO2, SO2, H2S)",
        timescale="years",
        predictability=0.4,
        data_sources=["NOVAC", "TROPOMI", "OMI"],
        current_state_indicators=["SO2_flux", "CO2_flux", "deformation"]
    ),
    
    "SUPERVOLCANO": PrimaryDriver(
        id="SUPERVOLCANO",
        name="Supervulkan",
        category=PrimaryDriverCategory.VOLCANIC,
        description="Eruption mit VEI≥8, globale Auswirkungen",
        timescale="millennia",
        predictability=0.01,
        data_sources=["Smithsonian GVP", "Caldera Monitoring"],
        current_state_indicators=["caldera_deformation", "seismicity", "gas_emissions"]
    ),
    
    # ═══════════════════════════════════════════════════════════════════════
    # SOLARE TREIBER
    # ═══════════════════════════════════════════════════════════════════════
    
    "SOLAR_IRRADIANCE": PrimaryDriver(
        id="SOLAR_IRRADIANCE",
        name="Solare Einstrahlung",
        category=PrimaryDriverCategory.SOLAR,
        description="Variation der Sonnenenergie (11-Jahres-Zyklus)",
        timescale="years",
        predictability=0.7,
        data_sources=["SOHO", "SDO", "SORCE", "TSIS"],
        current_state_indicators=["TSI", "sunspot_number", "F10.7_index"]
    ),
    
    "SOLAR_FLARE": PrimaryDriver(
        id="SOLAR_FLARE",
        name="Sonneneruption",
        category=PrimaryDriverCategory.SOLAR,
        description="Plötzliche Energiefreisetzung in der Sonnenkorona",
        timescale="hours",
        predictability=0.3,
        data_sources=["NOAA SWPC", "SDO", "GOES"],
        current_state_indicators=["X-ray_flux", "proton_flux", "CME_velocity"]
    ),
    
    "GEOMAGNETIC_STORM": PrimaryDriver(
        id="GEOMAGNETIC_STORM",
        name="Geomagnetischer Sturm",
        category=PrimaryDriverCategory.SOLAR,
        description="Störung des Erdmagnetfelds durch Sonnenwind",
        timescale="hours",
        predictability=0.5,
        data_sources=["NOAA SWPC", "USGS Geomagnetism"],
        current_state_indicators=["Kp_index", "Dst_index", "auroral_boundary"]
    ),
    
    # ═══════════════════════════════════════════════════════════════════════
    # ORBITALE TREIBER (Milankovitch-Zyklen)
    # ═══════════════════════════════════════════════════════════════════════
    
    "ORBITAL_ECCENTRICITY": PrimaryDriver(
        id="ORBITAL_ECCENTRICITY",
        name="Orbitale Exzentrizität",
        category=PrimaryDriverCategory.ORBITAL,
        description="Variation der Elliptizität der Erdbahn (100.000 Jahre Zyklus)",
        timescale="millennia",
        predictability=0.99,
        data_sources=["Astronomical Calculations"],
        current_state_indicators=["eccentricity_value"]
    ),
    
    "AXIAL_TILT": PrimaryDriver(
        id="AXIAL_TILT",
        name="Achsneigung (Obliquität)",
        category=PrimaryDriverCategory.ORBITAL,
        description="Variation der Erdachsenneigung (41.000 Jahre Zyklus)",
        timescale="millennia",
        predictability=0.99,
        data_sources=["Astronomical Calculations"],
        current_state_indicators=["obliquity_degrees"]
    ),
    
    "PRECESSION": PrimaryDriver(
        id="PRECESSION",
        name="Präzession",
        category=PrimaryDriverCategory.ORBITAL,
        description="Kreiselbewegung der Erdachse (26.000 Jahre Zyklus)",
        timescale="millennia",
        predictability=0.99,
        data_sources=["Astronomical Calculations"],
        current_state_indicators=["precession_angle"]
    ),
    
    # ═══════════════════════════════════════════════════════════════════════
    # OZEANISCHE TREIBER
    # ═══════════════════════════════════════════════════════════════════════
    
    "THERMOHALINE_CIRCULATION": PrimaryDriver(
        id="THERMOHALINE_CIRCULATION",
        name="Thermohaline Zirkulation",
        category=PrimaryDriverCategory.OCEANIC,
        description="Globale Ozeanzirkulation angetrieben durch Dichte-Unterschiede",
        timescale="decades",
        predictability=0.4,
        data_sources=["ARGO", "RAPID Array", "OSNAP"],
        current_state_indicators=["AMOC_strength", "deep_water_formation", "meridional_heat_transport"]
    ),
    
    "OCEAN_HEAT_CONTENT": PrimaryDriver(
        id="OCEAN_HEAT_CONTENT",
        name="Ozean-Wärmeinhalt",
        category=PrimaryDriverCategory.OCEANIC,
        description="Gespeicherte thermische Energie im Ozean",
        timescale="years",
        predictability=0.6,
        data_sources=["ARGO", "XBT", "NOAA NODC"],
        current_state_indicators=["OHC_0-700m", "OHC_0-2000m", "thermosteric_sea_level"]
    ),
    
    "UPWELLING": PrimaryDriver(
        id="UPWELLING",
        name="Auftrieb (Upwelling)",
        category=PrimaryDriverCategory.OCEANIC,
        description="Aufsteigen von kaltem, nährstoffreichem Tiefenwasser",
        timescale="months",
        predictability=0.6,
        data_sources=["Satellite SST", "Chlorophyll", "Coastal Stations"],
        current_state_indicators=["SST_anomaly", "chlorophyll_concentration", "wind_stress"]
    ),
    
    "SEA_SURFACE_TEMPERATURE": PrimaryDriver(
        id="SEA_SURFACE_TEMPERATURE",
        name="Meeresoberflächentemperatur (SST)",
        category=PrimaryDriverCategory.OCEANIC,
        description="Temperatur der obersten Ozeanschicht",
        timescale="days",
        predictability=0.7,
        data_sources=["NOAA OISST", "ERSST", "AVHRR", "MODIS"],
        current_state_indicators=["SST", "SST_anomaly", "marine_heatwave_days"]
    ),
    
    "OCEAN_SALINITY": PrimaryDriver(
        id="OCEAN_SALINITY",
        name="Ozean-Salinität",
        category=PrimaryDriverCategory.OCEANIC,
        description="Salzgehalt des Meerwassers, beeinflusst Dichte und Zirkulation",
        timescale="months",
        predictability=0.5,
        data_sources=["ARGO", "SMOS", "Aquarius"],
        current_state_indicators=["salinity", "freshwater_flux"]
    ),
    
    # ═══════════════════════════════════════════════════════════════════════
    # ATMOSPHÄRISCHE TREIBER
    # ═══════════════════════════════════════════════════════════════════════
    
    "JET_STREAM": PrimaryDriver(
        id="JET_STREAM",
        name="Jetstream",
        category=PrimaryDriverCategory.ATMOSPHERIC,
        description="Schnelle Höhenwinde in der oberen Troposphäre",
        timescale="days",
        predictability=0.6,
        data_sources=["ECMWF", "GFS", "Radiosondes"],
        current_state_indicators=["jet_position", "jet_speed", "waviness"]
    ),
    
    "POLAR_VORTEX": PrimaryDriver(
        id="POLAR_VORTEX",
        name="Polarwirbel",
        category=PrimaryDriverCategory.ATMOSPHERIC,
        description="Tiefdruckgebiet über den Polarregionen",
        timescale="days",
        predictability=0.5,
        data_sources=["ECMWF", "GFS", "Radiosonde"],
        current_state_indicators=["vortex_strength", "stratospheric_temperature", "SSW_events"]
    ),
    
    "HADLEY_CELL": PrimaryDriver(
        id="HADLEY_CELL",
        name="Hadley-Zelle",
        category=PrimaryDriverCategory.ATMOSPHERIC,
        description="Tropische atmosphärische Zirkulation",
        timescale="months",
        predictability=0.7,
        data_sources=["Reanalysis Data", "Satellite"],
        current_state_indicators=["ITCZ_position", "trade_wind_strength", "subtropical_high_strength"]
    ),
    
    "MONSOON_SYSTEM": PrimaryDriver(
        id="MONSOON_SYSTEM",
        name="Monsun-System",
        category=PrimaryDriverCategory.ATMOSPHERIC,
        description="Saisonale Umkehr der Windrichtung durch Land-Meer-Kontrast",
        timescale="months",
        predictability=0.6,
        data_sources=["IMD", "ECMWF", "CPC"],
        current_state_indicators=["monsoon_onset", "rainfall_anomaly", "wind_reversal"]
    ),
    
    "ATMOSPHERIC_BLOCKING": PrimaryDriver(
        id="ATMOSPHERIC_BLOCKING",
        name="Atmosphärische Blockierung",
        category=PrimaryDriverCategory.ATMOSPHERIC,
        description="Stationäre Hochdruckgebiete, die normale Westwinddrift blockieren",
        timescale="days",
        predictability=0.4,
        data_sources=["ECMWF", "GFS"],
        current_state_indicators=["blocking_index", "persistence", "amplitude"]
    ),
    
    "STRATOSPHERIC_WARMING": PrimaryDriver(
        id="STRATOSPHERIC_WARMING",
        name="Stratosphärische Erwärmung (SSW)",
        category=PrimaryDriverCategory.ATMOSPHERIC,
        description="Plötzliche Erwärmung der Stratosphäre, schwächt Polarwirbel",
        timescale="days",
        predictability=0.3,
        data_sources=["ECMWF", "Radiosondes", "MLS"],
        current_state_indicators=["stratospheric_temperature", "wind_reversal", "NAM_index"]
    ),
    
    # ═══════════════════════════════════════════════════════════════════════
    # KRYOSPHÄRISCHE TREIBER
    # ═══════════════════════════════════════════════════════════════════════
    
    "SEA_ICE_EXTENT": PrimaryDriver(
        id="SEA_ICE_EXTENT",
        name="Meereis-Ausdehnung",
        category=PrimaryDriverCategory.CRYOSPHERIC,
        description="Fläche des arktischen/antarktischen Meereises",
        timescale="months",
        predictability=0.6,
        data_sources=["NSIDC", "OSI-SAF", "JAXA"],
        current_state_indicators=["sea_ice_extent", "sea_ice_area", "ice_age"]
    ),
    
    "ICE_SHEET_DYNAMICS": PrimaryDriver(
        id="ICE_SHEET_DYNAMICS",
        name="Eisschild-Dynamik",
        category=PrimaryDriverCategory.CRYOSPHERIC,
        description="Bewegung und Schmelze von Grönland/Antarktis",
        timescale="years",
        predictability=0.5,
        data_sources=["GRACE", "ICESat-2", "Sentinel-1"],
        current_state_indicators=["mass_balance", "ice_velocity", "calving_rate"]
    ),
    
    "PERMAFROST_THAW": PrimaryDriver(
        id="PERMAFROST_THAW",
        name="Permafrost-Auftauen",
        category=PrimaryDriverCategory.CRYOSPHERIC,
        description="Schmelzen von dauerhaft gefrorenem Boden",
        timescale="years",
        predictability=0.5,
        data_sources=["GTN-P", "ESA CCI", "In-situ"],
        current_state_indicators=["active_layer_thickness", "ground_temperature", "methane_emissions"]
    ),
    
    "GLACIER_RETREAT": PrimaryDriver(
        id="GLACIER_RETREAT",
        name="Gletscherrückzug",
        category=PrimaryDriverCategory.CRYOSPHERIC,
        description="Schmelzen und Rückzug von Bergletschern",
        timescale="years",
        predictability=0.6,
        data_sources=["WGMS", "GLIMS", "Sentinel-2"],
        current_state_indicators=["terminus_position", "mass_balance", "ELA"]
    ),
    
    # ═══════════════════════════════════════════════════════════════════════
    # BIOSPHÄRISCHE TREIBER
    # ═══════════════════════════════════════════════════════════════════════
    
    "VEGETATION_CHANGE": PrimaryDriver(
        id="VEGETATION_CHANGE",
        name="Vegetationsänderung",
        category=PrimaryDriverCategory.BIOSPHERIC,
        description="Änderungen in Vegetationsbedeckung (Abholzung, Wüstenbildung)",
        timescale="years",
        predictability=0.5,
        data_sources=["MODIS NDVI", "Landsat", "ESA CCI LC"],
        current_state_indicators=["NDVI", "LAI", "forest_cover", "desertification_index"]
    ),
    
    "CARBON_CYCLE": PrimaryDriver(
        id="CARBON_CYCLE",
        name="Kohlenstoffzyklus",
        category=PrimaryDriverCategory.BIOSPHERIC,
        description="Austausch von CO2 zwischen Atmosphäre, Ozean und Land",
        timescale="years",
        predictability=0.6,
        data_sources=["NOAA ESRL", "OCO-2", "FLUXNET"],
        current_state_indicators=["CO2_concentration", "carbon_flux", "ocean_uptake"]
    ),
    
    "METHANE_EMISSIONS": PrimaryDriver(
        id="METHANE_EMISSIONS",
        name="Methan-Emissionen",
        category=PrimaryDriverCategory.BIOSPHERIC,
        description="Freisetzung von CH4 aus Feuchtgebieten, Permafrost, Landwirtschaft",
        timescale="years",
        predictability=0.4,
        data_sources=["NOAA ESRL", "TROPOMI", "GOSAT"],
        current_state_indicators=["CH4_concentration", "wetland_emissions", "permafrost_emissions"]
    ),
    
    # ═══════════════════════════════════════════════════════════════════════
    # ANTHROPOGENE TREIBER
    # ═══════════════════════════════════════════════════════════════════════
    
    "GREENHOUSE_GAS_FORCING": PrimaryDriver(
        id="GREENHOUSE_GAS_FORCING",
        name="Treibhausgas-Antrieb",
        category=PrimaryDriverCategory.ANTHROPOGENIC,
        description="Strahlungsantrieb durch CO2, CH4, N2O, etc.",
        timescale="years",
        predictability=0.8,
        data_sources=["NOAA ESRL", "IPCC", "GCP"],
        current_state_indicators=["CO2_ppm", "radiative_forcing", "emission_rate"]
    ),
    
    "AEROSOL_FORCING": PrimaryDriver(
        id="AEROSOL_FORCING",
        name="Aerosol-Antrieb",
        category=PrimaryDriverCategory.ANTHROPOGENIC,
        description="Kühlender Effekt durch anthropogene Aerosole",
        timescale="days",
        predictability=0.5,
        data_sources=["AERONET", "MODIS", "CAMS"],
        current_state_indicators=["AOD", "aerosol_forcing", "sulfate_emissions"]
    ),
    
    "LAND_USE_CHANGE": PrimaryDriver(
        id="LAND_USE_CHANGE",
        name="Landnutzungsänderung",
        category=PrimaryDriverCategory.ANTHROPOGENIC,
        description="Umwandlung von Wäldern, Urbanisierung, Landwirtschaft",
        timescale="years",
        predictability=0.6,
        data_sources=["ESA CCI LC", "FAO", "Hansen GFC"],
        current_state_indicators=["deforestation_rate", "urban_expansion", "agricultural_area"]
    ),
    
    "URBANIZATION": PrimaryDriver(
        id="URBANIZATION",
        name="Urbanisierung",
        category=PrimaryDriverCategory.ANTHROPOGENIC,
        description="Städtewachstum mit Wärmeinseleffekt und verändertem Wasserkreislauf",
        timescale="years",
        predictability=0.7,
        data_sources=["WorldPop", "GHSL", "Nightlights"],
        current_state_indicators=["urban_extent", "population_density", "UHI_intensity"]
    ),
    
    "WATER_MANAGEMENT": PrimaryDriver(
        id="WATER_MANAGEMENT",
        name="Wassermanagement",
        category=PrimaryDriverCategory.ANTHROPOGENIC,
        description="Staudämme, Bewässerung, Grundwasserentnahme",
        timescale="years",
        predictability=0.7,
        data_sources=["GRACE", "GRanD", "FAO Aquastat"],
        current_state_indicators=["reservoir_storage", "irrigation_area", "groundwater_depletion"]
    ),
    
    # ═══════════════════════════════════════════════════════════════════════
    # EXTRATERRESTRISCHE TREIBER
    # ═══════════════════════════════════════════════════════════════════════
    
    "COSMIC_RAY_FLUX": PrimaryDriver(
        id="COSMIC_RAY_FLUX",
        name="Kosmische Strahlung",
        category=PrimaryDriverCategory.EXTRATERRESTRIAL,
        description="Hochenergetische Teilchen aus dem Weltall (moduliert durch Sonne)",
        timescale="years",
        predictability=0.6,
        data_sources=["Moscow Neutron Monitor", "NMDB"],
        current_state_indicators=["neutron_count", "muon_flux"]
    ),
    
    "ASTEROID_IMPACT": PrimaryDriver(
        id="ASTEROID_IMPACT",
        name="Asteroideneinschlag",
        category=PrimaryDriverCategory.EXTRATERRESTRIAL,
        description="Kollision mit Asteroiden/Kometen (extrem selten, katastrophal)",
        timescale="millennia",
        predictability=0.7,  # NEO-Überwachung ist gut
        data_sources=["NASA CNEOS", "ESA SSA", "Minor Planet Center"],
        current_state_indicators=["NEO_catalog", "close_approach_probability"]
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# TEIL 2: EXTREMEREIGNISSE (Finale Outputs)
# ═══════════════════════════════════════════════════════════════════════════════

class ExtremeEvent(Enum):
    """Alle möglichen Extremereignisse."""
    # Hydrologisch
    FLOOD_RIVER = "flood_river"
    FLOOD_COASTAL = "flood_coastal"
    FLOOD_FLASH = "flood_flash"
    FLOOD_PLUVIAL = "flood_pluvial"
    
    # Dürre
    DROUGHT_METEOROLOGICAL = "drought_meteorological"
    DROUGHT_AGRICULTURAL = "drought_agricultural"
    DROUGHT_HYDROLOGICAL = "drought_hydrological"
    
    # Stürme
    TROPICAL_CYCLONE = "tropical_cyclone"
    EXTRATROPICAL_STORM = "extratropical_storm"
    TORNADO = "tornado"
    DERECHO = "derecho"
    HAILSTORM = "hailstorm"
    THUNDERSTORM = "thunderstorm"
    
    # Temperatur
    HEAT_WAVE = "heat_wave"
    COLD_WAVE = "cold_wave"
    FROST = "frost"
    
    # Feuer
    WILDFIRE = "wildfire"
    PEAT_FIRE = "peat_fire"
    
    # Tektonisch
    EARTHQUAKE = "earthquake"
    TSUNAMI = "tsunami"
    VOLCANIC_ERUPTION = "volcanic_eruption"
    LAHAR = "lahar"
    PYROCLASTIC_FLOW = "pyroclastic_flow"
    
    # Massenbewegungen
    LANDSLIDE = "landslide"
    DEBRIS_FLOW = "debris_flow"
    AVALANCHE = "avalanche"
    ROCKFALL = "rockfall"
    SUBSIDENCE = "subsidence"
    
    # Küsten
    STORM_SURGE = "storm_surge"
    COASTAL_EROSION = "coastal_erosion"
    SEA_LEVEL_RISE = "sea_level_rise"
    
    # Andere
    DUST_STORM = "dust_storm"
    SANDSTORM = "sandstorm"
    FOG = "fog"
    ICE_STORM = "ice_storm"
    BLIZZARD = "blizzard"


# ═══════════════════════════════════════════════════════════════════════════════
# TEIL 3: KAUSALE VERBINDUNGEN
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CausalLink:
    """Eine kausale Verbindung zwischen zwei Elementen."""
    source: str  # Driver ID oder Event
    target: str  # Driver ID oder Event
    mechanism: str  # Physikalische Erklärung
    strength: float  # 0-1 Stärke der Verbindung
    delay_typical: str  # Typische Verzögerung
    delay_range: Tuple[float, float]  # (min, max) in Tagen
    confidence: float  # Wissenschaftliche Sicherheit
    reversible: bool  # Ist die Wirkung umkehrbar?
    threshold: Optional[float] = None  # Schwellenwert für Aktivierung


# Der vollständige Kausal-Graph
CAUSAL_LINKS: List[CausalLink] = [
    
    # ═══════════════════════════════════════════════════════════════════════
    # TEKTONIK → EREIGNISSE
    # ═══════════════════════════════════════════════════════════════════════
    
    CausalLink(
        source="EARTHQUAKE",
        target="TSUNAMI",
        mechanism="Unterwasser-Erdbeben (M≥7.5) versetzt Wassersäule und erzeugt Wellenfront",
        strength=0.7,
        delay_typical="minutes",
        delay_range=(0.01, 0.5),  # Minuten bis Stunden
        confidence=0.95,
        reversible=False,
        threshold=7.5  # Magnitude
    ),
    
    CausalLink(
        source="EARTHQUAKE",
        target="LANDSLIDE",
        mechanism="Bodenerschütterung destabilisiert Hänge, besonders bei gesättigtem Boden",
        strength=0.6,
        delay_typical="seconds",
        delay_range=(0, 1),
        confidence=0.90,
        reversible=False,
        threshold=5.0
    ),
    
    CausalLink(
        source="EARTHQUAKE",
        target="VOLCANIC_ERUPTION",
        mechanism="Seismische Aktivität kann Magmakammer destabilisieren",
        strength=0.3,
        delay_typical="days to months",
        delay_range=(0, 365),
        confidence=0.60,
        reversible=False
    ),
    
    # ═══════════════════════════════════════════════════════════════════════
    # VULKANISMUS → EREIGNISSE
    # ═══════════════════════════════════════════════════════════════════════
    
    CausalLink(
        source="VOLCANIC_ERUPTION",
        target="EARTHQUAKE",
        mechanism="Magmabewegung und Druckentlastung verursachen vulkanische Erdbeben",
        strength=0.8,
        delay_typical="hours",
        delay_range=(0, 30),
        confidence=0.90,
        reversible=False
    ),
    
    CausalLink(
        source="VOLCANIC_ERUPTION",
        target="SEAFLOOR_SPREADING",
        mechanism="Unterseeische Eruption aktiviert Lavaströme und hydrothermale Systeme",
        strength=0.5,
        delay_typical="days",
        delay_range=(0, 60),
        confidence=0.70,
        reversible=False
    ),
    
    CausalLink(
        source="VOLCANIC_ERUPTION",
        target="SEA_SURFACE_TEMPERATURE",
        mechanism="1) Aerosole in Stratosphäre → Abkühlung, 2) Unterwasser-Wärme → lokale Erwärmung",
        strength=0.6,
        delay_typical="weeks to months",
        delay_range=(14, 365),
        confidence=0.80,
        reversible=True
    ),
    
    CausalLink(
        source="VOLCANIC_ERUPTION",
        target="PYROCLASTIC_FLOW",
        mechanism="Kollaps der Eruptionssäule oder Lavadome erzeugt heiße Gasströme",
        strength=0.9,
        delay_typical="minutes",
        delay_range=(0, 0.1),
        confidence=0.95,
        reversible=False,
        threshold=3  # VEI
    ),
    
    CausalLink(
        source="VOLCANIC_ERUPTION",
        target="LAHAR",
        mechanism="Schmelzen von Schnee/Eis oder Niederschlag mobilisiert vulkanische Asche",
        strength=0.7,
        delay_typical="hours to days",
        delay_range=(0.1, 30),
        confidence=0.85,
        reversible=False
    ),
    
    CausalLink(
        source="VOLCANIC_ERUPTION",
        target="DROUGHT_METEOROLOGICAL",
        mechanism="Stratosphärische Aerosole reduzieren Monsun und Niederschlag regional",
        strength=0.5,
        delay_typical="months",
        delay_range=(60, 365),
        confidence=0.70,
        reversible=True
    ),
    
    # ═══════════════════════════════════════════════════════════════════════
    # SST → KLIMA-MODI → EREIGNISSE
    # ═══════════════════════════════════════════════════════════════════════
    
    CausalLink(
        source="SEA_SURFACE_TEMPERATURE",
        target="ENSO",
        mechanism="Anhaltende SST-Anomalie im äquatorialen Pazifik definiert El Niño/La Niña",
        strength=0.9,
        delay_typical="weeks",
        delay_range=(14, 90),
        confidence=0.95,
        reversible=True,
        threshold=0.5  # °C Anomalie für 5 Monate
    ),
    
    CausalLink(
        source="ENSO_POSITIVE",  # El Niño
        target="FLOOD_RIVER",
        mechanism="Verstärkte Niederschläge in Peru/Ecuador durch warmes Küstenwasser",
        strength=0.8,
        delay_typical="months",
        delay_range=(60, 240),
        confidence=0.90,
        reversible=True
    ),
    
    CausalLink(
        source="ENSO_POSITIVE",
        target="DROUGHT_METEOROLOGICAL",
        mechanism="Geschwächte Walker-Zirkulation reduziert Niederschlag in Australien/Indonesien",
        strength=0.75,
        delay_typical="months",
        delay_range=(60, 180),
        confidence=0.88,
        reversible=True
    ),
    
    CausalLink(
        source="ENSO_POSITIVE",
        target="WILDFIRE",
        mechanism="Dürrebedingungen durch El Niño erhöhen Brandgefahr drastisch",
        strength=0.7,
        delay_typical="months",
        delay_range=(90, 270),
        confidence=0.85,
        reversible=True
    ),
    
    CausalLink(
        source="ENSO_POSITIVE",
        target="TROPICAL_CYCLONE",
        mechanism="Wärmerer Pazifik verlagert Entstehungszone, mehr Stürme im Zentralpazifik",
        strength=0.6,
        delay_typical="months",
        delay_range=(30, 180),
        confidence=0.75,
        reversible=True
    ),
    
    # ═══════════════════════════════════════════════════════════════════════
    # ATMOSPHÄRE → EREIGNISSE
    # ═══════════════════════════════════════════════════════════════════════
    
    CausalLink(
        source="JET_STREAM",
        target="HEAT_WAVE",
        mechanism="Gewellter Jetstream ermöglicht persistente Hochdruckgebiete (Blocking)",
        strength=0.7,
        delay_typical="days",
        delay_range=(3, 14),
        confidence=0.80,
        reversible=True
    ),
    
    CausalLink(
        source="JET_STREAM",
        target="COLD_WAVE",
        mechanism="Southward dip im Jetstream transportiert arktische Luft in mittlere Breiten",
        strength=0.7,
        delay_typical="days",
        delay_range=(3, 14),
        confidence=0.80,
        reversible=True
    ),
    
    CausalLink(
        source="POLAR_VORTEX",
        target="COLD_WAVE",
        mechanism="Geschwächter Polarwirbel (SSW) ermöglicht Kaltluftausbrüche",
        strength=0.8,
        delay_typical="weeks",
        delay_range=(14, 60),
        confidence=0.85,
        reversible=True
    ),
    
    CausalLink(
        source="ATMOSPHERIC_BLOCKING",
        target="HEAT_WAVE",
        mechanism="Stationäres Hoch verhindert Wolkenbildung, fördert Aufheizung",
        strength=0.85,
        delay_typical="days",
        delay_range=(3, 7),
        confidence=0.90,
        reversible=True
    ),
    
    CausalLink(
        source="ATMOSPHERIC_BLOCKING",
        target="DROUGHT_METEOROLOGICAL",
        mechanism="Persistentes Hoch blockiert Niederschlag über Wochen",
        strength=0.8,
        delay_typical="weeks",
        delay_range=(14, 60),
        confidence=0.85,
        reversible=True
    ),
    
    CausalLink(
        source="MONSOON_SYSTEM",
        target="FLOOD_RIVER",
        mechanism="Verstärkter Monsun bringt extreme Niederschläge",
        strength=0.8,
        delay_typical="days",
        delay_range=(1, 30),
        confidence=0.90,
        reversible=True
    ),
    
    CausalLink(
        source="MONSOON_SYSTEM",
        target="LANDSLIDE",
        mechanism="Intensive Monsunregen sättigen Böden und destabilisieren Hänge",
        strength=0.7,
        delay_typical="days",
        delay_range=(1, 30),
        confidence=0.85,
        reversible=False
    ),
    
    # ═══════════════════════════════════════════════════════════════════════
    # KRYOSPHÄRE → EREIGNISSE
    # ═══════════════════════════════════════════════════════════════════════
    
    CausalLink(
        source="SEA_ICE_EXTENT",
        target="POLAR_VORTEX",
        mechanism="Reduziertes Meereis erwärmt Arktis, schwächt Temperaturgradienten → instabiler Vortex",
        strength=0.6,
        delay_typical="weeks",
        delay_range=(14, 90),
        confidence=0.75,
        reversible=True
    ),
    
    CausalLink(
        source="GLACIER_RETREAT",
        target="FLOOD_RIVER",
        mechanism="GLOF (Glacier Lake Outburst Flood) durch Brechen von Gletscherseen",
        strength=0.7,
        delay_typical="days",
        delay_range=(0, 7),
        confidence=0.80,
        reversible=False
    ),
    
    CausalLink(
        source="ICE_SHEET_DYNAMICS",
        target="SEA_LEVEL_RISE",
        mechanism="Beschleunigter Eisverlust erhöht globalen Meeresspiegel",
        strength=0.9,
        delay_typical="years",
        delay_range=(365, 36500),
        confidence=0.95,
        reversible=False  # Auf menschlichen Zeitskalen
    ),
    
    CausalLink(
        source="PERMAFROST_THAW",
        target="LANDSLIDE",
        mechanism="Auftauender Permafrost destabilisiert Böden in Polarregionen",
        strength=0.7,
        delay_typical="months",
        delay_range=(30, 365),
        confidence=0.80,
        reversible=False
    ),
    
    CausalLink(
        source="PERMAFROST_THAW",
        target="SUBSIDENCE",
        mechanism="Volumenreduktion beim Auftauen verursacht Geländeabsenkung",
        strength=0.8,
        delay_typical="months",
        delay_range=(30, 365),
        confidence=0.85,
        reversible=False
    ),
    
    # ═══════════════════════════════════════════════════════════════════════
    # ANTHROPOGEN → EREIGNISSE (Verstärkung)
    # ═══════════════════════════════════════════════════════════════════════
    
    CausalLink(
        source="GREENHOUSE_GAS_FORCING",
        target="HEAT_WAVE",
        mechanism="Erhöhte Basistemperatur macht Extremwerte wahrscheinlicher",
        strength=0.7,
        delay_typical="decades",
        delay_range=(3650, 36500),
        confidence=0.95,
        reversible=True  # Langfristig
    ),
    
    CausalLink(
        source="GREENHOUSE_GAS_FORCING",
        target="SEA_SURFACE_TEMPERATURE",
        mechanism="Ozean absorbiert 90% der zusätzlichen Wärme → SST steigt",
        strength=0.9,
        delay_typical="decades",
        delay_range=(3650, 36500),
        confidence=0.95,
        reversible=True
    ),
    
    CausalLink(
        source="URBANIZATION",
        target="HEAT_WAVE",
        mechanism="Urban Heat Island verstärkt Hitzewellen in Städten um 2-5°C",
        strength=0.7,
        delay_typical="hours",
        delay_range=(0.1, 1),
        confidence=0.90,
        reversible=True
    ),
    
    CausalLink(
        source="URBANIZATION",
        target="FLOOD_PLUVIAL",
        mechanism="Versiegelte Flächen verhindern Versickerung → schneller Abfluss",
        strength=0.8,
        delay_typical="hours",
        delay_range=(0.1, 0.5),
        confidence=0.90,
        reversible=True
    ),
    
    CausalLink(
        source="LAND_USE_CHANGE",
        target="WILDFIRE",
        mechanism="Abholzung schafft brennbares Material, reduziert Feuchte",
        strength=0.6,
        delay_typical="months",
        delay_range=(30, 365),
        confidence=0.80,
        reversible=True
    ),
    
    CausalLink(
        source="LAND_USE_CHANGE",
        target="FLOOD_RIVER",
        mechanism="Entwaldung reduziert Wasserrückhalt, erhöht Abfluss und Erosion",
        strength=0.6,
        delay_typical="months",
        delay_range=(30, 365),
        confidence=0.80,
        reversible=True
    ),
    
    CausalLink(
        source="WATER_MANAGEMENT",
        target="DROUGHT_HYDROLOGICAL",
        mechanism="Übernutzung von Grundwasser und Flüssen verstärkt Wassermangel",
        strength=0.7,
        delay_typical="years",
        delay_range=(365, 3650),
        confidence=0.85,
        reversible=True
    ),
    
    # ═══════════════════════════════════════════════════════════════════════
    # SOLAR → EREIGNISSE
    # ═══════════════════════════════════════════════════════════════════════
    
    CausalLink(
        source="SOLAR_IRRADIANCE",
        target="DROUGHT_METEOROLOGICAL",
        mechanism="Solarminima korrelieren mit regionalen Dürren (umstritten)",
        strength=0.2,
        delay_typical="years",
        delay_range=(365, 3650),
        confidence=0.40,
        reversible=True
    ),
    
    CausalLink(
        source="GEOMAGNETIC_STORM",
        target="POWER_GRID_FAILURE",  # Nicht direkt Klima, aber relevant
        mechanism="Geomagnetisch induzierte Ströme können Transformatoren zerstören",
        strength=0.6,
        delay_typical="hours",
        delay_range=(0.1, 1),
        confidence=0.80,
        reversible=True
    ),
    
    # ═══════════════════════════════════════════════════════════════════════
    # KASKADEN (Ereignis → Ereignis)
    # ═══════════════════════════════════════════════════════════════════════
    
    CausalLink(
        source="DROUGHT_METEOROLOGICAL",
        target="WILDFIRE",
        mechanism="Trockene Vegetation ist hochentzündlich",
        strength=0.8,
        delay_typical="weeks",
        delay_range=(7, 90),
        confidence=0.90,
        reversible=False
    ),
    
    CausalLink(
        source="WILDFIRE",
        target="LANDSLIDE",
        mechanism="Verbrannte Hänge verlieren Vegetation → erhöhte Erosion bei nächstem Regen",
        strength=0.7,
        delay_typical="months",
        delay_range=(30, 365),
        confidence=0.80,
        reversible=False
    ),
    
    CausalLink(
        source="WILDFIRE",
        target="FLOOD_FLASH",
        mechanism="Hydrophobe verbrannte Böden → verstärkter Abfluss",
        strength=0.7,
        delay_typical="days",
        delay_range=(1, 60),
        confidence=0.85,
        reversible=False
    ),
    
    CausalLink(
        source="FLOOD_RIVER",
        target="LANDSLIDE",
        mechanism="Gesättigte Böden werden instabil",
        strength=0.6,
        delay_typical="days",
        delay_range=(1, 14),
        confidence=0.80,
        reversible=False
    ),
    
    CausalLink(
        source="HEAT_WAVE",
        target="WILDFIRE",
        mechanism="Hitze trocknet Vegetation, senkt Zündtemperatur",
        strength=0.7,
        delay_typical="days",
        delay_range=(3, 30),
        confidence=0.85,
        reversible=True
    ),
    
    CausalLink(
        source="TROPICAL_CYCLONE",
        target="FLOOD_COASTAL",
        mechanism="Sturmflut durch Windstau und niedrigen Druck",
        strength=0.9,
        delay_typical="hours",
        delay_range=(0.1, 1),
        confidence=0.95,
        reversible=False
    ),
    
    CausalLink(
        source="TROPICAL_CYCLONE",
        target="FLOOD_RIVER",
        mechanism="Extreme Niederschläge im Sturmsystem",
        strength=0.8,
        delay_typical="days",
        delay_range=(0.5, 7),
        confidence=0.90,
        reversible=False
    ),
    
    CausalLink(
        source="TROPICAL_CYCLONE",
        target="LANDSLIDE",
        mechanism="Extreme Niederschläge sättigen Böden",
        strength=0.7,
        delay_typical="days",
        delay_range=(0.5, 7),
        confidence=0.85,
        reversible=False
    ),
]


# ═══════════════════════════════════════════════════════════════════════════════
# TEIL 4: GRAPH-KONSTRUKTION UND ANALYSE
# ═══════════════════════════════════════════════════════════════════════════════

class CompleteCausalGraph:
    """
    Der vollständige kausale Graph aller Treiber und Ereignisse.
    """
    
    def __init__(self):
        self.drivers = PRIMARY_DRIVERS
        self.events = list(ExtremeEvent)
        self.links = CAUSAL_LINKS
        self._build_adjacency()
    
    def _build_adjacency(self):
        """Baue Adjazenzlisten für schnelle Abfragen."""
        self.outgoing: Dict[str, List[CausalLink]] = {}
        self.incoming: Dict[str, List[CausalLink]] = {}
        
        for link in self.links:
            if link.source not in self.outgoing:
                self.outgoing[link.source] = []
            self.outgoing[link.source].append(link)
            
            if link.target not in self.incoming:
                self.incoming[link.target] = []
            self.incoming[link.target].append(link)
    
    def get_all_causes(self, event: str, max_depth: int = 10) -> List[Dict]:
        """
        Finde ALLE möglichen Ursachen für ein Ereignis.
        
        Traversiert den Graphen rückwärts bis zu den primären Treibern.
        """
        causes = []
        visited = set()
        
        def traverse(current: str, path: List[str], cumulative_strength: float, depth: int):
            if depth > max_depth or current in visited:
                return
            
            visited.add(current)
            
            # Prüfe ob primärer Treiber
            if current in self.drivers:
                driver = self.drivers[current]
                causes.append({
                    "primary_driver": current,
                    "driver_info": {
                        "name": driver.name,
                        "category": driver.category.value,
                        "timescale": driver.timescale,
                        "predictability": driver.predictability,
                        "data_sources": driver.data_sources
                    },
                    "causal_path": path,
                    "cumulative_strength": round(cumulative_strength, 3),
                    "chain_length": len(path)
                })
            
            # Traversiere rückwärts
            for link in self.incoming.get(current, []):
                new_path = [link.source] + path
                new_strength = cumulative_strength * link.strength
                traverse(link.source, new_path, new_strength, depth + 1)
            
            visited.remove(current)
        
        traverse(event, [event], 1.0, 0)
        return sorted(causes, key=lambda x: x["cumulative_strength"], reverse=True)
    
    def get_all_effects(self, driver: str, max_depth: int = 10) -> List[Dict]:
        """
        Finde ALLE möglichen Effekte eines Treibers.
        
        Traversiert den Graphen vorwärts bis zu den Extremereignissen.
        """
        effects = []
        visited = set()
        
        def traverse(current: str, path: List[str], cumulative_strength: float, 
                     cumulative_delay: float, depth: int):
            if depth > max_depth or current in visited:
                return
            
            visited.add(current)
            
            # Prüfe ob Extremereignis
            try:
                ExtremeEvent(current)
                effects.append({
                    "extreme_event": current,
                    "causal_path": path,
                    "cumulative_strength": round(cumulative_strength, 3),
                    "cumulative_delay_days": round(cumulative_delay, 1),
                    "chain_length": len(path) - 1
                })
            except ValueError:
                pass
            
            # Traversiere vorwärts
            for link in self.outgoing.get(current, []):
                new_path = path + [link.target]
                new_strength = cumulative_strength * link.strength
                avg_delay = (link.delay_range[0] + link.delay_range[1]) / 2
                new_delay = cumulative_delay + avg_delay
                traverse(link.target, new_path, new_strength, new_delay, depth + 1)
            
            visited.remove(current)
        
        traverse(driver, [driver], 1.0, 0, 0)
        return sorted(effects, key=lambda x: x["cumulative_strength"], reverse=True)
    
    def get_complete_causal_chain(self, event: str) -> Dict:
        """
        Erstelle den vollständigen kausalen Graphen für ein Ereignis.
        """
        causes = self.get_all_causes(event)
        
        # Gruppiere nach Kategorie
        by_category = {}
        for cause in causes:
            cat = cause["driver_info"]["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(cause)
        
        return {
            "event": event,
            "total_causal_paths": len(causes),
            "primary_drivers_count": len(set(c["primary_driver"] for c in causes)),
            "by_category": by_category,
            "strongest_paths": causes[:10],
            "all_paths": causes
        }
    
    def print_event_analysis(self, event: str):
        """Drucke eine übersichtliche Analyse für ein Ereignis."""
        analysis = self.get_complete_causal_chain(event)
        
        print(f"\n{'='*80}")
        print(f"KAUSALE ANALYSE: {event.upper()}")
        print(f"{'='*80}")
        print(f"\n📊 {analysis['total_causal_paths']} kausale Pfade von "
              f"{analysis['primary_drivers_count']} primären Treibern\n")
        
        print("PRIMÄRE TREIBER nach Kategorie:")
        print("-" * 40)
        for category, paths in analysis['by_category'].items():
            print(f"\n  📁 {category.upper()}:")
            unique_drivers = list(set(p['primary_driver'] for p in paths))
            for driver in unique_drivers:
                strongest = max([p for p in paths if p['primary_driver'] == driver],
                               key=lambda x: x['cumulative_strength'])
                print(f"     • {self.drivers[driver].name}")
                print(f"       Stärke: {strongest['cumulative_strength']:.1%}, "
                      f"Kette: {' → '.join(strongest['causal_path'])}")
        
        print(f"\n{'─'*80}")
        print("TOP 5 STÄRKSTE KAUSALKETTEN:")
        print("─" * 80)
        for i, path in enumerate(analysis['strongest_paths'][:5], 1):
            print(f"\n  {i}. {path['primary_driver']} ({path['driver_info']['name']})")
            print(f"     Kategorie: {path['driver_info']['category']}")
            print(f"     Stärke: {path['cumulative_strength']:.1%}")
            print(f"     Kette: {' → '.join(path['causal_path'])}")
            print(f"     Zeitskala: {path['driver_info']['timescale']}")
            print(f"     Datenquellen: {', '.join(path['driver_info']['data_sources'][:2])}")


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    graph = CompleteCausalGraph()
    
    print("\n" + "="*80)
    print("TERA V2: VOLLSTÄNDIGE KAUSAL-TAXONOMIE")
    print("="*80)
    
    print(f"\n📊 STATISTIK:")
    print(f"   • {len(PRIMARY_DRIVERS)} Primäre Treiber definiert")
    print(f"   • {len(list(ExtremeEvent))} Extremereignis-Typen definiert")
    print(f"   • {len(CAUSAL_LINKS)} Kausale Verbindungen definiert")
    
    # Analysiere verschiedene Ereignisse
    events_to_analyze = [
        "wildfire",
        "flood_river", 
        "tropical_cyclone",
        "heat_wave",
        "tsunami"
    ]
    
    for event in events_to_analyze:
        graph.print_event_analysis(event)
    
    # Zeige alle Effekte eines Treibers
    print("\n" + "="*80)
    print("VULKANAUSBRUCH: ALLE MÖGLICHEN EFFEKTE")
    print("="*80)
    
    effects = graph.get_all_effects("VOLCANIC_ERUPTION")
    print(f"\n{len(effects)} mögliche Extremereignisse können folgen:\n")
    
    for effect in effects[:10]:
        print(f"  → {effect['extreme_event']:25s} | "
              f"Stärke: {effect['cumulative_strength']:.1%} | "
              f"Delay: {effect['cumulative_delay_days']:.0f} Tage")
        print(f"    Kette: {' → '.join(effect['causal_path'])}")












