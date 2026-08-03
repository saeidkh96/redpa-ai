from __future__ import annotations

from uuid import UUID

from app.a2a_multi.policy import (
    A2AApprovalPolicy,
)
from app.distributed_durable.repository import (
    DurableWorkflowRepository,
)
from app.distributed_durable.schemas import (
    DurableWorkflowCreate,
    DurableWorkflowExecutionResponse,
    DurableWorkflowResume,
)
from app.distributed_multi.schemas import (
    DistributedSubtask,
    DistributedWorkflowRequest,
)
from app.distributed_multi.service import (
    DistributedMultiAgentService,
)


class DurableDistributedWorkflowService:
    @classmethod
    async def create_and_execute(
        cls,
        payload: DurableWorkflowCreate,
    ) -> DurableWorkflowExecutionResponse:
        subtasks = (
            payload.subtasks
            if payload.subtasks
            else DistributedMultiAgentService.create_subtasks(
                payload.request,
            )
        )

        workflow_id = (
            await DurableWorkflowRepository.create_workflow(
                request=payload.request,
                subtasks=subtasks,
                max_parallelism=payload.max_parallelism,
                timeout_seconds=payload.timeout_seconds,
                approval_granted=payload.approval_granted,
            )
        )

        return await cls._execute(
            workflow_id=workflow_id,
            subtasks=subtasks,
            approval_granted=payload.approval_granted,
            resumed=False,
        )

    @classmethod
    async def resume(
        cls,
        workflow_id: UUID,
        payload: DurableWorkflowResume,
    ) -> DurableWorkflowExecutionResponse:
        workflow = (
            await DurableWorkflowRepository.get_workflow(
                workflow_id,
            )
        )

        retry_statuses = {
            "pending",
        }

        if payload.retry_failed:
            retry_statuses.add(
                "failed",
            )

        if payload.retry_running:
            retry_statuses.add(
                "running",
            )

        subtasks = [
            DistributedSubtask(
                id=subtask.subtask_key,
                instruction=subtask.instruction,
            )
            for subtask in workflow.subtasks
            if subtask.status in retry_statuses
        ]

        if not subtasks:
            return DurableWorkflowExecutionResponse(
                workflow=workflow,
                resumed=True,
                executed_subtasks=[],
            )

        return await cls._execute(
            workflow_id=workflow_id,
            subtasks=subtasks,
            approval_granted=(
                payload.approval_granted
                or workflow.approval_granted
            ),
            resumed=True,
        )

    @classmethod
    async def _execute(
        cls,
        *,
        workflow_id: UUID,
        subtasks: list[DistributedSubtask],
        approval_granted: bool,
        resumed: bool,
    ) -> DurableWorkflowExecutionResponse:
        workflow = (
            await DurableWorkflowRepository.get_workflow(
                workflow_id,
            )
        )

        approval = A2AApprovalPolicy.evaluate(
            workflow.request,
        )

        if (
            approval.required
            and not approval_granted
        ):
            await (
                DurableWorkflowRepository
                .mark_approval_required(
                    workflow_id,
                    reason=approval.reason,
                )
            )

            return DurableWorkflowExecutionResponse(
                workflow=(
                    await DurableWorkflowRepository
                    .get_workflow(
                        workflow_id,
                    )
                ),
                resumed=resumed,
                executed_subtasks=[],
            )

        await DurableWorkflowRepository.mark_workflow_running(
            workflow_id,
            approval_granted=approval_granted,
        )

        await DurableWorkflowRepository.mark_subtasks_running(
            workflow_id,
            [
                subtask.id
                for subtask in subtasks
            ],
        )

        execution = await DistributedMultiAgentService.execute(
            DistributedWorkflowRequest(
                request=workflow.request,
                subtasks=subtasks,
                max_parallelism=workflow.max_parallelism,
                timeout_seconds=workflow.timeout_seconds,
                approval_granted=approval_granted,
            )
        )

        await DurableWorkflowRepository.save_subtask_results(
            workflow_id,
            execution.results,
        )

        current = await DurableWorkflowRepository.get_workflow(
            workflow_id,
        )

        successful = sum(
            1
            for subtask in current.subtasks
            if subtask.status == "completed"
        )

        failed = sum(
            1
            for subtask in current.subtasks
            if subtask.status == "failed"
        )

        pending_or_running = any(
            subtask.status in {
                "pending",
                "running",
            }
            for subtask in current.subtasks
        )

        if pending_or_running:
            final_status = "running"
        elif failed == 0 and successful > 0:
            final_status = "completed"
        elif successful > 0:
            final_status = "partial"
        else:
            final_status = "failed"

        aggregated = (
            DistributedMultiAgentService.aggregate_results(
                request=workflow.request,
                results=[
                    result
                    for result in execution.results
                ],
            )
        )

        await DurableWorkflowRepository.finalize_workflow(
            workflow_id,
            status=final_status,
            aggregated_response=aggregated,
            successful_subtasks=successful,
            failed_subtasks=failed,
            metadata={
                **execution.metadata,
                "durable": True,
                "resumed": resumed,
            },
        )

        return DurableWorkflowExecutionResponse(
            workflow=(
                await DurableWorkflowRepository
                .get_workflow(
                    workflow_id,
                )
            ),
            resumed=resumed,
            executed_subtasks=execution.results,
        )
