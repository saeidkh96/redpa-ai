from __future__ import annotations

import logging
import os
import re
import time
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Engine

from app.performance.metrics import (
    SLOW_SQL_QUERIES_TOTAL,
    SQL_QUERY_DURATION_SECONDS,
)


logger = logging.getLogger(
    "redpa.sql.performance",
)

_REGISTERED = False


def _operation(
    statement: str,
) -> str:
    match = re.match(
        r"\s*([A-Za-z]+)",
        statement or "",
    )

    return (
        match.group(1).upper()
        if match
        else "UNKNOWN"
    )


def register_sql_performance_monitor(
    engine: Any,
) -> None:
    global _REGISTERED

    if _REGISTERED:
        return

    threshold_ms = float(
        os.getenv(
            "SLOW_QUERY_THRESHOLD_MS",
            "500",
        )
    )

    sync_engine: Engine = getattr(
        engine,
        "sync_engine",
        engine,
    )

    @event.listens_for(
        sync_engine,
        "before_cursor_execute",
    )
    def before_cursor_execute(
        connection,
        cursor,
        statement,
        parameters,
        context,
        executemany,
    ) -> None:
        context._redpa_query_started = (
            time.perf_counter()
        )

    @event.listens_for(
        sync_engine,
        "after_cursor_execute",
    )
    def after_cursor_execute(
        connection,
        cursor,
        statement,
        parameters,
        context,
        executemany,
    ) -> None:
        started = getattr(
            context,
            "_redpa_query_started",
            None,
        )

        if started is None:
            return

        duration_seconds = (
            time.perf_counter()
            - started
        )

        duration_ms = (
            duration_seconds
            * 1000
        )

        operation = _operation(
            statement,
        )

        SQL_QUERY_DURATION_SECONDS.labels(
            operation=operation,
        ).observe(
            duration_seconds,
        )

        if duration_ms >= threshold_ms:
            SLOW_SQL_QUERIES_TOTAL.labels(
                operation=operation,
            ).inc()

            logger.warning(
                "Slow SQL query detected",
                extra={
                    "process_time_ms": round(
                        duration_ms,
                        2,
                    ),
                    "sql_operation": operation,
                    "sql_statement": (
                        statement[:1000]
                        if statement
                        else None
                    ),
                },
            )

    _REGISTERED = True
