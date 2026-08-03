from __future__ import annotations

import asyncio
import re
import time
from typing import Any

from app.a2a_multi.metrics import (
    A2A_APPROVAL_REQUIRED_TOTAL,
    A2A_MULTI_DURATION_SECONDS,
    A2A_MULTI_REQUESTS_TOTAL,
    A2A_MULTI_SUBTASK_DURATION_SECONDS,
    A2A_MULTI_SUBTASKS_TOTAL,
)
from app.a2a_multi.policy import A2AApprovalPolicy
from app.a2a_multi.schemas import (
    MultiAgentExecutionItem,
    MultiAgentRequest,
    MultiAgentResponse,
    MultiAgentSubtask,
)
from app.a2a_remote.bootstrap import (
    RemoteAgentBootstrapService,
)
from app.a2a_remote.client import (
    RemoteA2AClient,
    RemoteA2AError,
)
from app.a2a_remote.registry import (
    RemoteAgentRecord,
    remote_agent_registry,
)
from app.services.a2a_chat_service import A2AChatService


class MultiAgentWorkflowService:
    @classmethod
    async def execute(
        cls,
        request: MultiAgentRequest,
    ) -> MultiAgentResponse:
        workflow_started = time.perf_counter()

        approval = A2AApprovalPolicy.evaluate(
            request.request,
        )

        if (
            approval.required
            and not request.approval_granted
        ):
            A2A_APPROVAL_REQUIRED_TOTAL.labels(
                reason=approval.matched_signal or "policy",
            ).inc()

            A2A_MULTI_REQUESTS_TOTAL.labels(
                status="approval_required",
            ).inc()

            return MultiAgentResponse(
                success=False,
                approval_required=True,
                review_reason=approval.reason,
                request=request.request,
                results=[],
                aggregated_response=(
                    "This multi-agent workflow requires human approval "
                    "before remote delegation can begin."
                ),
                total_subtasks=0,
                successful_subtasks=0,
                failed_subtasks=0,
                execution_time_ms=round(
                    (
                        time.perf_counter()
                        - workflow_started
                    )
                    * 1_000,
                    2,
                ),
                metadata={
                    "matched_signal": approval.matched_signal,
                },
            )

        await RemoteAgentBootstrapService.ensure_defaults()

        records = [
            record
            for record in await remote_agent_registry.list()
            if record.enabled
        ]

        if not records:
            A2A_MULTI_REQUESTS_TOTAL.labels(
                status="failed",
            ).inc()

            return MultiAgentResponse(
                success=False,
                approval_required=False,
                review_reason=None,
                request=request.request,
                results=[],
                aggregated_response=(
                    "No enabled remote A2A agent is available."
                ),
                total_subtasks=0,
                successful_subtasks=0,
                failed_subtasks=0,
                execution_time_ms=round(
                    (
                        time.perf_counter()
                        - workflow_started
                    )
                    * 1_000,
                    2,
                ),
                metadata={},
            )

        subtasks = (
            request.subtasks
            if request.subtasks
            else cls.create_subtasks(
                request.request,
            )
        )

        semaphore = asyncio.Semaphore(
            request.max_parallelism,
        )

        async def run_one(
            subtask: MultiAgentSubtask,
        ) -> MultiAgentExecutionItem:
            async with semaphore:
                return await cls._execute_subtask(
                    subtask=subtask,
                    records=records,
                    timeout_seconds=request.timeout_seconds,
                )

        try:
            async with asyncio.timeout(
                request.timeout_seconds,
            ):
                results = await asyncio.gather(
                    *[
                        run_one(
                            subtask,
                        )
                        for subtask in subtasks
                    ]
                )
        except TimeoutError:
            A2A_MULTI_REQUESTS_TOTAL.labels(
                status="timeout",
            ).inc()

            elapsed = (
                time.perf_counter()
                - workflow_started
            )

            A2A_MULTI_DURATION_SECONDS.observe(
                elapsed,
            )

            return MultiAgentResponse(
                success=False,
                approval_required=False,
                review_reason=None,
                request=request.request,
                results=[],
                aggregated_response=(
                    "The multi-agent workflow timed out."
                ),
                total_subtasks=len(
                    subtasks,
                ),
                successful_subtasks=0,
                failed_subtasks=len(
                    subtasks,
                ),
                execution_time_ms=round(
                    elapsed
                    * 1_000,
                    2,
                ),
                metadata={
                    "timeout_seconds": request.timeout_seconds,
                },
            )

        successful = sum(
            1
            for result in results
            if result.success
        )

        failed = len(
            results,
        ) - successful

        success = (
            successful > 0
            and failed == 0
        )

        status_label = (
            "success"
            if success
            else (
                "partial"
                if successful > 0
                else "failed"
            )
        )

        A2A_MULTI_REQUESTS_TOTAL.labels(
            status=status_label,
        ).inc()

        elapsed = (
            time.perf_counter()
            - workflow_started
        )

        A2A_MULTI_DURATION_SECONDS.observe(
            elapsed,
        )

        return MultiAgentResponse(
            success=success,
            approval_required=False,
            review_reason=None,
            request=request.request,
            results=results,
            aggregated_response=cls.aggregate_results(
                request=request.request,
                results=results,
            ),
            total_subtasks=len(
                subtasks,
            ),
            successful_subtasks=successful,
            failed_subtasks=failed,
            execution_time_ms=round(
                elapsed
                * 1_000,
                2,
            ),
            metadata={
                "max_parallelism": request.max_parallelism,
                "remote_agents": sorted(
                    {
                        result.remote_agent
                        for result in results
                        if result.remote_agent
                    }
                ),
            },
        )

    @classmethod
    async def _execute_subtask(
        cls,
        *,
        subtask: MultiAgentSubtask,
        records: list[RemoteAgentRecord],
        timeout_seconds: float,
    ) -> MultiAgentExecutionItem:
        started = time.perf_counter()

        selected, selection = A2AChatService.select_remote_agent(
            user_message=subtask.instruction,
            records=records,
        )

        try:
            delegation = await RemoteA2AClient.delegate(
                selected,
                subtask.instruction,
                timeout_seconds=timeout_seconds,
            )

            task_payload = A2AChatService._extract_task_payload(
                delegation.final_response,
            )

            response = A2AChatService._extract_artifact_text(
                task_payload,
            )

            success = bool(
                delegation.success
            )

            error = delegation.error

        except RemoteA2AError as exception:
            delegation = None
            task_payload = {}
            response = None
            success = False
            error = str(
                exception,
            )

        elapsed = (
            time.perf_counter()
            - started
        )

        remote_agent_name = selected.name

        A2A_MULTI_SUBTASKS_TOTAL.labels(
            status=(
                "success"
                if success
                else "failed"
            ),
            remote_agent=remote_agent_name,
        ).inc()

        A2A_MULTI_SUBTASK_DURATION_SECONDS.labels(
            remote_agent=remote_agent_name,
        ).observe(
            elapsed,
        )

        return MultiAgentExecutionItem(
            subtask_id=subtask.id,
            instruction=subtask.instruction,
            remote_agent=remote_agent_name,
            selected_skill=selection.get(
                "selected_skill",
            ),
            success=success,
            response=response,
            task_id=A2AChatService._optional_string(
                task_payload.get(
                    "id",
                )
            ),
            context_id=A2AChatService._optional_string(
                task_payload.get(
                    "context_id",
                )
            ),
            execution_time_ms=round(
                elapsed
                * 1_000,
                2,
            ),
            error=error,
        )

    @staticmethod
    def create_subtasks(
        request: str,
    ) -> list[MultiAgentSubtask]:
        normalized = str(
            request
            or "",
        ).strip()

        segments = [
            segment.strip(
                " .,:;\n\t"
            )
            for segment in re.split(
                r"\s*(?:;|\n|\bthen\b|\band\s+also\b)\s*",
                normalized,
                flags=re.IGNORECASE,
            )
            if segment.strip(
                " .,:;\n\t"
            )
        ]

        if len(
            segments,
        ) <= 1:
            segments = [
                normalized,
            ]

        return [
            MultiAgentSubtask(
                id=f"subtask-{index}",
                instruction=segment,
            )
            for index, segment in enumerate(
                segments,
                start=1,
            )
        ]

    @staticmethod
    def aggregate_results(
        *,
        request: str,
        results: list[MultiAgentExecutionItem],
    ) -> str:
        sections = [
            "# Multi-Agent Result",
            "",
            f"Original request: {request}",
            "",
        ]

        for result in results:
            sections.extend(
                [
                    (
                        f"## {result.subtask_id} — "
                        f"{result.remote_agent or 'unassigned'}"
                    ),
                    "",
                    f"Instruction: {result.instruction}",
                    "",
                    (
                        result.response
                        if result.success and result.response
                        else (
                            "Subtask failed: "
                            f"{result.error or 'unknown error'}"
                        )
                    ),
                    "",
                ]
            )

        return "\n".join(
            sections,
        ).strip()
