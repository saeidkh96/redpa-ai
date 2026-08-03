import json
import logging

from app.logging_config.json_formatter import (
    JSONLogFormatter,
)


def test_json_log_formatter() -> None:
    formatter = JSONLogFormatter()

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="hello",
        args=(),
        exc_info=None,
    )

    payload = json.loads(
        formatter.format(
            record,
        )
    )

    assert payload["message"] == "hello"
    assert payload["level"] == "INFO"
