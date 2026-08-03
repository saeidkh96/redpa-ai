from __future__ import annotations

import asyncio

from app.background_jobs.heartbeat import (
    BackgroundHeartbeat,
)
from app.background_jobs.repository import (
    BackgroundJobRepository,
)
from app.background_jobs.schemas import (
    BackgroundJobCreate,
)


async def run() -> None:
    while True:
        await BackgroundHeartbeat.scheduler()

        await BackgroundJobRepository.enqueue(
            BackgroundJobCreate(
                job_type="sleep",
                payload={
                    "seconds": 1,
                },
                delay_seconds=300,
            )
        )

        await asyncio.sleep(30)


def main() -> None:
    asyncio.run(
        run()
    )


if __name__ == "__main__":
    main()