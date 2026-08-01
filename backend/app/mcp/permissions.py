from __future__ import annotations

from dataclasses import dataclass

from app.mcp.schemas import (
    MCPServerConfig,
    MCPToolInfo,
)


class MCPApprovalRequiredError(Exception):
    """Raised when an MCP tool call requires explicit approval."""


class MCPToolNotAllowedError(Exception):
    """Raised when a tool is outside the configured allowlist."""


@dataclass(frozen=True, slots=True)
class MCPPermissionDecision:
    allowed: bool
    requires_approval: bool
    reason: str


class MCPPermissionService:
    """Deterministic permission policy for MCP tool execution."""

    @staticmethod
    def evaluate(
        *,
        server: MCPServerConfig,
        tool: MCPToolInfo,
        approval_granted: bool,
    ) -> MCPPermissionDecision:
        if (
            server.allowed_tools is not None
            and tool.name not in server.allowed_tools
        ):
            return MCPPermissionDecision(
                allowed=False,
                requires_approval=False,
                reason=(
                    f"Tool '{tool.name}' is outside the configured "
                    f"allowlist for server '{server.name}'."
                ),
            )

        requires_approval = (
            server.requires_approval
            or tool.requires_approval
        )

        if requires_approval and not approval_granted:
            return MCPPermissionDecision(
                allowed=False,
                requires_approval=True,
                reason=(
                    f"MCP tool '{server.name}:{tool.name}' requires "
                    "explicit approval before execution."
                ),
            )

        return MCPPermissionDecision(
            allowed=True,
            requires_approval=requires_approval,
            reason="MCP tool execution is permitted.",
        )

    @classmethod
    def enforce(
        cls,
        *,
        server: MCPServerConfig,
        tool: MCPToolInfo,
        approval_granted: bool,
    ) -> None:
        decision = cls.evaluate(
            server=server,
            tool=tool,
            approval_granted=approval_granted,
        )

        if decision.allowed:
            return

        if decision.requires_approval:
            raise MCPApprovalRequiredError(
                decision.reason,
            )

        raise MCPToolNotAllowedError(
            decision.reason,
        )
