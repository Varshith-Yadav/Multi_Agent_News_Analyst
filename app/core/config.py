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
    llm_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai"
    llm_api_key: str | None = None
    llm_api_key_env: str | None = "GEMINI_API_KEY"
    llm_model: str = "gemini-2.0-flash-lite"
    llm_fallback_models_csv: str = ""
    llm_fallbacks_json: str = "[]"
    llm_max_retries: int = 3
    llm_retry_backoff_seconds: float = 1.5
    embedding_model: str = "all-MiniLM-L6-v2"
    job_queue_key: str = "mana:jobs:queue"
    job_key_prefix: str = "mana:jobs"
    cache_key_prefix: str = "mana:cache"
    job_ttl_seconds: int = 60 * 60 * 24
    cache_ttl_seconds: int = 60 * 30
    worker_poll_timeout_seconds: int = 5
    frontend_origin: str = "http://localhost:5173"
    auth_secret_key: str = "change-me-in-production"
    auth_token_expire_minutes: int = 60
    auth_algorithm: str = "HS256"
    auth_demo_users_json: dict[str, Any] = Field(
        default_factory=lambda: {
            "admin": {"password": "admin123", "roles": ["admin", "analyst", "viewer"]},
            "analyst": {"password": "analyst123", "roles": ["analyst", "viewer"]},
            "viewer": {"password": "viewer123", "roles": ["viewer"]},
        }
    )
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
