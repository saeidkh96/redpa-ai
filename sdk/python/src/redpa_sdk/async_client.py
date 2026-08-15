from __future__ import annotations

from typing import Any

import httpx

from redpa_sdk.client import RedPAError
from redpa_sdk.config import RedPAConfig
from redpa_sdk.models import Health, Provider, ProviderHealth, ReliabilityScorecard


class AsyncRedPA:
    def __init__(
        self,
        config: RedPAConfig | None = None,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.config = config or RedPAConfig.from_env()
        headers = {"Accept": "application/json"}
        if self.config.token:
            headers["Authorization"] = f"Bearer {self.config.token}"
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout_seconds,
            headers=headers,
            transport=transport,
        )

    async def __aenter__(self) -> "AsyncRedPA":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    @staticmethod
    def _detail(response: httpx.Response) -> Any:
        try:
            body = response.json()
        except ValueError:
            return response.text
        return body.get("detail", body) if isinstance(body, dict) else body

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = await self._client.request(method, path, **kwargs)
        except httpx.RequestError as exc:
            raise RedPAError(
                f"Cannot connect to RedPA API at {self.config.base_url}.",
                detail={
                    "type": exc.__class__.__name__,
                    "message": str(exc),
                    "hint": "Start or rebuild the RedPA backend, or set REDPA_API_URL to the correct API address.",
                },
            ) from exc
        if response.is_error:
            raise RedPAError(
                f"RedPA API request failed with HTTP {response.status_code}.",
                status_code=response.status_code,
                detail=self._detail(response),
            )
        if response.status_code == 204:
            return None
        return response.json()

    async def health(self) -> Health:
        return Health.model_validate(await self._request("GET", "/api/v1/health"))

    async def providers(self) -> list[Provider]:
        payload = await self._request("GET", "/api/v1/model-gateway/providers")
        return [Provider.model_validate(item) for item in payload]

    async def provider_health(self) -> list[ProviderHealth]:
        payload = await self._request("GET", "/api/v1/model-gateway/health")
        return [ProviderHealth.model_validate(item) for item in payload]

    async def reliability_scorecard(self) -> ReliabilityScorecard:
        return ReliabilityScorecard.model_validate(
            await self._request("GET", "/api/v1/model-gateway/reliability/scorecard")
        )

    async def workflows(self, *, limit: int = 50) -> list[dict[str, Any]]:
        return await self._request(
            "GET",
            "/api/v1/agents/distributed/durable",
            params={"limit": limit},
        )

    async def workflow(self, workflow_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/api/v1/agents/distributed/durable/{workflow_id}")

    async def reviews(self, *, status: str | None = None, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        return await self._request("GET", "/api/v1/reviews", params=params)

    async def approve_review(self, review_id: str, *, feedback: str | None = None) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/api/v1/reviews/{review_id}/approve",
            json={"feedback": feedback},
        )

    async def mcp_health(self) -> dict[str, Any]:
        return await self._request("GET", "/api/v1/mcp/health")

    async def execute_mcp_tool(
        self,
        qualified_name: str,
        *,
        arguments: dict[str, Any] | None = None,
        approval_granted: bool = False,
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/api/v1/mcp/tools/execute",
            json={
                "qualified_name": qualified_name,
                "arguments": arguments or {},
                "approval_granted": approval_granted,
            },
        )

    async def research_runs(self, *, limit: int = 50) -> dict[str, Any]:
        return await self._request(
            "GET",
            "/api/v1/research/runs",
            params={"limit": limit},
        )

    async def research_run(self, run_id: str) -> dict[str, Any]:
        return await self._request(
            "GET",
            f"/api/v1/research/runs/{run_id}",
        )

    async def start_research(
        self,
        query: str,
        *,
        max_results: int = 8,
        minimum_quality_score: float = 0.65,
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/api/v1/research/runs",
            json={
                "query": query,
                "max_results": max_results,
                "minimum_quality_score": minimum_quality_score,
            },
        )


    async def analytics_catalog(self) -> dict[str, Any]:
        return await self._request("GET", "/api/v1/analytics/catalog")

    async def ingest_analytics(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return await self._request("POST", "/api/v1/analytics/events", json={"items": items})

    async def query_kpi(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/api/v1/analytics/query", json=payload)

    async def connectors(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return await self._request("GET", "/api/v1/connectors", params={"limit": limit})

    async def create_connector(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/api/v1/connectors", json=payload)

    async def execute_connector(self, connector_id: str, *, payload: dict[str, Any], approval_granted: bool = False, dry_run: bool = True) -> dict[str, Any]:
        return await self._request("POST", f"/api/v1/connectors/{connector_id}/execute", json={"payload": payload, "approval_granted": approval_granted, "dry_run": dry_run})

    async def evaluate_slo(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/api/v1/operations/slo/evaluate", json=payload)

    async def list_incidents(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return await self._request("GET", "/api/v1/operations/v9/incidents", params={"limit": limit})

    async def create_incident(self, service: str, summary: str, *, severity: str = "warning") -> dict[str, Any]:
        return await self._request("POST", "/api/v1/operations/v9/incidents", json={"service": service, "summary": summary, "severity": severity, "source": "sdk", "metadata": {}})

    async def estimate_cloud_cost(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/api/v1/operations/v9/cost/estimate", json=payload)

    async def release_readiness(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/api/v1/operations/v9/release/readiness", json=payload)
