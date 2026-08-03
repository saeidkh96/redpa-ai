# Project Structure

```text
redpa-ai/
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── a2a/
│   │   │   ├── builtin_agents.py
│   │   │   ├── registry.py
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   ├── a2a_multi/
│   │   │   ├── metrics.py
│   │   │   ├── policy.py
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   ├── a2a_protocol/
│   │   │   ├── card.py
│   │   │   ├── coordinator.py
│   │   │   ├── executor.py
│   │   │   └── server.py
│   │   ├── a2a_remote/
│   │   │   ├── bootstrap.py
│   │   │   ├── client.py
│   │   │   ├── registry.py
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   ├── agents/
│   │   │   ├── nodes/
│   │   │   ├── graph.py
│   │   │   ├── router.py
│   │   │   └── state.py
│   │   ├── api/v1/
│   │   ├── clients/
│   │   ├── core/
│   │   ├── database/
│   │   ├── exceptions/
│   │   ├── formatters/
│   │   ├── mcp/
│   │   ├── mcp_servers/
│   │   ├── middleware/
│   │   ├── models/
│   │   ├── monitoring/
│   │   ├── prompts/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── tools/
│   │   └── utils/
│   ├── config/
│   └── storage/
├── docs/
├── monitoring/
│   ├── grafana/
│   └── prometheus/
├── scripts/
├── tests/
├── docker-compose.yml
├── Dockerfile
├── pytest.ini
├── requirements.txt
└── README.md
```

## Major Packages

### `app/a2a`

Internal Agent Registry and capability models.

### `app/a2a_protocol`

Public A2A Coordinator server and Agent Card.

### `app/a2a_remote`

Remote Agent registration, card resolution, delegation, and bootstrap.

### `app/a2a_multi`

Parallel Multi-Agent execution, aggregation, metrics, and approval policy.

### `app/mcp`

MCP client, registry, manager, permissions, schemas, and catalog.

### `app/mcp_servers`

Independently deployed read-only MCP servers.

### `app/agents`

LangGraph workflow, planner routing, Agent state, and workflow nodes.

### `app/services`

Business logic for chat, RAG, research, Human Review, tools, MCP, and A2A.

## Documentation

```text
docs/ARCHITECTURE.md
docs/A2A_PLATFORM.md
docs/API_REFERENCE.md
docs/DEPLOYMENT.md
docs/HUMAN_REVIEW.md
docs/MCP_PLATFORM.md
docs/MONITORING.md
docs/PROJECT_STRUCTURE.md
docs/RESEARCH_PIPELINE.md
docs/ROADMAP.md
docs/TESTING.md
docs/TOOL_RUNTIME.md
```
