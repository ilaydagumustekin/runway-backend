"""
Open-Meteo API üzerinden gerçek hava durumu verisi.
Ücretsiz, API key gerektirmez.
https://open-meteo.com/en/docs
"""
import json
import logging
import time
import urllib.request
import urllib.error
from typing import Any

logger = logging.getLogger(__name__)

# ── Basit önbellek (TTL 5 dakika) ──
_weather_cache: dict[str, Any] = {}
_cache_timestamp: float = 0.0
_CACHE_TTL_SECONDS = 300  # 5 dakika


def _wmo_to_condition(wmo_code: int) -> tuple[str, str]:
    """WMO hava durumu kodunu okunabilir metne çevirir."""
    mapping = {
        0: ("Açık", "sunny"),
        1: ("Az Bulutlu", "partly_cloudy"),
        2: ("Parçalı Bulutlu", "cloudy"),
        3: ("Kapalı", "overcast"),
        45: ("Sisli", "foggy"),
        48: ("Kırağılı Sis", "foggy"),
        51: ("Hafif Çisenti", "drizzle"),
        53: ("Çisenti", "drizzle"),
        55: ("Yoğun Çisenti", "drizzle"),
        61: ("Hafif Yağmur", "rainy"),
        63: ("Yağmur", "rainy"),
        65: ("Şiddetli Yağmur", "rainy"),
        71: ("Hafif Kar", "snowy"),
        73: ("Kar", "snowy"),
        75: ("Yoğun Kar", "snowy"),
        80: ("Hafif Sağanak", "rainy"),
        81: ("Sağanak", "rainy"),
        82: ("Şiddetli Sağanak", "rainy"),
        95: ("Gök Gürültülü Fırtına", "thunderstorm"),
    }
    return mapping.get(wmo_code, ("Belirsiz", "unknown"))


def fetch_current_weather(lat: float = 37.76, lon: float = 30.55) -> dict[str, Any] | None:
    """
    Open-Meteo API'den anlık hava durumu ve saatlik tahmin çeker.
    Varsayılan koordinatlar: Isparta Merkez.
    """
    global _weather_cache, _cache_timestamp

    cache_key = f"{lat:.2f},{lon:.2f}"
    now = time.time()

    # Önbellekteyse ve TTL geçmemişse döndür
    if cache_key in _weather_cache and (now - _cache_timestamp) < _CACHE_TTL_SECONDS:
        return _weather_cache[cache_key]

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,weathercode,relative_humidity_2m,wind_speed_10m"
        f"&hourly=temperature_2m,weathercode"
        f"&forecast_days=1"
        f"&timezone=Europe%2FIstanbul"
    )

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        # Anlık veriler
        current = data.get("current", {})
        temp = current.get("temperature_2m", 0)
        wmo = current.get("weathercode", 0)
        humidity = current.get("relative_humidity_2m", 0)
        wind = current.get("wind_speed_10m", 0)
        condition_text, condition_key = _wmo_to_condition(wmo)

        # Saatlik veriler (sonraki 5 saat)
        hourly = data.get("hourly", {})
        hourly_times = hourly.get("time", [])
        hourly_temps = hourly.get("temperature_2m", [])
        hourly_codes = hourly.get("weathercode", [])

        # Şu anki saatten sonraki 5 saati al
        from datetime import datetime
        now_hour = datetime.now().hour
        hourly_forecast = []
        count = 0
        for i, t_str in enumerate(hourly_times):
            hour = int(t_str.split("T")[1].split(":")[0])
            if hour >= now_hour and count < 5:
                label = "Şimdi" if count == 0 else f"{hour:02d}:00"
                h_cond_text, h_cond_key = _wmo_to_condition(hourly_codes[i] if i < len(hourly_codes) else 0)
                hourly_forecast.append({
                    "time": label,
                    "temperature": round(hourly_temps[i]) if i < len(hourly_temps) else 0,
                    "condition": h_cond_key,
                    "condition_text": h_cond_text,
                })
                count += 1

        result = {
            "temperature": round(temp),
            "condition_text": condition_text,
            "condition_key": condition_key,
            "humidity": humidity,
            "wind_speed": wind,
            "hourly_forecast": hourly_forecast,
            "source": "open-meteo",
        }

        _weather_cache[cache_key] = result
        _cache_timestamp = now
        return result

    except Exception as e:
        logger.error(f"Open-Meteo API hatası: {e}")
        return None
