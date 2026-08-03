# MCP Platform

## Purpose

The RedPA MCP platform allows the planner and unified tool runtime to discover and execute capabilities from independently deployed MCP servers.

MCP is used for tool access. A2A is used for Agent discovery, delegation, and distributed workflows. The planner decides which integration model is appropriate for each request.

## Components

### Configuration Loader

Loads MCP server definitions from:

```text
backend/config/mcp_servers.json
```

### Registry

Tracks configured servers and enabled state.

### Client

Connects to MCP servers through supported transports.

### Manager

Coordinates:

- health checks;
- tool discovery;
- cache refresh;
- execution;
- server-level error isolation.

### Catalog

Combines internal and MCP tools into one normalized representation.

### Qualified Names

```text
internal:<tool>
mcp:<server>:<tool>
```

Examples:

```text
internal:calculator
mcp:redpa-filesystem:read_file
mcp:redpa-github:repository
mcp:redpa-postgres:query
mcp:redpa-docker:list_containers
```

## Dynamic Selection

The selector:

1. loads the live catalog;
2. filters MCP tools;
3. ranks candidates;
4. supplies a bounded shortlist to the planner;
5. validates the selected qualified name;
6. validates required and unknown arguments;
7. executes through the unified runtime.

## Planner Priority

High-level A2A discovery intent is evaluated before MCP tool selection.

Example:

```text
Which agent can inspect Docker containers?
```

This request uses the `a2a` route because the user is asking which Agent owns the capability.

By contrast:

```text
Inspect Docker container redpa-postgres
```

uses the Docker MCP server because the user is requesting direct tool execution.

## Server Inventory

### redpa-filesystem

Read-only access to allowed project files.

### redpa-github

Read-only public GitHub repository data.

### redpa-postgres

Strictly read-only PostgreSQL metadata and query execution.

### redpa-docker

Read-only Docker Engine inspection.

## MCP and A2A Relationship

```text
User Request
  → Planner
  ├── Direct operation → MCP Tool Runtime
  └── Agent discovery or delegation → A2A Runtime
```

MCP exposes tools. A2A exposes Agents and task lifecycles.

## Security

Every MCP server exposes a deliberately small capability surface.

RedPA does not expose:

- a generic filesystem proxy;
- unrestricted SQL;
- a generic GitHub mutation client;
- arbitrary Docker Engine access.

Security controls include:

- allowlists;
- input schemas;
- read-only defaults;
- path sandboxing;
- SQL validation;
- GET-only Docker operations;
- timeout handling;
- structured execution metadata.
