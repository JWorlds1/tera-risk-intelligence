"""
H3 Grid Engine - Generates H3 hexagonal grids for geographic regions
Uses the H3 library for discrete global grid system (DGGS)
"""

from typing import List, Dict, Tuple, Optional
import h3.api.basic_str as h3
from dataclasses import dataclass


@dataclass
class H3Cell:
    """Represents a single H3 hexagonal cell"""
    h3_index: str
    center_lat: float
    center_lng: float
    resolution: int
    boundary: List[Tuple[float, float]]  # List of (lat, lng) tuples


@dataclass
class H3Grid:
    """Represents a complete H3 grid for a region"""
    cells: List[H3Cell]
    center_lat: float
    center_lng: float
    resolution: int
    scale: str
    region_name: str


class H3GridEngine:
    """Engine for generating H3 hexagonal grids"""
    
    # Resolution mapping based on scale
    RESOLUTION_MAP = {
        'neighborhood': [10, 11],  # ~80m to ~40m hexagons
        'city': [8, 9],           # ~250m to ~1.2km hexagons
        'region': [6, 7]          # ~1.5km to ~6km hexagons
    }
    
    # Ring size mapping for different scales
    RING_SIZE_MAP = {
        'neighborhood': 12,
        'city': 10,
        'region': 8
    }
    
    def __init__(self):
        """Initialize the H3 Grid Engine"""
        pass
    
    def get_resolution(self, scale: str, use_fine: bool = False) -> int:
        """
        Get H3 resolution for a given scale
        
        Args:
            scale: 'neighborhood', 'city', or 'region'
            use_fine: If True, use finer resolution (higher number)
        
        Returns:
            H3 resolution (0-15)
        """
        if scale not in self.RESOLUTION_MAP:
            scale = 'city'  # Default
        
        resolutions = self.RESOLUTION_MAP[scale]
        return resolutions[1] if use_fine else resolutions[0]
    
    def generate_grid(
        self,
        center_lat: float,
        center_lng: float,
        scale: str = 'city',
        region_name: str = 'Unknown'
    ) -> H3Grid:
        """
        Generate an H3 grid centered at the given coordinates
        
        Args:
            center_lat: Center latitude
            center_lng: Center longitude
            scale: Scale of analysis ('neighborhood', 'city', 'region')
            region_name: Name of the region
        
        Returns:
            H3Grid object with all cells
        """
        resolution = self.get_resolution(scale)
        ring_size = self.RING_SIZE_MAP.get(scale, 10)
        
        # Get center H3 index
        center_h3_index = h3.latlng_to_cell(center_lat, center_lng, resolution)
        
        # Get all H3 indices in k-ring around center
        h3_indices = set([center_h3_index])
        for k in range(1, ring_size + 1):
            ring = h3.grid_ring(center_h3_index, k)
            h3_indices.update(ring)
        
        # Convert to H3Cell objects
        cells = []
        for h3_idx in h3_indices:
            # Get center coordinates (returns (lat, lng))
            center = h3.cell_to_latlng(h3_idx)
            
            # Get boundary coordinates (returns list of (lat, lng) tuples)
            boundary = h3.cell_to_boundary(h3_idx)
            
            cell = H3Cell(
                h3_index=h3_idx,
                center_lat=center[0],
                center_lng=center[1],
                resolution=resolution,
                boundary=[(lat, lng) for lat, lng in boundary]  # Already in (lat, lng) format
            )
            cells.append(cell)
        
        return H3Grid(
            cells=cells,
            center_lat=center_lat,
            center_lng=center_lng,
            resolution=resolution,
            scale=scale,
            region_name=region_name
        )
    
    def get_cell_by_index(self, h3_index: str) -> Optional[H3Cell]:
        """
        Get a single H3 cell by its index
        
        Args:
            h3_index: H3 hexagon index
        
        Returns:
            H3Cell object or None if invalid
        """
        try:
            center = h3.cell_to_latlng(h3_index)
            boundary = h3.cell_to_boundary(h3_index)
            # Get resolution by traversing parent chain
            temp_cell = h3_index
            resolution = 15  # Start at max resolution
            while temp_cell:
                parent = h3.cell_to_parent(temp_cell)
                if not parent or parent == temp_cell:
                    break
                resolution -= 1
                temp_cell = parent
                if resolution < 0:
                    resolution = 9  # Default fallback
                    break
            
            return H3Cell(
                h3_index=h3_index,
                center_lat=center[0],
                center_lng=center[1],
                resolution=resolution,
                boundary=[(lat, lng) for lat, lng in boundary]
            )
        except Exception:
            return None
    
    def get_neighbors(self, h3_index: str, k: int = 1) -> List[str]:
        """
        Get neighboring H3 cells
        
        Args:
            h3_index: H3 hexagon index
            k: Ring size (default: 1 for immediate neighbors)
        
        Returns:
            List of neighboring H3 indices
        """
        neighbors = set([h3_index])
        for ring_k in range(1, k + 1):
            ring = h3.grid_ring(h3_index, ring_k)
            neighbors.update(ring)
        return list(neighbors)
    
    def get_cells_in_polygon(
        self,
        polygon: List[Tuple[float, float]],
        resolution: int
    ) -> List[str]:
        """
        Get all H3 cells that intersect with a polygon
        
        Args:
            polygon: List of (lat, lng) tuples defining polygon
            resolution: H3 resolution
        
        Returns:
            List of H3 indices
        """
        # Use polygon_to_cells for polygon filling
        from h3.api.basic_str import LatLngPoly
        poly = LatLngPoly(exterior=tuple(polygon))
        return list(h3.polygon_to_cells(poly, resolution))
    
    def get_cells_in_bbox(
        self,
        min_lat: float,
        min_lng: float,
        max_lat: float,
        max_lng: float,
        resolution: int
    ) -> List[str]:
        """
        Get all H3 cells in a bounding box
        
        Args:
            min_lat: Minimum latitude
            min_lng: Minimum longitude
            max_lat: Maximum latitude
            max_lng: Maximum longitude
            resolution: H3 resolution
        
        Returns:
            List of H3 indices
        """
        # Create polygon from bbox
        polygon = [
            (min_lat, min_lng),
            (max_lat, min_lng),
            (max_lat, max_lng),
            (min_lat, max_lng),
            (min_lat, min_lng)  # Close polygon
        ]
        
        return self.get_cells_in_polygon(polygon, resolution)


# Example usage
if __name__ == '__main__':
    engine = H3GridEngine()
    
    # Generate grid for Jakarta
    grid = engine.generate_grid(
        center_lat=-6.2088,
        center_lng=106.8456,
        scale='city',
        region_name='Jakarta'
    )
    
    print(f"Generated {len(grid.cells)} H3 cells for {grid.region_name}")
    print(f"Resolution: {grid.resolution}")
    print(f"Center: ({grid.center_lat}, {grid.center_lng})")
    print(f"First cell: {grid.cells[0].h3_index}")

