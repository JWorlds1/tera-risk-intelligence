-- =====================================================
-- TERA EARTH CYCLES DATABASE SCHEMA
-- Erdzyklen: Energie, Wasser, Carbon, Atmosphäre
-- Für Echtzeit-Vorhersagen 2026-2027
-- =====================================================

-- =====================================================
-- ENERGY BUDGET (Master-Zyklus)
-- =====================================================
CREATE TABLE IF NOT EXISTS h3_energy_budget (
    h3_index VARCHAR(20) PRIMARY KEY,
    observation_date DATE NOT NULL,
    
    -- Incoming radiation (W/m²)
    shortwave_incoming REAL,        -- Kurzwellige Einstrahlung
    shortwave_reflected REAL,       -- Reflektiert (Albedo)
    
    -- Outgoing radiation
    longwave_outgoing REAL,         -- Langwellige Ausstrahlung
    net_radiation REAL,             -- Netto-Strahlung
    
    -- Surface fluxes
    sensible_heat_flux REAL,        -- Fühlbarer Wärmefluss
    latent_heat_flux REAL,          -- Latenter Wärmefluss (Verdunstung)
    ground_heat_flux REAL,          -- Bodenwärmefluss
    
    -- Albedo
    surface_albedo REAL,            -- 0-1
    cloud_albedo REAL,
    
    -- Temperature
    surface_temp_k REAL,
    air_temp_2m_k REAL,
    
    -- Source
    source VARCHAR(50) DEFAULT 'ERA5',
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_energy_date ON h3_energy_budget (observation_date DESC);

-- =====================================================
-- WATER CYCLE (Wasserkreislauf)
-- =====================================================
CREATE TABLE IF NOT EXISTS h3_water_cycle (
    h3_index VARCHAR(20) PRIMARY KEY,
    observation_date DATE NOT NULL,
    
    -- Fluxes (mm/day or kg/m²/day)
    evaporation REAL,               -- Verdunstung
    transpiration REAL,             -- Transpiration (Pflanzen)
    evapotranspiration REAL,        -- ET gesamt
    precipitation REAL,             -- Niederschlag
    runoff REAL,                    -- Abfluss
    infiltration REAL,              -- Infiltration
    snowmelt REAL,                  -- Schneeschmelze
    
    -- Storages (mm or kg/m²)
    soil_moisture_0_7cm REAL,       -- Oberflächennahe Bodenfeuchte
    soil_moisture_7_28cm REAL,      -- Mittlere Schicht
    soil_moisture_28_100cm REAL,    -- Tiefe Schicht
    groundwater_level REAL,         -- Grundwasserstand
    snow_water_equivalent REAL,     -- Schneewasseräquivalent
    
    -- Atmospheric water
    total_column_water REAL,        -- Gesamtsäule Wasserdampf
    cloud_water REAL,
    
    -- Anomalies
    precip_anomaly_pct REAL,        -- % vs. Klimatologie
    soil_moisture_anomaly REAL,
    
    -- Drought indicators
    spi_3month REAL,                -- Standardized Precipitation Index
    spei_3month REAL,               -- Standardized Precipitation-Evapotranspiration Index
    
    source VARCHAR(50) DEFAULT 'ERA5-Land',
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_water_date ON h3_water_cycle (observation_date DESC);

-- =====================================================
-- CARBON CYCLE (Kohlenstoffkreislauf)
-- =====================================================
CREATE TABLE IF NOT EXISTS h3_carbon_cycle (
    h3_index VARCHAR(20) PRIMARY KEY,
    observation_date DATE NOT NULL,
    
    -- Atmospheric CO2
    co2_concentration_ppm REAL,     -- Atmosphärische Konzentration
    co2_anomaly_ppm REAL,           -- Anomalie vs. Baseline
    
    -- Fluxes (gC/m²/day)
    gpp REAL,                       -- Gross Primary Production (Photosynthese)
    npp REAL,                       -- Net Primary Production
    respiration_ecosystem REAL,     -- Ökosystem-Respiration
    nee REAL,                       -- Net Ecosystem Exchange
    
    -- Land-Atmosphere Exchange
    land_sink REAL,                 -- Land-Senke
    
    -- Vegetation
    ndvi REAL,                      -- Normalized Difference Vegetation Index
    lai REAL,                       -- Leaf Area Index
    fpar REAL,                      -- Fraction of Absorbed PAR
    
    -- Fire emissions
    fire_carbon_emissions REAL,     -- Feuer-Emissionen (gC/m²)
    burned_area_ha REAL,            -- Verbrannte Fläche
    
    source VARCHAR(50) DEFAULT 'MODIS/ERA5',
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_carbon_date ON h3_carbon_cycle (observation_date DESC);

-- =====================================================
-- ATMOSPHERIC DYNAMICS
-- =====================================================
CREATE TABLE IF NOT EXISTS h3_atmosphere (
    h3_index VARCHAR(20) PRIMARY KEY,
    observation_time TIMESTAMP NOT NULL,
    
    -- Wind (m/s)
    wind_u_10m REAL,                -- U-Komponente
    wind_v_10m REAL,                -- V-Komponente
    wind_speed_10m REAL,            -- Geschwindigkeit
    wind_direction_deg REAL,        -- Richtung
    
    -- Pressure
    surface_pressure_hpa REAL,
    sea_level_pressure_hpa REAL,
    
    -- Boundary Layer
    boundary_layer_height REAL,     -- Grenzschichthöhe (m)
    
    -- Aerosols & Pollution
    aod_550nm REAL,                 -- Aerosol Optical Depth
    pm25_ugm3 REAL,                 -- Feinstaub
    dust_aod REAL,                  -- Staub-AOD
    
    -- Stability
    cape REAL,                      -- Convective Available Potential Energy
    cin REAL,                       -- Convective Inhibition
    
    -- Weather phenomena
    total_cloud_cover REAL,         -- 0-1
    convective_precip REAL,
    
    source VARCHAR(50) DEFAULT 'ERA5/CAMS',
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_atmo_time ON h3_atmosphere (observation_time DESC);

-- =====================================================
-- OCEAN DYNAMICS (für Küstenzellen)
-- =====================================================
CREATE TABLE IF NOT EXISTS h3_ocean (
    h3_index VARCHAR(20) PRIMARY KEY,
    observation_date DATE NOT NULL,
    
    -- Temperature
    sst_k REAL,                     -- Sea Surface Temperature
    sst_anomaly_k REAL,             -- SST Anomalie
    
    -- Currents
    current_u REAL,                 -- m/s
    current_v REAL,
    current_speed REAL,
    
    -- Sea Level
    sea_level_m REAL,               -- Relative to reference
    sea_level_anomaly_m REAL,
    
    -- Waves
    significant_wave_height REAL,   -- m
    wave_period REAL,               -- s
    
    -- Biogeochemistry
    chlorophyll_a REAL,             -- mg/m³
    oxygen_surface REAL,            -- ml/l
    
    -- Ice (polar regions)
    sea_ice_concentration REAL,     -- 0-1
    sea_ice_thickness REAL,         -- m
    
    source VARCHAR(50) DEFAULT 'Copernicus-Marine',
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ocean_date ON h3_ocean (observation_date DESC);

-- =====================================================
-- NRT OBSERVATIONS (Near Real-Time)
-- =====================================================
CREATE TABLE IF NOT EXISTS nrt_observations (
    id SERIAL PRIMARY KEY,
    h3_index VARCHAR(20),
    observation_time TIMESTAMP NOT NULL,
    
    -- Satellite info
    satellite VARCHAR(50),          -- Sentinel-2, MODIS, VIIRS, GOES
    product VARCHAR(100),
    
    -- Location
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    geom GEOMETRY(Point, 4326),
    
    -- Observation type
    obs_type VARCHAR(50),           -- fire, flood, vegetation, temperature
    
    -- Values
    value REAL,
    unit VARCHAR(20),
    confidence REAL,                -- 0-1
    
    -- Raw data
    raw_data JSONB,
    
    -- Processing
    processed BOOLEAN DEFAULT FALSE,
    ingested_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_nrt_time ON nrt_observations (observation_time DESC);
CREATE INDEX IF NOT EXISTS idx_nrt_type ON nrt_observations (obs_type);
CREATE INDEX IF NOT EXISTS idx_nrt_h3 ON nrt_observations (h3_index);

-- =====================================================
-- FORECASTS (Vorhersagen 2026-2027)
-- =====================================================
CREATE TABLE IF NOT EXISTS forecasts (
    id SERIAL PRIMARY KEY,
    h3_index VARCHAR(20) NOT NULL,
    forecast_date DATE NOT NULL,
    target_date DATE NOT NULL,      -- Vorhersageziel
    lead_days INT,                  -- Tage in die Zukunft
    
    -- Model info
    model_name VARCHAR(100),
    model_version VARCHAR(50),
    ensemble_member INT,
    
    -- Predicted variables
    temperature_2m REAL,
    precipitation REAL,
    soil_moisture REAL,
    ndvi REAL,
    
    -- Risk predictions
    drought_probability REAL,
    flood_probability REAL,
    heatwave_probability REAL,
    fire_probability REAL,
    conflict_probability REAL,
    
    -- Combined risk
    combined_risk_score REAL,
    risk_category VARCHAR(20),      -- low, medium, high, critical
    
    -- Uncertainty
    confidence_lower REAL,
    confidence_upper REAL,
    ensemble_spread REAL,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_forecast_target ON forecasts (target_date);
CREATE INDEX IF NOT EXISTS idx_forecast_h3 ON forecasts (h3_index);
CREATE UNIQUE INDEX IF NOT EXISTS idx_forecast_unique 
    ON forecasts (h3_index, target_date, model_name, COALESCE(ensemble_member, 0));

-- =====================================================
-- DATA SOURCES CATALOG
-- =====================================================
CREATE TABLE IF NOT EXISTS data_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50),           -- satellite, reanalysis, forecast, in-situ
    
    -- API Access
    base_url TEXT,
    api_type VARCHAR(50),           -- stac, rest, cds, opendap
    auth_required BOOLEAN DEFAULT FALSE,
    
    -- Coverage
    spatial_resolution_km REAL,
    temporal_resolution VARCHAR(50),
    latency VARCHAR(50),            -- NRT, daily, weekly
    
    -- Variables provided
    variables TEXT[],
    
    -- Status
    enabled BOOLEAN DEFAULT TRUE,
    last_sync TIMESTAMP,
    sync_status VARCHAR(20),
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert key data sources
INSERT INTO data_sources (name, category, base_url, api_type, spatial_resolution_km, temporal_resolution, latency, variables) VALUES
('ERA5', 'reanalysis', 'https://cds.climate.copernicus.eu', 'cds', 31, 'hourly', 'monthly', ARRAY['temperature', 'precipitation', 'wind', 'radiation', 'soil_moisture']),
('ERA5-Land', 'reanalysis', 'https://cds.climate.copernicus.eu', 'cds', 9, 'hourly', 'monthly', ARRAY['soil_moisture', 'evaporation', 'runoff', 'snow']),
('Sentinel-2', 'satellite', 'https://planetarycomputer.microsoft.com/api/stac/v1', 'stac', 0.01, '5-day', 'NRT', ARRAY['ndvi', 'evi', 'reflectance', 'land_cover']),
('Sentinel-3', 'satellite', 'https://dataspace.copernicus.eu', 'stac', 0.3, 'daily', 'NRT', ARRAY['sst', 'chlorophyll', 'fire_radiative_power']),
('MODIS', 'satellite', 'https://planetarycomputer.microsoft.com/api/stac/v1', 'stac', 0.25, 'daily', 'NRT', ARRAY['ndvi', 'lst', 'fire', 'aod']),
('VIIRS-FIRMS', 'satellite', 'https://firms.modaps.eosdis.nasa.gov/api', 'rest', 0.375, '15-min', 'NRT', ARRAY['fire_detection', 'frp']),
('GOES-18', 'satellite', 's3://noaa-goes18', 's3', 2, '15-min', 'NRT', ARRAY['cloud', 'aod', 'lst', 'fire']),
('GFS', 'forecast', 'https://nomads.ncep.noaa.gov', 'opendap', 25, '6-hourly', 'NRT', ARRAY['temperature', 'precipitation', 'wind', 'pressure']),
('ECMWF-IFS', 'forecast', 'https://data.ecmwf.int', 'cds', 9, '6-hourly', 'NRT', ARRAY['temperature', 'precipitation', 'wind']),
('Copernicus-Marine', 'reanalysis', 'https://data.marine.copernicus.eu', 'cds', 8, 'daily', 'weekly', ARRAY['sst', 'currents', 'sea_level', 'waves'])
ON CONFLICT (name) DO NOTHING;

-- =====================================================
-- CLIMATE NORMALS (1991-2020 Baseline)
-- =====================================================
CREATE TABLE IF NOT EXISTS h3_climate_normals (
    h3_index VARCHAR(20),
    month INT CHECK (month >= 1 AND month <= 12),
    
    -- Temperature normals
    temp_mean REAL,
    temp_std REAL,
    temp_min_mean REAL,
    temp_max_mean REAL,
    
    -- Precipitation normals
    precip_mean REAL,
    precip_std REAL,
    wet_days_mean REAL,
    
    -- Other
    soil_moisture_mean REAL,
    ndvi_mean REAL,
    
    PRIMARY KEY (h3_index, month)
);

-- =====================================================
-- MATERIALIZED VIEW: Current Earth State
-- =====================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS current_earth_state AS
SELECT 
    t.h3_index,
    t.country_name,
    t.climate_zone,
    t.elevation_m,
    t.is_coastal,
    
    -- Latest energy budget
    e.net_radiation,
    e.surface_temp_k - 273.15 as surface_temp_c,
    
    -- Latest water cycle
    w.precipitation,
    w.evapotranspiration,
    w.soil_moisture_0_7cm,
    w.spi_3month as drought_index,
    
    -- Latest carbon
    c.ndvi,
    c.gpp,
    c.fire_carbon_emissions,
    
    -- Latest atmosphere
    a.wind_speed_10m,
    a.total_cloud_cover,
    a.aod_550nm as aerosol
    
FROM h3_topology t
LEFT JOIN LATERAL (
    SELECT * FROM h3_energy_budget 
    WHERE h3_index = t.h3_index 
    ORDER BY observation_date DESC LIMIT 1
) e ON true
LEFT JOIN LATERAL (
    SELECT * FROM h3_water_cycle 
    WHERE h3_index = t.h3_index 
    ORDER BY observation_date DESC LIMIT 1
) w ON true
LEFT JOIN LATERAL (
    SELECT * FROM h3_carbon_cycle 
    WHERE h3_index = t.h3_index 
    ORDER BY observation_date DESC LIMIT 1
) c ON true
LEFT JOIN LATERAL (
    SELECT * FROM h3_atmosphere 
    WHERE h3_index = t.h3_index 
    ORDER BY observation_time DESC LIMIT 1
) a ON true;

SELECT 'Earth Cycles Schema erfolgreich erstellt!' as status;
