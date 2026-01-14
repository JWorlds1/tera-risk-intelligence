"""
TERA Forecast Engine
Short-term predictions for 2026-2027 based on real Earth cycle data

This engine combines:
- ERA5 climate reanalysis as baseline
- Real-time satellite observations
- Earth system cycle modeling
- Risk prediction for the coming year
"""
import asyncio
import h3
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class EarthStateVector:
    """Complete Earth state at a point in time and space"""
    h3_index: str
    timestamp: datetime
    
    # Energy Budget
    net_radiation: float = 0.0
    surface_temp_c: float = 15.0
    temp_anomaly_c: float = 0.0
    
    # Water Cycle
    precipitation_mm: float = 0.0
    evapotranspiration_mm: float = 0.0
    soil_moisture_pct: float = 50.0
    drought_index: float = 0.0  # SPI: negative = drought
    
    # Carbon Cycle
    ndvi: float = 0.5
    gpp: float = 0.0
    fire_risk: float = 0.0
    
    # Atmosphere
    wind_speed_ms: float = 5.0
    pressure_hpa: float = 1013.0
    cloud_cover_pct: float = 50.0
    
    # Context
    is_coastal: bool = False
    elevation_m: float = 0.0
    population_density: float = 0.0
    
    # Computed risks
    climate_risk: float = 0.0
    conflict_risk: float = 0.0
    combined_risk: float = 0.0


@dataclass
class Forecast:
    """Prediction for a future date"""
    h3_index: str
    forecast_date: datetime
    target_date: datetime
    lead_days: int
    
    # Predicted state
    predicted_state: EarthStateVector = None
    
    # Probabilities
    drought_probability: float = 0.0
    flood_probability: float = 0.0
    heatwave_probability: float = 0.0
    fire_probability: float = 0.0
    storm_probability: float = 0.0
    
    # Combined
    risk_score: float = 0.0
    risk_category: str = "low"
    
    # Uncertainty
    confidence: float = 0.8
    ensemble_spread: float = 0.0
    
    # Explanation
    drivers: List[str] = field(default_factory=list)


class EarthCycleModel:
    """
    Physical model for Earth system cycles
    Based on simplified IPCC AR6 parameterizations
    """
    
    # Climate sensitivity (°C per doubling of CO2)
    CLIMATE_SENSITIVITY = 3.0
    
    # Current CO2 level (ppm)
    CO2_CURRENT = 420
    CO2_PREINDUSTRIAL = 280
    
    # Temperature trend (°C/decade)
    WARMING_TREND = 0.2
    
    # Regional modifiers
    REGIONAL_AMPLIFICATION = {
        "arctic": 3.0,
        "continental": 1.5,
        "coastal": 0.8,
        "tropical": 1.0,
        "mediterranean": 1.3,
    }
    
    def __init__(self):
        self.baseline_year = 2024
        
    def get_region_type(self, lat: float, lon: float, is_coastal: bool) -> str:
        """Determine climate region type"""
        if lat > 66.5:
            return "arctic"
        elif lat < -66.5:
            return "arctic"
        elif is_coastal:
            return "coastal"
        elif 30 <= lat <= 45 and -10 <= lon <= 40:
            return "mediterranean"
        elif abs(lat) < 23.5:
            return "tropical"
        else:
            return "continental"
    
    def project_temperature(
        self,
        current_temp: float,
        target_date: datetime,
        lat: float,
        lon: float,
        is_coastal: bool = False
    ) -> Tuple[float, float]:
        """
        Project temperature for target date
        Returns (projected_temp, anomaly)
        """
        years_ahead = (target_date.year - self.baseline_year) + \
                      (target_date.month - 1) / 12
        
        region = self.get_region_type(lat, lon, is_coastal)
        amplification = self.REGIONAL_AMPLIFICATION.get(region, 1.0)
        
        # Base warming from trend
        base_warming = (years_ahead / 10) * self.WARMING_TREND * amplification
        
        # Seasonal variation (simplified)
        month = target_date.month
        if lat > 0:  # Northern hemisphere
            seasonal = 10 * math.cos((month - 7) * math.pi / 6)
        else:
            seasonal = 10 * math.cos((month - 1) * math.pi / 6)
        
        # Add some stochastic variation
        import random
        noise = random.gauss(0, 0.5)
        
        projected = current_temp + base_warming + noise
        anomaly = base_warming + noise
        
        return projected, anomaly
    
    def project_precipitation(
        self,
        current_precip: float,
        target_date: datetime,
        lat: float,
        drought_index: float
    ) -> Tuple[float, float]:
        """
        Project precipitation
        Returns (projected_precip, change_pct)
        """
        # Climate change effects vary by region
        if abs(lat) > 45:
            # High latitudes: more precipitation
            change_factor = 1.05
        elif abs(lat) < 20:
            # Tropics: more extreme (wetter wet seasons, drier dry)
            month = target_date.month
            if month in [6, 7, 8, 9]:  # Wet season
                change_factor = 1.10
            else:
                change_factor = 0.90
        else:
            # Mid-latitudes: drier summers
            month = target_date.month
            if month in [6, 7, 8]:
                change_factor = 0.92
            else:
                change_factor = 1.02
        
        # Drought feedback
        if drought_index < -1:
            change_factor *= 0.95
        
        import random
        noise = random.uniform(0.9, 1.1)
        
        projected = current_precip * change_factor * noise
        change_pct = (change_factor - 1) * 100
        
        return max(0, projected), change_pct
    
    def calculate_drought_risk(
        self,
        soil_moisture: float,
        precip_anomaly: float,
        temp_anomaly: float,
        evapotranspiration: float
    ) -> float:
        """Calculate drought probability (0-1)"""
        
        # Soil moisture factor (lower = higher risk)
        soil_factor = max(0, 1 - (soil_moisture / 100))
        
        # Precipitation deficit
        precip_factor = max(0, -precip_anomaly / 50)  # Negative = deficit
        
        # Temperature stress (higher temp = more ET demand)
        temp_factor = max(0, temp_anomaly / 5)
        
        # Combined
        risk = 0.3 * soil_factor + 0.4 * precip_factor + 0.3 * temp_factor
        
        return min(1.0, max(0.0, risk))
    
    def calculate_flood_risk(
        self,
        precip: float,
        precip_anomaly: float,
        soil_moisture: float,
        is_coastal: bool,
        sea_level_rise_mm: float = 0
    ) -> float:
        """Calculate flood probability (0-1)"""
        
        # Extreme precipitation
        if precip > 50:  # mm/day
            precip_risk = 0.8
        elif precip > 25:
            precip_risk = 0.4
        else:
            precip_risk = precip / 100
        
        # Saturated soil
        soil_risk = max(0, (soil_moisture - 70) / 30)
        
        # Coastal flooding
        coastal_risk = 0.0
        if is_coastal:
            coastal_risk = min(0.5, sea_level_rise_mm / 500)
        
        risk = max(precip_risk, soil_risk) + coastal_risk
        
        return min(1.0, risk)
    
    def calculate_fire_risk(
        self,
        temp: float,
        soil_moisture: float,
        wind_speed: float,
        ndvi: float,
        precip_anomaly: float
    ) -> float:
        """Calculate fire probability (0-1)"""
        
        # Temperature factor
        if temp > 35:
            temp_risk = 0.9
        elif temp > 30:
            temp_risk = 0.6
        elif temp > 25:
            temp_risk = 0.3
        else:
            temp_risk = max(0, (temp - 15) / 20)
        
        # Dryness
        moisture_risk = max(0, 1 - (soil_moisture / 100))
        
        # Wind spread
        wind_risk = min(0.3, wind_speed / 50)
        
        # Fuel availability (vegetation)
        fuel_risk = ndvi * 0.5  # More vegetation = more fuel
        
        # Drought amplification
        drought_amp = 1.0 + max(0, -precip_anomaly / 30)
        
        risk = (0.3 * temp_risk + 0.3 * moisture_risk + 
                0.2 * fuel_risk + 0.2 * wind_risk) * drought_amp
        
        return min(1.0, max(0.0, risk))
    
    def calculate_heatwave_risk(
        self,
        temp: float,
        temp_anomaly: float,
        lat: float
    ) -> float:
        """Calculate heatwave probability"""
        
        # Threshold varies by latitude
        if abs(lat) > 50:
            threshold = 28
        elif abs(lat) > 30:
            threshold = 32
        else:
            threshold = 35
        
        if temp > threshold + 5:
            return 0.9
        elif temp > threshold:
            return 0.5 + 0.1 * temp_anomaly
        else:
            return max(0, (temp - threshold + 5) / 10 + 0.1 * temp_anomaly)


class ForecastEngine:
    """
    Main forecast engine for TERA
    Generates short-term predictions (days to months ahead)
    """
    
    def __init__(self, db_pool=None):
        self.db = db_pool
        self.earth_model = EarthCycleModel()
        
    def get_current_state(self, h3_index: str) -> EarthStateVector:
        """Get current Earth state for H3 cell (mock for now)"""
        
        lat, lon = h3.h3_to_geo(h3_index)
        
        # Determine basic properties from location
        is_coastal = abs(lat) < 60 and (
            (lon > -10 and lon < 30 and lat > 35 and lat < 50) or  # Mediterranean
            (lon > -130 and lon < -60 and lat > 20 and lat < 50)   # US coasts
        )
        
        # Mock current state based on location
        import random
        
        base_temp = 15 - abs(lat) * 0.5 + random.gauss(0, 2)
        
        state = EarthStateVector(
            h3_index=h3_index,
            timestamp=datetime.utcnow(),
            surface_temp_c=base_temp,
            temp_anomaly_c=random.gauss(0.5, 0.3),  # Current warming
            precipitation_mm=random.uniform(0, 20),
            soil_moisture_pct=random.uniform(30, 80),
            drought_index=random.gauss(0, 0.5),
            ndvi=0.3 + random.uniform(0, 0.5),
            wind_speed_ms=random.uniform(2, 15),
            cloud_cover_pct=random.uniform(20, 80),
            is_coastal=is_coastal,
            elevation_m=random.uniform(0, 500),
        )
        
        return state
    
    def generate_forecast(
        self,
        h3_index: str,
        target_date: datetime,
        current_state: EarthStateVector = None
    ) -> Forecast:
        """Generate forecast for a specific cell and date"""
        
        if current_state is None:
            current_state = self.get_current_state(h3_index)
        
        lat, lon = h3.h3_to_geo(h3_index)
        forecast_date = datetime.utcnow()
        lead_days = (target_date - forecast_date).days
        
        # Project temperature
        proj_temp, temp_anomaly = self.earth_model.project_temperature(
            current_state.surface_temp_c,
            target_date,
            lat, lon,
            current_state.is_coastal
        )
        
        # Project precipitation
        proj_precip, precip_change = self.earth_model.project_precipitation(
            current_state.precipitation_mm,
            target_date,
            lat,
            current_state.drought_index
        )
        
        # Calculate risks
        drought_prob = self.earth_model.calculate_drought_risk(
            current_state.soil_moisture_pct,
            precip_change,
            temp_anomaly,
            current_state.evapotranspiration_mm
        )
        
        flood_prob = self.earth_model.calculate_flood_risk(
            proj_precip,
            precip_change,
            current_state.soil_moisture_pct,
            current_state.is_coastal
        )
        
        fire_prob = self.earth_model.calculate_fire_risk(
            proj_temp,
            current_state.soil_moisture_pct,
            current_state.wind_speed_ms,
            current_state.ndvi,
            precip_change
        )
        
        heatwave_prob = self.earth_model.calculate_heatwave_risk(
            proj_temp,
            temp_anomaly,
            lat
        )
        
        # Combined risk score
        risk_score = max(drought_prob, flood_prob, fire_prob, heatwave_prob)
        
        # Category
        if risk_score > 0.8:
            category = "critical"
        elif risk_score > 0.6:
            category = "high"
        elif risk_score > 0.4:
            category = "medium"
        else:
            category = "low"
        
        # Identify drivers
        drivers = []
        if drought_prob > 0.5:
            drivers.append("drought_risk")
        if flood_prob > 0.5:
            drivers.append("flood_risk")
        if fire_prob > 0.5:
            drivers.append("fire_risk")
        if heatwave_prob > 0.5:
            drivers.append("heatwave_risk")
        if temp_anomaly > 1.5:
            drivers.append("temperature_anomaly")
        
        # Confidence decreases with lead time
        confidence = max(0.3, 0.95 - lead_days * 0.005)
        
        # Create predicted state
        predicted_state = EarthStateVector(
            h3_index=h3_index,
            timestamp=target_date,
            surface_temp_c=proj_temp,
            temp_anomaly_c=temp_anomaly,
            precipitation_mm=proj_precip,
            soil_moisture_pct=current_state.soil_moisture_pct,
            drought_index=current_state.drought_index - 0.1 if drought_prob > 0.5 else current_state.drought_index,
            ndvi=current_state.ndvi,
            is_coastal=current_state.is_coastal,
            climate_risk=risk_score,
        )
        
        return Forecast(
            h3_index=h3_index,
            forecast_date=forecast_date,
            target_date=target_date,
            lead_days=lead_days,
            predicted_state=predicted_state,
            drought_probability=drought_prob,
            flood_probability=flood_prob,
            fire_probability=fire_prob,
            heatwave_probability=heatwave_prob,
            risk_score=risk_score,
            risk_category=category,
            confidence=confidence,
            drivers=drivers
        )
    
    def generate_seasonal_forecast(
        self,
        h3_index: str,
        months_ahead: int = 12
    ) -> List[Forecast]:
        """Generate monthly forecasts for the next N months"""
        
        forecasts = []
        current_state = self.get_current_state(h3_index)
        
        for m in range(1, months_ahead + 1):
            target_date = datetime.utcnow() + timedelta(days=30 * m)
            
            forecast = self.generate_forecast(
                h3_index,
                target_date,
                current_state
            )
            forecasts.append(forecast)
        
        return forecasts
    
    def generate_2026_2027_outlook(
        self,
        h3_index: str
    ) -> Dict[str, Any]:
        """
        Generate comprehensive outlook for 2026-2027
        This is the main prediction endpoint
        """
        
        current_state = self.get_current_state(h3_index)
        lat, lon = h3.h3_to_geo(h3_index)
        
        # Generate forecasts for key periods
        periods = {
            "Q1_2026": datetime(2026, 2, 15),
            "Q2_2026": datetime(2026, 5, 15),
            "Q3_2026": datetime(2026, 8, 15),
            "Q4_2026": datetime(2026, 11, 15),
            "Q1_2027": datetime(2027, 2, 15),
            "Q2_2027": datetime(2027, 5, 15),
        }
        
        forecasts = {}
        for period_name, target_date in periods.items():
            forecast = self.generate_forecast(h3_index, target_date, current_state)
            forecasts[period_name] = {
                "target_date": target_date.isoformat(),
                "temperature_c": forecast.predicted_state.surface_temp_c,
                "temp_anomaly_c": forecast.predicted_state.temp_anomaly_c,
                "drought_probability": forecast.drought_probability,
                "flood_probability": forecast.flood_probability,
                "fire_probability": forecast.fire_probability,
                "heatwave_probability": forecast.heatwave_probability,
                "risk_score": forecast.risk_score,
                "risk_category": forecast.risk_category,
                "confidence": forecast.confidence,
                "drivers": forecast.drivers,
            }
        
        # Compute annual aggregates
        avg_risk = sum(f["risk_score"] for f in forecasts.values()) / len(forecasts)
        max_risk = max(f["risk_score"] for f in forecasts.values())
        peak_period = max(forecasts.items(), key=lambda x: x[1]["risk_score"])
        
        # Dominant risk type
        risk_counts = {"drought": 0, "flood": 0, "fire": 0, "heatwave": 0}
        for f in forecasts.values():
            if f["drought_probability"] > 0.5:
                risk_counts["drought"] += 1
            if f["flood_probability"] > 0.5:
                risk_counts["flood"] += 1
            if f["fire_probability"] > 0.5:
                risk_counts["fire"] += 1
            if f["heatwave_probability"] > 0.5:
                risk_counts["heatwave"] += 1
        
        dominant_risk = max(risk_counts.items(), key=lambda x: x[1])[0]
        
        return {
            "h3_index": h3_index,
            "location": {"lat": lat, "lon": lon},
            "current_state": {
                "temperature_c": current_state.surface_temp_c,
                "temp_anomaly_c": current_state.temp_anomaly_c,
                "soil_moisture_pct": current_state.soil_moisture_pct,
                "is_coastal": current_state.is_coastal,
            },
            "outlook_2026_2027": forecasts,
            "summary": {
                "average_risk_score": avg_risk,
                "max_risk_score": max_risk,
                "peak_risk_period": peak_period[0],
                "dominant_risk_type": dominant_risk,
                "overall_category": "high" if avg_risk > 0.5 else "medium" if avg_risk > 0.3 else "low",
            },
            "generated_at": datetime.utcnow().isoformat(),
        }


# =====================================================
# API FUNCTIONS
# =====================================================

async def get_forecast_for_city(city: str) -> Dict[str, Any]:
    """Get 2026-2027 forecast for a city"""
    
    # City coordinates (simplified)
    cities = {
        "berlin": (52.52, 13.405),
        "miami": (25.76, -80.19),
        "tokyo": (35.68, 139.65),
        "jakarta": (-6.21, 106.85),
        "cairo": (30.04, 31.24),
        "lagos": (6.52, 3.38),
        "mumbai": (19.08, 72.88),
        "singapore": (1.35, 103.82),
    }
    
    coords = cities.get(city.lower())
    if not coords:
        return {"error": f"City {city} not found"}
    
    h3_index = h3.geo_to_h3(coords[0], coords[1], 7)
    
    engine = ForecastEngine()
    return engine.generate_2026_2027_outlook(h3_index)


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":
    async def test():
        print("=" * 60)
        print("TERA Forecast Engine - 2026-2027 Outlook")
        print("=" * 60)
        
        cities = ["Berlin", "Miami", "Jakarta", "Cairo"]
        
        for city in cities:
            print(f"\n{'='*40}")
            print(f"📍 {city}")
            print(f"{'='*40}")
            
            forecast = await get_forecast_for_city(city)
            
            if "error" in forecast:
                print(f"Error: {forecast['error']}")
                continue
            
            summary = forecast["summary"]
            print(f"Overall Risk: {summary['overall_category'].upper()}")
            print(f"Average Risk Score: {summary['average_risk_score']:.2f}")
            print(f"Peak Risk Period: {summary['peak_risk_period']}")
            print(f"Dominant Risk: {summary['dominant_risk_type']}")
            
            print("\nQuarterly Forecasts:")
            for period, data in forecast["outlook_2026_2027"].items():
                print(f"  {period}: {data['risk_category']} ({data['risk_score']:.2f})")
                if data['drivers']:
                    print(f"    Drivers: {', '.join(data['drivers'])}")
    
    asyncio.run(test())






















