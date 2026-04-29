from app.models.environmental_data import EnvironmentalData


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


def calculate_myki_from_environmental_data(record: EnvironmentalData) -> tuple[float, str]:
    air_score = _normalize_inverse(record.aqi, good=50, bad=200)
    green_score = _normalize_direct(record.green_area_ratio, min_value=0, max_value=100)
    noise_score = _normalize_inverse(record.noise_level_dba, good=40, bad=90)

    total_score = (air_score * 0.4) + (green_score * 0.35) + (noise_score * 0.25)
    total_score = round(_clamp(total_score), 2)

    if total_score < 25:
        category = "low"
    elif total_score < 50:
        category = "medium"
    elif total_score < 75:
        category = "high"
    else:
        category = "very high"

    return total_score, category
