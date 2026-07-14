from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="DataWhisperer AI", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")

    backend_cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:8501", "http://127.0.0.1:8501"],
        alias="BACKEND_CORS_ORIGINS",
    )

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-3.5-flash", alias="GEMINI_MODEL")
    gemini_timeout_seconds: float = Field(default=30.0, alias="GEMINI_TIMEOUT_SECONDS")
    gemini_max_retries: int = Field(default=3, alias="GEMINI_MAX_RETRIES")
    gemini_temperature: float = Field(default=0.2, alias="GEMINI_TEMPERATURE")

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
