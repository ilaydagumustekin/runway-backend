"""
Mahalle Yaşam Kalitesi İndeksi (MYKI) hesaplama servisi.

Birincil yöntem: Mamdani bulanık mantık çıkarımı (fuzzy_engine).
Yedek yöntem: Basit ağırlıklı lineer normalizasyon (fuzzy sistemi
kullanılamıyorsa otomatik devreye girer).
"""

from __future__ import annotations

import logging

from app.models.environmental_data import EnvironmentalData

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Yedek (fallback) – eski basit hesaplama
# ---------------------------------------------------------------------------

def _clamp(value: float, min_value: float = 0, max_value: float = 100) -> float:
    return max(min_value, min(value, max_value))


def _normalize_inverse(value: float, good: float, bad: float) -> float:
    if bad <= good:
        return 0
    score = (bad - value) / (bad - good) * 100
    return _clamp(score)


def _normalize_direct(value: float, min_value: float, max_value: float) -> float:
    if max_value <= min_value:
        return 0
    score = (value - min_value) / (max_value - min_value) * 100
    return _clamp(score)


def _calculate_weighted_myki(aqi: float, green_area_ratio: float, noise_level_dba: float) -> float:
    """Basit ağırlıklı ortalama ile MYKI (fallback)."""
    air_score = _normalize_inverse(aqi, good=50, bad=200)
    green_score = _normalize_direct(green_area_ratio, min_value=0, max_value=100)
    noise_score = _normalize_inverse(noise_level_dba, good=40, bad=90)

    total_score = (air_score * 0.4) + (green_score * 0.35) + (noise_score * 0.25)
    return round(_clamp(total_score), 2)


# ---------------------------------------------------------------------------
# Birincil – Bulanık Mantık
# ---------------------------------------------------------------------------

_FUZZY_AVAILABLE = True

try:
    from app.services.fuzzy_engine import calculate_fuzzy_myki, myki_category
    logger.info("[FUZZY_DEBUG] fuzzy engine loaded successfully")
except Exception as _fuzzy_load_err:  # pragma: no cover
    _FUZZY_AVAILABLE = False
    logger.warning("[FUZZY_DEBUG] fuzzy engine load failed: %s", repr(_fuzzy_load_err))


def _category_from_score(score: float) -> str:
    if score < 25:
        return "low"
    elif score < 50:
        return "medium"
    elif score < 75:
        return "high"
    return "very_high"


# ---------------------------------------------------------------------------
# Ana API
# ---------------------------------------------------------------------------

def calculate_myki_from_environmental_data(
    record: EnvironmentalData,
) -> tuple[float, str]:
    """
    EnvironmentalData kaydından MYKI skoru ve kategorisi hesaplar.

    Bulanık mantık sistemi kullanılabilir durumdaysa Mamdani çıkarımı,
    aksi halde basit ağırlıklı ortalama ile hesaplanır.
    """
    aqi = record.aqi
    green_area = record.green_area_ratio
    noise = record.noise_level_dba

    if _FUZZY_AVAILABLE:
        try:
            score = calculate_fuzzy_myki(aqi, green_area, noise)
            category = myki_category(score)
            return score, category
        except Exception as calc_err:
            logger.warning("[FUZZY_DEBUG] using weighted average fallback because: %s", repr(calc_err))

    # Fallback
    if not _FUZZY_AVAILABLE:
        logger.debug("[FUZZY_DEBUG] using weighted average fallback because: fuzzy engine not loaded")
    score = _calculate_weighted_myki(aqi, green_area, noise)
    category = _category_from_score(score)
    return score, category
