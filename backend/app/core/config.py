from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CVision"
    app_description: str = "AI-assisted recruitment platform for candidates, companies, and admins."
    app_version: str = "1.0.0"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60 * 24
    database_url: str = "postgresql+psycopg://cvision:cvision@db:5432/cvision"
    redis_url: str = "redis://redis:6379/0"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_timeout_seconds: int = 25
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://frontend:5173",
    ]
    upload_dir: str = "uploads"
    bootstrap_on_startup: bool = True
    admin_email: str = "admin@cvision.io"
    admin_password: str = "Admin123!"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
