"""
logger.py
Centralized logging configuration for the Agentic RAG Research Assistant.

Usage:
    from logger import get_logger
    logger = get_logger(__name__)
    logger.info("message")
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def _configure_root_logger() -> None:
    """Configure the root logger once with console + rotating file handlers."""
    global _configured
    if _configured:
        return

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    log_file = settings.base_dir / Path(settings.LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers on Streamlit re-runs
    if not root_logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        root_logger.addHandler(console_handler)

        file_handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Return a configured logger instance for the given module name.

    Args:
        name: Typically `__name__` of the calling module.

    Returns:
        A configured `logging.Logger` instance.
    """
    _configure_root_logger()
    return logging.getLogger(name)
