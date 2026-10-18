"""Central logging setup for the application."""

import logging

DEFAULT_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def setup_logging(level: str | int = "INFO", fmt: str = DEFAULT_FORMAT) -> None:
    """Configure the root logger. Call once at application startup."""
    logging.basicConfig(level=level, format=fmt)
