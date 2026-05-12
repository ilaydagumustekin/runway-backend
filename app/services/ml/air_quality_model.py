"""
Makine öğrenmesi tabanlı hava kalitesi tahmin modeli.
Random Forest, Gradient Boosting ve XGBoost algoritmaları kullanılarak tahminler üretilir.
"""
import os
import logging
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)

_MODEL_AVAILABLE = True
_XGB_AVAILABLE = True
_IMPORT_ERRORS: list[str] = []

try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score
except ImportError as e:
    _MODEL_AVAILABLE = False
    _IMPORT_ERRORS.append(f"scikit-learn: {e}")

try:
    import joblib
except ImportError as e:
    _MODEL_AVAILABLE = False
    _IMPORT_ERRORS.append(f"joblib: {e}")

try:
    import pandas as pd
except ImportError as e:
    _MODEL_AVAILABLE = False
    _IMPORT_ERRORS.append(f"pandas: {e}")

# xgboost optional: yoksa RF+GB ensemble ile devam
try:
    from xgboost import XGBRegressor
except ImportError as e:
    _XGB_AVAILABLE = False
    XGBRegressor = None  # type: ignore[assignment]
    _IMPORT_ERRORS.append(f"xgboost (optional): {e}")

if _IMPORT_ERRORS:
    logger.warning("ML import issues: %s", "; ".join(_IMPORT_ERRORS))
if not _MODEL_AVAILABLE:
    logger.warning(
        "Core ML libs (sklearn/joblib/pandas) eksik; ML modeli devre dışı. "
        "pip install scikit-learn==1.6.1 joblib pandas"
    )
elif not _XGB_AVAILABLE:
    logger.info("xgboost yok; RF+GB ensemble kullanılacak.")

MODEL_DIR = os.path.join(os.path.dirname(__file__), "saved_models")

def generate_features(df: 'pd.DataFrame') -> 'pd.DataFrame':
    """Zaman serisi, lag ve rolling mean feature'larini uretir."""
    if not _MODEL_AVAILABLE:
        return df
        
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['measured_at']):
        df['measured_at'] = pd.to_datetime(df['measured_at'])
        
    df['hour'] = df['measured_at'].dt.hour
    df['dayofweek'] = df['measured_at'].dt.dayofweek
    df['month'] = df['measured_at'].dt.month
    
    df = df.sort_values(['station_id', 'measured_at'])
    
    # Lag features (Gecikmeler)
    df['aqi_lag_1h'] = df.groupby('station_id')['aqi'].shift(1)
    df['aqi_lag_2h'] = df.groupby('station_id')['aqi'].shift(2)
    df['aqi_lag_6h'] = df.groupby('station_id')['aqi'].shift(6)
    df['aqi_lag_24h'] = df.groupby('station_id')['aqi'].shift(24)
    
    # Rolling Means (Kayan Ortalamalar)
    df['aqi_rolling_3h'] = df.groupby('station_id')['aqi'].transform(lambda x: x.rolling(3, min_periods=1).mean())
    df['aqi_rolling_12h'] = df.groupby('station_id')['aqi'].transform(lambda x: x.rolling(12, min_periods=1).mean())
    
    df = df.dropna()
    return df

class AirQualityPredictor:
    def __init__(self):
        self.rf_model = None
        self.gb_model = None
        self.xgb_model = None
        self.is_trained = False
        self.metrics = {}
        
        # Baslangicta kayitli model varsa yukle
        self.load_model()
        
    def save_model(self):
        """Eğitilmiş modelleri diske kaydeder.

        Read-only FS (Vercel/Lambda) durumunda sessizce skip eder; in-memory model
        zaten predict için yeterli. Yalnızca cold-start sonrası kalıcılık kaybolur.
        """
        if not self.is_trained:
            return

        try:
            os.makedirs(MODEL_DIR, exist_ok=True)
            joblib.dump(self.rf_model, os.path.join(MODEL_DIR, "rf_model.joblib"))
            joblib.dump(self.gb_model, os.path.join(MODEL_DIR, "gb_model.joblib"))
            if self.xgb_model is not None:
                joblib.dump(self.xgb_model, os.path.join(MODEL_DIR, "xgb_model.joblib"))
            joblib.dump(self.metrics, os.path.join(MODEL_DIR, "metrics.joblib"))
            logger.info("Modeller diske kaydedildi (xgb=%s).", self.xgb_model is not None)
        except OSError as e:
            logger.warning(
                "save_model skipped (read-only fs?): %s — model is still in memory.", e
            )

    def load_model(self):
        """Diskte kayıtlı model varsa RAM'e yükler.

        xgb modeli opsiyonel: yoksa veya yüklenemezse RF+GB ile devam edilir.
        """
        if not _MODEL_AVAILABLE:
            return

        rf_path = os.path.join(MODEL_DIR, "rf_model.joblib")
        gb_path = os.path.join(MODEL_DIR, "gb_model.joblib")
        xgb_path = os.path.join(MODEL_DIR, "xgb_model.joblib")
        metrics_path = os.path.join(MODEL_DIR, "metrics.joblib")

        if not (os.path.exists(rf_path) and os.path.exists(gb_path)):
            return

        try:
            self.rf_model = joblib.load(rf_path)
            self.gb_model = joblib.load(gb_path)
            self.xgb_model = None
            if _XGB_AVAILABLE and os.path.exists(xgb_path):
                try:
                    self.xgb_model = joblib.load(xgb_path)
                except Exception as e:
                    logger.warning("[ML_DEBUG] xgb load failed (continuing without): %s", e)
                    self.xgb_model = None
            if os.path.exists(metrics_path):
                self.metrics = joblib.load(metrics_path)
            self.is_trained = True
            logger.info(
                "[ML_DEBUG] model loaded path=%s xgb=%s",
                MODEL_DIR, self.xgb_model is not None,
            )
        except Exception as e:
            # Genelde numpy/sklearn sürüm uyumsuzluğu (pickle protocol)
            # veya bozuk dosya. Stack trace yerine kısa warning + fallback.
            self.rf_model = self.gb_model = self.xgb_model = None
            self.is_trained = False
            logger.warning(
                "[ML_DEBUG] model load failed (%s); will retrain on next opportunity.",
                repr(e),
            )

    def train(self, data_records: list[dict], min_samples: int = 50):
        """Modeli eğitir. `min_samples`: ham kayıt sayısı eşiği (lag üretiminden önce)."""
        if not _MODEL_AVAILABLE:
            raise RuntimeError("ML libraries missing")

        if not data_records or len(data_records) < min_samples:
            logger.warning("Yetersiz veri. Model egitilemiyor.")
            return False
            
        df = pd.DataFrame(data_records)
        df = generate_features(df)
        
        if len(df) < 15:
            logger.warning("Feature generation sonrasi yetersiz veri.")
            return False
            
        features = ['hour', 'dayofweek', 'month', 'aqi_lag_1h', 'aqi_lag_2h', 
                    'aqi_lag_6h', 'aqi_lag_24h', 'aqi_rolling_3h', 'aqi_rolling_12h']
        target = 'aqi'
        
        X = df[features]
        y = df[target]
        
        # %70 train, %15 val, %15 test
        X_temp, X_test, y_temp, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
        X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=0.176, random_state=42)
        
        self.rf_model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
        self.rf_model.fit(X_train, y_train)

        self.gb_model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.05, max_depth=5, random_state=42)
        self.gb_model.fit(X_train, y_train)

        preds_stack = [self.rf_model.predict(X_test), self.gb_model.predict(X_test)]
        used = ["rf", "gb"]

        if _XGB_AVAILABLE and XGBRegressor is not None:
            self.xgb_model = XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=5, random_state=42)
            self.xgb_model.fit(X_train, y_train)
            preds_stack.append(self.xgb_model.predict(X_test))
            used.append("xgb")
        else:
            self.xgb_model = None

        final_preds = np.mean(np.vstack(preds_stack), axis=0)

        mae = mean_absolute_error(y_test, final_preds)
        r2 = r2_score(y_test, final_preds)

        self.metrics = {
            "mae": float(mae),
            "r2": float(r2),
            "samples_trained": len(X_train),
            "models": used,
        }
        self.is_trained = True
        
        # Egitim basariliysa otomatik kaydet
        self.save_model()
        return True

    def predict(self, current_aqi: float, hours_ahead: list[int]) -> dict[int, float]:
        """Verilen saat ufukları için AQI tahminleri döndürür."""
        if not _MODEL_AVAILABLE:
            raise RuntimeError(
                "ML libraries are not installed; cannot predict air quality."
            )
        if not self.is_trained:
            raise RuntimeError(
                "Model is not trained yet; train it before requesting predictions."
            )
            
        now = datetime.utcnow()
        predictions = {}
        for h in hours_ahead:
            future_time = now + timedelta(hours=h)
            
            row = pd.DataFrame([{
                'hour': future_time.hour,
                'dayofweek': future_time.weekday(),
                'month': future_time.month,
                'aqi_lag_1h': current_aqi,
                'aqi_lag_2h': current_aqi,
                'aqi_lag_6h': current_aqi,
                'aqi_lag_24h': current_aqi,
                'aqi_rolling_3h': current_aqi,
                'aqi_rolling_12h': current_aqi
            }])
            
            preds = [
                float(self.rf_model.predict(row)[0]),
                float(self.gb_model.predict(row)[0]),
            ]
            if self.xgb_model is not None:
                preds.append(float(self.xgb_model.predict(row)[0]))
            predictions[h] = sum(preds) / len(preds)

        return predictions

# Singleton instance
predictor = AirQualityPredictor()
