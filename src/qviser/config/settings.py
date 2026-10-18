"""Loads application settings and secrets from environment variables / .env."""

import os
from dataclasses import dataclass, field
from functools import lru_cache

from dotenv import load_dotenv


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ConfigError(
            f"Missing environment variable {name}; copy .env.example to .env and fill it in."
        )
    return value


@dataclass(frozen=True)
class Settings:
    dhan_client_id: str
    # repr=False keeps the token out of logs and tracebacks.
    dhan_access_token: str = field(repr=False)
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            dhan_client_id=_require_env("DHAN_CLIENT_ID"),
            dhan_access_token=_require_env("DHAN_ACCESS_TOKEN"),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the application settings, loaded once on first call."""
    return Settings.from_env()
