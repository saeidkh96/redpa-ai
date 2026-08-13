# Tool Runtime

## Unified Catalog

RedPA normalizes internal tools and MCP tools.

Examples:

```text
internal:calculator
internal:web_search
mcp:redpa-filesystem:read_file
mcp:redpa-github:repository
mcp:redpa-postgres:query
mcp:redpa-docker:list_containers
```

## Execution Flow

```text
Planner
  → qualified tool
  → permission check
  → approval check
  → runtime dispatch
  → structured result
  → formatter
  → persisted response
```

## A2A Flow

A2A uses a separate execution path:

```text
Planner
  → a2a route
  → Remote Agent Registry
  → capability ranking
  → A2A client
  → SendMessageRequest
  → remote task lifecycle
  → artifact extraction
  → persisted response
```

## MCP vs A2A

Use MCP when the request is a direct operation:

```text
Show Docker containers
Read backend/app/main.py
Run SELECT COUNT(*) FROM users
```

Use A2A when the request is about Agent discovery or delegation:

```text
Which agent can inspect Docker containers?
Find an agent for web research
Ask the remote coordinator to show available agents
```

## Safety

The tool runtime validates:

- tool existence;
- qualified names;
- input arguments;
- required approval;
- server allowlists;
- MCP connection state.

The A2A runtime validates:

- Remote Agent registration;
- HTTP or HTTPS base URL;
- Agent Card resolution;
- enabled state;
- delegation timeout;
- approval policy before Multi-Agent execution.

## Execution Metadata

Tool metadata may include:

```text
tool_name
tool_source
mcp_server
execution_time_ms
```

A2A metadata may include:

```text
remote_agent
remote_base_url
selected_skill
selection_score
selection_terms
task_id
context_id
event_count
execution_time_ms
success
error
```
