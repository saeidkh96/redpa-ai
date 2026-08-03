from app.distributed_durable.schemas import (
    DurableWorkflowResume,
)


def test_resume_defaults_retry_failed_and_running() -> None:
    payload = DurableWorkflowResume()

    assert payload.retry_failed is True
    assert payload.retry_running is True
    assert payload.approval_granted is False
