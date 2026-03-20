from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ROUTER_P_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Router-P"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: Literal["debug", "info", "warning", "error", "critical"] = "info"

    api_key: str = "dev-router-p-key"
    request_timeout_seconds: float = Field(default=30.0, gt=0)

    ollama_base_url: str = "http://localhost:11434"
    local_boundary_model: str = "phi4-mini"
    local_general_model: str = "qwen3:4b"
    local_code_model: str = "qwen2.5-coder:7b"

    cloud_base_url: str | None = None
    cloud_api_key: str | None = None
    cloud_general_model: str | None = None
    cloud_code_model: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
