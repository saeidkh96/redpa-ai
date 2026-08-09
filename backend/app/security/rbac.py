from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    OPERATOR = "operator"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


class Permission(StrEnum):
    TENANT_READ = "tenant:read"
    TENANT_WRITE = "tenant:write"
    MEMBER_READ = "member:read"
    MEMBER_WRITE = "member:write"
    REVIEW_READ = "review:read"
    REVIEW_DECIDE = "review:decide"
    POLICY_READ = "policy:read"
    POLICY_ENFORCE = "policy:enforce"
    MODEL_GATEWAY_READ = "model-gateway:read"
    MODEL_GATEWAY_INVOKE = "model-gateway:invoke"
    MCP_READ = "mcp:read"
    MCP_EXECUTE = "mcp:execute"
    AUDIT_READ = "audit:read"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.OWNER: frozenset(Permission),
    Role.ADMIN: frozenset(Permission),
    Role.OPERATOR: frozenset(
        {
            Permission.TENANT_READ,
            Permission.MEMBER_READ,
            Permission.REVIEW_READ,
            Permission.POLICY_READ,
            Permission.POLICY_ENFORCE,
            Permission.MODEL_GATEWAY_READ,
            Permission.MODEL_GATEWAY_INVOKE,
            Permission.MCP_READ,
            Permission.MCP_EXECUTE,
            Permission.AUDIT_READ,
        }
    ),
    Role.REVIEWER: frozenset(
        {
            Permission.TENANT_READ,
            Permission.MEMBER_READ,
            Permission.REVIEW_READ,
            Permission.REVIEW_DECIDE,
            Permission.POLICY_READ,
            Permission.AUDIT_READ,
        }
    ),
    Role.VIEWER: frozenset(
        {
            Permission.TENANT_READ,
            Permission.MEMBER_READ,
            Permission.REVIEW_READ,
            Permission.POLICY_READ,
            Permission.MODEL_GATEWAY_READ,
            Permission.MCP_READ,
            Permission.AUDIT_READ,
        }
    ),
}


def role_allows(
    role: Role | str,
    permission: Permission | str,
) -> bool:
    normalized_role = Role(role)
    normalized_permission = Permission(permission)
    return normalized_permission in ROLE_PERMISSIONS[normalized_role]


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    allowed: bool
    role: Role
    permission: Permission
    reason: str


def authorize(
    role: Role | str,
    permission: Permission | str,
) -> AuthorizationDecision:
    normalized_role = Role(role)
    normalized_permission = Permission(permission)
    allowed = role_allows(
        normalized_role,
        normalized_permission,
    )
    return AuthorizationDecision(
        allowed=allowed,
        role=normalized_role,
        permission=normalized_permission,
        reason=(
            "role grants permission"
            if allowed
            else "role does not grant permission"
        ),
    )
