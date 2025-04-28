import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from .params import APP_LOG_DIR, SCRAPER_LOG_DIR


def make_log_dir():
    """Ensure the log directories exist."""
    os.makedirs(APP_LOG_DIR, exist_ok=True)
    os.makedirs(SCRAPER_LOG_DIR, exist_ok=True)


log_time = datetime.now().strftime("%Y%m%d_%H%M%S")

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "filename": os.path.join(APP_LOG_DIR, f"{log_time}.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 50,
            "level": "INFO",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "uvicorn": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
        "uvicorn.access": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
    },
}


def setup_logger():
    """Setup the logger by creating the directories and configuring the logging system."""
    make_log_dir()
    logging.config.dictConfig(LOGGING_CONFIG)