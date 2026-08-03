from __future__ import annotations

import logging
import sys

from app.logging_config.json_formatter import (
    JSONLogFormatter,
)


def configure_logging(
    *,
    level: str = "INFO",
    json_logs: bool = True,
) -> None:
    root = logging.getLogger()

    for handler in list(
        root.handlers,
    ):
        root.removeHandler(
            handler,
        )

    handler = logging.StreamHandler(
        sys.stdout,
    )

    if json_logs:
        handler.setFormatter(
            JSONLogFormatter()
        )
    else:
        handler.setFormatter(
            logging.Formatter(
                (
                    "%(asctime)s "
                    "%(levelname)s "
                    "%(name)s "
                    "%(message)s"
                )
            )
        )

    root.addHandler(
        handler,
    )

    root.setLevel(
        getattr(
            logging,
            level.upper(),
            logging.INFO,
        )
    )

    for logger_name in (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "sqlalchemy.engine",
    ):
        logger = logging.getLogger(
            logger_name,
        )

        logger.handlers.clear()
        logger.propagate = True
