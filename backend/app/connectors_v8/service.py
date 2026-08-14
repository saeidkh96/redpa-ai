from __future__ import annotations

import asyncio
import os
from uuid import UUID

import httpx

from app.connectors_v8.repository import ConnectorRepository
from app.connectors_v8.schemas import ConnectorExecuteRequest, ConnectorExecuteResponse


class ConnectorApprovalRequiredError(PermissionError):
    pass


class ConnectorService:
    @classmethod
    async def execute(cls, connector_id: UUID, payload: ConnectorExecuteRequest) -> ConnectorExecuteResponse:
        connector = await ConnectorRepository.get(connector_id)
        delivery_id = await ConnectorRepository.create_delivery(connector_id, dry_run=payload.dry_run)

        if not connector.enabled:
            delivery = await ConnectorRepository.finish_delivery(
                delivery_id, status="disabled", attempt_count=0, error="Connector is disabled."
            )
            return ConnectorExecuteResponse(connector=connector, delivery=delivery)

        if not payload.dry_run and not payload.approval_granted:
            delivery = await ConnectorRepository.finish_delivery(
                delivery_id, status="review_required", attempt_count=0,
                error="Approval is required for external side effects."
            )
            raise ConnectorApprovalRequiredError("Approval is required before executing this connector.")

        if payload.dry_run:
            delivery = await ConnectorRepository.finish_delivery(
                delivery_id, status="dry_run", attempt_count=0, response_status=None
            )
            return ConnectorExecuteResponse(connector=connector, delivery=delivery)

        headers = {"User-Agent": "RedPA-AI/8.0"}
        secret = os.getenv(connector.secret_env_var, "").strip() if connector.secret_env_var else ""
        if connector.kind == "github_dispatch":
            headers["Accept"] = "application/vnd.github+json"
            if secret:
                headers["Authorization"] = f"Bearer {secret}"
        elif secret:
            headers["Authorization"] = f"Bearer {secret}"

        last_error: str | None = None
        last_status: int | None = None
        attempts = 0
        async with httpx.AsyncClient(timeout=20.0) as client:
            for attempts in range(1, 4):
                try:
                    response = await client.post(connector.endpoint_url, json=payload.payload, headers=headers)
                    last_status = response.status_code
                    if response.is_success:
                        delivery = await ConnectorRepository.finish_delivery(
                            delivery_id, status="delivered", attempt_count=attempts,
                            response_status=response.status_code,
                        )
                        return ConnectorExecuteResponse(connector=connector, delivery=delivery)
                    last_error = f"HTTP {response.status_code}: {response.text[:500]}"
                except httpx.HTTPError as exc:
                    last_error = str(exc)
                if attempts < 3:
                    await asyncio.sleep(0.25 * (2 ** (attempts - 1)))

        delivery = await ConnectorRepository.finish_delivery(
            delivery_id, status="failed", attempt_count=attempts,
            response_status=last_status, error=last_error,
        )
        return ConnectorExecuteResponse(connector=connector, delivery=delivery)
