from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "URL Shortener API"
    app_env: Literal["development", "test", "production"] = "development"
    app_version: str = Field(default="0.1.0", min_length=1, max_length=50)
    debug: bool = False

    database_url: str
    base_url: str = "http://localhost:8000"
    redis_url: str = "redis://localhost:6379/0"

    app_host: str = "127.0.0.1"
    app_port: int = Field(default=8000, ge=1, le=65535)

    db_connect_timeout: int = Field(default=5, ge=1, le=60)
    db_pool_size: int = Field(default=5, ge=1, le=50)
    db_max_overflow: int = Field(default=5, ge=0, le=50)
    db_pool_timeout: int = Field(default=10, ge=1, le=120)
    db_pool_recycle: int = Field(default=1800, ge=60, le=86400)
    db_statement_timeout_ms: int = Field(default=10000, ge=1000, le=300000)
    db_idle_transaction_timeout_ms: int = Field(default=60000, ge=1000, le=600000)

    rate_limit_create_requests: int = Field(default=10, ge=1, le=10000)
    rate_limit_create_window_seconds: int = Field(default=60, ge=1, le=3600)

    max_request_body_bytes: int = Field(
        default=16384,
        ge=1024,
        le=1048576
    )


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()