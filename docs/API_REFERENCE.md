# API Reference

## Base Prefix

```text
/api/v1
```

The OpenAPI schema is the authoritative source for current request and response models.

## Authentication

RedPA uses OAuth2 password flow and JWT access tokens.

## Main API Groups

- Health
- Authentication
- Users
- Conversations
- Messages
- Chat
- Documents
- Human Reviews
- Internal Tools
- MCP
- Agent Registry
- Remote A2A Agents
- Multi-Agent Workflows
- Metrics

## Health

```text
GET /health
GET /api/v1/health
```

## Authentication

```text
POST /api/v1/auth/login
POST /api/v1/auth/logout
```

## Conversations and Messages

```text
POST /api/v1/conversations
GET  /api/v1/conversations
GET  /api/v1/conversations/{conversation_id}

GET  /api/v1/conversations/{conversation_id}/messages
```

## Chat

The Chat API executes the LangGraph workflow and persists both the user and assistant messages.

The planner may select:

```text
chat
rag
research
a2a
tool
sql
human_review
```

A2A Chat requests include metadata such as:

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

## Documents and RAG

Document endpoints support ingestion and retrieval workflows backed by Qdrant.

## Human Reviews

```text
GET  /api/v1/reviews
GET  /api/v1/reviews/{review_id}
POST /api/v1/reviews/{review_id}/approve
POST /api/v1/reviews/{review_id}/reject
POST /api/v1/reviews/{review_id}/resume
```

## Internal Tools

The internal runtime lists and executes typed RedPA tools.

## MCP

```text
GET  /api/v1/mcp/servers
POST /api/v1/mcp/servers/reload
GET  /api/v1/mcp/health
GET  /api/v1/mcp/tools
GET  /api/v1/mcp/tools/{qualified_name}
POST /api/v1/mcp/tools/execute
GET  /api/v1/mcp/servers/{server_name}/tools
POST /api/v1/mcp/servers/{server_name}/tools/{tool_name}/call
```

Qualified MCP names use:

```text
mcp:<server-name>:<tool-name>
```

## Agent Registry

```text
GET /api/v1/agents
GET /api/v1/agents/health
GET /api/v1/agents/discover
GET /api/v1/agents/{agent_id}
```

Built-in Agent Cards include:

- Planner Agent
- Research Agent
- RAG Agent
- Tool Agent
- Human Review Agent

## Remote A2A Agents

### Register a Remote Agent

```text
POST /api/v1/agents/remotes
```

Example:

```json
{
  "name": "redpa-coordinator",
  "base_url": "http://a2a-coordinator:8050",
  "enabled": true,
  "timeout_seconds": 30
}
```

### List Remote Agents

```text
GET /api/v1/agents/remotes
```

### Read or Refresh an Agent Card

```text
GET /api/v1/agents/remotes/{name}/card
GET /api/v1/agents/remotes/{name}/card?refresh=true
```

### Delegate a Task

```text
POST /api/v1/agents/remotes/{name}/delegate
```

Example:

```json
{
  "message": "Show available agents and health",
  "timeout_seconds": 60
}
```

### Remove a Remote Agent

```text
DELETE /api/v1/agents/remotes/{name}
```

## Multi-Agent Workflow

```text
POST /api/v1/agents/multi/delegate
```

Example:

```json
{
  "request": "Research and infrastructure inspection",
  "subtasks": [
    {
      "id": "research",
      "instruction": "Find an agent for web research and evidence"
    },
    {
      "id": "docker",
      "instruction": "Which agent can inspect Docker containers?"
    }
  ],
  "max_parallelism": 2,
  "timeout_seconds": 90,
  "approval_granted": false
}
```

The response contains:

```text
success
approval_required
review_reason
results
aggregated_response
total_subtasks
successful_subtasks
failed_subtasks
execution_time_ms
metadata
```

## A2A Protocol Service

The standalone Coordinator service runs separately from the FastAPI backend.

```text
GET  http://localhost:8050/health
GET  http://localhost:8050/.well-known/agent-card.json
POST http://localhost:8050/
```

The root endpoint implements JSON-RPC through the official Google A2A Python SDK.

## Interactive Documentation

```text
/docs
/redoc
/openapi.json
```
