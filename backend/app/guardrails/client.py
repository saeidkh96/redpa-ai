from __future__ import annotations

import os

import httpx

from app.guardrails.contracts import (
    GuardrailDecision,
    GuardrailEvaluation,
    GuardrailRequest,
    RiskLevel,
)


class PolicyServiceError(RuntimeError):
    pass


class PolicyServiceClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float = 5.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = (
            base_url
            or os.getenv(
                "POLICY_SERVICE_URL",
                "http://localhost:8090",
            )
        ).rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._transport = transport

    async def evaluate(
        self,
        request: GuardrailRequest,
    ) -> GuardrailEvaluation:
        payload = {
            "action": request.action.action,
            "resource": request.action.resource,
            "arguments": request.action.arguments,
            "agentId": request.agent_id,
            "userId": request.user_id,
            "workflowId": request.workflow_id,
            "metadata": request.metadata,
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                transport=self._transport,
            ) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/policies/evaluate",
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise PolicyServiceError(
                f"Policy service request failed: {exc}",
            ) from exc

        try:
            data = response.json()
            return GuardrailEvaluation(
                decision=GuardrailDecision(data["decision"]),
                risk=RiskLevel(data["risk"]),
                reason=str(data["reason"]),
                matched_rules=tuple(
                    str(item)
                    for item in data.get("matchedRules", [])
                ),
                policy_version=str(
                    data.get("policyVersion", "unknown")
                ),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise PolicyServiceError(
                "Policy service returned an invalid response.",
            ) from exc

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(
                timeout=min(self.timeout_seconds, 3.0),
                transport=self._transport,
            ) as client:
                response = await client.get(
                    f"{self.base_url}/actuator/health",
                )
                response.raise_for_status()
                payload = response.json()
                return payload.get("status") == "UP"
        except (httpx.HTTPError, ValueError, TypeError):
            return False
