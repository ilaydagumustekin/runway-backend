import logging
from app.schemas.validation import ValidationResult

logger = logging.getLogger(__name__)

def validate_metric(indicator_name: str, measured: float | None, reference: float | None, tolerance_percent: float = 20.0) -> dict:
    """
    Ölçülen değeri referans değer ile karşılaştırır.
    measured veya reference yoksa is_valid=False döner; numerik alanlar None olur.
    """
    if measured is None:
        return {
            "indicator": indicator_name,
            "measured_value": None,
            "reference_value": round(reference, 2) if reference is not None else None,
            "absolute_error": None,
            "percentage_error": None,
            "is_valid": False,
            "status_message": "Olcum verisi bulunamadi",
        }

    if reference is None:
        return {
            "indicator": indicator_name,
            "measured_value": round(measured, 2),
            "reference_value": None,
            "absolute_error": None,
            "percentage_error": None,
            "is_valid": False,
            "status_message": "Referans veri bulunamadi",
        }

    abs_error = abs(measured - reference)
    pct_error = (abs_error / reference * 100) if reference > 0 else 0

    is_valid = pct_error <= tolerance_percent

    return {
        "indicator": indicator_name,
        "measured_value": round(measured, 2),
        "reference_value": round(reference, 2),
        "absolute_error": round(abs_error, 2),
        "percentage_error": round(pct_error, 2),
        "is_valid": is_valid,
        "status_message": "Basarili" if is_valid else f"Hata payi ({pct_error:.1f}%) toleransin ({tolerance_percent}%) uzerinde.",
    }
