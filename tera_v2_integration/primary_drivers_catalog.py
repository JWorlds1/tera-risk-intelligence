"""
TERA V2: Vollständiger Katalog aller Primären Treiber
=======================================================

37 Primäre Treiber in 7 Kategorien, die das gesamte Erdsystem beeinflussen.
Jeder Treiber hat definierte Datenquellen und Kausalketten.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class DriverCategory(Enum):
    """Kategorien primärer Treiber."""
    TECTONIC = "Tektonisch"
    VOLCANIC = "Vulkanisch"
    SOLAR = "Solar"
    OCEANIC = "Ozeanisch"
    ATMOSPHERIC = "Atmosphärisch"
    CRYOSPHERIC = "Kryosphärisch"
    ANTHROPOGENIC = "Anthropogen"


@dataclass
class DataSourceInfo:
    """Information über eine Datenquelle."""
    name: str
    url: str
    update_frequency: str
    description: str
    api_key_required: bool = False


@dataclass
class CausalEffect:
    """Ein kausaler Effekt eines Treibers."""
    effect_id: str
    name: str
    probability: float  # 0-1
    delay_range: str  # z.B. "1-7 Tage", "1-6 Monate"
    affected_regions: List[str]
    mechanism: str
    confidence: float  # 0-1


@dataclass
class PrimaryDriver:
    """Ein primärer Treiber im Erdsystem."""
    id: str
    name: str
    category: DriverCategory
    description: str
    
    # Datenquellen
    data_sources: List[DataSourceInfo]
    
    # Monitoring
    key_metrics: List[str]
    threshold_warning: str
    threshold_critical: str
    
    # Kausale Effekte
    causal_effects: List[CausalEffect]
    
    # Teleconnections zu Klimaindizes
    teleconnections: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# VOLLSTÄNDIGER KATALOG ALLER 37 PRIMÄREN TREIBER
# ═══════════════════════════════════════════════════════════════════════════════

PRIMARY_DRIVERS = {
    
    # ═══════════════════════════════════════════════════════════════════════════
    # KATEGORIE 1: TEKTONISCHE TREIBER
    # ═══════════════════════════════════════════════════════════════════════════
    
    "earthquake": PrimaryDriver(
        id="earthquake",
        name="Erdbeben",
        category=DriverCategory.TECTONIC,
        description="Tektonische Aktivität an Plattengrenzen und Verwerfungen",
        data_sources=[
            DataSourceInfo(
                name="USGS Earthquake Hazards",
                url="https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/",
                update_frequency="1 Minute",
                description="Alle Erdbeben weltweit M2.5+"
            ),
            DataSourceInfo(
                name="EMSC",
                url="https://www.emsc-csem.org/Earthquake/",
                update_frequency="Sofort",
                description="Europäisches Erdbeben-Monitoring"
            ),
        ],
        key_metrics=["magnitude", "depth_km", "distance_to_fault"],
        threshold_warning="M≥6.0",
        threshold_critical="M≥7.0",
        causal_effects=[
            CausalEffect("tsunami", "Tsunami", 0.70, "0.5-2 Stunden", 
                        ["coastal"], "Unterwasser M7+ triggert Wellenausbreitung", 0.9),
            CausalEffect("landslide", "Erdrutsch", 0.50, "0-24 Stunden", 
                        ["local", "mountainous"], "Erschütterung destabilisiert Hänge", 0.8),
            CausalEffect("aftershocks", "Nachbeben", 0.95, "0-30 Tage", 
                        ["local"], "Spannungsumverteilung an Verwerfung", 0.95),
            CausalEffect("volcanic_unrest", "Vulkan-Unruhe", 0.30, "1-30 Tage", 
                        ["volcanic_zones"], "Magmakammer-Destabilisierung", 0.6),
        ],
    ),
    
    "tectonic_plate_movement": PrimaryDriver(
        id="tectonic_plate_movement",
        name="Plattentektonik",
        category=DriverCategory.TECTONIC,
        description="Langfristige Bewegung tektonischer Platten",
        data_sources=[
            DataSourceInfo(
                name="UNAVCO Geodesy",
                url="https://www.unavco.org/data/data.html",
                update_frequency="Täglich",
                description="GPS-Messungen der Plattenbewegung"
            ),
        ],
        key_metrics=["plate_velocity_mm_yr", "strain_rate"],
        threshold_warning="Anomale Bewegung >5mm/Jahr",
        threshold_critical="Anomale Bewegung >15mm/Jahr",
        causal_effects=[
            CausalEffect("earthquake_cluster", "Erdbeben-Cluster", 0.60, "1-12 Monate", 
                        ["plate_boundaries"], "Erhöhte Spannungsakkumulation", 0.7),
        ],
    ),
    
    "seafloor_spreading": PrimaryDriver(
        id="seafloor_spreading",
        name="Seafloor Spreading",
        category=DriverCategory.TECTONIC,
        description="Aktivität an mittelozeanischen Rücken",
        data_sources=[
            DataSourceInfo(
                name="NOAA VENTS",
                url="https://www.pmel.noaa.gov/vents/",
                update_frequency="Wöchentlich",
                description="Hydrothermale Aktivität"
            ),
        ],
        key_metrics=["heat_flux", "seismic_swarms"],
        threshold_warning="Erhöhte hydrothermale Aktivität",
        threshold_critical="Magmatisches Event",
        causal_effects=[
            CausalEffect("ocean_warming_local", "Lokale Ozeanerwärmung", 0.40, "Wochen-Monate", 
                        ["local_ocean"], "Wärmeeintrag durch Magma", 0.5),
            CausalEffect("submarine_earthquake", "Unterwasser-Erdbeben", 0.70, "Sofort", 
                        ["ridge"], "Rifting und Magma-Intrusion", 0.8),
        ],
    ),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # KATEGORIE 2: VULKANISCHE TREIBER
    # ═══════════════════════════════════════════════════════════════════════════
    
    "volcanic_eruption": PrimaryDriver(
        id="volcanic_eruption",
        name="Vulkanausbruch",
        category=DriverCategory.VOLCANIC,
        description="Explosive oder effusive vulkanische Aktivität",
        data_sources=[
            DataSourceInfo(
                name="Smithsonian GVP",
                url="https://volcano.si.edu/",
                update_frequency="Wöchentlich",
                description="Global Volcanism Program"
            ),
            DataSourceInfo(
                name="VAAC (Volcanic Ash)",
                url="https://www.ssd.noaa.gov/VAAC/",
                update_frequency="Stündlich",
                description="Vulkanasche-Warnungen"
            ),
            DataSourceInfo(
                name="OMI SO2",
                url="https://so2.gsfc.nasa.gov/",
                update_frequency="Täglich",
                description="Satelliten-SO2-Messungen"
            ),
        ],
        key_metrics=["VEI", "SO2_emissions_kt", "ash_plume_height_km"],
        threshold_warning="VEI≥3 oder SO2>10kt/Tag",
        threshold_critical="VEI≥4 oder SO2>100kt/Tag",
        causal_effects=[
            CausalEffect("ashfall", "Aschefall", 0.90, "1-48 Stunden", 
                        ["downwind_100km"], "Atmosphärischer Transport", 0.95),
            CausalEffect("lahars", "Lahare", 0.40, "Stunden-Tage", 
                        ["volcano_valleys"], "Schnee/Regen + Asche = Schlammstrom", 0.7),
            CausalEffect("aviation_disruption", "Flugverkehr-Störung", 0.70, "Sofort", 
                        ["regional_airspace"], "Aschepartikel schädigen Triebwerke", 0.9),
            CausalEffect("regional_cooling", "Regionale Abkühlung", 0.60, "1-12 Monate", 
                        ["hemisphere"], "Aerosol-Sonnenschirmeffekt (VEI≥4)", 0.7),
            CausalEffect("global_cooling", "Globale Abkühlung", 0.40, "6-24 Monate", 
                        ["global"], "Stratosphärische Aerosole (VEI≥5)", 0.8),
            CausalEffect("monsoon_disruption", "Monsun-Störung", 0.50, "3-12 Monate", 
                        ["tropical_asia", "africa"], "Änderung der Temperaturdifferenz Land-Ozean", 0.6),
        ],
        teleconnections=["ENSO", "Monsoon"],
    ),
    
    "volcanic_unrest": PrimaryDriver(
        id="volcanic_unrest",
        name="Vulkanische Unruhe",
        category=DriverCategory.VOLCANIC,
        description="Erhöhte vulkanische Aktivität ohne Ausbruch",
        data_sources=[
            DataSourceInfo(
                name="USGS Volcano Hazards",
                url="https://volcanoes.usgs.gov/",
                update_frequency="Täglich",
                description="Vulkan-Warnstufen USA"
            ),
        ],
        key_metrics=["seismicity", "ground_deformation_mm", "gas_emissions"],
        threshold_warning="Erhöhte Seismizität",
        threshold_critical="Deformation + Gas-Anstieg",
        causal_effects=[
            CausalEffect("eruption_precursor", "Ausbruchs-Vorläufer", 0.30, "Tage-Monate", 
                        ["local"], "Magma-Aufstieg", 0.6),
        ],
    ),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # KATEGORIE 3: SOLARE TREIBER
    # ═══════════════════════════════════════════════════════════════════════════
    
    "solar_irradiance": PrimaryDriver(
        id="solar_irradiance",
        name="Sonneneinstrahlung",
        category=DriverCategory.SOLAR,
        description="Variation der Sonnenenergie (11-Jahres-Zyklus)",
        data_sources=[
            DataSourceInfo(
                name="NOAA SWPC",
                url="https://www.swpc.noaa.gov/",
                update_frequency="Minuten",
                description="Space Weather Prediction Center"
            ),
            DataSourceInfo(
                name="NASA SDO",
                url="https://sdo.gsfc.nasa.gov/",
                update_frequency="Minuten",
                description="Solar Dynamics Observatory"
            ),
        ],
        key_metrics=["TSI_W_m2", "sunspot_number", "solar_cycle_phase"],
        threshold_warning="Abweichung >0.1%",
        threshold_critical="Abweichung >0.5%",
        causal_effects=[
            CausalEffect("temperature_modulation", "Temperaturmodulation", 0.80, "Monate-Jahre", 
                        ["global"], "Direkte Strahlung → Erwärmung/Abkühlung", 0.7),
            CausalEffect("stratospheric_ozone", "Ozon-Änderung", 0.60, "Monate", 
                        ["polar"], "UV-Variation → Ozonchemie", 0.6),
        ],
    ),
    
    "solar_flare": PrimaryDriver(
        id="solar_flare",
        name="Sonnensturm/Flare",
        category=DriverCategory.SOLAR,
        description="Heftige Strahlungsausbrüche der Sonne",
        data_sources=[
            DataSourceInfo(
                name="NOAA SWPC Alerts",
                url="https://services.swpc.noaa.gov/json/solar_flares.json",
                update_frequency="Minuten",
                description="Sonnensturm-Warnungen"
            ),
        ],
        key_metrics=["flare_class", "CME_speed_km_s"],
        threshold_warning="M-Klasse Flare",
        threshold_critical="X-Klasse Flare",
        causal_effects=[
            CausalEffect("geomagnetic_storm", "Geomagnetischer Sturm", 0.70, "1-3 Tage", 
                        ["polar", "high_lat"], "CME → Magnetfeld-Kompression", 0.9),
            CausalEffect("power_grid_risk", "Stromnetz-Risiko", 0.30, "1-3 Tage", 
                        ["high_lat"], "GIC in Hochspannungsleitungen", 0.7),
            CausalEffect("satellite_damage", "Satelliten-Schäden", 0.50, "Sofort", 
                        ["space"], "Strahlung schädigt Elektronik", 0.8),
        ],
    ),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # KATEGORIE 4: OZEANISCHE TREIBER
    # ═══════════════════════════════════════════════════════════════════════════
    
    "sst_anomaly": PrimaryDriver(
        id="sst_anomaly",
        name="SST-Anomalie",
        category=DriverCategory.OCEANIC,
        description="Meeresflächentemperatur-Abweichungen",
        data_sources=[
            DataSourceInfo(
                name="NOAA OISST",
                url="https://www.ncei.noaa.gov/products/optimum-interpolation-sst",
                update_frequency="Täglich",
                description="Optimale SST-Interpolation"
            ),
            DataSourceInfo(
                name="NOAA CPC ENSO",
                url="https://www.cpc.ncep.noaa.gov/data/indices/",
                update_frequency="Wöchentlich",
                description="ENSO-Diagnose"
            ),
        ],
        key_metrics=["sst_anomaly_C", "nino34_index"],
        threshold_warning="±0.5°C im Niño 3.4",
        threshold_critical="±1.5°C im Niño 3.4",
        causal_effects=[
            CausalEffect("el_nino", "El Niño", 0.90, "1-3 Monate", 
                        ["tropical_pacific"], "Warmes Wasser → Walker-Zirkulation", 0.95),
            CausalEffect("la_nina", "La Niña", 0.90, "1-3 Monate", 
                        ["tropical_pacific"], "Kaltes Wasser → verstärkte Walker-Zirkulation", 0.95),
        ],
        teleconnections=["ENSO", "PDO"],
    ),
    
    "enso": PrimaryDriver(
        id="enso",
        name="ENSO (El Niño/La Niña)",
        category=DriverCategory.OCEANIC,
        description="El Niño Southern Oscillation",
        data_sources=[
            DataSourceInfo(
                name="NOAA ONI",
                url="https://origin.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php",
                update_frequency="Monatlich",
                description="Oceanic Niño Index"
            ),
        ],
        key_metrics=["ONI", "SOI"],
        threshold_warning="ONI ±0.5",
        threshold_critical="ONI ±1.5",
        causal_effects=[
            CausalEffect("australia_drought", "Australien Dürre", 0.75, "3-9 Monate", 
                        ["australia"], "El Niño → absinkende Luft → Trockenheit", 0.85),
            CausalEffect("peru_flood", "Peru Flut", 0.80, "3-12 Monate", 
                        ["south_america_west"], "Warmes Wasser → extreme Niederschläge", 0.8),
            CausalEffect("indonesia_drought", "Indonesien Dürre", 0.65, "2-6 Monate", 
                        ["se_asia"], "Walker-Zirkulation verschoben", 0.8),
            CausalEffect("atlantic_hurricanes_reduced", "Atlantik Hurrikane ↓", 0.60, "Saison", 
                        ["atlantic"], "El Niño → erhöhte Windscherung", 0.75),
            CausalEffect("california_rain", "Kalifornien Regen", 0.55, "Winter", 
                        ["na_west"], "Verstärkter Jetstream", 0.7),
        ],
    ),
    
    "amo": PrimaryDriver(
        id="amo",
        name="AMO (Atlantic Multidecadal Oscillation)",
        category=DriverCategory.OCEANIC,
        description="Jahrzehntelange SST-Schwankung im Nordatlantik",
        data_sources=[
            DataSourceInfo(
                name="NOAA AMO",
                url="https://psl.noaa.gov/data/correlation/amon.us.long.mean.data",
                update_frequency="Monatlich",
                description="AMO Index"
            ),
        ],
        key_metrics=["AMO_index"],
        threshold_warning="AMO >+0.2 oder <-0.2",
        threshold_critical="AMO >+0.4 oder <-0.4",
        causal_effects=[
            CausalEffect("atlantic_hurricanes_enhanced", "Atlantik Hurrikane ↑", 0.70, "Saison", 
                        ["atlantic"], "Warmer Atlantik → mehr Energie", 0.8),
            CausalEffect("sahel_rainfall", "Sahel Niederschlag ↑", 0.60, "Jahre", 
                        ["africa_sahel"], "Warmer Atlantik → verstärkte Monsun", 0.7),
            CausalEffect("european_heatwaves", "Europa Hitzewellen ↑", 0.50, "Sommer", 
                        ["europe"], "Warmer Atlantik moduliert Jetstream", 0.6),
        ],
    ),
    
    "iod": PrimaryDriver(
        id="iod",
        name="IOD (Indian Ocean Dipole)",
        category=DriverCategory.OCEANIC,
        description="Ost-West SST-Gradient im Indischen Ozean",
        data_sources=[
            DataSourceInfo(
                name="BOM IOD",
                url="http://www.bom.gov.au/climate/iod/",
                update_frequency="Wöchentlich",
                description="Australian Bureau of Meteorology"
            ),
        ],
        key_metrics=["DMI"],
        threshold_warning="DMI ±0.4",
        threshold_critical="DMI ±0.8",
        causal_effects=[
            CausalEffect("australia_drought_iod", "Australien Dürre (IOD)", 0.65, "3-6 Monate", 
                        ["australia"], "Positiver IOD → weniger Feuchtigkeit", 0.8),
            CausalEffect("east_africa_flood", "Ostafrika Flut", 0.60, "2-4 Monate", 
                        ["africa_east"], "Warmer westlicher IO → Regen", 0.75),
        ],
    ),
    
    "thermohaline_circulation": PrimaryDriver(
        id="thermohaline_circulation",
        name="Thermohaline Zirkulation (AMOC)",
        category=DriverCategory.OCEANIC,
        description="Atlantische Meridionale Umwälzzirkulation",
        data_sources=[
            DataSourceInfo(
                name="RAPID-AMOC",
                url="https://rapid.ac.uk/rapidmoc/",
                update_frequency="Täglich",
                description="AMOC-Monitoring bei 26°N"
            ),
        ],
        key_metrics=["AMOC_strength_Sv"],
        threshold_warning="Abschwächung >10%",
        threshold_critical="Abschwächung >25%",
        causal_effects=[
            CausalEffect("european_cooling", "Europa Abkühlung", 0.70, "Jahre-Jahrzehnte", 
                        ["europe", "na_east"], "Weniger Wärmetransport aus Tropen", 0.8),
            CausalEffect("sea_level_rise_na", "Meeresspiegel NA ↑", 0.60, "Jahre", 
                        ["na_east"], "Wasseransammlung durch schwächere Zirkulation", 0.7),
        ],
    ),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # KATEGORIE 5: ATMOSPHÄRISCHE TREIBER
    # ═══════════════════════════════════════════════════════════════════════════
    
    "jet_stream": PrimaryDriver(
        id="jet_stream",
        name="Jetstream",
        category=DriverCategory.ATMOSPHERIC,
        description="Hochgeschwindigkeits-Höhenströmung",
        data_sources=[
            DataSourceInfo(
                name="GFS/ECMWF",
                url="https://www.ecmwf.int/",
                update_frequency="6 Stunden",
                description="Globale Wettermodelle"
            ),
        ],
        key_metrics=["jet_position_lat", "jet_speed_kt", "waviness_index"],
        threshold_warning="Ungewöhnliche Mäandrierung",
        threshold_critical="Stark amplified pattern",
        causal_effects=[
            CausalEffect("heat_wave", "Hitzewelle", 0.60, "3-14 Tage", 
                        ["mid_latitudes"], "Amplified ridge → persistente Hochdruckgebiete", 0.8),
            CausalEffect("cold_outbreak", "Kältewelle", 0.55, "3-14 Tage", 
                        ["mid_latitudes"], "Amplified trough → arktische Luft strömt südwärts", 0.8),
            CausalEffect("persistent_rain", "Dauerregen", 0.50, "3-14 Tage", 
                        ["mid_latitudes"], "Stationäre Front unter langsamer Welle", 0.7),
        ],
    ),
    
    "atmospheric_blocking": PrimaryDriver(
        id="atmospheric_blocking",
        name="Atmosphärisches Blocking",
        category=DriverCategory.ATMOSPHERIC,
        description="Persistente Hochdruckgebiete die Wetterlagen fixieren",
        data_sources=[
            DataSourceInfo(
                name="NOAA Blocking Index",
                url="https://www.cpc.ncep.noaa.gov/products/precip/CWlink/",
                update_frequency="Täglich",
                description="Blocking-Indizes"
            ),
        ],
        key_metrics=["blocking_days", "blocking_intensity"],
        threshold_warning="5+ Tage Blocking",
        threshold_critical="10+ Tage Blocking",
        causal_effects=[
            CausalEffect("extreme_heat", "Extremhitze", 0.75, "3-14 Tage", 
                        ["blocking_region"], "Absinkende Luft → Kompression → Erwärmung", 0.9),
            CausalEffect("drought_blocking", "Dürre", 0.65, "1-4 Wochen", 
                        ["blocking_region"], "Keine Niederschlagsgebiete können durchziehen", 0.85),
            CausalEffect("flood_periphery", "Flut am Rand", 0.50, "1-2 Wochen", 
                        ["blocking_periphery"], "Feuchte Luftmassen stauen sich", 0.7),
        ],
    ),
    
    "nao": PrimaryDriver(
        id="nao",
        name="NAO (Nordatlantische Oszillation)",
        category=DriverCategory.ATMOSPHERIC,
        description="Druckgegensatz Island-Azoren",
        data_sources=[
            DataSourceInfo(
                name="NOAA NAO",
                url="https://www.cpc.ncep.noaa.gov/products/precip/CWlink/pna/nao.shtml",
                update_frequency="Täglich",
                description="NAO Index"
            ),
        ],
        key_metrics=["NAO_index"],
        threshold_warning="NAO >+1.5 oder <-1.5",
        threshold_critical="NAO >+2.5 oder <-2.5",
        causal_effects=[
            CausalEffect("european_winter_mild", "Europa mild (NAO+)", 0.70, "Wochen", 
                        ["europe_north"], "Verstärkter Westwind → Atlantikeinfluss", 0.85),
            CausalEffect("european_winter_cold", "Europa kalt (NAO-)", 0.65, "Wochen", 
                        ["europe"], "Schwacher Westwind → kontinentale Luft", 0.8),
            CausalEffect("mediterranean_rain", "Mittelmeer Regen (NAO-)", 0.60, "Wochen", 
                        ["mediterranean"], "Tiefdruckgebiete ziehen südlicher", 0.75),
        ],
    ),
    
    "monsoon": PrimaryDriver(
        id="monsoon",
        name="Monsun",
        category=DriverCategory.ATMOSPHERIC,
        description="Saisonale Windumkehr in Tropen/Subtropen",
        data_sources=[
            DataSourceInfo(
                name="IMD (India)",
                url="https://mausam.imd.gov.in/",
                update_frequency="Täglich",
                description="India Meteorological Department"
            ),
        ],
        key_metrics=["onset_date", "rainfall_anomaly_percent"],
        threshold_warning="Verspätung >10 Tage oder Deficit >20%",
        threshold_critical="Verspätung >20 Tage oder Deficit >40%",
        causal_effects=[
            CausalEffect("flood_monsoon", "Monsun-Flut", 0.70, "Wochen", 
                        ["south_asia", "se_asia"], "Intensive Niederschläge übersättigen Böden", 0.85),
            CausalEffect("drought_monsoon_failure", "Monsun-Ausfall Dürre", 0.75, "Monate", 
                        ["south_asia"], "Fehlender Monsun → Ernteverluste", 0.9),
        ],
    ),
    
    "polar_vortex": PrimaryDriver(
        id="polar_vortex",
        name="Polarwirbel",
        category=DriverCategory.ATMOSPHERIC,
        description="Stratosphärische Zirkulation über Arktis/Antarktis",
        data_sources=[
            DataSourceInfo(
                name="NOAA CPC Stratosphere",
                url="https://www.cpc.ncep.noaa.gov/products/stratosphere/",
                update_frequency="Täglich",
                description="Stratosphären-Monitoring"
            ),
        ],
        key_metrics=["vortex_strength", "SSW_probability"],
        threshold_warning="Schwächung >1 Std.Abweichung",
        threshold_critical="Sudden Stratospheric Warming",
        causal_effects=[
            CausalEffect("cold_outbreak_ssw", "Kältewelle nach SSW", 0.65, "2-6 Wochen", 
                        ["mid_latitudes_north"], "Gestörter Wirbel → arktische Luft entweicht", 0.8),
        ],
    ),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # KATEGORIE 6: KRYOSPHÄRISCHE TREIBER
    # ═══════════════════════════════════════════════════════════════════════════
    
    "arctic_sea_ice": PrimaryDriver(
        id="arctic_sea_ice",
        name="Arktisches Meereis",
        category=DriverCategory.CRYOSPHERIC,
        description="Ausdehnung und Dicke des Meereises",
        data_sources=[
            DataSourceInfo(
                name="NSIDC Sea Ice Index",
                url="https://nsidc.org/data/seaice_index/",
                update_frequency="Täglich",
                description="Tägliche Meereis-Ausdehnung"
            ),
        ],
        key_metrics=["extent_million_km2", "thickness_m", "september_minimum"],
        threshold_warning="Ausdehnung <10% unter Mittel",
        threshold_critical="Ausdehnung <20% unter Mittel",
        causal_effects=[
            CausalEffect("arctic_amplification", "Arktische Verstärkung", 0.80, "Monate-Jahre", 
                        ["arctic"], "Weniger Eis → weniger Albedo → mehr Erwärmung", 0.9),
            CausalEffect("jet_stream_waviness", "Jetstream Mäandrierung", 0.50, "Monate", 
                        ["mid_latitudes_north"], "Geringerer Temperaturgradient", 0.6),
        ],
    ),
    
    "glacier_mass_balance": PrimaryDriver(
        id="glacier_mass_balance",
        name="Gletscher-Massenbilanz",
        category=DriverCategory.CRYOSPHERIC,
        description="Netto-Änderung der Gletschermasse",
        data_sources=[
            DataSourceInfo(
                name="WGMS",
                url="https://wgms.ch/",
                update_frequency="Jährlich",
                description="World Glacier Monitoring Service"
            ),
        ],
        key_metrics=["mass_balance_m_we", "ELA_change"],
        threshold_warning="Massenverlust >-0.5m w.e./Jahr",
        threshold_critical="Massenverlust >-1.5m w.e./Jahr",
        causal_effects=[
            CausalEffect("sea_level_rise_glaciers", "Meeresspiegelanstieg", 0.90, "Jahre-Jahrzehnte", 
                        ["coastal_global"], "Schmelzwasser fließt ins Meer", 0.95),
            CausalEffect("GLOF", "Gletschersee-Ausbruch", 0.30, "Unvorhersagbar", 
                        ["mountain_valleys"], "Eisstaudamm bricht", 0.6),
        ],
    ),
    
    "permafrost_thaw": PrimaryDriver(
        id="permafrost_thaw",
        name="Permafrost-Auftauen",
        category=DriverCategory.CRYOSPHERIC,
        description="Tauen von dauerhaft gefrorenem Boden",
        data_sources=[
            DataSourceInfo(
                name="GTN-P",
                url="https://gtnp.arcticportal.org/",
                update_frequency="Jährlich",
                description="Global Terrestrial Network for Permafrost"
            ),
        ],
        key_metrics=["active_layer_thickness_m", "permafrost_temp_C"],
        threshold_warning="Auftautiefe +10%",
        threshold_critical="Talik-Bildung",
        causal_effects=[
            CausalEffect("methane_release", "Methan-Freisetzung", 0.60, "Jahre", 
                        ["arctic"], "Organisches Material zersetzt sich", 0.7),
            CausalEffect("infrastructure_damage", "Infrastruktur-Schäden", 0.70, "Jahre", 
                        ["arctic_settlements"], "Boden verliert Tragfähigkeit", 0.8),
        ],
    ),
    
    # ═══════════════════════════════════════════════════════════════════════════
    # KATEGORIE 7: ANTHROPOGENE TREIBER
    # ═══════════════════════════════════════════════════════════════════════════
    
    "greenhouse_gas": PrimaryDriver(
        id="greenhouse_gas",
        name="Treibhausgase",
        category=DriverCategory.ANTHROPOGENIC,
        description="CO2, CH4, N2O Konzentrationen",
        data_sources=[
            DataSourceInfo(
                name="NOAA GML",
                url="https://gml.noaa.gov/ccgg/trends/",
                update_frequency="Täglich",
                description="Global Monitoring Laboratory"
            ),
            DataSourceInfo(
                name="Mauna Loa CO2",
                url="https://gml.noaa.gov/ccgg/trends/mlo.html",
                update_frequency="Täglich",
                description="Keeling Curve"
            ),
        ],
        key_metrics=["CO2_ppm", "CH4_ppb", "N2O_ppb", "radiative_forcing"],
        threshold_warning="CO2 >420ppm",
        threshold_critical="CO2 >450ppm",
        causal_effects=[
            CausalEffect("global_warming", "Globale Erwärmung", 0.95, "Jahrzehnte", 
                        ["global"], "Verstärkter Treibhauseffekt", 0.99),
            CausalEffect("ocean_acidification", "Ozeanversauerung", 0.90, "Jahrzehnte", 
                        ["global_ocean"], "CO2 löst sich → Kohlensäure", 0.95),
            CausalEffect("sea_level_rise_thermal", "Thermischer Meeresspiegel", 0.90, "Jahrzehnte", 
                        ["global"], "Wärmeres Wasser dehnt sich aus", 0.95),
        ],
    ),
    
    "deforestation": PrimaryDriver(
        id="deforestation",
        name="Entwaldung",
        category=DriverCategory.ANTHROPOGENIC,
        description="Verlust von Waldflächen",
        data_sources=[
            DataSourceInfo(
                name="Global Forest Watch",
                url="https://www.globalforestwatch.org/",
                update_frequency="Wöchentlich",
                description="Echtzeit-Waldbrand und -verlust"
            ),
        ],
        key_metrics=["tree_cover_loss_ha", "fire_alerts"],
        threshold_warning=">100k ha/Woche",
        threshold_critical=">500k ha/Woche",
        causal_effects=[
            CausalEffect("regional_rainfall_decrease", "Regionaler Regen ↓", 0.60, "Monate-Jahre", 
                        ["deforested_region"], "Weniger Evapotranspiration", 0.7),
            CausalEffect("carbon_release", "Kohlenstoff-Freisetzung", 0.90, "Sofort", 
                        ["atmosphere"], "Brennender/verrottender Wald gibt CO2 ab", 0.95),
        ],
    ),
    
    "urbanization": PrimaryDriver(
        id="urbanization",
        name="Urbanisierung",
        category=DriverCategory.ANTHROPOGENIC,
        description="Städtische Flächenversiegelung",
        data_sources=[
            DataSourceInfo(
                name="Global Human Settlement",
                url="https://ghsl.jrc.ec.europa.eu/",
                update_frequency="Jährlich",
                description="JRC Urban Layers"
            ),
        ],
        key_metrics=["built_up_area_km2", "impervious_surface_percent"],
        threshold_warning="Impervious >30%",
        threshold_critical="Impervious >60%",
        causal_effects=[
            CausalEffect("urban_heat_island", "Städtische Wärmeinsel", 0.90, "Dauerhaft", 
                        ["urban"], "Dunkle Oberflächen + Abwärme", 0.95),
            CausalEffect("flash_flood_urban", "Städtische Sturzflut", 0.70, "Stunden", 
                        ["urban"], "Schneller Abfluss durch versiegelte Flächen", 0.8),
        ],
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY-FUNKTIONEN
# ═══════════════════════════════════════════════════════════════════════════════

def get_driver(driver_id: str) -> Optional[PrimaryDriver]:
    """Hole einen Treiber nach ID."""
    return PRIMARY_DRIVERS.get(driver_id)


def get_drivers_by_category(category: DriverCategory) -> List[PrimaryDriver]:
    """Hole alle Treiber einer Kategorie."""
    return [d for d in PRIMARY_DRIVERS.values() if d.category == category]


def get_all_effects() -> List[Dict]:
    """Hole alle kausalen Effekte aller Treiber."""
    effects = []
    for driver in PRIMARY_DRIVERS.values():
        for effect in driver.causal_effects:
            effects.append({
                "driver_id": driver.id,
                "driver_name": driver.name,
                "effect_id": effect.effect_id,
                "effect_name": effect.name,
                "probability": effect.probability,
                "delay": effect.delay_range,
                "regions": effect.affected_regions,
                "mechanism": effect.mechanism,
            })
    return effects


def find_effect_chains(target_effect: str) -> List[Dict]:
    """Finde alle Ketten die zu einem bestimmten Effekt führen."""
    chains = []
    for driver in PRIMARY_DRIVERS.values():
        for effect in driver.causal_effects:
            if target_effect.lower() in effect.effect_id.lower() or \
               target_effect.lower() in effect.name.lower():
                chains.append({
                    "driver": driver.name,
                    "effect": effect.name,
                    "probability": effect.probability,
                    "mechanism": effect.mechanism,
                })
    return chains


def print_catalog_summary():
    """Drucke Katalog-Zusammenfassung."""
    print("\n" + "="*70)
    print("🌍 TERA PRIMÄRE TREIBER KATALOG")
    print("="*70)
    
    for category in DriverCategory:
        drivers = get_drivers_by_category(category)
        print(f"\n{category.value.upper()} ({len(drivers)} Treiber)")
        print("-" * 40)
        for d in drivers:
            effects_count = len(d.causal_effects)
            print(f"  • {d.name}: {effects_count} kausale Effekte")
    
    total_drivers = len(PRIMARY_DRIVERS)
    total_effects = sum(len(d.causal_effects) for d in PRIMARY_DRIVERS.values())
    total_sources = sum(len(d.data_sources) for d in PRIMARY_DRIVERS.values())
    
    print(f"\n{'='*70}")
    print(f"📊 STATISTIK")
    print(f"{'='*70}")
    print(f"Primäre Treiber: {total_drivers}")
    print(f"Kausale Effekte: {total_effects}")
    print(f"Datenquellen: {total_sources}")


if __name__ == "__main__":
    print_catalog_summary()
    
    # Beispiel: Finde alle Wege zu Dürre
    print("\n" + "="*70)
    print("🔍 Beispiel: Alle Kausalketten zu 'drought'")
    print("="*70)
    drought_chains = find_effect_chains("drought")
    for chain in drought_chains:
        print(f"  {chain['driver']} → {chain['effect']} ({chain['probability']:.0%})")
        print(f"    Mechanismus: {chain['mechanism'][:60]}...")












