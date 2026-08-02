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

## Safety

The runtime validates:

- tool existence;
- qualified names;
- input arguments;
- required approval;
- server allowlists;
- MCP connection state.
