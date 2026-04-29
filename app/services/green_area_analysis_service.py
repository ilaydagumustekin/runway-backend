def analyze_green_area_placeholder(neighborhood_id: int) -> dict:
    return {
        "neighborhood_id": neighborhood_id,
        "status": "placeholder",
        "message": "Satellite and VLM integration will be added later.",
        "supported_future_providers": [
            "Google Maps Satellite API",
            "GPT Vision",
            "Gemini Vision",
            "Claude Vision",
            "Open-source VLM alternatives",
        ],
    }
