import sys
import os
import asyncio
from dotenv import load_dotenv

# Run backend init
sys.path.append("/Users/asimsinanyuksel/Desktop/runway-backend")
load_dotenv("/Users/asimsinanyuksel/Desktop/runway-backend/.env")

from app.database import Base, engine, SessionLocal
from app.models import Neighborhood, EnvironmentalData, TuikReferenceData
from app.services.external.openaq_client import fetch_latest_measurements_by_coordinates
from app.services.ml.air_quality_model import AirQualityPredictor
from app.services.external.google_maps_satellite import fetch_satellite_image
from app.services.vlm.green_area_detector import analyze_green_area
from app.services.fuzzy_engine import calculate_fuzzy_myki
from app.services.tuik_validation_service import validate_neighborhood_data
from app.services.route_optimizer import find_best_route

async def run_tests():
    db = SessionLocal()
    Base.metadata.create_all(bind=engine)
    
    print("=== FAZ 1: OpenAQ & ML Hava Kalitesi Testi ===")
    lat, lon = 41.0082, 28.9784 # Istanbul
    print(f"Location: Istanbul ({lat}, {lon})")
    try:
        # Fallback to mock data if OpenAQ fails due to missing API key
        api_key = os.getenv("OPENAQ_API_KEY")
        aq_data = fetch_latest_measurements_by_coordinates(lat, lon, api_key=api_key)
        if not aq_data:
            print("OpenAQ didn't return data or 401. Using mock data for ML...")
            aq_data = {'pm25': 12.0, 'pm10': 25.0, 'no2': 18.0, 'o3': 30.0}
            
        print("OpenAQ Data (or Mock):", aq_data)
        predictor = AirQualityPredictor()
        import pandas as pd
        from datetime import datetime, timedelta
        
        print("Predicting with ML Model...")
        current_aqi = aq_data.get('pm10', 20.0) # Using PM10 as a proxy for AQI for the test
        forecast = predictor.predict(current_aqi, hours_ahead=[3, 6, 24])
        print("ML Forecast for 3, 6, 24 hours ahead:", forecast)
    except Exception as e:
        print("Faz 1 Error:", e)

    print("\n=== FAZ 2: Google Maps & Gemini VLM Yeşil Alan Testi ===")
    park_lat, park_lon = 41.0422, 28.9936 # Maçka Parkı (Green)
    city_lat, city_lon = 41.0082, 28.9784 # Eminönü (Concrete)
    try:
        print("Fetching Park Image...")
        park_img = fetch_satellite_image(park_lat, park_lon, zoom=16)
        if park_img != b"mock_image_bytes":
            park_res = analyze_green_area(park_img)
            print("Park Analysis:", park_res)
        else:
            print("Google Maps returned mock image (API Key missing or invalid).")

        print("Fetching Concrete Image...")
        city_img = fetch_satellite_image(city_lat, city_lon, zoom=16)
        if city_img != b"mock_image_bytes":
            city_res = analyze_green_area(city_img)
            print("Concrete Analysis:", city_res)
    except Exception as e:
        print("Faz 2 Error:", e)

    print("\n=== FAZ 3: Scikit-Fuzzy (Bulanık Mantık) Gerçek MYKI Testi ===")
    try:
        ideal_aqi, ideal_green, ideal_noise = 20.0, 60.0, 40.0
        ideal_score = calculate_fuzzy_myki(ideal_aqi, ideal_green, ideal_noise)
        print(f"Ideal Scenario (AQI={ideal_aqi}, Green={ideal_green}%, Noise={ideal_noise}dB) -> MYKI: {ideal_score}")

        bad_aqi, bad_green, bad_noise = 150.0, 5.0, 85.0
        bad_score = calculate_fuzzy_myki(bad_aqi, bad_green, bad_noise)
        print(f"Bad Scenario (AQI={bad_aqi}, Green={bad_green}%, Noise={bad_noise}dB) -> MYKI: {bad_score}")
    except Exception as e:
        print("Faz 3 Error:", e)

    print("\n=== FAZ 4: TÜİK Validasyon Engine Limit Testi ===")
    try:
        n = Neighborhood(name="Test Validasyon", city="Isparta", district="Merkez", latitude=park_lat, longitude=park_lon)
        db.add(n)
        db.commit()
        db.refresh(n)

        env = EnvironmentalData(neighborhood_id=n.id, pm25=10, pm10=20, no2=15, o3=25, aqi=20, green_area_ratio=45.0, noise_level_dba=50)
        db.add(env)
        
        # Add TUIK Reference (match indicator exact name expected by validation logic)
        refs = [
            TuikReferenceData(city="Isparta", district="Merkez", indicator_type="Hava Kalitesi (AQI)", value=25.0, year=2024),
            TuikReferenceData(city="Isparta", district="Merkez", indicator_type="Yesil Alan Orani", value=50.0, year=2024),
            TuikReferenceData(city="Isparta", district="Merkez", indicator_type="Gürültü (dBA)", value=55.0, year=2024)
        ]
        db.add_all(refs)
        db.commit()

        val_result = validate_neighborhood_data(db, n)
        print("Validation Result (should check against refs):", val_result)

        db.delete(env)
        db.delete(n)
        for r in refs: db.delete(r)
        db.commit()
    except Exception as e:
        print("Faz 4 Error:", e)

    print("\n=== FAZ 5: A* Graf Algoritması ile Rota Optimizasyonu Testi ===")
    try:
        # A (Start) - B - C
        #           - D -
        # create coordinates where B is closer but bad environment, D is slightly further but great environment
        nodes = [
            Neighborhood(name="A", city="Test", district="Test", latitude=37.0, longitude=30.0),
            Neighborhood(name="B", city="Test", district="Test", latitude=37.01, longitude=30.01), # Path 1
            Neighborhood(name="C", city="Test", district="Test", latitude=37.02, longitude=30.02), # Destination
            Neighborhood(name="D", city="Test", district="Test", latitude=37.01, longitude=29.99), # Path 2 (Alternative)
        ]
        db.add_all(nodes)
        db.commit()
        for n in nodes: db.refresh(n)

        envs = [
            EnvironmentalData(neighborhood_id=nodes[0].id, pm25=10, pm10=10, no2=10, o3=10, aqi=20, green_area_ratio=50, noise_level_dba=40),
            EnvironmentalData(neighborhood_id=nodes[1].id, pm25=150, pm10=150, no2=50, o3=50, aqi=200, green_area_ratio=5, noise_level_dba=90), # B is BAD
            EnvironmentalData(neighborhood_id=nodes[2].id, pm25=10, pm10=10, no2=10, o3=10, aqi=20, green_area_ratio=50, noise_level_dba=40),
            EnvironmentalData(neighborhood_id=nodes[3].id, pm25=10, pm10=10, no2=10, o3=10, aqi=20, green_area_ratio=50, noise_level_dba=40), # D is GOOD
        ]
        db.add_all(envs)
        db.commit()

        path = find_best_route(db, 37.0, 30.0, 37.02, 30.02, optimize_for="environment")
        print("Path Nodes (Should avoid B):", [p.name for p in path] if path else "None")

        for e in envs: db.delete(e)
        for n in nodes: db.delete(n)
        db.commit()
    except Exception as e:
        print("Faz 5 Error:", e)

if __name__ == "__main__":
    asyncio.run(run_tests())
