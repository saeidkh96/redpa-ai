from app.security.rbac import (
    Permission,
    Role,
    authorize,
    role_allows,
)


def test_owner_has_every_permission() -> None:
    for permission in Permission:
        assert role_allows(Role.OWNER, permission)


def test_reviewer_can_decide_reviews() -> None:
    assert role_allows(
        Role.REVIEWER,
        Permission.REVIEW_DECIDE,
    )


def test_viewer_cannot_execute_mcp() -> None:
    assert not role_allows(
        Role.VIEWER,
        Permission.MCP_EXECUTE,
    )


def test_authorization_decision_explains_denial() -> None:
    decision = authorize(
        Role.VIEWER,
        Permission.MEMBER_WRITE,
    )

    assert not decision.allowed
    assert "does not grant" in decision.reason
