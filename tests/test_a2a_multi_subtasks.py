from app.a2a_multi.service import (
    MultiAgentWorkflowService,
)


def test_creates_multiple_subtasks() -> None:
    result = MultiAgentWorkflowService.create_subtasks(
        "Research the topic; then inspect Docker containers"
    )

    assert len(result) == 2
    assert result[0].id == "subtask-1"
    assert result[1].id == "subtask-2"


def test_aggregates_results() -> None:
    from app.a2a_multi.schemas import (
        MultiAgentExecutionItem,
    )

    result = MultiAgentWorkflowService.aggregate_results(
        request="Test",
        results=[
            MultiAgentExecutionItem(
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

    assert "Multi-Agent Result" in result
    assert "research-agent" in result
    assert "Done" in result
