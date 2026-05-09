"""
ML Model Eğitim, Kaydetme ve Yükleme Testi
- Adım 1: Sentetik geçmiş veri üretir
- Adım 2: Modeli eğitir ve metrikleri raporlar (R², MAE)
- Adım 3: Modelin diske kaydedildiğini doğrular
- Adım 4: Yeni bir predictor nesnesi oluşturup diskten yükleme yaparak tahmin üretir
"""
import sys
import os
import math
import random
import shutil
from datetime import datetime, timedelta, timezone

sys.path.append("/Users/asimsinanyuksel/Desktop/runway-backend")

MODEL_DIR = os.path.join(
    "/Users/asimsinanyuksel/Desktop/runway-backend",
    "app", "services", "ml", "saved_models"
)


def generate_mock_historical_data(num_days=60):
    """
    Gerçeğe yakın sentetik hava kalitesi verisi üretir.
    - Gündüz trafik saatlerinde kirlilik artar (sinüs dalgası)
    - Hafta sonu daha düşük kirlilik (trafik az)
    - Rastgele gürültü eklenir
    """
    records = []
    base_time = datetime.now(timezone.utc) - timedelta(days=num_days)

    for i in range(num_days * 24):
        current_time = base_time + timedelta(hours=i)

        base_aqi = 22.0

        # Saatlik sinüs dalgası (08-18 arası zirve)
        hour_factor = math.sin((current_time.hour - 4) * (math.pi / 12)) * 18.0

        # Hafta sonu etkisi (Cumartesi/Pazar daha düşük)
        weekend_factor = -5.0 if current_time.weekday() >= 5 else 0.0

        # Rastgele gürültü
        noise = random.uniform(-4.0, 8.0)

        aqi_value = max(1.0, base_aqi + hour_factor + weekend_factor + noise)

        records.append({
            'station_id': 'istanbul_eminonu',
            'measured_at': current_time,
            'aqi': aqi_value
        })

    return records


def test_training_and_persistence():
    print("=" * 70)
    print("  ML MODEL EĞİTİM, KARŞILAŞTIRMA VE KALICILIK (PERSISTENCE) TESTİ")
    print("=" * 70)

    # ── Temizlik: Önceki kayıtlı modelleri sil ──
    if os.path.exists(MODEL_DIR):
        shutil.rmtree(MODEL_DIR)
        print("\n🗑  Önceki kayıtlı modeller temizlendi.\n")

    # ── Adım 1: Veri Üretimi ──
    print("ADIM 1 ▸ Geçmiş Veri Üretiliyor...")
    data = generate_mock_historical_data(num_days=60)
    print(f"  Toplam {len(data)} saatlik ölçüm üretildi (60 gün × 24 saat).\n")

    # ── Adım 2: Eğitim ──
    print("ADIM 2 ▸ Model Eğitiliyor (RF + GBM + XGBoost Ensemble)...")
    from app.services.ml.air_quality_model import AirQualityPredictor

    trainer = AirQualityPredictor.__new__(AirQualityPredictor)
    trainer.rf_model = None
    trainer.gb_model = None
    trainer.xgb_model = None
    trainer.is_trained = False
    trainer.metrics = {}

    success = trainer.train(data)

    if not success:
        print("  ❌ Eğitim başarısız oldu!")
        return

    print("  ✅ Eğitim başarılı!\n")
    print("  ┌─────────────────────────────────────────────────────┐")
    print(f"  │  Eğitilen Örnek Sayısı : {trainer.metrics['samples_trained']:>6}                    │")
    print(f"  │  MAE (Ortalama Hata)   : {trainer.metrics['mae']:>10.4f}                │")
    print(f"  │  R² Skoru              : {trainer.metrics['r2']:>10.4f}                │")
    print("  └─────────────────────────────────────────────────────┘")

    r2 = trainer.metrics['r2']
    if r2 >= 0.95:
        badge = "🏆 MÜKEMMEL"
    elif r2 >= 0.90:
        badge = "🥇 ÇOK İYİ"
    elif r2 >= 0.85:
        badge = "🥈 İYİ"
    else:
        badge = "🥉 GELİŞTİRİLMELİ"
    print(f"\n  Değerlendirme: {badge} (R² = {r2:.4f})\n")

    # ── Adım 3: Kayıt Doğrulama ──
    print("ADIM 3 ▸ Modelin Diske Kaydedildiği Kontrol Ediliyor...")
    expected_files = ["rf_model.joblib", "gb_model.joblib", "xgb_model.joblib", "metrics.joblib"]
    all_found = True
    for f in expected_files:
        path = os.path.join(MODEL_DIR, f)
        exists = os.path.exists(path)
        size_kb = os.path.getsize(path) / 1024 if exists else 0
        status = f"✅ {size_kb:.1f} KB" if exists else "❌ BULUNAMADI"
        print(f"  {f:<22} → {status}")
        if not exists:
            all_found = False

    if all_found:
        print("\n  Tüm model dosyaları başarıyla kaydedildi.\n")
    else:
        print("\n  ⚠️  Bazı model dosyaları eksik!\n")
        return

    # ── Adım 4: Diskten Yükleme ve Tahmin ──
    print("ADIM 4 ▸ Yeni Predictor Oluşturuluyor (Diskten Yükleme Testi)...")
    fresh_predictor = AirQualityPredictor()  # __init__ içinde load_model() çağrılır

    if not fresh_predictor.is_trained:
        print("  ❌ Diskten yükleme başarısız! Model eğitilmemiş olarak işaretli.")
        return

    print("  ✅ Model diskten başarıyla yüklendi!\n")
    print(f"  Yüklenen Metrikler → R²: {fresh_predictor.metrics.get('r2', 'N/A'):.4f}, "
          f"MAE: {fresh_predictor.metrics.get('mae', 'N/A'):.4f}\n")

    print("ADIM 5 ▸ Yüklenen Model İle Gerçek Tahmin Yapılıyor...")
    current_aqi = 15.93  # OpenAQ'dan gelen gerçek veri
    hours = [3, 6, 12, 24]
    forecast = fresh_predictor.predict(current_aqi, hours_ahead=hours)

    print(f"  Mevcut AQI: {current_aqi}")
    for h, val in forecast.items():
        print(f"    +{h:>2} saat sonra → AQI tahmini: {val:.2f}")

    # Fallback kontrolü: Fallback durumunda tahminler current_aqi + h*0.1 olurdu
    fallback_vals = {h: current_aqi + h * 0.1 for h in hours}
    is_fallback = all(abs(forecast[h] - fallback_vals[h]) < 0.01 for h in hours)

    if is_fallback:
        print("\n  ⚠️  DİKKAT: Tahminler Fallback (sahte) formülüyle üretilmiş!")
    else:
        print("\n  ✅ Tahminler eğitilmiş ML modeli tarafından üretildi (Fallback DEĞİL).")

    print("\n" + "=" * 70)
    print("  TÜM ADIMLAR TAMAMLANDI")
    print("=" * 70)


if __name__ == "__main__":
    test_training_and_persistence()
