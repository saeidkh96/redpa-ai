from __future__ import annotations

from typing import Any

import httpx

from redpa_sdk.config import RedPAConfig
from redpa_sdk.models import (
    AgentList,
    Health,
    Provider,
    ProviderHealth,
    ReliabilityScorecard,
    ReleaseGateResult,
    ToolCatalog,
)


class RedPAError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, detail: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


class RedPA:
    def __init__(
        self,
        config: RedPAConfig | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.config = config or RedPAConfig.from_env()
        headers = {"Accept": "application/json"}
        if self.config.token:
            headers["Authorization"] = f"Bearer {self.config.token}"

        self._client = httpx.Client(
            base_url=self.config.base_url,
            timeout=self.config.timeout_seconds,
            headers=headers,
            transport=transport,
        )

    def __enter__(self) -> "RedPA":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    @staticmethod
    def _detail(response: httpx.Response) -> Any:
        try:
            body = response.json()
        except ValueError:
            return response.text
        if isinstance(body, dict) and "detail" in body:
            return body["detail"]
        return body

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = self._client.request(method, path, **kwargs)
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
            detail = self._detail(response)
            raise RedPAError(
                f"RedPA API request failed with HTTP {response.status_code}.",
                status_code=response.status_code,
                detail=detail,
            )
        if response.status_code == 204:
            return None
        return response.json()

    def health(self) -> Health:
        return Health.model_validate(self._request("GET", "/api/v1/health"))

    def agents(self) -> AgentList:
        return AgentList.model_validate(self._request("GET", "/api/v1/agents"))

    def discover_agents(self, query: str, *, limit: int = 10) -> dict[str, Any]:
        return self._request(
            "GET",
            "/api/v1/agents/discover",
            params={"query": query, "limit": limit},
        )

    def providers(self) -> list[Provider]:
        payload = self._request("GET", "/api/v1/model-gateway/providers")
        return [Provider.model_validate(item) for item in payload]

    def provider_health(self) -> list[ProviderHealth]:
        payload = self._request("GET", "/api/v1/model-gateway/health")
        return [ProviderHealth.model_validate(item) for item in payload]

    def tools(self, *, refresh: bool = False) -> ToolCatalog:
        return ToolCatalog.model_validate(
            self._request(
                "GET",
                "/api/v1/tools/catalog",
                params={"refresh": str(refresh).lower()},
            )
        )

    def reliability_scorecard(self) -> ReliabilityScorecard:
        return ReliabilityScorecard.model_validate(
            self._request("GET", "/api/v1/model-gateway/reliability/scorecard")
        )

    def release_gate(
        self,
        *,
        baseline_run_id: str,
        candidate_run_id: str,
        release_label: str | None = None,
        max_aggregate_drop: float = 0.05,
        max_metric_drop: float = 0.10,
        minimum_candidate_score: float | None = 0.70,
        require_candidate_pass: bool = True,
    ) -> ReleaseGateResult:
        body = {
            "baseline_run_id": baseline_run_id,
            "candidate_run_id": candidate_run_id,
            "release_label": release_label,
            "max_aggregate_drop": max_aggregate_drop,
            "max_metric_drop": max_metric_drop,
            "minimum_candidate_score": minimum_candidate_score,
            "require_candidate_pass": require_candidate_pass,
            "metadata": {"source": "python_sdk"},
        }
        return ReleaseGateResult.model_validate(
            self._request(
                "POST",
                "/api/v1/evaluations/release-gates/evaluate",
                json=body,
            )
        )

    def candidate_report(self, candidate_run_id: str) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/api/v1/evaluations/release-candidates/{candidate_run_id}/report",
        )
