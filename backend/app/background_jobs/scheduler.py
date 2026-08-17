from __future__ import annotations

import asyncio
import os

from app.background_jobs.heartbeat import BackgroundHeartbeat
from app.background_jobs.repository import BackgroundJobRepository
from app.background_jobs.schemas import BackgroundJobCreate
from app.production_validation.runtime import production_validation_runtime


async def run() -> None:
    sleep_job_counter = 0

    while True:
        await BackgroundHeartbeat.scheduler()

        if os.getenv(
            "PRODUCTION_VALIDATION_ENABLED",
            "true",
        ).lower() in {"1", "true", "yes", "on"}:
            try:
                await production_validation_runtime.check_once()
            except Exception as exc:
                # Detection must not kill the scheduler.
                print(
                    f"[production-validation] check failed: "
                    f"{type(exc).__name__}: {exc}"
                )

        # Preserve the existing background-job smoke path without
        # enqueueing a delayed sleep job on every scheduler iteration.
        sleep_job_counter += 1
        if sleep_job_counter >= 10:
            await BackgroundJobRepository.enqueue(
                BackgroundJobCreate(
                    job_type="sleep",
                    payload={"seconds": 1},
                    delay_seconds=300,
                )
            )
            sleep_job_counter = 0

        await asyncio.sleep(
            float(os.getenv("BACKGROUND_SCHEDULER_POLL_SECONDS", "30"))
        )


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
