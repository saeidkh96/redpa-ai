# RedPA AI

> **Production-oriented Agentic AI Platform with LangGraph, MCP, A2A, RAG, Human Review, and Multi-Agent Workflows**

RedPA AI is a modular backend platform for building secure, observable, tool-using, and human-supervised AI systems.

It combines **FastAPI**, **LangGraph**, **PostgreSQL**, **Qdrant**, **Ollama**, the **Model Context Protocol (MCP)**, the **Google Agent-to-Agent (A2A) Protocol**, **Prometheus**, **Grafana**, and **Docker Compose** in one extensible architecture.

RedPA AI is not a single-purpose chatbot. It is an agent platform that supports planning, deterministic routing, retrieval, research, internal and external tools, remote agent delegation, workflow interruption, human approval, persistence, monitoring, and multi-agent coordination.

<p align="center">
  <strong>FastAPI · LangGraph · MCP · A2A · PostgreSQL · Qdrant · Ollama · Docker · Prometheus · Grafana</strong>
</p>

---

## Project Status

RedPA AI currently includes:

- JWT authentication and user management
- persistent conversations and messages
- LangGraph-based orchestration
- planner-driven routing
- conversational AI through Ollama
- retrieval-augmented generation with Qdrant
- web research with ranked evidence
- internal tool runtime
- dynamic MCP tool discovery and execution
- human review with approve, reject, and resume
- read-only Filesystem, GitHub, PostgreSQL, and Docker MCP servers
- internal Agent Registry
- typed Agent Cards
- Agent capability discovery
- official A2A Protocol server
- public Agent Card discovery
- Remote Agent Registry
- remote Agent Card resolution
- remote task delegation
- automatic capability-based Agent Selection
- Chat integration through the `a2a` route
- Multi-Agent workflow execution
- parallel subtask scheduling
- result aggregation
- human approval gate for sensitive distributed workflows
- A2A and Multi-Agent Prometheus metrics
- Prometheus metrics and Grafana dashboards
- Docker Compose deployment
- GitHub Actions CI
- unit and integration tests for routing, security, MCP, A2A, tools, and workflows

**Phase 5, covering A2A and Multi-Agent orchestration, is complete.**

---

## Why RedPA AI?

Many LLM applications stop at prompt-response interaction.

RedPA AI focuses on the infrastructure required for dependable agentic systems:

- deterministic routing around LLM decisions
- explicit workflow state
- typed request and response boundaries
- structured tool contracts
- read-only infrastructure integrations
- human approval before sensitive actions
- remote agent discovery and delegation
- observable execution
- persistent application state
- modular services
- bounded timeouts
- isolated failure handling
- testable components

The architecture is designed so that tools, models, retrieval backends, remote agents, and workflow nodes can be replaced independently.

---

## High-Level Architecture

```mermaid
flowchart TD
    U[User or API Client] --> API[FastAPI API Layer]
    API --> AUTH[JWT Authentication]
    AUTH --> ORCH[LangGraph Orchestrator]

    ORCH --> PLAN[Planner]

    PLAN --> CHAT[Chat Workflow]
    PLAN --> RAG[RAG Workflow]
    PLAN --> RESEARCH[Research Workflow]
    PLAN --> TOOL[Unified Tool Runtime]
    PLAN --> REVIEW[Human Review]
    PLAN --> A2A[A2A Runtime]

    TOOL --> INTERNAL[Internal Tools]
    TOOL --> MCP[MCP Runtime]

    MCP --> FS[Filesystem MCP]
    MCP --> GH[GitHub MCP]
    MCP --> PG[PostgreSQL MCP]
    MCP --> DK[Docker MCP]

    A2A --> RREG[Remote Agent Registry]
    RREG --> COORD[RedPA Coordinator Agent]
    COORD --> DISC[Capability Discovery]
    COORD --> MULTI[Multi-Agent Workflow]
    MULTI --> APPROVAL[Approval Gate]
    MULTI --> AGG[Result Aggregation]

    RAG --> QD[Qdrant]
    CHAT --> OL[Ollama]
    RESEARCH --> WEB[Web Search]

    ORCH --> DB[(PostgreSQL)]
    ORCH --> METRICS[Prometheus]
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
- persistent Human Review records
- async SQLAlchemy
- Alembic migrations
- PostgreSQL storage

### LangGraph Orchestration

LangGraph coordinates:

- planner execution
- route selection
- Chat generation
- RAG retrieval
- Research
- Tool execution
- A2A delegation
- Human Review interruption
- workflow resume after approval
- final response assembly

### Planner

The planner combines structured LLM planning with deterministic rules.

Supported routes:

```text
chat
rag
research
a2a
tool
sql
human_review
```

The planner applies deterministic intent detection before dynamic MCP selection for high-level A2A discovery requests.

For example:

```text
Which agent can inspect Docker containers?
```

routes to:

```text
a2a
```

while:

```text
Inspect Docker container redpa-postgres
```

routes to:

```text
tool
```

### Retrieval-Augmented Generation

The RAG pipeline supports:

- document ingestion
- text extraction
- chunking
- embedding generation
- Qdrant storage
- semantic retrieval
- source-grounded response generation

### Research Workflow

The Research workflow supports:

- public web search
- evidence collection
- evidence normalization
- duplicate removal
- ranking
- bounded context construction
- source-aware synthesis
- research metadata
- isolated search and generation failures

### Human Review

Sensitive workflows can pause for approval.

```text
Request
  → Planner
  → Approval required
  → Human Review created
  → Approve or reject
  → Resume workflow
  → Execute or terminate safely
```

---

## Agent-to-Agent Platform

RedPA AI implements the Google Agent-to-Agent Protocol using the official Python SDK.

### Current A2A Capabilities

- internal Agent Registry
- typed Agent Cards
- Agent capability discovery
- public A2A Coordinator service
- JSON-RPC task execution
- Remote Agent Registry
- remote Agent Card resolution
- remote task delegation
- automatic Agent Selection
- Chat-level A2A routing
- task and context metadata
- artifact extraction
- Multi-Agent execution
- parallel subtask scheduling
- result aggregation
- human approval gate
- A2A metrics

### Built-in Agents

| Agent | Capability | Routes |
|---|---|---|
| Planner Agent | Route selection | Chat, Research, RAG, Tool, Human Review, A2A |
| Research Agent | Web research | Research |
| RAG Agent | Document retrieval | RAG |
| Tool Agent | Internal and MCP tool execution | Tool |
| Human Review Agent | Approval coordination | Human Review |

### A2A Service

```text
http://localhost:8050/health
http://localhost:8050/.well-known/agent-card.json
```

JSON-RPC endpoint:

```text
http://localhost:8050/
```

### A2A Flow

```text
User Request
  → Planner
  → A2A Route
  → Remote Agent Registry
  → Agent Card Discovery
  → Capability Ranking
  → SendMessageRequest
  → Remote Task Lifecycle
  → Artifact Extraction
  → Persisted Chat Response
```

### Automatic Agent Selection

Remote Agent selection ranks:

- Agent name
- Agent description
- Skill ID
- Skill name
- Skill description
- tags
- examples

Selection metadata may include:

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

### Multi-Agent Workflow

The Multi-Agent service supports:

- explicit subtasks
- automatic subtask generation
- bounded parallelism
- workflow timeouts
- per-subtask Agent Selection
- partial failure reporting
- result aggregation

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

### Multi-Agent Approval Gate

Sensitive distributed workflows stop before remote delegation.

Current high-risk categories include:

- sending email
- deleting or removing data
- restarting or stopping infrastructure
- modifying persistent data
- refunds
- production deployment

Example:

```json
{
  "request": "Send an email to the project manager",
  "subtasks": [],
  "max_parallelism": 2,
  "timeout_seconds": 90,
  "approval_granted": false
}
```

Expected response:

```text
success: false
approval_required: true
results: []
```

No Remote Agent is contacted before approval.

---

## MCP Platform

RedPA includes a unified MCP runtime with:

- server configuration
- transport validation
- health checks
- tool discovery
- qualified tool names
- input schema discovery
- allowlists
- approval policies
- cache management
- unified internal and MCP catalog
- dynamic planner selection
- structured execution metadata

Qualified names use:

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

Security controls:

- strict sandbox boundaries
- path normalization
- parent traversal rejection
- blocked credential files
- binary file rejection
- read-only operation

### GitHub MCP

A read-only server for public GitHub data.

| Tool | Purpose |
|---|---|
| `repository` | Repository metadata |
| `branches` | Branch listing |
| `commits` | Recent commits |
| `issues` | Repository issues |
| `pull_requests` | Pull requests |

### PostgreSQL MCP

A strictly read-only PostgreSQL server.

| Tool | Purpose |
|---|---|
| `list_schemas` | List visible schemas |
| `list_tables` | List tables and views |
| `describe_table` | Inspect columns, constraints, and indexes |
| `query` | Run one validated read-only query |
| `explain` | Return a JSON execution plan |

Allowed SQL entry points:

```text
SELECT
WITH
VALUES
```

Rejected operations include:

- INSERT
- UPDATE
- DELETE
- MERGE
- COPY
- DDL
- administrative operations
- multiple statements
- SQL comments
- row locks
- unsafe PostgreSQL functions

### Docker MCP

A read-only Docker Engine integration.

| Tool | Purpose |
|---|---|
| `list_containers` | List containers |
| `inspect_container` | Return safe container metadata |
| `container_logs` | Read recent logs |
| `list_images` | List images |
| `system_info` | Return Docker Engine information |

Not exposed:

- start
- stop
- restart
- kill
- remove
- create
- exec
- image mutation
- volume mutation
- network mutation

---

## Internal Tools

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

### Chat

```text
Explain how LangGraph state transitions work.
```

### RAG

```text
Search inside my uploaded document for the deployment requirements.
```

### Research

```text
Research the latest developments in agentic AI.
Search the web and summarize recent LangGraph updates.
```

### A2A

```text
Ask the remote coordinator to show available agents and health.
Which agent can inspect Docker containers?
Find an agent for web research and evidence.
Show available agents.
```

### Filesystem MCP

```text
Show files inside backend/app/mcp
Read backend/app/main.py
Search for MCPManager in backend/app
Show file info for README.md
```

### GitHub MCP

```text
Show repository langchain-ai/langgraph
Show latest 5 commits of saeidkh96/redpa-ai
List open issues of langchain-ai/langgraph
List branches of openai/openai-python
```

### PostgreSQL MCP

```text
List database schemas
Show database tables
Describe table users
Run query SELECT COUNT(*) AS user_count FROM users
Explain SELECT * FROM messages
```

### Docker MCP

```text
Show Docker containers
List running Docker containers
Show last 50 logs for redpa-backend
Inspect Docker container redpa-postgres
List Docker images
Show Docker system info
```

---

## API Overview

Base prefix:

```text
/api/v1
```

Main groups:

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
- Remote Agents
- Multi-Agent Workflows
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

## MCP API

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

## A2A API

### Internal Agent Registry

```text
GET /api/v1/agents
GET /api/v1/agents/health
GET /api/v1/agents/discover
GET /api/v1/agents/{agent_id}
```

### Remote Agents

```text
POST   /api/v1/agents/remotes
GET    /api/v1/agents/remotes
GET    /api/v1/agents/remotes/{name}/card
POST   /api/v1/agents/remotes/{name}/delegate
DELETE /api/v1/agents/remotes/{name}
```

### Multi-Agent Workflow

```text
POST /api/v1/agents/multi/delegate
```

### A2A Protocol Service

```text
GET  http://localhost:8050/health
GET  http://localhost:8050/.well-known/agent-card.json
POST http://localhost:8050/
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

- Google Agent-to-Agent Protocol 1.0
- JSON-RPC
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
│   │   ├── a2a/
│   │   ├── a2a_multi/
│   │   ├── a2a_protocol/
│   │   ├── a2a_remote/
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
├── scripts/
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
- Ollama

### Clone

```bash
git clone https://github.com/saeidkh96/redpa-ai.git
cd redpa-ai
```

### Environment

Create a `.env` file.

```env
APP_NAME=RedPA AI
APP_VERSION=0.5.0
ENVIRONMENT=development
DEBUG=true

DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/redpa_ai
QDRANT_URL=http://qdrant:6333
OLLAMA_BASE_URL=http://host.docker.internal:11434

GITHUB_TOKEN=

A2A_HOST=0.0.0.0
A2A_PORT=8050
A2A_PUBLIC_URL=http://a2a-coordinator:8050

A2A_REMOTE_DEFAULT_ENABLED=true
A2A_REMOTE_DEFAULT_NAME=redpa-coordinator
A2A_REMOTE_DEFAULT_URL=http://a2a-coordinator:8050
A2A_REMOTE_DEFAULT_TIMEOUT_SECONDS=30
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
docker compose logs --tail=150 a2a-coordinator
docker compose logs --tail=150 filesystem-mcp
docker compose logs --tail=150 github-mcp
docker compose logs --tail=150 postgres-mcp
docker compose logs --tail=150 docker-mcp
```

---

## Service Endpoints

| Service | URL |
|---|---|
| FastAPI Docs | `http://localhost:8000/docs` |
| FastAPI OpenAPI | `http://localhost:8000/openapi.json` |
| A2A Health | `http://localhost:8050/health` |
| A2A Agent Card | `http://localhost:8050/.well-known/agent-card.json` |
| Prometheus | `http://localhost:9090` |
| Grafana | `http://localhost:3000` |
| Qdrant | `http://localhost:6333` |

---

## Testing

Run the full suite:

```bash
python -m pytest tests -v
```

Compile backend modules:

```bash
python -m compileall backend/app
```

Validate Docker Compose:

```bash
docker compose config
```

The suite covers:

- planner routing
- deterministic route priority
- MCP naming
- MCP Registry behavior
- MCP discovery
- MCP v2 compatibility
- private network policy
- Filesystem sandboxing
- GitHub parsing and formatting
- PostgreSQL SQL validation
- Docker argument validation
- dynamic MCP selection
- unified tool behavior
- Research ranking
- A2A Agent Cards
- Remote Agent Registry
- Remote delegation
- automatic Agent Selection
- Multi-Agent subtask generation
- approval policy

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

- HTTP request count
- HTTP latency
- response status
- internal tool execution
- MCP tool execution
- A2A requests
- Multi-Agent subtasks
- Multi-Agent workflow duration
- per-Agent subtask duration
- approval-required decisions

A2A metrics:

```text
redpa_a2a_multi_requests_total
redpa_a2a_multi_subtasks_total
redpa_a2a_multi_duration_seconds
redpa_a2a_multi_subtask_duration_seconds
redpa_a2a_approval_required_total
```

---

## Security Model

RedPA applies security at several layers.

### Authentication

- JWT access control
- current-user boundaries

### Planner

- deterministic safety rules
- explicit route selection
- A2A intent priority before MCP execution

### Human Review

- approval gates
- persisted decisions
- resumable execution

### Tool Runtime

- qualified tool names
- allowlists
- input schemas
- permission checks

### Filesystem MCP

- sandboxing
- traversal prevention
- blocked files

### PostgreSQL MCP

- read-only transactions
- SQL validation
- row and timeout limits

### Docker MCP

- fixed GET-only operations
- no mutation tools
- safe identifier validation

### A2A

- explicit Remote Agent registration
- URL validation
- Agent Card resolution
- bounded timeouts
- approval before sensitive distributed execution
- task and context metadata

### Infrastructure

- isolated Docker services
- health checks
- observable execution

See [SECURITY.md](SECURITY.md).

---

## Current Limitations

The current A2A Coordinator performs capability discovery and coordination.

Independent specialist Remote Agent services that directly execute Research, Docker, SQL, Filesystem, or GitHub tasks are not yet implemented.

The current Multi-Agent approval gate is request-based and is not yet persisted through the existing Human Review database workflow.

The Remote Agent Registry is currently bootstrapped in memory and should be persisted in a later phase.

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
- [x] Human Review
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
- [x] Dynamic MCP selection
- [x] Agent Registry
- [x] Agent Cards
- [x] Agent Discovery
- [x] Google A2A Protocol
- [x] A2A Coordinator
- [x] Remote Agent Registry
- [x] Remote task delegation
- [x] automatic Agent Selection
- [x] Chat-level A2A routing
- [x] Multi-Agent workflow
- [x] parallel subtask execution
- [x] result aggregation
- [x] A2A metrics
- [x] human approval gate

### In Progress

- [ ] independent specialist Remote Agents
  - [ ] Research Agent
  - [ ] SQL Agent
  - [ ] Docker Agent
  - [ ] Filesystem Agent
  - [ ] GitHub Agent

### Planned

- [ ] persisted Remote Agent Registry
- [ ] shared Agent context
- [ ] streaming A2A responses
- [ ] durable long-running workflows
- [ ] background retries and recovery
- [ ] Agent memory
- [ ] distributed tracing
- [ ] cloud deployment
- [ ] Kubernetes
- [ ] enterprise observability

Detailed planning is available in [docs/ROADMAP.md](docs/ROADMAP.md).

---

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [A2A Platform](docs/A2A_PLATFORM.md)
- [MCP Platform](docs/MCP_PLATFORM.md)
- [API Reference](docs/API_REFERENCE.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Human Review](docs/HUMAN_REVIEW.md)
- [Monitoring](docs/MONITORING.md)
- [Research Pipeline](docs/RESEARCH_PIPELINE.md)
- [Tool Runtime](docs/TOOL_RUNTIME.md)
- [Testing](docs/TESTING.md)
- [Project Structure](docs/PROJECT_STRUCTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Security](SECURITY.md)
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
