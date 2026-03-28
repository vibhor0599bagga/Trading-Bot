"""
Logging configuration for the Trading Bot.
Sets up both console and file handlers with consistent formatting.
"""

import logging
import os
from pathlib import Path

LOG_FILE = Path(__file__).parent.parent / "trading_bot.log"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger with the given name.
    Configures root logger on first call (idempotent).
    """
    root = logging.getLogger()

    if not root.handlers:
        root.setLevel(logging.DEBUG)

        # Console handler — INFO and above
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

        # File handler — DEBUG and above (captures full API payloads)
        file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

        root.addHandler(console_handler)
        root.addHandler(file_handler)

    return logging.getLogger(name)
