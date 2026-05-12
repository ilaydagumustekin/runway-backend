"""
VLM (Vision Language Model) based Green Area Detector.
Uses Google Gemini to estimate green area ratio from satellite images.
"""
import json
import logging
import base64
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def encode_image(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def _gemini_error_detail(status_code: int, body: str) -> str:
    try:
        data = json.loads(body)
        err = data.get("error") or {}
        msg = err.get("message") or body[:500]
        return f"HTTP {status_code}: {msg}"
    except json.JSONDecodeError:
        return f"HTTP {status_code}: {body[:500]}"


def analyze_green_area(image_bytes: bytes) -> dict[str, Any]:
    """
    Analyzes satellite image using Gemini Vision API to estimate green area percentage.
    Returns a dict with 'green_percentage' and 'confidence'.
    """
    api_key = (settings.gemini_api_key or "").strip()
    model = (settings.gemini_model or "gemini-2.0-flash").strip()

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

    gemini_url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        f"?key={api_key}"
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inlineData": {"mimeType": "image/jpeg", "data": base64_image}},
                ]
            }
        ],
        "generationConfig": {"responseMimeType": "application/json"},
    }

    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(
                gemini_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            if resp.status_code != 200:
                detail = _gemini_error_detail(resp.status_code, resp.text)
                logger.error("Gemini API error: %s", detail)
                return {
                    "green_percentage": 0.0,
                    "confidence": 0.0,
                    "error": detail,
                    "model": model,
                    "hint": _hint_for_gemini_error(resp.status_code, resp.text),
                }

            resp_body = resp.json()
            text_result = (
                resp_body.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )

            if text_result:
                return json.loads(text_result)
            return {"green_percentage": 0.0, "confidence": 0.0, "detected_areas": []}

    except httpx.HTTPError as e:
        logger.error("VLM HTTP error: %s", e)
        return {
            "green_percentage": 0.0,
            "confidence": 0.0,
            "error": str(e),
            "model": model,
        }
    except json.JSONDecodeError as e:
        logger.error("VLM JSON parse error: %s", e)
        return {
            "green_percentage": 0.0,
            "confidence": 0.0,
            "error": f"Invalid JSON from model: {e}",
            "model": model,
        }
    except Exception as e:
        logger.error("VLM analysis failed: %s", e)
        return {
            "green_percentage": 0.0,
            "confidence": 0.0,
            "error": str(e),
            "model": model,
        }


def _hint_for_gemini_error(status_code: int, body: str) -> str:
    if status_code == 403:
        return (
            "403: Anahtar kısıtlaması (HTTP referrer / Android / iOS), Generative Language API kapalı, "
            "veya faturalandırma eksik olabilir. Google AI Studio / Cloud Console’da anahtarı "
            "'Generative Language API' için sınırsız veya sunucu uyumlu yapın; gerekirse GEMINI_MODEL=gemini-1.5-flash deneyin."
        )
    if status_code == 429:
        return "Kota aşıldı; kısa süre sonra tekrar deneyin veya kotayı artırın."
    if "API_KEY_INVALID" in body or "invalid" in body.lower():
        return "API anahtarı geçersiz veya süresi dolmuş olabilir."
    return ""
