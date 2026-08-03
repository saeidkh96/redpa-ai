from app.a2a_multi.policy import (
    A2AApprovalPolicy,
)


def test_safe_request_does_not_require_approval() -> None:
    result = A2AApprovalPolicy.evaluate(
        "Research current AI trends and summarize the evidence."
    )

    assert result.required is False


def test_email_request_requires_approval() -> None:
    result = A2AApprovalPolicy.evaluate(
        "Send an email to the project manager."
    )

    assert result.required is True
    assert result.reason is not None
