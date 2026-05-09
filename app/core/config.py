from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Yapay Zeka Destekli Mahalle Yasam Kalitesi API"
    app_version: str = "0.1.0"
    database_url: str = "sqlite:///./runway.db"
    cors_origins: str = "*"
    seed_demo_data: bool = True
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"
    openai_api_key: str = ""
    google_maps_api_key: str = ""
    gemini_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
