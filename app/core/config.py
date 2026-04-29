from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Yapay Zeka Destekli Mahalle Yasam Kalitesi API"
    app_version: str = "0.1.0"
    database_url: str = "sqlite:///./runway.db"
    cors_origins: str = "*"
    seed_demo_data: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
