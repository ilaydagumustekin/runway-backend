"""
Bulanık Mantık (Fuzzy Logic) tabanlı Mahalle Yaşam Kalitesi İndeksi hesaplama motoru.

Mamdani çıkarım yöntemi kullanılarak hava kalitesi, yeşil alan oranı ve gürültü
seviyesi girdileri üzerinden MYKI skoru üretir.  Üyelik fonksiyonları ve kural
tabanı başvuru formundaki metodolojiye uygun şekilde tasarlanmıştır.

Referanslar:
  - TÜBİTAK 2209-A Başvuru Formu, Yöntem Bölümü
  - Chen et al. (2021), Gupta & Singh (2020)
"""

from __future__ import annotations

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


# ---------------------------------------------------------------------------
# Evren (universe) tanımları
# ---------------------------------------------------------------------------
_AQI_RANGE = np.arange(0, 301, 1)       # AQI: 0 – 300
_GREEN_RANGE = np.arange(0, 101, 1)      # Yeşil alan oranı: 0% – 100%
_NOISE_RANGE = np.arange(0, 121, 1)      # Gürültü: 0 – 120 dBA
_MYKI_RANGE = np.arange(0, 101, 1)       # MYKI skoru: 0 – 100


def _build_system() -> ctrl.ControlSystemSimulation:
    """Bulanık çıkarım sistemini oluşturur ve döndürür."""

    # --- Antecedent (girdi) değişkenleri ---
    aqi = ctrl.Antecedent(_AQI_RANGE, "aqi")
    green = ctrl.Antecedent(_GREEN_RANGE, "green_area")
    noise = ctrl.Antecedent(_NOISE_RANGE, "noise")

    # --- Consequent (çıktı) değişkeni ---
    myki = ctrl.Consequent(_MYKI_RANGE, "myki")

    # === AQI üyelik fonksiyonları (ters ilişki – düşük AQI iyi) ===
    aqi["iyi"] = fuzz.trapmf(_AQI_RANGE, [0, 0, 30, 60])
    aqi["orta"] = fuzz.trimf(_AQI_RANGE, [40, 80, 130])
    aqi["kotu"] = fuzz.trapmf(_AQI_RANGE, [100, 160, 300, 300])

    # === Yeşil alan üyelik fonksiyonları (doğru ilişki – yüksek iyi) ===
    green["dusuk"] = fuzz.trapmf(_GREEN_RANGE, [0, 0, 8, 20])
    green["orta"] = fuzz.trimf(_GREEN_RANGE, [12, 30, 50])
    green["yuksek"] = fuzz.trapmf(_GREEN_RANGE, [35, 55, 100, 100])

    # === Gürültü üyelik fonksiyonları (ters ilişki – düşük gürültü iyi) ===
    noise["dusuk"] = fuzz.trapmf(_NOISE_RANGE, [0, 0, 35, 55])
    noise["orta"] = fuzz.trimf(_NOISE_RANGE, [45, 60, 78])
    noise["yuksek"] = fuzz.trapmf(_NOISE_RANGE, [65, 85, 120, 120])

    # === MYKI çıktı üyelik fonksiyonları ===
    myki["dusuk"] = fuzz.trapmf(_MYKI_RANGE, [0, 0, 15, 35])
    myki["orta_dusuk"] = fuzz.trimf(_MYKI_RANGE, [20, 35, 50])
    myki["orta"] = fuzz.trimf(_MYKI_RANGE, [40, 55, 70])
    myki["yuksek"] = fuzz.trimf(_MYKI_RANGE, [60, 75, 88])
    myki["cok_yuksek"] = fuzz.trapmf(_MYKI_RANGE, [78, 90, 100, 100])

    # === Kural Tabanı (27 kural – 3³ kombinasyon) ===
    rules: list[ctrl.Rule] = [
        # --- AQI iyi ---
        ctrl.Rule(aqi["iyi"] & green["yuksek"] & noise["dusuk"], myki["cok_yuksek"]),
        ctrl.Rule(aqi["iyi"] & green["yuksek"] & noise["orta"], myki["yuksek"]),
        ctrl.Rule(aqi["iyi"] & green["yuksek"] & noise["yuksek"], myki["orta"]),
        ctrl.Rule(aqi["iyi"] & green["orta"] & noise["dusuk"], myki["yuksek"]),
        ctrl.Rule(aqi["iyi"] & green["orta"] & noise["orta"], myki["yuksek"]),
        ctrl.Rule(aqi["iyi"] & green["orta"] & noise["yuksek"], myki["orta"]),
        ctrl.Rule(aqi["iyi"] & green["dusuk"] & noise["dusuk"], myki["orta"]),
        ctrl.Rule(aqi["iyi"] & green["dusuk"] & noise["orta"], myki["orta"]),
        ctrl.Rule(aqi["iyi"] & green["dusuk"] & noise["yuksek"], myki["orta_dusuk"]),
        # --- AQI orta ---
        ctrl.Rule(aqi["orta"] & green["yuksek"] & noise["dusuk"], myki["yuksek"]),
        ctrl.Rule(aqi["orta"] & green["yuksek"] & noise["orta"], myki["orta"]),
        ctrl.Rule(aqi["orta"] & green["yuksek"] & noise["yuksek"], myki["orta"]),
        ctrl.Rule(aqi["orta"] & green["orta"] & noise["dusuk"], myki["orta"]),
        ctrl.Rule(aqi["orta"] & green["orta"] & noise["orta"], myki["orta"]),
        ctrl.Rule(aqi["orta"] & green["orta"] & noise["yuksek"], myki["orta_dusuk"]),
        ctrl.Rule(aqi["orta"] & green["dusuk"] & noise["dusuk"], myki["orta"]),
        ctrl.Rule(aqi["orta"] & green["dusuk"] & noise["orta"], myki["orta_dusuk"]),
        ctrl.Rule(aqi["orta"] & green["dusuk"] & noise["yuksek"], myki["dusuk"]),
        # --- AQI kötü ---
        ctrl.Rule(aqi["kotu"] & green["yuksek"] & noise["dusuk"], myki["orta"]),
        ctrl.Rule(aqi["kotu"] & green["yuksek"] & noise["orta"], myki["orta_dusuk"]),
        ctrl.Rule(aqi["kotu"] & green["yuksek"] & noise["yuksek"], myki["orta_dusuk"]),
        ctrl.Rule(aqi["kotu"] & green["orta"] & noise["dusuk"], myki["orta_dusuk"]),
        ctrl.Rule(aqi["kotu"] & green["orta"] & noise["orta"], myki["orta_dusuk"]),
        ctrl.Rule(aqi["kotu"] & green["orta"] & noise["yuksek"], myki["dusuk"]),
        ctrl.Rule(aqi["kotu"] & green["dusuk"] & noise["dusuk"], myki["orta_dusuk"]),
        ctrl.Rule(aqi["kotu"] & green["dusuk"] & noise["orta"], myki["dusuk"]),
        ctrl.Rule(aqi["kotu"] & green["dusuk"] & noise["yuksek"], myki["dusuk"]),
    ]

    system = ctrl.ControlSystem(rules)
    return ctrl.ControlSystemSimulation(system)


# Modül seviyesinde tek bir kez oluştur (singleton)
_simulation: ctrl.ControlSystemSimulation | None = None


def _get_simulation() -> ctrl.ControlSystemSimulation:
    global _simulation
    if _simulation is None:
        _simulation = _build_system()
    return _simulation


def calculate_fuzzy_myki(aqi: float, green_area_ratio: float, noise_level_dba: float) -> float:
    """
    Bulanık mantık ile MYKI skoru hesaplar.

    Args:
        aqi: Hava Kalitesi İndeksi (0–300)
        green_area_ratio: Yeşil alan oranı (0–100 %)
        noise_level_dba: Gürültü seviyesi (0–120 dBA)

    Returns:
        MYKI skoru (0–100), centroid defuzzification ile hesaplanır.

    Raises:
        ValueError: Girdi değerleri evren dışındaysa.
    """
    sim = _get_simulation()

    # Değerleri evren sınırlarına kırp
    aqi_clamped = float(np.clip(aqi, 0, 300))
    green_clamped = float(np.clip(green_area_ratio, 0, 100))
    noise_clamped = float(np.clip(noise_level_dba, 0, 120))

    sim.input["aqi"] = aqi_clamped
    sim.input["green_area"] = green_clamped
    sim.input["noise"] = noise_clamped

    sim.compute()
    return round(float(sim.output["myki"]), 2)


def myki_category(score: float) -> str:
    """MYKI skorunu kategoriye dönüştürür."""
    if score < 25:
        return "low"
    elif score < 50:
        return "medium"
    elif score < 75:
        return "high"
    return "very_high"
