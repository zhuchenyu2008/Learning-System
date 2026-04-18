from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "learning-system"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False
    environment: Literal["development", "test", "production"] = "development"

    database_url: str = "sqlite+aiosqlite:///./learning_system.db"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None
    celery_task_always_eager: bool = False
    celery_task_store_eager_result: bool = True
    workspace_root: str = "./workspace"
    jwt_secret_key: str = Field(default="change-me-in-production", min_length=16)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    initial_admin_username: str = "admin"
    initial_admin_password: str = "ChangeMe123!"
    initial_admin_email: str = "admin@example.com"

    obsidian_headless_path: str = "obsidian-headless"
    obsidian_vault: str | None = None
    obsidian_config_dir: str | None = None
    obsidian_device_name: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
