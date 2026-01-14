#!/usr/bin/env python3
"""
Bild-Verarbeitung für Geodaten-Prognose
CLIP-Embeddings für Multi-Modal Vektorraum
"""
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
import numpy as np
from PIL import Image
import requests
from io import BytesIO

sys.path.append(str(Path(__file__).parent))

from rich.console import Console

console = Console()


class ImageProcessor:
    """Verarbeitet Bilder für Geodaten-Analyse"""
    
    def __init__(self):
        self.clip_available = False
        self.clip_model = None
        self.clip_processor = None
        
        # Prüfe CLIP-Installation
        try:
            import clip
            import torch
            self.clip_available = True
            console.print("[green]✅ CLIP verfügbar[/green]")
        except ImportError:
            console.print("[yellow]⚠️  CLIP nicht installiert. Installiere mit: pip install git+https://github.com/openai/CLIP.git[/yellow]")
            console.print("[yellow]   Alternative: Verwende OpenAI CLIP API oder andere Embedding-Modelle[/yellow]")
    
    def load_clip_model(self, model_name: str = "ViT-B/32"):
        """Lade CLIP-Modell"""
        if not self.clip_available:
            return False
        
        try:
            import clip
            import torch
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.clip_model, self.clip_processor = clip.load(model_name, device=device)
            self.device = device
            
            console.print(f"[green]✅ CLIP-Modell geladen: {model_name} auf {device}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ CLIP-Ladefehler: {e}[/red]")
            return False
    
    def download_image(self, url: str, timeout: int = 10) -> Optional[Image.Image]:
        """Lade Bild von URL"""
        try:
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status()
            
            # Prüfe Content-Type
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                return None
            
            # Lade Bild
            image = Image.open(BytesIO(response.content))
            return image
        except Exception as e:
            console.print(f"[yellow]⚠️  Bild-Download fehlgeschlagen {url}: {e}[/yellow]")
            return None
    
    def extract_clip_embedding(self, image: Image.Image) -> Optional[np.ndarray]:
        """Extrahiere CLIP-Embedding aus Bild"""
        if not self.clip_available or self.clip_model is None:
            return None
        
        try:
            import torch
            
            # Preprocess Bild
            image_tensor = self.clip_processor(image).unsqueeze(0).to(self.device)
            
            # Extrahiere Embedding
            with torch.no_grad():
                image_features = self.clip_model.encode_image(image_tensor)
                # Normalisiere
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            # Konvertiere zu numpy
            embedding = image_features.cpu().numpy()[0]
            
            return embedding
        except Exception as e:
            console.print(f"[red]❌ CLIP-Embedding-Fehler: {e}[/red]")
            return None
    
    def process_image_url(self, url: str) -> Optional[np.ndarray]:
        """Verarbeite Bild von URL und extrahiere Embedding"""
        image = self.download_image(url)
        if image is None:
            return None
        
        embedding = self.extract_clip_embedding(image)
        return embedding
    
    def process_image_batch(self, urls: List[str], max_images: int = 50) -> Dict[str, np.ndarray]:
        """Verarbeite mehrere Bilder"""
        embeddings = {}
        
        if not self.clip_available:
            console.print("[yellow]⚠️  CLIP nicht verfügbar, überspringe Bild-Verarbeitung[/yellow]")
            return embeddings
        
        if self.clip_model is None:
            if not self.load_clip_model():
                return embeddings
        
        console.print(f"[cyan]🖼️  Verarbeite {min(len(urls), max_images)} Bilder...[/cyan]")
        
        for i, url in enumerate(urls[:max_images]):
            try:
                embedding = self.process_image_url(url)
                if embedding is not None:
                    embeddings[url] = embedding
                    if (i + 1) % 10 == 0:
                        console.print(f"  ✅ {i + 1}/{min(len(urls), max_images)} Bilder verarbeitet")
            except Exception as e:
                console.print(f"  ⚠️  Fehler bei {url}: {e}")
                continue
        
        console.print(f"[green]✅ {len(embeddings)} Bild-Embeddings extrahiert[/green]")
        return embeddings
    
    def extract_geospatial_features_from_image(
        self,
        image: Image.Image,
        coordinates: tuple
    ) -> Dict[str, Any]:
        """Extrahiere geospatiale Features aus Bild"""
        features = {
            'coordinates': coordinates,
            'image_size': image.size,
            'image_mode': image.mode,
            'has_geospatial_data': False
        }
        
        # Versuche EXIF-Daten zu extrahieren
        try:
            exif = image._getexif()
            if exif:
                # GPS-Daten aus EXIF
                gps_info = exif.get(34853)  # GPSInfo tag
                if gps_info:
                    features['has_geospatial_data'] = True
                    features['exif_gps'] = gps_info
        except:
            pass
        
        return features


class GeospatialImageAnalyzer:
    """Analysiert Bilder für Geodaten-Prognose"""
    
    def __init__(self):
        self.processor = ImageProcessor()
    
    def analyze_city_images(
        self,
        city: str,
        image_urls: List[str],
        coordinates: tuple
    ) -> Dict[str, Any]:
        """Analysiere Bilder für eine Stadt"""
        console.print(f"\n[bold cyan]🖼️  Analysiere Bilder für {city}[/bold cyan]")
        
        # Verarbeite Bilder
        embeddings = self.processor.process_image_batch(image_urls, max_images=20)
        
        # Extrahiere Features
        features = []
        for url, embedding in embeddings.items():
            try:
                image = self.processor.download_image(url)
                if image:
                    geo_features = self.processor.extract_geospatial_features_from_image(
                        image, coordinates
                    )
                    features.append({
                        'url': url,
                        'embedding': embedding.tolist(),  # Für JSON-Serialisierung
                        'features': geo_features
                    })
            except Exception as e:
                console.print(f"  ⚠️  Fehler bei {url}: {e}")
                continue
        
        return {
            'city': city,
            'coordinates': coordinates,
            'total_images': len(image_urls),
            'processed_images': len(embeddings),
            'features': features
        }


if __name__ == "__main__":
    # Test
    analyzer = GeospatialImageAnalyzer()
    
    test_urls = [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg"
    ]
    
    result = analyzer.analyze_city_images(
        "Athens",
        test_urls,
        (37.9838, 23.7275)
    )
    
    console.print(f"\n[green]✅ Analyse abgeschlossen:[/green]")
    console.print(f"  Verarbeitet: {result['processed_images']}/{result['total_images']}")



