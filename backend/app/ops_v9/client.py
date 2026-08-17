from __future__ import annotations
import asyncio
import os
import time

import httpx


class OpsAgentClient:
    def __init__(self) -> None:
        self.base_url = os.getenv('OPS_AGENT_URL','http://ops-agent:8070').rstrip('/')

    async def diagnose(self, container: str) -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f'{self.base_url}/containers/{container}/diagnose')
            response.raise_for_status()
            return response.json()

    async def restart(self, container: str, *, approved: bool, reason: str) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f'{self.base_url}/containers/{container}/restart',
                json={'approved': approved, 'reason': reason},
            )
            response.raise_for_status()
            return response.json()


    async def wait_until_healthy(
        self, container: str, *, timeout_seconds: float = 60.0, poll_seconds: float = 2.0
    ) -> dict:
        deadline = time.monotonic() + timeout_seconds
        last: dict = {}
        while time.monotonic() < deadline:
            last = await self.diagnose(container)
            state = last.get("state")
            health = last.get("health")
            if state == "running" and health in {None, "healthy"}:
                return last
            await asyncio.sleep(poll_seconds)
        raise RuntimeError(
            f"Recovery verification timed out for {container}: {last}"
        )
