"""
Google Maps Static API client for fetching satellite images.
"""
import logging
import httpx
from io import BytesIO
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)

def fetch_satellite_image(lat: float, lon: float, zoom: int = 16, size: str = "600x400") -> bytes | None:
    """
    Fetches a satellite image for a given coordinate.
    Returns the image bytes, or None if failed.
    """
    api_key = settings.google_maps_api_key
    if not api_key:
        logger.error("GOOGLE_MAPS_API_KEY not set; cannot fetch satellite image.")
        return None
        
    url = "https://maps.googleapis.com/maps/api/staticmap"
    params = {
        "center": f"{lat},{lon}",
        "zoom": zoom,
        "size": size,
        "maptype": "satellite",
        "key": api_key
    }
    
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            
            # Verify it's a valid image
            img = Image.open(BytesIO(resp.content))
            img.verify()
            
            return resp.content
    except Exception as e:
        logger.error(f"Failed to fetch satellite image: {e}")
        return None
