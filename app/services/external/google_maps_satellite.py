"""
Google Maps Static API client for fetching satellite images.
"""
import logging
import httpx
from io import BytesIO
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)

def fetch_satellite_image(
    lat: float,
    lon: float,
    zoom: int = 16,
    size: str = "640x640",
    scale: int = 2,
) -> bytes | None:
    """
    Google Maps Static API üzerinden mahalle merkezli uydu görüntüsü getirir.

    Determinizm için:
      - Sabit zoom (16) ve sabit boyut (640x640, scale=2 → 1280x1280 px) kullanılır.
      - Aynı (lat, lon) → aynı görüntü → VLM aynı yanıtı verme şansı artar.
      - format=png ile sıkıştırma artefaktları minimuma iner.

    Başarısızsa None döner.
    """
    api_key = settings.google_maps_api_key
    if not api_key:
        logger.error("GOOGLE_MAPS_API_KEY not set; cannot fetch satellite image.")
        return None

    # Koordinatı sabit ondalığa yuvarla → Static API cache hit + identical request
    lat_q = round(float(lat), 5)
    lon_q = round(float(lon), 5)

    url = "https://maps.googleapis.com/maps/api/staticmap"
    params = {
        "center": f"{lat_q},{lon_q}",
        "zoom": zoom,
        "size": size,
        "scale": scale,
        "maptype": "satellite",
        "format": "png",
        "key": api_key,
    }

    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()

            img = Image.open(BytesIO(resp.content))
            img.verify()

            return resp.content
    except Exception as e:
        logger.error(f"Failed to fetch satellite image: {e}")
        return None
