from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.a2a.registry import agent_registry
from app.a2a_remote.client import RemoteA2AClient, RemoteA2AError


@dataclass(slots=True)
class _ReplacementAgentRecord:
    name: str
    base_url: str
    timeout_seconds: float = 60.0
    enabled: bool = True
    card: Any | None = None
    connected: bool = False
    error: str | None = None
    last_checked_at: Any | None = None


class ReplacementExecutionAdapter:
    """
    V12 Stage 6 real A2A replacement-agent execution.

    Flow:
        replacement agent
        -> AgentRegistry
        -> endpoint resolution
        -> existing RemoteA2AClient
        -> A2A send_message()
        -> response collection
        -> verification
    """

    DEFAULT_TIMEOUT_SECONDS = 60.0

    @staticmethod
    def _timeout_from_metadata(
        metadata: dict[str, Any],
    ) -> float:
        raw = metadata.get(
            "timeout_seconds",
            ReplacementExecutionAdapter.DEFAULT_TIMEOUT_SECONDS,
        )

        try:
            timeout = float(raw)
        except (TypeError, ValueError):
            timeout = ReplacementExecutionAdapter.DEFAULT_TIMEOUT_SECONDS

        if timeout <= 0:
            timeout = ReplacementExecutionAdapter.DEFAULT_TIMEOUT_SECONDS

        return min(timeout, 300.0)

    async def execute(
        self,
        handoff: dict[str, Any],
    ) -> dict[str, Any]:
        target_agent_id = str(
            handoff.get("target_agent_id") or ""
        ).strip()

        task = str(
            handoff.get("task") or ""
        ).strip()

        if not target_agent_id:
            raise RuntimeError(
                "Replacement handoff does not contain target_agent_id."
            )

        if not task:
            raise RuntimeError(
                "Replacement handoff does not contain a task."
            )

        card = await agent_registry.get(target_agent_id)

        endpoint = card.endpoint

        if endpoint is None:
            raise RuntimeError(
                f"Replacement agent '{target_agent_id}' "
                "does not expose an A2A endpoint."
            )

        base_url = RemoteA2AClient.validate_base_url(
            endpoint.url
        )

        metadata = dict(card.metadata or {})

        timeout_seconds = self._timeout_from_metadata(
            metadata
        )

        record = _ReplacementAgentRecord(
            name=card.id,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
        )

        try:
            response = await RemoteA2AClient.delegate(
                record,
                task,
                timeout_seconds=timeout_seconds,
            )

        except RemoteA2AError:
            raise

        except Exception as exc:
            raise RuntimeError(
                f"A2A replacement execution failed for "
                f"'{target_agent_id}': {exc}"
            ) from exc

        return {
            "accepted": response.success,
            "agent_id": target_agent_id,
            "task": task,
            "base_url": base_url,
            "workflow_id": handoff.get("workflow_id"),
            "run_id": handoff.get("run_id"),
            "trace_id": handoff.get("trace_id"),
            "event_count": response.event_count,
            "events": response.events,
            "final_response": response.final_response,
            "execution_time_ms": response.execution_time_ms,
            "remote_error": response.error,
        }

    async def verify(
        self,
        *,
        target_agent_id: str,
        execution_result: dict[str, Any],
    ) -> dict[str, Any]:
        accepted = bool(
            execution_result.get("accepted")
        )

        event_count = int(
            execution_result.get("event_count") or 0
        )

        final_response = execution_result.get(
            "final_response"
        )

        remote_error = execution_result.get(
            "remote_error"
        )

        healthy = (
            accepted
            and event_count > 0
            and final_response is not None
            and not remote_error
        )

        return {
            "agent_id": target_agent_id,
            "healthy": healthy,
            "accepted": accepted,
            "event_count": event_count,
            "final_response_present": final_response is not None,
            "remote_error": remote_error,
            "execution_time_ms": execution_result.get(
                "execution_time_ms"
            ),
        }


replacement_execution_adapter = ReplacementExecutionAdapter()
