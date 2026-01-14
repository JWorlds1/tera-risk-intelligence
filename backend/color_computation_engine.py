"""
Color Computation Engine - Mathematische Farbberechnung basierend auf Kontext-Tensor
Implementiert Normalisierung, Gewichtung, Interpolation und divergierende Transformationen
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from context_tensor_engine import ContextTensor


@dataclass
class RGB:
    """RGB color representation"""
    r: int
    g: int
    b: int
    
    def to_hex(self) -> str:
        """Convert to hex string"""
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"
    
    def to_rgba(self, alpha: float = 1.0) -> str:
        """Convert to RGBA string"""
        return f"rgba({self.r}, {self.g}, {self.b}, {alpha})"


@dataclass
class ColorPalette:
    """Color palette configuration"""
    low_color: RGB  # Green for low risk
    mid_color: RGB  # Yellow for medium risk
    high_color: RGB  # Red for high risk
    breakpoint: float = 50.0  # Breakpoint between low and high


class ColorComputationEngine:
    """Engine for computing colors based on context tensors"""
    
    # Standard diverging palette (ColorBrewer)
    DEFAULT_PALETTE = ColorPalette(
        low_color=RGB(44, 162, 95),    # #2ca25f (Green)
        mid_color=RGB(255, 255, 191),  # #ffffbf (Yellow)
        high_color=RGB(222, 45, 38),   # #de2d26 (Red)
        breakpoint=50.0
    )
    
    # Context-adaptive color adjustments
    WATER_COLOR = RGB(33, 150, 243)    # Blue for water bodies
    URBAN_COLOR_BOOST = RGB(10, 0, 0)  # Red boost for urban areas
    RURAL_COLOR_BOOST = RGB(0, 10, 0)  # Green boost for rural areas
    
    def __init__(self, palette: Optional[ColorPalette] = None):
        """
        Initialize the Color Computation Engine
        
        Args:
            palette: Custom color palette (default: ColorBrewer diverging)
        """
        self.palette = palette or self.DEFAULT_PALETTE
    
    def normalize_value(
        self,
        value: float,
        min_val: float,
        max_val: float,
        method: str = 'min_max'
    ) -> float:
        """
        Normalize a value to 0-1 range
        
        Args:
            value: Value to normalize
            min_val: Minimum value
            max_val: Maximum value
            method: Normalization method ('min_max', 'z_score', 'robust')
        
        Returns:
            Normalized value (0-1)
        """
        if method == 'min_max':
            if max_val == min_val:
                return 0.5
            return (value - min_val) / (max_val - min_val)
        
        elif method == 'z_score':
            # Requires mean and std_dev - simplified version
            mean = (min_val + max_val) / 2
            std_dev = (max_val - min_val) / 4  # Approximation
            if std_dev == 0:
                return 0.5
            normalized = (value - mean) / std_dev
            # Convert to 0-1 range using sigmoid
            return 1 / (1 + np.exp(-normalized))
        
        elif method == 'robust':
            # Median-based scaling (simplified)
            median = (min_val + max_val) / 2
            iqr = (max_val - min_val) / 2
            if iqr == 0:
                return 0.5
            return np.clip((value - median) / iqr, -1, 1) * 0.5 + 0.5
        
        return 0.5
    
    def interpolate_color(
        self,
        color1: RGB,
        color2: RGB,
        t: float
    ) -> RGB:
        """
        Linear interpolation between two colors
        
        Args:
            color1: First color
            color2: Second color
            t: Interpolation factor (0-1)
        
        Returns:
            Interpolated RGB color
        """
        t = np.clip(t, 0.0, 1.0)
        return RGB(
            r=int(color1.r + (color2.r - color1.r) * t),
            g=int(color1.g + (color2.g - color1.g) * t),
            b=int(color1.b + (color2.b - color1.b) * t)
        )
    
    def diverging_color(
        self,
        score: float,
        min_score: float = 0.0,
        max_score: float = 100.0,
        use_sigmoid: bool = True
    ) -> RGB:
        """
        Compute diverging color for risk score
        
        Args:
            score: Risk score (0-100)
            min_score: Minimum score
            max_score: Maximum score
            use_sigmoid: Use sigmoid function for smoother transitions
        
        Returns:
            RGB color
        """
        # Normalize score to 0-100
        normalized = self.normalize_value(score, min_score, max_score) * 100
        
        # Center at breakpoint
        t = (normalized - self.palette.breakpoint) / self.palette.breakpoint
        
        # Apply sigmoid for smoother transition
        if use_sigmoid:
            t_smooth = 1 / (1 + np.exp(-t * 2))
        else:
            t_smooth = np.clip(t, -1, 1) * 0.5 + 0.5
        
        # Interpolate based on position relative to breakpoint
        if normalized <= self.palette.breakpoint:
            # Green to Yellow
            t_local = normalized / self.palette.breakpoint
            return self.interpolate_color(
                self.palette.low_color,
                self.palette.mid_color,
                t_local
            )
        else:
            # Yellow to Red
            t_local = (normalized - self.palette.breakpoint) / (100 - self.palette.breakpoint)
            return self.interpolate_color(
                self.palette.mid_color,
                self.palette.high_color,
                t_local
            )
    
    def weighted_context_combination(
        self,
        tensor: ContextTensor,
        layer_mode: str = 'composite',
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Compute weighted combination of tensor dimensions
        
        Args:
            tensor: ContextTensor object
            layer_mode: 'composite', 'hazard', 'exposure', 'vulnerability'
            weights: Custom weights (optional)
        
        Returns:
            Combined score (0-100)
        """
        if weights is None:
            # Default weights based on layer mode
            if layer_mode == 'hazard':
                weights = {
                    'climate': 0.6,
                    'geography': 0.4
                }
            elif layer_mode == 'exposure':
                weights = {
                    'socioeconomic': 0.5,
                    'infrastructure': 0.5
                }
            elif layer_mode == 'vulnerability':
                weights = {
                    'vulnerability': 1.0
                }
            else:  # composite
                weights = {
                    'climate': 0.2,
                    'geography': 0.15,
                    'socioeconomic': 0.2,
                    'infrastructure': 0.15,
                    'vulnerability': 0.3
                }
        
        # Extract dimension values
        dim_values = {}
        
        if 'climate' in weights:
            climate = tensor.dimensions.get('climate')
            if climate:
                # Combine climate indicators
                dim_values['climate'] = (
                    climate.temp_mean * 0.3 +
                    climate.precipitation * 0.2 +
                    climate.extreme_events_frequency * 0.5
                ) / 100.0 * 100
        
        if 'geography' in weights:
            geography = tensor.dimensions.get('geography')
            if geography:
                dim_values['geography'] = (
                    (100 - geography.elevation / 10) * 0.3 +
                    (geography.coastal_proximity / 10) * 0.7
                )
        
        if 'socioeconomic' in weights:
            socio = tensor.dimensions.get('socioeconomic')
            if socio:
                dim_values['socioeconomic'] = (
                    socio.population_density / 10 +
                    (100 - socio.poverty_rate) * 0.5
                )
        
        if 'infrastructure' in weights:
            infra = tensor.dimensions.get('infrastructure')
            if infra:
                dim_values['infrastructure'] = (
                    infra.road_density * 10 +
                    (100 - infra.hospital_proximity * 5) * 0.5
                )
        
        if 'vulnerability' in weights:
            vuln = tensor.dimensions.get('vulnerability')
            if vuln:
                dim_values['vulnerability'] = (
                    vuln.social_vulnerability_index * 100 +
                    (100 - vuln.governance_quality * 100) * 0.5
                )
        
        # Weighted sum
        total_weight = sum(weights.values())
        if total_weight == 0:
            return 50.0
        
        weighted_sum = sum(
            dim_values.get(dim, 50.0) * weight
            for dim, weight in weights.items()
        )
        
        return weighted_sum / total_weight
    
    def context_adaptive_color(
        self,
        tensor: ContextTensor,
        base_color: RGB,
        layer_mode: str = 'composite'
    ) -> RGB:
        """
        Apply context-adaptive color adjustments
        
        Args:
            tensor: ContextTensor object
            base_color: Base RGB color
            layer_mode: Layer mode
        
        Returns:
            Adjusted RGB color
        """
        geography = tensor.dimensions.get('geography')
        
        # Water bodies: constant blue
        if geography and geography.water_body:
            return self.WATER_COLOR
        
        # Urban areas: boost red/orange
        if geography and geography.land_cover_class == 'Urban':
            adjusted = RGB(
                r=min(255, base_color.r + self.URBAN_COLOR_BOOST.r),
                g=max(0, base_color.g - self.URBAN_COLOR_BOOST.g),
                b=max(0, base_color.b - self.URBAN_COLOR_BOOST.b)
            )
            return adjusted
        
        # Rural areas: boost green
        if geography and geography.land_cover_class in ['Rural', 'Agriculture', 'Forest']:
            adjusted = RGB(
                r=max(0, base_color.r - self.RURAL_COLOR_BOOST.r),
                g=min(255, base_color.g + self.RURAL_COLOR_BOOST.g),
                b=max(0, base_color.b - self.RURAL_COLOR_BOOST.b)
            )
            return adjusted
        
        return base_color
    
    def compute_uncertainty_alpha(
        self,
        uncertainty_score: float,
        base_alpha: float = 0.8
    ) -> float:
        """
        Compute alpha channel based on uncertainty
        
        Args:
            uncertainty_score: Uncertainty score (0-1, higher = more uncertain)
            base_alpha: Base alpha value
        
        Returns:
            Alpha value (0-1)
        """
        # Higher uncertainty = lower alpha (more transparent)
        return base_alpha * (1 - uncertainty_score * 0.5)
    
    def compute_polygon_gradient(
        self,
        center_color: RGB,
        edge_color: RGB,
        distance_from_center: float,
        radius: float
    ) -> RGB:
        """
        Compute radial gradient color for polygon
        
        Args:
            center_color: Color at center
            edge_color: Color at edge
            distance_from_center: Distance from center (0-radius)
            radius: Polygon radius
        
        Returns:
            Interpolated RGB color
        """
        if radius == 0:
            return center_color
        
        intensity = 1 - (distance_from_center / radius)
        intensity = np.clip(intensity, 0.0, 1.0)
        
        return self.interpolate_color(edge_color, center_color, intensity)
    
    def compute_neighbor_interpolation(
        self,
        cell_color: RGB,
        neighbor_colors: List[Tuple[RGB, float]],  # (color, distance)
        influence_radius: float = 1.0
    ) -> RGB:
        """
        Interpolate color based on neighbors
        
        Args:
            cell_color: Base cell color
            neighbor_colors: List of (neighbor_color, distance) tuples
            influence_radius: Maximum influence radius
        
        Returns:
            Interpolated RGB color
        """
        if not neighbor_colors:
            return cell_color
        
        # Compute weighted average
        total_weight = 0.0
        weighted_r = 0.0
        weighted_g = 0.0
        weighted_b = 0.0
        
        for neighbor_color, distance in neighbor_colors:
            if distance > influence_radius:
                continue
            
            # Weight inversely proportional to distance
            weight = 1.0 / (1.0 + distance)
            total_weight += weight
            
            weighted_r += neighbor_color.r * weight
            weighted_g += neighbor_color.g * weight
            weighted_b += neighbor_color.b * weight
        
        if total_weight == 0:
            return cell_color
        
        # Blend with original color (50/50)
        interpolated = RGB(
            r=int((weighted_r / total_weight + cell_color.r) / 2),
            g=int((weighted_g / total_weight + cell_color.g) / 2),
            b=int((weighted_b / total_weight + cell_color.b) / 2)
        )
        
        return interpolated
    
    def compute_final_color(
        self,
        tensor: ContextTensor,
        layer_mode: str = 'composite',
        use_gradient: bool = True,
        uncertainty: float = 0.0
    ) -> Tuple[RGB, float]:
        """
        Compute final color for a context tensor
        
        Args:
            tensor: ContextTensor object
            layer_mode: Layer mode
            use_gradient: Whether to apply gradient effects
            uncertainty: Uncertainty score (0-1)
        
        Returns:
            (RGB color, alpha value)
        """
        # Compute base score
        score = self.weighted_context_combination(tensor, layer_mode)
        
        # Compute diverging color
        base_color = self.diverging_color(score)
        
        # Apply context-adaptive adjustments
        final_color = self.context_adaptive_color(tensor, base_color, layer_mode)
        
        # Compute alpha based on uncertainty
        alpha = self.compute_uncertainty_alpha(uncertainty)
        
        return final_color, alpha


# Example usage
if __name__ == '__main__':
    from context_tensor_engine import ClimateDimension, GeographyDimension
    
    engine = ColorComputationEngine()
    
    # Create test tensor
    tensor = ContextTensor(
        h3_index="87194e64dffffff",
        timestamp=None
    )
    tensor.dimensions['climate'] = ClimateDimension(
        temp_mean=25.0,
        precipitation=150.0,
        extreme_events_frequency=0.3
    )
    tensor.dimensions['geography'] = GeographyDimension(
        elevation=50.0,
        land_cover_class='Urban',
        water_body=False
    )
    
    # Compute color
    color, alpha = engine.compute_final_color(tensor, layer_mode='composite')
    print(f"Color: {color.to_hex()}, Alpha: {alpha}")
    print(f"RGBA: {color.to_rgba(alpha)}")


