"""
VLM (Vision Language Model) based Green Area Detector.
Uses Google Gemini to estimate green area ratio from satellite images.
"""
import logging
import json
import base64
import urllib.request
import urllib.error
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

def encode_image(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode('utf-8')

def analyze_green_area(image_bytes: bytes) -> dict[str, Any]:
    """
    Analyzes satellite image using Gemini Vision API to estimate green area percentage.
    Returns a dict with 'green_percentage' and 'confidence'.
    """
    api_key = settings.gemini_api_key

    if not api_key:
        logger.error("GEMINI_API_KEY not set; cannot run VLM analysis.")
        return {
            "error": "missing_api_key",
            "message": "GEMINI_API_KEY environment variable is not configured.",
        }

    if not image_bytes:
        return {
            "error": "missing_image",
            "message": "No image bytes were provided for analysis.",
        }
        
    base64_image = encode_image(image_bytes)
    
    prompt = (
        "You are an environmental analysis AI. Analyze this satellite image. "
        "Identify all green areas (parks, gardens, trees, grass). "
        "Return the estimated green area percentage as a JSON object with this exact structure: "
        '{"green_percentage": <float 0-100>, "confidence": <float 0-1>, "detected_areas": [<string list>]}'
    )
    
    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inlineData": {"mimeType": "image/jpeg", "data": base64_image}}
            ]
        }],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    
    data = json.dumps(payload).encode("utf-8")
    
    try:
        req = urllib.request.Request(gemini_url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as response:
            resp_body = json.loads(response.read().decode())
            text_result = resp_body.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            
            if text_result:
                return json.loads(text_result)
            return {"green_percentage": 0.0, "confidence": 0.0, "detected_areas": []}
            
    except Exception as e:
        logger.error(f"VLM analysis failed: {e}")
        return {
            "green_percentage": 0.0,
            "confidence": 0.0,
            "error": str(e)
        }
