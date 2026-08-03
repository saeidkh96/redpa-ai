from app.distributed_durable.repository import (
    DurableWorkflowRepository,
)


def test_normalizes_json_string_metadata() -> None:
    result = (
        DurableWorkflowRepository
        ._normalize_metadata(
            '{"status": "partial", "durable": true}'
        )
    )

    assert result == {
        "status": "partial",
        "durable": True,
    }


def test_normalizes_dict_metadata() -> None:
    payload = {
        "status": "completed",
    }

    result = (
        DurableWorkflowRepository
        ._normalize_metadata(
            payload,
        )
    )

    assert result == payload


def test_normalizes_empty_metadata() -> None:
    assert (
        DurableWorkflowRepository
        ._normalize_metadata(
            None,
        )
        == {}
    )
