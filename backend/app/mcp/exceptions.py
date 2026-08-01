from __future__ import annotations


class MCPClientError(Exception):
    """Base exception for RedPA MCP client operations."""


class MCPConfigurationError(MCPClientError):
    """Raised when an MCP server configuration is invalid."""


class MCPConnectionError(MCPClientError):
    """Raised when RedPA cannot connect to an MCP server."""


class MCPRequestError(MCPClientError):
    """Raised when an MCP protocol request fails."""


class MCPToolExecutionError(MCPClientError):
    """Raised when an MCP tool reports an execution failure."""
