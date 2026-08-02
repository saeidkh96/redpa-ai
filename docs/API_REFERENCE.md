# API Reference

Base prefix:

```text
/api/v1
```

## Authentication

Authentication uses OAuth2 password flow and JWT access tokens.

## Main Groups

### Health

Application and database health.

### Authentication

Login and token management.

### Users

Current-user operations.

### Conversations

Create and list conversations.

### Messages

List messages in a conversation.

### Chat

Execute the LangGraph workflow and persist the result.

### Documents

Document ingestion and RAG-related operations.

### Human Reviews

List, inspect, approve, reject, and resume reviews.

### Tools

List and execute internal tools.

### MCP

```text
GET  /mcp/servers
POST /mcp/servers/reload
GET  /mcp/health
GET  /mcp/tools
GET  /mcp/tools/{qualified_name}
POST /mcp/tools/execute
GET  /mcp/servers/{server_name}/tools
POST /mcp/servers/{server_name}/tools/{tool_name}/call
```

## Interactive Documentation

```text
/docs
/redoc
/openapi.json
```

The OpenAPI specification is the authoritative source for current request and response schemas.
