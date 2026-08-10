from __future__ import annotations

import asyncio
import logging
import os
import signal
from contextlib import suppress

from app.database.session import (
    AsyncSessionFactory,
    close_database_connection,
)
from app.services.event_publisher_service import (
    event_publisher_service,
)


logger = logging.getLogger("redpa.outbox_publisher")


def _read_positive_float(
    name: str,
    default: float,
) -> float:
    raw_value = os.getenv(name)

    if raw_value is None:
        return default

    try:
        value = float(raw_value)
    except ValueError:
        logger.warning(
            "Invalid %s=%r; using default %.2f",
            name,
            raw_value,
            default,
        )
        return default

    if value <= 0:
        logger.warning(
            "%s must be > 0; using default %.2f",
            name,
            default,
        )
        return default

    return value


def _read_positive_int(
    name: str,
    default: int,
) -> int:
    raw_value = os.getenv(name)

    if raw_value is None:
        return default

    try:
        value = int(raw_value)
    except ValueError:
        logger.warning(
            "Invalid %s=%r; using default %d",
            name,
            raw_value,
            default,
        )
        return default

    if value <= 0:
        logger.warning(
            "%s must be > 0; using default %d",
            name,
            default,
        )
        return default

    return value


class OutboxPublisher:
    def __init__(
        self,
        *,
        poll_seconds: float | None = None,
        batch_size: int | None = None,
    ) -> None:
        self.poll_seconds = (
            poll_seconds
            if poll_seconds is not None
            else _read_positive_float(
                "OUTBOX_PUBLISHER_POLL_SECONDS",
                1.0,
            )
        )

        self.batch_size = (
            batch_size
            if batch_size is not None
            else _read_positive_int(
                "OUTBOX_PUBLISHER_BATCH_SIZE",
                100,
            )
        )

        self._stop_event = asyncio.Event()

    def request_shutdown(self) -> None:
        if not self._stop_event.is_set():
            logger.info(
                "Outbox publisher shutdown requested."
            )

        self._stop_event.set()

    async def flush_once(self) -> int:
        async with AsyncSessionFactory() as session:
            try:
                result = await event_publisher_service.flush(
                    session=session,
                    limit=self.batch_size,
                )
            except Exception:
                await session.rollback()
                raise

        if (
            result.inspected > 0
            or result.published > 0
            or result.failed > 0
        ):
            logger.info(
                (
                    "Outbox flush completed: "
                    "inspected=%d published=%d failed=%d"
                ),
                result.inspected,
                result.published,
                result.failed,
            )

        return result.inspected

    async def run(self) -> None:
        logger.info(
            (
                "Starting RedPA outbox publisher "
                "(poll_seconds=%.2f, batch_size=%d)."
            ),
            self.poll_seconds,
            self.batch_size,
        )

        while not self._stop_event.is_set():
            try:
                inspected = await self.flush_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception(
                    "Outbox flush failed."
                )
                inspected = 0

            if inspected >= self.batch_size:
                continue

            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.poll_seconds,
                )
            except TimeoutError:
                pass

        logger.info(
            "RedPA outbox publisher stopped."
        )


async def run() -> None:
    publisher = OutboxPublisher()
    loop = asyncio.get_running_loop()

    for signal_name in (
        signal.SIGTERM,
        signal.SIGINT,
    ):
        with suppress(
            NotImplementedError,
            RuntimeError,
        ):
            loop.add_signal_handler(
                signal_name,
                publisher.request_shutdown,
            )

    try:
        await publisher.run()
    finally:
        await close_database_connection()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()