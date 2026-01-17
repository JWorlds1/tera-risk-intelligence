"""TERA Topography Foundation (MVP)

Was ist damit gelöst?
- Land/Meer pro Punkt (global_land_mask)
- Echte Höhe pro Punkt (DEM Terrarium Tiles)
- Caching (Disk + Memory) -> stabil und schnell

Hinweis:
- Terrarium ist global verfügbar und liefert reale Höhenwerte.
- Für Research/Enterprise lässt sich später Copernicus DEM / STAC sauber integrieren.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple
import math

import httpx
from global_land_mask import globe
from PIL import Image


TERRARIUM_URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"


def _deg2num(lat: float, lon: float, zoom: int) -> Tuple[int, int]:
    lat_rad = math.radians(lat)
    n = 2.0**zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile


def _pixel_xy(lat: float, lon: float, zoom: int, xtile: int, ytile: int) -> Tuple[int, int]:
    lat_rad = math.radians(lat)
    n = 2.0**zoom
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n
    px = int((x - xtile) * 256)
    py = int((y - ytile) * 256)
    return max(0, min(255, px)), max(0, min(255, py))


def decode_terrarium(rgb: Tuple[int, int, int]) -> float:
    # elevation = (R*256 + G + B/256) - 32768
    r, g, b = rgb
    return (r * 256.0 + g + b / 256.0) - 32768.0


@dataclass
class TopographyPoint:
    lat: float
    lon: float
    is_ocean: bool
    elevation_m: Optional[float]


class TopographyService:
    def __init__(
        self,
        cache_dir: Optional[str] = None,
        http_timeout_s: float = 8.0,
        mem_cache_max: int = 64,
    ):
        # Use cross-platform cache directory
        if cache_dir is None:
            import os
            # Use temp directory or project-relative cache
            base_cache = os.path.join(os.path.expanduser("~"), ".tera_cache")
            cache_dir = os.path.join(base_cache, "elevation_cache")
        
        self.cache_dir = Path(cache_dir)
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # Fallback to temp directory if cache creation fails
            import tempfile
            self.cache_dir = Path(tempfile.gettempdir()) / "tera_elevation_cache"
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = http_timeout_s
        self._mem_cache_max = mem_cache_max
        self._tile_mem: Dict[str, Image.Image] = {}

    def is_ocean(self, lat: float, lon: float) -> bool:
        try:
            return bool(globe.is_ocean(lat, lon))
        except Exception:
            return False

    def _mem_get(self, key: str) -> Optional[Image.Image]:
        return self._tile_mem.get(key)

    def _mem_put(self, key: str, img: Image.Image) -> None:
        if key in self._tile_mem:
            self._tile_mem[key] = img
            return
        if len(self._tile_mem) >= self._mem_cache_max:
            # simple eviction
            self._tile_mem.pop(next(iter(self._tile_mem)))
        self._tile_mem[key] = img

    async def elevation_m(self, lat: float, lon: float, zoom: int = 12) -> Optional[float]:
        xtile, ytile = _deg2num(lat, lon, zoom)
        px, py = _pixel_xy(lat, lon, zoom, xtile, ytile)

        key = f"z{zoom}_x{xtile}_y{ytile}"
        tile_path = self.cache_dir / f"terrarium_{key}.png"

        # in-memory cache
        img = self._mem_get(key)
        if img is not None:
            return float(decode_terrarium(img.getpixel((px, py))))

        # disk cache
        if tile_path.exists():
            try:
                img = Image.open(tile_path).convert("RGB")
                self._mem_put(key, img)
                return float(decode_terrarium(img.getpixel((px, py))))
            except Exception:
                try:
                    tile_path.unlink(missing_ok=True)
                except Exception:
                    pass

        # fetch
        url = TERRARIUM_URL.format(z=zoom, x=xtile, y=ytile)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.get(url)
                r.raise_for_status()
                tile_path.write_bytes(r.content)
                img = Image.open(tile_path).convert("RGB")
                self._mem_put(key, img)
                return float(decode_terrarium(img.getpixel((px, py))))
        except Exception:
            return None

    async def get_point(self, lat: float, lon: float) -> TopographyPoint:
        return TopographyPoint(
            lat=lat,
            lon=lon,
            is_ocean=self.is_ocean(lat, lon),
            elevation_m=await self.elevation_m(lat, lon, zoom=12),
        )
