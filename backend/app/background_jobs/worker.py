from __future__ import annotations

from app.background_jobs.heartbeat import BackgroundHeartbeat
import asyncio
import os
from app.background_jobs.repository import BackgroundJobRepository

class BackgroundWorker:
    async def run(self):
        while True:
            await BackgroundHeartbeat.worker()
            job = await BackgroundJobRepository.claim_next()
            if job is None:
                await asyncio.sleep(float(os.getenv("BACKGROUND_WORKER_POLL_SECONDS", "2")))
                continue
            try:
                if job.job_type == "sleep":
                    await asyncio.sleep(float(job.payload.get("seconds", 1)))
                else:
                    raise ValueError(f"Unknown job type: {job.job_type}")
                await BackgroundJobRepository.complete(job.id)
            except Exception as exc:
                await BackgroundJobRepository.fail(job, str(exc))

def main():
    asyncio.run(BackgroundWorker().run())

if __name__ == "__main__":
    main()
