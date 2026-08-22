"""
Centralized logging configuration for QuakMeeting.
Provides formatted console output and rotating file logs.
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.expanduser("~/.quakmeeting")
LOG_FILE = os.path.join(LOG_DIR, "quakmeeting.log")

def setup_logging(level=logging.INFO) -> logging.Logger:
    """Configures root logger with formatted console and rotating file handlers."""
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
    except Exception:
        pass

    root_logger = logging.getLogger("QuakMeeting")
    root_logger.setLevel(level)

    # Avoid duplicate handlers on reload
    if not root_logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%H:%M:%S"
        )

        # 1. Console Stream Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # 2. Rotating File Handler (max 2MB, up to 3 backups)
        try:
            file_handler = RotatingFileHandler(
                LOG_FILE,
                maxBytes=2 * 1024 * 1024,
                backupCount=3,
                encoding="utf-8"
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            sys.stderr.write(f"Warning: could not initialize file logger: {e}\n")

    return root_logger

# Initialize global logger
logger = setup_logging()
