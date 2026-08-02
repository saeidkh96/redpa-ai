<p align="center">
  <img src="docs/assets/logo.png" width="220" alt="RedPA AI Logo">
</p>

<h1 align="center">RedPA AI</h1>

<p align="center">
Production-ready Agentic AI Platform with MCP, RAG, Human Review and Multi-Agent Workflows.
</p>

# RedPA AI

> **Production-ready Agentic AI Platform with MCP, RAG, Human Review and Multi-Agent Workflows**

RedPA AI is a production-oriented backend platform for building secure, observable, tool-using, and human-supervised AI systems. It combines **FastAPI**, **LangGraph**, **PostgreSQL**, **Qdrant**, **Ollama**, **Model Context Protocol (MCP)**, **Prometheus**, **Grafana**, and **Docker Compose** in a modular architecture designed for real agentic workflows.

RedPA is not a single-purpose chatbot. It is an extensible agent platform that supports planning, routing, retrieval, research, tool execution, workflow interruption, human approval, persistence, monitoring, and resumable execution.

<p align="center">
  <strong>FastAPI · LangGraph · MCP · PostgreSQL · Qdrant · Ollama · Docker · Prometheus · Grafana</strong>
</p>

---

## Project Status

RedPA AI currently includes:

- JWT authentication and user management
- Persistent conversations and messages
- LangGraph-based orchestration
- Planner-driven routing
- Conversational AI through Ollama
- Retrieval-augmented generation with Qdrant
- Web research with ranked evidence
- Internal tool runtime
- Dynamic MCP tool discovery and execution
- Human review with approve, reject, and resume
- Read-only Filesystem, GitHub, PostgreSQL, and Docker MCP servers
- Prometheus metrics and Grafana dashboards
- Docker Compose deployment
- GitHub Actions continuous integration
- A test suite covering routing, security, MCP compatibility, formatting, and tool behavior

The next major development phase is **Agent-to-Agent (A2A) coordination**.

---

## Why RedPA AI?

Many LLM applications stop at prompt-response interaction. RedPA AI focuses on the infrastructure required for dependable agentic systems:

- deterministic routing around LLM decisions;
- explicit state management;
- durable workflow boundaries;
- structured tool contracts;
- human approval for sensitive actions;
- read-only security policies for infrastructure tools;
- persistent application data;
- observable execution;
- modular integration of external capabilities.

The architecture is designed to make capabilities replaceable and independently testable.

---

## High-Level Architecture

```mermaid
flowchart TD
    U[User or API Client] --> API[FastAPI API Layer]
    API --> AUTH[JWT Authentication]
    AUTH --> ORCH[LangGraph Orchestrator]

    ORCH --> PLAN[Planner]
    PLAN --> CHAT[Chat Workflow]
    PLAN --> RESEARCH[Research Workflow]
    PLAN --> RAG[RAG Workflow]
    PLAN --> TOOLS[Unified Tool Runtime]
    PLAN --> REVIEW[Human Review]

    TOOLS --> INTERNAL[Internal Tools]
    TOOLS --> MCP[MCP Runtime]

    MCP --> FS[Filesystem MCP]
    MCP --> GH[GitHub MCP]
    MCP --> PG[PostgreSQL MCP]
    MCP --> DK[Docker MCP]

    RAG --> QD[Qdrant]
    CHAT --> OL[Ollama]
    RESEARCH --> WEB[Web Search]

    ORCH --> DB[(PostgreSQL)]
    ORCH --> METRICS[Prometheus Metrics]
    METRICS --> GRAFANA[Grafana]
```

---

## Core Capabilities

### Authentication and Persistence

- OAuth2 password flow
- JWT access tokens
- persistent users
- persistent conversations
- persistent user and assistant messages
- persistent human-review records
- async SQLAlchemy
- Alembic migrations
- PostgreSQL storage

### LangGraph Orchestration

RedPA uses LangGraph as its workflow runtime. The orchestrator coordinates:

- planning;
- route selection;
- chat generation;
- RAG retrieval;
- web research;
- tool execution;
- human-review interruption;
- workflow continuation after approval.

### Planner

The planner combines structured LLM planning with deterministic fallback rules. It can route requests to:

- `chat`
- `rag`
- `research`
- `tool`
- `human_review`

For MCP requests, the planner can use deterministic intent extraction or dynamic catalog-based tool selection.

### Retrieval-Augmented Generation

The RAG pipeline supports:

- document ingestion;
- text extraction;
- chunking;
- embedding generation;
- Qdrant storage;
- semantic retrieval;
- source-grounded response generation.

### Research Workflow

The research workflow supports:

- current web search;
- evidence collection;
- deduplication;
- ranking;
- source-aware synthesis;
- research metadata;
- failure isolation between search and generation.

### Human Review

Sensitive workflows can be interrupted and persisted for human approval.

Supported lifecycle:

```text
Request
  → Planner
  → Approval required
  → Human review created
  → Approve or reject
  → Resume workflow
  → Tool execution or safe termination
```

---

## MCP Platform

RedPA includes a unified MCP runtime with:

- server configuration;
- transport validation;
- health checks;
- tool discovery;
- qualified tool names;
- input-schema discovery;
- allowlists;
- approval policies;
- cache management;
- unified internal and MCP tool catalog;
- dynamic planner selection;
- structured execution metadata.

Qualified names use the following format:

```text
mcp:<server-name>:<tool-name>
```

Example:

```text
mcp:redpa-github:commits
```

### Filesystem MCP

A sandboxed, read-only filesystem server.

| Tool | Purpose |
|---|---|
| `list_files` | List visible files and directories |
| `read_file` | Read safe UTF-8 text files |
| `search_files` | Search text content |
| `file_info` | Return safe file metadata |

Security controls include:

- strict sandbox boundaries;
- path normalization;
- parent-traversal rejection;
- blocked credential files;
- binary-file rejection;
- read-only operation.

### GitHub MCP

A read-only server for public GitHub repository data.

| Tool | Purpose |
|---|---|
| `repository` | Repository metadata |
| `branches` | Branch listing |
| `commits` | Recent commits |
| `issues` | Repository issues |
| `pull_requests` | Pull requests |

Authentication through `GITHUB_TOKEN` is optional and used only to improve API limits.

### PostgreSQL MCP

A strictly read-only PostgreSQL server.

| Tool | Purpose |
|---|---|
| `list_schemas` | List user-visible schemas |
| `list_tables` | List tables and views |
| `describe_table` | Inspect columns, constraints, and indexes |
| `query` | Run one validated read-only query |
| `explain` | Return a JSON execution plan without `ANALYZE` |

The SQL security layer allows only:

- `SELECT`
- `WITH`
- `VALUES`

It rejects:

- `INSERT`
- `UPDATE`
- `DELETE`
- `MERGE`
- `COPY`
- DDL
- administrative operations
- multiple statements
- SQL comments
- row-locking queries
- unsafe PostgreSQL filesystem and administration functions

Every database operation runs inside a read-only transaction with row and timeout limits.

### Docker MCP

A read-only Docker Engine integration.

| Tool | Purpose |
|---|---|
| `list_containers` | List running or stopped containers |
| `inspect_container` | Return safe container metadata |
| `container_logs` | Read recent logs |
| `list_images` | List images |
| `system_info` | Return Docker Engine information |

RedPA does **not** expose tools for:

- start;
- stop;
- restart;
- kill;
- remove;
- create;
- exec;
- image mutation;
- volume mutation;
- network mutation.

---

## Internal Tools

The built-in tool runtime currently includes:

| Tool | Purpose |
|---|---|
| Calculator | Safe arithmetic evaluation |
| DateTime | Time-zone-aware date and time |
| Weather | Current weather using Open-Meteo |
| Currency | Currency conversion using Frankfurter |
| GitHub | Public repository metadata |
| News | Hacker News stories |
| Web Search | Public web search through DDGS |

Internal and MCP tools are exposed through a unified catalog.

---

## Example Requests

### Filesystem

```text
Show files inside backend/app/mcp
Read backend/app/main.py
Search for MCPManager in backend/app
Show file info for README.md
```

### GitHub

```text
Show repository langchain-ai/langgraph
Show latest 5 commits of saeidkh96/redpa-ai
List open issues of langchain-ai/langgraph
List branches of openai/openai-python
```

### PostgreSQL

```text
List database schemas
Show database tables
Describe table users
Run query SELECT COUNT(*) AS user_count FROM users
Explain SELECT * FROM messages
```

### Docker

```text
Show Docker containers
List running Docker containers
Show last 50 logs for redpa-backend
Inspect Docker container redpa-postgres
List Docker images
Show Docker system info
```

### Research

```text
Research LangGraph durable execution.
Search the web and summarize recent developments in agentic AI.
Research the latest developments in automotive AI.
```

---

## API Overview

The FastAPI application exposes versioned endpoints under:

```text
/api/v1
```

Main API groups include:

- Health
- Authentication
- Users
- Conversations
- Messages
- Chat
- LLM
- Documents
- Human Reviews
- Internal Tools
- MCP
- Metrics

Interactive documentation:

```text
http://localhost:8000/docs
```

OpenAPI schema:

```text
http://localhost:8000/openapi.json
```

---

## MCP API Overview

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

---

## Technology Stack

### Backend

- Python 3.13
- FastAPI
- Pydantic
- SQLAlchemy Async
- Alembic
- asyncpg
- HTTPX

### AI and Orchestration

- LangGraph
- LangChain
- Ollama
- Qwen 2.5 7B
- Nomic Embed Text
- structured prompting
- deterministic routing
- retrieval-augmented generation

### Data and Infrastructure

- PostgreSQL 17
- Qdrant
- Docker
- Docker Compose
- Prometheus
- Grafana

### Protocols and Integrations

- Model Context Protocol
- GitHub REST API
- Docker Engine API
- Open-Meteo
- Frankfurter
- Hacker News API
- DDGS

---

## Project Structure

```text
redpa-ai/
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── agents/
│   │   │   └── nodes/
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
├── tests/
├── docker-compose.yml
├── Dockerfile
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## Local Development

### Requirements

- Docker Desktop
- Docker Compose
- Python 3.13+
- Git

### Clone

```bash
git clone https://github.com/saeidkh96/redpa-ai.git
cd redpa-ai
```

### Environment

Create a `.env` file based on the project configuration.

Important values include:

```env
APP_NAME=RedPA AI
APP_VERSION=0.4.0
ENVIRONMENT=development
DEBUG=true

DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/redpa_ai
QDRANT_URL=http://qdrant:6333
OLLAMA_BASE_URL=http://host.docker.internal:11434

GITHUB_TOKEN=
```

Never commit real credentials.

### Run

```bash
docker compose up -d --build
```

### Check Services

```bash
docker compose ps
```

### Logs

```bash
docker compose logs --tail=150 backend
docker compose logs --tail=150 filesystem-mcp
docker compose logs --tail=150 github-mcp
docker compose logs --tail=150 postgres-mcp
docker compose logs --tail=150 docker-mcp
```

---

## Testing

Run the full test suite:

```bash
python -m pytest tests -v
```

Compile all backend modules:

```bash
python -m compileall backend/app
```

Validate Docker Compose:

```bash
docker compose config
```

The suite covers:

- MCP naming;
- registry behavior;
- tool discovery;
- MCP v2 compatibility;
- private-network policy;
- filesystem sandboxing;
- GitHub parsing and formatting;
- PostgreSQL SQL validation;
- Docker argument validation;
- planner intent detection;
- dynamic MCP selection;
- unified tool behavior;
- research ranking.

---

## Monitoring

### Prometheus

```text
http://localhost:9090
```

### Grafana

```text
http://localhost:3000
```

Metrics include:

- HTTP request count;
- HTTP latency;
- response status;
- internal-tool execution;
- MCP-tool execution;
- execution duration;
- workflow behavior.

---

## Security Model

RedPA applies security at several layers:

1. **Authentication**
   - JWT access control
   - current-user boundaries

2. **Planner**
   - deterministic safety rules
   - explicit route selection

3. **Human Review**
   - approval gates
   - persisted decisions
   - resumable execution

4. **Tool Runtime**
   - qualified tool names
   - allowlists
   - input schemas
   - permission checks

5. **Filesystem MCP**
   - sandboxing
   - traversal prevention
   - blocked files

6. **PostgreSQL MCP**
   - read-only transactions
   - SQL validation
   - row and timeout limits

7. **Docker MCP**
   - fixed GET-only operations
   - no mutation tools
   - safe identifier validation

8. **Infrastructure**
   - isolated Docker services
   - health checks
   - observable execution

See [SECURITY.md](SECURITY.md) for reporting guidance.

---

## Roadmap

### Completed

- [x] Core FastAPI backend
- [x] Async PostgreSQL persistence
- [x] JWT authentication
- [x] Conversations and messages
- [x] LangGraph orchestration
- [x] Chat workflow
- [x] RAG pipeline
- [x] Research workflow
- [x] Human review
- [x] Approve, reject, and resume
- [x] Internal tool runtime
- [x] Prometheus and Grafana
- [x] Docker Compose
- [x] GitHub Actions CI
- [x] MCP platform foundation
- [x] Filesystem MCP
- [x] GitHub MCP
- [x] PostgreSQL MCP
- [x] Docker MCP
- [x] Dynamic MCP tool selection

### Planned

- [ ] Agent Registry
- [ ] Agent Cards
- [ ] Agent discovery
- [ ] A2A task delegation
- [ ] Coordinator Agent
- [ ] Multi-agent workflows
- [ ] Shared agent context
- [ ] Long-running workflows
- [ ] Durable background execution
- [ ] Agent memory
- [ ] Cloud deployment

Detailed planning is available in [docs/ROADMAP.md](docs/ROADMAP.md).

---

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [MCP Platform](docs/MCP_PLATFORM.md)
- [API Reference](docs/API_REFERENCE.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Security](SECURITY.md)
- [Roadmap](docs/ROADMAP.md)
- [Contributing](CONTRIBUTING.md)

---

## Author

**Saeid Khalilian**

- GitHub: `saeidkh96`
- Email: `saeedkhalilian75@gmail.com`

---

## License

RedPA AI is licensed under the MIT License.

See [LICENSE](LICENSE).
