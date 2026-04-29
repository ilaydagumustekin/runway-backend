from datetime import datetime, timedelta


def predict_air_quality_for_next_hours(neighborhood_id: int, hours: int = 24) -> dict:
    now = datetime.utcnow()
    points = []

    for index in range(0, min(max(hours, 24), 72), 6):
        points.append(
            {
                "timestamp": (now + timedelta(hours=index)).isoformat(),
                "predicted_aqi": 55 + index * 0.3,
                "predicted_pm25": 18 + index * 0.2,
            }
        )

    return {
        "neighborhood_id": neighborhood_id,
        "horizon_hours": hours,
        "source": "placeholder-model",
        "forecast": points,
    }
