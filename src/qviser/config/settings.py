"""Loads application settings and secrets from environment variables / .env."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

ENV_FILE = ".env"


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    dhan_client_id: str = Field(min_length=1)
    # SecretStr keeps the token out of logs, reprs and tracebacks.
    dhan_access_token: SecretStr
    # Renew the access token at startup when it has less than this many hours left.
    dhan_token_renew_before_hours: float = Field(default=12, gt=0, le=24)
    dhan_token_auto_renew: bool = True
    log_level: LogLevel = "INFO"

    @field_validator("log_level", mode="before")
    @classmethod
    def _upper_log_level(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the application settings, loaded once on first call."""
    try:
        return Settings()
    except ValidationError as exc:
        fields = ", ".join(".".join(map(str, e["loc"])).upper() for e in exc.errors())
        raise ConfigError(
            f"Invalid or missing configuration: {fields}; "
            "copy .env.example to .env and fill it in."
        ) from exc
