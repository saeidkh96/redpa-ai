from __future__ import annotations

import os
from typing import Any

import httpx

from app.core.config import settings


class N8NError(Exception):
    pass


class N8NClient:
    def __init__(self) -> None:
        self.base_url = settings.n8n_base_url.rstrip("/")
        self.timeout = settings.n8n_timeout_seconds
        self.allowed = {
            name.strip()
            for name in settings.n8n_allowed_workflows.split(",")
            if name.strip()
        }

    async def execute(
        self,
        workflow: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        if workflow not in self.allowed:
            raise N8NError("Workflow is not allowlisted")

        if not workflow or not all(
            char.isascii() and (char.isalnum() or char in "-_")
            for char in workflow
        ):
            raise N8NError("Invalid workflow name")

        url = f"{self.base_url}/webhook/{workflow}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise N8NError("n8n workflow execution failed") from exc

        if not isinstance(data, dict):
            raise N8NError("Unexpected n8n response format")

        return data
