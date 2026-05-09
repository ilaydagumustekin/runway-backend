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
try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score
    import joblib
    import pandas as pd
    from xgboost import XGBRegressor
except ImportError:
    _MODEL_AVAILABLE = False
    logger.warning("scikit-learn, pandas veya xgboost yuklu degil. ML modelleri kullanilamayacak.")

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
        """Eğitilmiş modelleri diske kaydeder."""
        if not self.is_trained:
            return
            
        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(self.rf_model, os.path.join(MODEL_DIR, "rf_model.joblib"))
        joblib.dump(self.gb_model, os.path.join(MODEL_DIR, "gb_model.joblib"))
        joblib.dump(self.xgb_model, os.path.join(MODEL_DIR, "xgb_model.joblib"))
        joblib.dump(self.metrics, os.path.join(MODEL_DIR, "metrics.joblib"))
        logger.info("Modeller diske kaydedildi.")

    def load_model(self):
        """Diskte kayitli model varsa RAM'e yukler."""
        if not _MODEL_AVAILABLE:
            return
            
        rf_path = os.path.join(MODEL_DIR, "rf_model.joblib")
        gb_path = os.path.join(MODEL_DIR, "gb_model.joblib")
        xgb_path = os.path.join(MODEL_DIR, "xgb_model.joblib")
        metrics_path = os.path.join(MODEL_DIR, "metrics.joblib")
        
        if os.path.exists(rf_path) and os.path.exists(gb_path) and os.path.exists(xgb_path):
            try:
                self.rf_model = joblib.load(rf_path)
                self.gb_model = joblib.load(gb_path)
                self.xgb_model = joblib.load(xgb_path)
                if os.path.exists(metrics_path):
                    self.metrics = joblib.load(metrics_path)
                self.is_trained = True
                logger.info("Kayitli modeller basariyla yuklendi.")
            except Exception as e:
                logger.error(f"Model yuklenirken hata olustu: {e}")

    def train(self, data_records: list[dict]):
        """Modeli eğitir."""
        if not _MODEL_AVAILABLE:
            raise RuntimeError("ML libraries missing")
            
        if not data_records or len(data_records) < 50:
            logger.warning("Yetersiz veri. Model egitilemiyor.")
            return False
            
        df = pd.DataFrame(data_records)
        df = generate_features(df)
        
        if len(df) < 20:
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
        
        self.xgb_model = XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=5, random_state=42)
        self.xgb_model.fit(X_train, y_train)
        
        # Test 
        rf_preds = self.rf_model.predict(X_test)
        gb_preds = self.gb_model.predict(X_test)
        xgb_preds = self.xgb_model.predict(X_test)
        
        # Ensemble prediction (Average of 3 models)
        final_preds = (rf_preds + gb_preds + xgb_preds) / 3
        
        mae = mean_absolute_error(y_test, final_preds)
        r2 = r2_score(y_test, final_preds)
        
        self.metrics = {
            "mae": float(mae),
            "r2": float(r2),
            "samples_trained": len(X_train)
        }
        self.is_trained = True
        
        # Egitim basariliysa otomatik kaydet
        self.save_model()
        return True

    def predict(self, current_aqi: float, hours_ahead: list[int]) -> dict[int, float]:
        """Verilen saat ufukları için AQI tahminleri döndürür."""
        if not _MODEL_AVAILABLE or not self.is_trained:
            # Fallback basit tahmin
            return {h: current_aqi + h * 0.1 for h in hours_ahead}
            
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
            
            rf_pred = self.rf_model.predict(row)[0]
            gb_pred = self.gb_model.predict(row)[0]
            xgb_pred = self.xgb_model.predict(row)[0]
            predictions[h] = float((rf_pred + gb_pred + xgb_pred) / 3)
            
        return predictions

# Singleton instance
predictor = AirQualityPredictor()
