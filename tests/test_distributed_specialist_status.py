from app.distributed_multi.service import (
    DistributedMultiAgentService,
)


def test_extracts_failed_specialist_status() -> None:
    success, error = (
        DistributedMultiAgentService
        ._extract_specialist_status(
            (
                '{"success": false, '
                '"error": "Container not found."}'
            )
        )
    )

    assert success is False
    assert error == "Container not found."


def test_extracts_successful_specialist_status() -> None:
    success, error = (
        DistributedMultiAgentService
        ._extract_specialist_status(
            (
                '{"success": true, '
                '"containers": []}'
            )
        )
    )

    assert success is True
    assert error is None


def test_ignores_non_json_response() -> None:
    success, error = (
        DistributedMultiAgentService
        ._extract_specialist_status(
            "Plain text response"
        )
    )

    assert success is None
    assert error is None
