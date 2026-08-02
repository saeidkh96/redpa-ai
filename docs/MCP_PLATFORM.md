# MCP Platform

## Purpose

The RedPA MCP platform allows the planner and tool runtime to discover and execute tools from independently deployed MCP servers.

## Components

### Configuration Loader

Loads MCP server definitions from:

```text
backend/config/mcp_servers.json
```

### Registry

Tracks configured servers and their enabled state.

### Client

Connects to MCP servers using supported transports.

### Manager

Coordinates:

- health checks;
- tool discovery;
- cache refresh;
- execution;
- error isolation.

### Catalog

Combines internal tools and MCP tools into one normalized representation.

### Qualified Names

```text
internal:<tool>
mcp:<server>:<tool>
```

### Dynamic Selection

The dynamic selector:

1. loads the live catalog;
2. filters MCP tools;
3. ranks candidates;
4. supplies a bounded shortlist to the LLM;
5. validates the selected qualified name;
6. validates required and unknown arguments;
7. executes through the unified runtime.

## Server Inventory

### redpa-filesystem

Read-only project files.

### redpa-github

Read-only public GitHub repository data.

### redpa-postgres

Strictly read-only PostgreSQL metadata and queries.

### redpa-docker

Read-only Docker Engine inspection.

## Security

Every MCP server exposes a deliberately small capability surface. RedPA does not expose a generic proxy to filesystems, SQL, GitHub, or Docker.
