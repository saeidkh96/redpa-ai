from app.distributed_multi.schemas import (
    DistributedSubtaskResult,
)
from app.distributed_multi.service import (
    DistributedMultiAgentService,
)


def test_creates_distributed_subtasks() -> None:
    result = DistributedMultiAgentService.create_subtasks(
        "Research AI; then show Docker containers"
    )

    assert len(result) == 2
    assert result[0].id == "subtask-1"
    assert result[1].id == "subtask-2"


def test_aggregates_distributed_results() -> None:
    result = DistributedMultiAgentService.aggregate_results(
        request="Test",
        results=[
            DistributedSubtaskResult(
                subtask_id="subtask-1",
                instruction="Research",
                remote_agent="research-agent",
                selected_skill="web_research",
                success=True,
                response="Done",
                task_id="task-1",
                context_id="context-1",
                execution_time_ms=10.0,
                error=None,
            )
        ],
    )

    assert "Distributed Multi-Agent Result" in result
    assert "research-agent" in result
    assert "Done" in result
