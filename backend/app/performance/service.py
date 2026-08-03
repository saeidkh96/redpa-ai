from __future__ import annotations

import os
from typing import Any

from app.background_jobs.repository import (
    BackgroundJobRepository,
)


class PerformanceStatusService:
    @classmethod
    async def snapshot(
        cls,
    ) -> dict[str, Any]:
        queued_jobs = await (
            BackgroundJobRepository.list(
                status="queued",
                limit=500,
            )
        )

        running_jobs = await (
            BackgroundJobRepository.list(
                status="running",
                limit=500,
            )
        )

        dead_letter_jobs = await (
            BackgroundJobRepository.list(
                status="dead_letter",
                limit=500,
            )
        )

        return {
            "thresholds": {
                "slow_request_ms": float(
                    os.getenv(
                        "SLOW_REQUEST_THRESHOLD_MS",
                        "1000",
                    )
                ),
                "slow_query_ms": float(
                    os.getenv(
                        "SLOW_QUERY_THRESHOLD_MS",
                        "500",
                    )
                ),
            },
            "background_jobs": {
                "queued": len(
                    queued_jobs,
                ),
                "running": len(
                    running_jobs,
                ),
                "dead_letter": len(
                    dead_letter_jobs,
                ),
            },
        }
