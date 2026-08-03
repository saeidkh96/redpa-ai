from __future__ import annotations

import asyncio
import json
import re
import time
from typing import Any

from app.a2a_multi.policy import A2AApprovalPolicy
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
from app.distributed_multi.metrics import (
    DISTRIBUTED_SUBTASK_DURATION_SECONDS,
    DISTRIBUTED_SUBTASKS_TOTAL,
    DISTRIBUTED_WORKFLOW_DURATION_SECONDS,
    DISTRIBUTED_WORKFLOWS_TOTAL,
)
from app.distributed_multi.schemas import (
    DistributedSubtask,
    DistributedSubtaskResult,
    DistributedWorkflowRequest,
    DistributedWorkflowResponse,
)
from app.services.a2a_chat_service import (
    A2AChatService,
)


class DistributedMultiAgentService:
    @classmethod
    async def execute(
        cls,
        request: DistributedWorkflowRequest,
    ) -> DistributedWorkflowResponse:
        started = time.perf_counter()

        approval = A2AApprovalPolicy.evaluate(
            request.request,
        )

        if (
            approval.required
            and not request.approval_granted
        ):
            DISTRIBUTED_WORKFLOWS_TOTAL.labels(
                status="approval_required",
            ).inc()

            return DistributedWorkflowResponse(
                success=False,
                approval_required=True,
                review_reason=approval.reason,
                request=request.request,
                results=[],
                aggregated_response=(
                    "Distributed execution requires "
                    "human approval."
                ),
                total_subtasks=0,
                successful_subtasks=0,
                failed_subtasks=0,
                execution_time_ms=round(
                    (
                        time.perf_counter()
                        - started
                    )
                    * 1000,
                    2,
                ),
                metadata={
                    "matched_signal": (
                        approval.matched_signal
                    ),
                },
            )

        await (
            RemoteAgentBootstrapService
            .ensure_defaults()
        )

        records = [
            record
            for record in (
                await remote_agent_registry.list()
            )
            if record.enabled
            and record.name != "redpa-coordinator"
        ]

        if not records:
            DISTRIBUTED_WORKFLOWS_TOTAL.labels(
                status="failed",
            ).inc()

            return cls._empty_failure(
                request=request.request,
                started=started,
                message=(
                    "No enabled specialist Remote "
                    "Agent is available."
                ),
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
            subtask: DistributedSubtask,
        ) -> DistributedSubtaskResult:
            async with semaphore:
                return await cls._run_subtask(
                    subtask=subtask,
                    records=records,
                    timeout_seconds=(
                        request.timeout_seconds
                    ),
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
            elapsed = (
                time.perf_counter()
                - started
            )

            DISTRIBUTED_WORKFLOWS_TOTAL.labels(
                status="timeout",
            ).inc()

            (
                DISTRIBUTED_WORKFLOW_DURATION_SECONDS
                .observe(
                    elapsed,
                )
            )

            return DistributedWorkflowResponse(
                success=False,
                approval_required=False,
                review_reason=None,
                request=request.request,
                results=[],
                aggregated_response=(
                    "Distributed multi-agent "
                    "workflow timed out."
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
                    * 1000,
                    2,
                ),
                metadata={
                    "timeout_seconds": (
                        request.timeout_seconds
                    ),
                },
            )

        successful = sum(
            1
            for result in results
            if result.success
        )

        failed = (
            len(
                results,
            )
            - successful
        )

        status = (
            "success"
            if failed == 0
            and successful > 0
            else "partial"
            if successful > 0
            else "failed"
        )

        DISTRIBUTED_WORKFLOWS_TOTAL.labels(
            status=status,
        ).inc()

        elapsed = (
            time.perf_counter()
            - started
        )

        (
            DISTRIBUTED_WORKFLOW_DURATION_SECONDS
            .observe(
                elapsed,
            )
        )

        return DistributedWorkflowResponse(
            success=(
                failed == 0
                and successful > 0
            ),
            approval_required=False,
            review_reason=None,
            request=request.request,
            results=results,
            aggregated_response=(
                cls.aggregate_results(
                    request=request.request,
                    results=results,
                )
            ),
            total_subtasks=len(
                results,
            ),
            successful_subtasks=successful,
            failed_subtasks=failed,
            execution_time_ms=round(
                elapsed
                * 1000,
                2,
            ),
            metadata={
                "max_parallelism": (
                    request.max_parallelism
                ),
                "remote_agents": sorted(
                    {
                        result.remote_agent
                        for result in results
                        if result.remote_agent
                    }
                ),
                "status": status,
            },
        )

    @classmethod
    async def _run_subtask(
        cls,
        *,
        subtask: DistributedSubtask,
        records: list[
            RemoteAgentRecord
        ],
        timeout_seconds: float,
    ) -> DistributedSubtaskResult:
        started = time.perf_counter()

        selected, selection = (
            A2AChatService
            .select_remote_agent(
                user_message=(
                    subtask.instruction
                ),
                records=records,
            )
        )

        try:
            delegation = (
                await RemoteA2AClient.delegate(
                    selected,
                    subtask.instruction,
                    timeout_seconds=(
                        timeout_seconds
                    ),
                )
            )

            task_payload = (
                A2AChatService
                ._extract_task_payload(
                    delegation.final_response,
                )
            )

            response = (
                A2AChatService
                ._extract_artifact_text(
                    task_payload,
                )
            )

            artifact_success, artifact_error = (
                cls._extract_specialist_status(
                    response,
                )
            )

            success = bool(
                delegation.success
            )

            if artifact_success is False:
                success = False

            error = (
                artifact_error
                or delegation.error
            )

        except RemoteA2AError as exception:
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

        DISTRIBUTED_SUBTASKS_TOTAL.labels(
            status=(
                "success"
                if success
                else "failed"
            ),
            remote_agent=selected.name,
        ).inc()

        (
            DISTRIBUTED_SUBTASK_DURATION_SECONDS
            .labels(
                remote_agent=selected.name,
            )
            .observe(
                elapsed,
            )
        )

        return DistributedSubtaskResult(
            subtask_id=subtask.id,
            instruction=subtask.instruction,
            remote_agent=selected.name,
            selected_skill=selection.get(
                "selected_skill",
            ),
            success=success,
            response=response,
            task_id=(
                A2AChatService
                ._optional_string(
                    task_payload.get(
                        "id",
                    )
                )
            ),
            context_id=(
                A2AChatService
                ._optional_string(
                    task_payload.get(
                        "context_id",
                    )
                )
            ),
            execution_time_ms=round(
                elapsed
                * 1000,
                2,
            ),
            error=error,
        )

    @staticmethod
    def _extract_specialist_status(
        response: str | None,
    ) -> tuple[
        bool | None,
        str | None,
    ]:
        if not response:
            return (
                None,
                None,
            )

        try:
            payload = json.loads(
                response,
            )
        except json.JSONDecodeError:
            return (
                None,
                None,
            )

        if not isinstance(
            payload,
            dict,
        ):
            return (
                None,
                None,
            )

        success_value = payload.get(
            "success",
        )

        if not isinstance(
            success_value,
            bool,
        ):
            return (
                None,
                None,
            )

        error_value = payload.get(
            "error",
        )

        error = (
            str(
                error_value,
            ).strip()
            if error_value is not None
            else None
        )

        return (
            success_value,
            error or None,
        )

    @staticmethod
    def create_subtasks(
        request: str,
    ) -> list[
        DistributedSubtask
    ]:
        text = str(
            request
            or "",
        ).strip()

        segments = [
            segment.strip(
                " .,:;\n\t"
            )
            for segment in re.split(
                (
                    r"\s*(?:;|\n|\bthen\b|"
                    r"\band\s+also\b)\s*"
                ),
                text,
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
                text,
            ]

        return [
            DistributedSubtask(
                id=(
                    f"subtask-{index}"
                ),
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
        results: list[
            DistributedSubtaskResult
        ],
    ) -> str:
        sections = [
            (
                "# Distributed "
                "Multi-Agent Result"
            ),
            "",
            (
                "Original request: "
                f"{request}"
            ),
            "",
        ]

        for result in results:
            sections.extend(
                [
                    (
                        f"## {result.subtask_id} "
                        f"— "
                        f"{result.remote_agent or 'unassigned'}"
                    ),
                    "",
                    (
                        "Instruction: "
                        f"{result.instruction}"
                    ),
                    "",
                    (
                        result.response
                        if result.success
                        and result.response
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

    @staticmethod
    def _empty_failure(
        *,
        request: str,
        started: float,
        message: str,
    ) -> DistributedWorkflowResponse:
        return DistributedWorkflowResponse(
            success=False,
            approval_required=False,
            review_reason=None,
            request=request,
            results=[],
            aggregated_response=message,
            total_subtasks=0,
            successful_subtasks=0,
            failed_subtasks=0,
            execution_time_ms=round(
                (
                    time.perf_counter()
                    - started
                )
                * 1000,
                2,
            ),
            metadata={},
        )
