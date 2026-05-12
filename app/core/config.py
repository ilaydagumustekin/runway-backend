import os
from typing import Self

from pydantic import model_validator
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
    # generateContent model id, e.g. gemini-2.0-flash, gemini-1.5-flash (avoid -latest aliases on server keys)
    gemini_model: str = "gemini-2.0-flash"
    # Vercel AI Gateway (OpenAI-compatible): https://vercel.com/docs/ai-gateway
    ai_gateway_api_key: str = ""
    ai_gateway_base_url: str = "https://ai-gateway.vercel.sh/v1"
    green_area_gateway_model: str = "openai/gpt-4o-mini"
    # Robustness knobs for green area VLM (deterministic + multi-sample median)
    green_area_samples: int = 3
    green_area_temperature: float = 0.0
    green_area_seed: int = 42
    openaq_api_key: str = ""
    openrouteservice_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @model_validator(mode="after")
    def _deployment_overrides(self) -> Self:
        """Vercel: writable SQLite path; OS env backfill for keys (Vercel injects process env)."""
        if os.environ.get("VERCEL"):
            url = self.database_url
            if url.startswith("sqlite:///./") or url == "sqlite:///./runway.db":
                object.__setattr__(self, "database_url", "sqlite:////tmp/runway.db")

        # pydantic-settings can miss or strip keys in some serverless setups; read OS env explicitly.
        backfill: tuple[tuple[str, tuple[str, ...]], ...] = (
            ("openaq_api_key", ("OPENAQ_API_KEY", "OPENAQ_KEY")),
            ("openrouteservice_api_key", ("OPENROUTESERVICE_API_KEY", "ORS_API_KEY")),
            ("google_maps_api_key", ("GOOGLE_MAPS_API_KEY",)),
            ("gemini_api_key", ("GEMINI_API_KEY", "GOOGLE_GENERATIVE_AI_API_KEY")),
            ("openai_api_key", ("OPENAI_API_KEY",)),
            ("ai_gateway_api_key", ("AI_GATEWAY_API_KEY",)),
            ("secret_key", ("SECRET_KEY",)),
        )
        for field, env_names in backfill:
            cur = getattr(self, field, "")
            if isinstance(cur, str) and cur.strip():
                continue
            for env in env_names:
                raw = os.environ.get(env, "")
                if isinstance(raw, str) and raw.strip():
                    object.__setattr__(self, field, raw.strip())
                    break
        return self


settings = Settings()
