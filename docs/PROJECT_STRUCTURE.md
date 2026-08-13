# Project Structure

```text
redpa-ai/
â”œâ”€â”€ backend/
â”‚   â”œâ”€â”€ alembic/
â”‚   â”œâ”€â”€ app/
â”‚   â”‚   â”œâ”€â”€ a2a/
â”‚   â”‚   â”‚   â”œâ”€â”€ builtin_agents.py
â”‚   â”‚   â”‚   â”œâ”€â”€ registry.py
â”‚   â”‚   â”‚   â”œâ”€â”€ schemas.py
â”‚   â”‚   â”‚   â””â”€â”€ service.py
â”‚   â”‚   â”œâ”€â”€ a2a_multi/
â”‚   â”‚   â”‚   â”œâ”€â”€ metrics.py
â”‚   â”‚   â”‚   â”œâ”€â”€ policy.py
â”‚   â”‚   â”‚   â”œâ”€â”€ schemas.py
â”‚   â”‚   â”‚   â””â”€â”€ service.py
â”‚   â”‚   â”œâ”€â”€ a2a_protocol/
â”‚   â”‚   â”‚   â”œâ”€â”€ card.py
â”‚   â”‚   â”‚   â”œâ”€â”€ coordinator.py
â”‚   â”‚   â”‚   â”œâ”€â”€ executor.py
â”‚   â”‚   â”‚   â””â”€â”€ server.py
â”‚   â”‚   â”œâ”€â”€ a2a_remote/
â”‚   â”‚   â”‚   â”œâ”€â”€ bootstrap.py
â”‚   â”‚   â”‚   â”œâ”€â”€ client.py
â”‚   â”‚   â”‚   â”œâ”€â”€ registry.py
â”‚   â”‚   â”‚   â”œâ”€â”€ schemas.py
â”‚   â”‚   â”‚   â””â”€â”€ service.py
â”‚   â”‚   â”œâ”€â”€ agents/
â”‚   â”‚   â”‚   â”œâ”€â”€ nodes/
â”‚   â”‚   â”‚   â”œâ”€â”€ graph.py
â”‚   â”‚   â”‚   â”œâ”€â”€ router.py
â”‚   â”‚   â”‚   â””â”€â”€ state.py
â”‚   â”‚   â”œâ”€â”€ api/v1/
â”‚   â”‚   â”œâ”€â”€ clients/
â”‚   â”‚   â”œâ”€â”€ core/
â”‚   â”‚   â”œâ”€â”€ database/
â”‚   â”‚   â”œâ”€â”€ exceptions/
â”‚   â”‚   â”œâ”€â”€ formatters/
â”‚   â”‚   â”œâ”€â”€ mcp/
â”‚   â”‚   â”œâ”€â”€ mcp_servers/
â”‚   â”‚   â”œâ”€â”€ middleware/
â”‚   â”‚   â”œâ”€â”€ models/
â”‚   â”‚   â”œâ”€â”€ monitoring/
â”‚   â”‚   â”œâ”€â”€ prompts/
â”‚   â”‚   â”œâ”€â”€ repositories/
â”‚   â”‚   â”œâ”€â”€ schemas/
â”‚   â”‚   â”œâ”€â”€ services/
â”‚   â”‚   â”œâ”€â”€ tools/
â”‚   â”‚   â””â”€â”€ utils/
â”‚   â”œâ”€â”€ config/
â”‚   â””â”€â”€ storage/
â”œâ”€â”€ docs/
â”œâ”€â”€ monitoring/
â”‚   â”œâ”€â”€ grafana/
â”‚   â””â”€â”€ prometheus/
â”œâ”€â”€ scripts/
â”œâ”€â”€ tests/
â”œâ”€â”€ docker-compose.yml
â”œâ”€â”€ Dockerfile
â”œâ”€â”€ pytest.ini
â”œâ”€â”€ requirements.txt
â””â”€â”€ README.md
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
docs/monitoring.md
docs/PROJECT_STRUCTURE.md
docs/RESEARCH_PIPELINE.md
docs/ROADMAP.md
docs/TESTING.md
docs/TOOL_RUNTIME.md
```
