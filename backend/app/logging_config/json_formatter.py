from __future__ import annotations

import json
import logging
from datetime import (
    datetime,
    timezone,
)

from app.logging_config.context import (
    correlation_id_context,
    request_id_context,
)


class JSONLogFormatter(
    logging.Formatter,
):
    def format(
        self,
        record: logging.LogRecord,
    ) -> str:
        payload = {
            "timestamp": datetime.now(
                timezone.utc,
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": (
                request_id_context.get()
            ),
            "correlation_id": (
                correlation_id_context.get()
            ),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        trace_id = getattr(
            record,
            "otelTraceID",
            None,
        )

        span_id = getattr(
            record,
            "otelSpanID",
            None,
        )

        if trace_id not in {
            None,
            "0",
            0,
        }:
            payload["trace_id"] = str(
                trace_id,
            )

        if span_id not in {
            None,
            "0",
            0,
        }:
            payload["span_id"] = str(
                span_id,
            )

        if record.exc_info:
            payload[
                "exception"
            ] = self.formatException(
                record.exc_info,
            )

        for field in (
            "error_id",
            "error_code",
            "http_method",
            "http_path",
            "http_status",
            "process_time_ms",
            "user_id",
            "agent_name",
            "workflow_id",
            "job_id",
        ):
            value = getattr(
                record,
                field,
                None,
            )

            if value is not None:
                payload[field] = value

        return json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        )
