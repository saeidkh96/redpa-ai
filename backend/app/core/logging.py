import logging
from logging.config import dictConfig

from app.core.config import settings
from app.middleware.request_context import get_request_id


class RequestIDFilter(logging.Filter):
    """Add the current request ID to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


def configure_logging() -> None:
    """Configure application-wide logging."""

    log_level = settings.log_level.upper()

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_id": {
                "()": RequestIDFilter,
            },
        },
        "formatters": {
            "default": {
                "format": (
                    "%(asctime)s | %(levelname)s | "
                    "request_id=%(request_id)s | "
                    "%(name)s | %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": (
                    "%(asctime)s | %(levelname)s | "
                    "request_id=%(request_id)s | "
                    "%(name)s | %(filename)s:%(lineno)d | "
                    "%(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "default",
                "filters": ["request_id"],
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console"],
        },
        "loggers": {
            "uvicorn": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }

    dictConfig(logging_config)