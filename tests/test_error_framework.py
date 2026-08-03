from app.errors.codes import ErrorCode
from app.errors.exceptions import (
    ResourceNotFoundError,
)


def test_resource_not_found_error() -> None:
    error = ResourceNotFoundError(
        "Conversation was not found.",
        details={
            "conversation_id": "123",
        },
    )

    assert error.status_code == 404
    assert error.code == ErrorCode.NOT_FOUND
    assert (
        error.details[
            "conversation_id"
        ]
        == "123"
    )
