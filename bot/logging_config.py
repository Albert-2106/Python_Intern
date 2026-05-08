"""
Logging configuration for the Binance Futures Trading Bot.
Sets up both file and console handlers with structured formatting.
"""

import logging
import logging.handlers
from pathlib import Path


LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "trading_bot.log"


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Configure application-wide logging with file and console handlers.

    Args:
        level: Logging level string (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Root logger configured with both handlers.
    """
    LOG_DIR.mkdir(exist_ok=True)

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    logger = logging.getLogger("trading_bot")
    logger.setLevel(logging.DEBUG)  # capture everything; handlers filter

    if logger.handlers:
        logger.handlers.clear()

    # --- File handler (DEBUG+) with rotating logs ---
    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # --- Console handler (INFO+ by default) ---
    console_formatter = logging.Formatter(
        fmt="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.debug("Logging initialised — file: %s", LOG_FILE.resolve())
    return logger


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the 'trading_bot' namespace."""
    return logging.getLogger(f"trading_bot.{name}")
