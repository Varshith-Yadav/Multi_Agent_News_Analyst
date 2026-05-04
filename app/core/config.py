from functools import lru_cache
from typing import Any
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Multi-Agent News Analyst"
    env: Literal["dev", "prod", "test"] = "dev"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "postgresql+psycopg2://postgres:postgres@postgres:5432/mana"
    redis_url: str = "redis://redis:6379/0"
    nvidia_api_key: str | None = None
    xai_api_key: str | None = None
    gemini_api_key: str | None = None
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai"
    gemini_model: str = "gemini-2.5-flash-lite"
    llm_base_url: str = "https://api.x.ai/v1"
    llm_api_key: str | None = None
    llm_api_key_env: str | None = "XAI_API_KEY"
    llm_model: str = "grok-4"
    llm_fallback_models_csv: str = "grok-4-latest,grok-3-mini"
    llm_fallbacks_json: str = "[]"
    llm_max_retries: int = 3
    llm_retry_backoff_seconds: float = 1.5
    llm_enable_stub_fallback: bool = True
    embedding_model: str = "all-MiniLM-L6-v2"
    job_queue_key: str = "mana:jobs:queue"
    job_key_prefix: str = "mana:jobs"
    cache_key_prefix: str = "mana:cache"
    job_ttl_seconds: int = 60 * 60 * 24
    cache_ttl_seconds: int = 60 * 30
    worker_poll_timeout_seconds: int = 5
    frontend_origin: str = "http://localhost:5173"
    frontend_origins_csv: str = "http://localhost:5173"
    auth_secret_key: str = "change-me-in-production"
    auth_token_expire_minutes: int = 60
    auth_algorithm: str = "HS256"
    auth_seed_users_json: dict[str, Any] = Field(default_factory=dict)
    allow_public_signup: bool = False
    encryption_key: str | None = None
    enforce_encryption: bool = False
    enforce_copyright_controls: bool = True
    max_summary_words: int = 220
    max_quote_words: int = 25
    audit_log_path: str = "logs/audit.log"
    trend_baseline_days: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def cors_origins(self) -> list[str]:
        origins = [self.frontend_origin, *self.frontend_origins_csv.split(",")]
        cleaned: list[str] = []
        for origin in origins:
            value = origin.strip()
            if value and value not in cleaned:
                cleaned.append(value)
        return cleaned

    def seed_users(self) -> dict[str, Any]:
        if self.auth_seed_users_json:
            return self.auth_seed_users_json
        if self.env != "prod":
            return {
                "admin": {"password": "admin123", "roles": ["admin", "analyst", "viewer"]},
                "analyst": {"password": "analyst123", "roles": ["analyst", "viewer"]},
                "viewer": {"password": "viewer123", "roles": ["viewer"]},
            }
        return {}

    def validate_runtime(self) -> None:
        if self.env != "prod":
            return
        if self.auth_secret_key == "change-me-in-production":
            raise ValueError("AUTH_SECRET_KEY must be set to a strong non-default value in prod.")
        if not self.encryption_key:
            raise ValueError("ENCRYPTION_KEY must be set in prod.")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_runtime()
    return settings
