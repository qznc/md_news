#!/usr/bin/env python3
"""Logging configuration for md-news.

This module sets up logging that writes to both stderr and _tmp/logs directory.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Create _tmp/logs directory if it doesn't exist
LOG_DIR = Path("_tmp/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Log file path with timestamp
LOG_FILE = LOG_DIR / f"md-news_{datetime.now().strftime('%Y-%m-%d')}.log"


def setup_logging(name: str = "md-news") -> logging.Logger:
    """Set up a logger that writes to both stderr and _tmp/logs file.

    Args:
        name: The name of the logger

    Returns:
        A configured logger instance
    """
    logger = logging.getLogger(name)

    # Prevent duplicate handlers if this is called multiple times
    if logger.handlers:
        return logger

    # Set level
    logger.setLevel(logging.DEBUG)

    # Format
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S"
    )

    # stderr handler (always writes to stderr)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.INFO)
    stderr_handler.setFormatter(formatter)
    logger.addHandler(stderr_handler)

    # File handler (writes to _tmp/logs/)
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info("Now is %s", datetime.now().isoformat())

    return logger


# Create a default logger for the application
logger = setup_logging("md-news")
