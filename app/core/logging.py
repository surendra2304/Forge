"""
Structured and colored logging configuration for FORGE.
"""

import logging
import sys
from rich.logging import RichHandler


def setup_logging(debug: bool = True) -> None:
    """Configure structured console logging using Rich."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                rich_tracebacks=True,
                markup=True,
                show_time=True,
                show_path=False,
            )
        ],
    )
    # Silence overly verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Retrieve a configured logger."""
    return logging.getLogger(f"forge.{name}")
