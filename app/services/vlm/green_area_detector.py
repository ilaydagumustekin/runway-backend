"""
Yeşil alan oranı: Vercel AI Gateway üzerinden OpenAI uyumlu vision modeli.

Dokümantasyon: https://vercel.com/docs/ai-gateway
OpenAI SDK / REST: base_url https://ai-gateway.vercel.sh/v1 , Authorization: Bearer AI_GATEWAY_API_KEY
Model örneği: openai/gpt-4o-mini

Robustluk stratejisi:
  - temperature=0 + seed → deterministik çıktı (provider destekliyorsa)
  - Net metodoloji (10x10 ızgara, piksel oranı) içeren prompt
  - N defa örnekle, medyanı al (outlier'a karşı)
  - Çıktıyı 0-100'e clamp + 1 ondalığa yuvarla
"""
from __future__ import annotations

import json
import logging
import base64
import re
import statistics
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "You are a deterministic remote-sensing analyst. "
    "Given a satellite or aerial image, you estimate the percentage of the image area covered by vegetation. "
    "Always follow the methodology exactly and always return the same answer for the same image."
)

USER_PROMPT = (
    "TASK: Estimate the vegetation cover percentage of this satellite image.\n\n"
    "DEFINITION of 'green / vegetation':\n"
    "  - Trees, forest canopy, shrubs, hedges\n"
    "  - Grass, lawns, parks, gardens, agricultural fields with active vegetation\n"
    "  - Any clearly green/olive pixels indicating live plants\n"
    "NOT vegetation: buildings, roads, parking lots, bare soil, water, rooftops "
    "(even if painted green), shadows, dry/yellow grass, sand.\n\n"
    "METHODOLOGY (must follow):\n"
    "  1. Mentally divide the image into a 10x10 grid (100 cells).\n"
    "  2. For each cell, decide what fraction (0, 0.25, 0.5, 0.75, 1.0) is vegetation.\n"
    "  3. Sum the fractions and multiply by 1 to get vegetation_percentage (0-100).\n"
    "  4. Round to the nearest 1 (integer percent).\n"
    "  5. Set confidence in [0, 1] based on image clarity, cloud cover, and shadows.\n\n"
    "OUTPUT: Respond with ONE single JSON object only. No prose, no markdown. Exact schema:\n"
    '{"green_percentage": <integer 0-100>, '
    '"confidence": <float 0-1, two decimals>, '
    '"detected_areas": [<short string>, ...]}\n'
    "Examples of detected_areas entries: \"park\", \"tree_canopy\", \"lawn\", \"agricultural_field\".\n"
)


def encode_image(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def _image_mime_type(image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    return "image/jpeg"


def _gateway_error_detail(status_code: int, body: str) -> str:
    try:
        data = json.loads(body)
        err = data.get("error") or {}
        if isinstance(err, dict):
            msg = err.get("message") or err.get("code") or body[:500]
        else:
            msg = str(err) or body[:500]
        return f"HTTP {status_code}: {msg}"
    except json.JSONDecodeError:
        return f"HTTP {status_code}: {body[:500]}"


def _parse_json_from_content(content: str) -> dict[str, Any]:
    text = (content or "").strip()
    if not text:
        raise ValueError("empty model content")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if fence:
        return json.loads(fence.group(1).strip())
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError(f"no JSON object in model output: {text[:200]}...")


def _hint_for_gateway_error(status_code: int, body: str) -> str:
    if status_code == 401:
        return "AI_GATEWAY_API_KEY geçersiz veya eksik; Vercel AI Gateway panelinden anahtar oluşturun."
    if status_code == 429:
        return "Kota veya hız limiti; kısa süre sonra tekrar deneyin."
    if status_code == 402 or "insufficient" in body.lower():
        return "Gateway / sağlayıcı faturalandırma veya kredi kontrolü gerekebilir."
    return "https://vercel.com/docs/ai-gateway adresindeki model ve auth gereksinimlerini doğrulayın."


def _validate_sample(parsed: dict[str, Any]) -> tuple[float, float, list[str]] | None:
    """parsed dict'i (green%, conf, detected) tuple'a normalize eder; geçersizse None."""
    raw_green = parsed.get("green_percentage")
    if raw_green is None:
        return None
    try:
        green = float(raw_green)
    except (TypeError, ValueError):
        return None
    if green != green:  # NaN
        return None
    green = max(0.0, min(100.0, green))

    raw_conf = parsed.get("confidence", 0.0)
    try:
        conf = float(raw_conf)
    except (TypeError, ValueError):
        conf = 0.0
    if conf != conf:
        conf = 0.0
    conf = max(0.0, min(1.0, conf))

    detected = parsed.get("detected_areas") or []
    if not isinstance(detected, list):
        detected = [str(detected)]
    detected = [str(x) for x in detected if x is not None][:10]

    return green, conf, detected


def _single_call(
    client: httpx.Client,
    url: str,
    api_key: str,
    model: str,
    data_url: str,
    seed: int,
    temperature: float,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "temperature": temperature,
        "top_p": 1.0,
        "seed": seed,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": USER_PROMPT},
                    {"type": "image_url", "image_url": {"url": data_url, "detail": "high"}},
                ],
            },
        ],
        "max_tokens": 400,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    resp = client.post(url, json=payload, headers=headers)
    if resp.status_code == 400 and "response_format" in resp.text.lower():
        payload.pop("response_format", None)
        resp = client.post(url, json=payload, headers=headers)
    if resp.status_code != 200:
        detail = _gateway_error_detail(resp.status_code, resp.text)
        logger.error("AI Gateway error: %s", detail)
        return {
            "ok": False,
            "error": detail,
            "hint": _hint_for_gateway_error(resp.status_code, resp.text),
        }

    body = resp.json()
    choices = body.get("choices") or []
    if not choices:
        return {"ok": False, "error": "empty_choices"}
    content = (choices[0].get("message") or {}).get("content") or ""
    try:
        parsed = _parse_json_from_content(content)
    except (json.JSONDecodeError, ValueError) as e:
        return {"ok": False, "error": f"Invalid JSON from model: {e}"}
    return {"ok": True, "parsed": parsed, "raw_content": content}


def analyze_green_area(image_bytes: bytes) -> dict[str, Any]:
    """
    Uydu görüntüsünden yeşil alan yüzdesi tahmini (robust).
    N örnek alır, medyanı döndürür.
    """
    api_key = (settings.ai_gateway_api_key or "").strip()
    base = (settings.ai_gateway_base_url or "https://ai-gateway.vercel.sh/v1").rstrip("/")
    model = (settings.green_area_gateway_model or "openai/gpt-4o-mini").strip()
    n_samples = max(1, int(getattr(settings, "green_area_samples", 3)))
    temperature = float(getattr(settings, "green_area_temperature", 0.0))
    base_seed = int(getattr(settings, "green_area_seed", 42))

    if not api_key:
        logger.error("AI_GATEWAY_API_KEY not set; cannot run green area vision analysis.")
        return {
            "error": "missing_api_key",
            "message": "AI_GATEWAY_API_KEY is not configured (Vercel AI Gateway).",
        }

    if not image_bytes:
        return {
            "error": "missing_image",
            "message": "No image bytes were provided for analysis.",
        }

    mime = _image_mime_type(image_bytes)
    b64 = encode_image(image_bytes)
    data_url = f"data:{mime};base64,{b64}"
    url = f"{base}/chat/completions"

    samples: list[tuple[float, float, list[str]]] = []
    last_error: dict[str, Any] | None = None

    try:
        with httpx.Client(timeout=120.0) as client:
            for i in range(n_samples):
                result = _single_call(
                    client=client,
                    url=url,
                    api_key=api_key,
                    model=model,
                    data_url=data_url,
                    seed=base_seed + i,
                    temperature=temperature,
                )
                if not result.get("ok"):
                    last_error = result
                    logger.warning("Green area sample %d failed: %s", i + 1, result.get("error"))
                    continue
                validated = _validate_sample(result["parsed"])
                if validated is None:
                    last_error = {"error": "invalid_payload", "raw": result.get("raw_content", "")[:200]}
                    logger.warning("Green area sample %d invalid payload", i + 1)
                    continue
                samples.append(validated)
    except httpx.HTTPError as e:
        logger.error("AI Gateway HTTP error: %s", e)
        return {
            "green_percentage": 0.0,
            "confidence": 0.0,
            "error": str(e),
            "model": model,
        }
    except Exception as e:
        logger.error("Green area analysis failed: %s", e)
        return {
            "green_percentage": 0.0,
            "confidence": 0.0,
            "error": str(e),
            "model": model,
        }

    if not samples:
        err = (last_error or {}).get("error", "no_valid_samples")
        return {
            "green_percentage": 0.0,
            "confidence": 0.0,
            "error": err,
            "model": model,
            "hint": (last_error or {}).get("hint"),
            "samples_collected": 0,
        }

    greens = [s[0] for s in samples]
    confs = [s[1] for s in samples]
    merged_detected: list[str] = []
    seen: set[str] = set()
    for _, _, det in samples:
        for tag in det:
            key = tag.lower().strip()
            if key and key not in seen:
                seen.add(key)
                merged_detected.append(tag)

    median_green = statistics.median(greens)
    spread = max(greens) - min(greens) if len(greens) > 1 else 0.0
    mean_conf = sum(confs) / len(confs)

    # Tutarsızlığa göre güveni cezalandır (örnekler çok dağılmışsa)
    consistency_penalty = min(spread / 100.0, 0.5)
    adjusted_conf = max(0.0, min(1.0, mean_conf * (1.0 - consistency_penalty)))

    return {
        "green_percentage": round(float(median_green), 1),
        "confidence": round(float(adjusted_conf), 2),
        "detected_areas": merged_detected,
        "model": model,
        "samples": [round(g, 1) for g in greens],
        "samples_collected": len(samples),
        "spread": round(spread, 1),
    }
