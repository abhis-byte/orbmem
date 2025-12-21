# utils/logger.py

import logging
import sys
from typing import Optional


def _create_handler() -> logging.Handler:
    """Create a console handler with a clean, simple format."""
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    return handler


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.

    Usage:
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Hello from OCDB")
    """
    logger_name = name or "ocdb"
    logger = logging.getLogger(logger_name)

    # Avoid adding multiple handlers if called many times
    if not logger.handlers:
        handler = _create_handler()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

    return logger
