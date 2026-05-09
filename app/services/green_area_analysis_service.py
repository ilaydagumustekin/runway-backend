import logging
from app.models.neighborhood import Neighborhood
from app.services.external.google_maps_satellite import fetch_satellite_image
from app.services.vlm.green_area_detector import analyze_green_area

logger = logging.getLogger(__name__)

def analyze_neighborhood_green_area(neighborhood: Neighborhood) -> dict:
    """
    Mahalle koordinatlarına göre uydu görüntüsünü alır ve VLM ile yeşil alan analizi yapar.
    """
    if not neighborhood.latitude or not neighborhood.longitude:
        return {
            "neighborhood_id": neighborhood.id,
            "status": "error",
            "message": "Neighborhood coordinates are missing."
        }
        
    image_bytes = fetch_satellite_image(neighborhood.latitude, neighborhood.longitude)
    if not image_bytes:
        return {
            "neighborhood_id": neighborhood.id,
            "status": "error",
            "message": "Failed to fetch satellite image."
        }
        
    analysis_result = analyze_green_area(image_bytes)
    
    return {
        "neighborhood_id": neighborhood.id,
        "status": "success",
        "analysis": analysis_result
    }
