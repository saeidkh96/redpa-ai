# RedPA AI

> An open-source Agentic AI Platform for building secure, observable, tool-using, and human-supervised AI applications.

**FastAPI · LangGraph · PostgreSQL · Qdrant · Ollama · Docker · Prometheus · Grafana**

## Overview

RedPA AI is a production-oriented backend platform for agentic AI systems. It can plan and route requests, answer general questions with a local LLM, retrieve knowledge from uploaded documents, execute registered tools, pause sensitive actions for human approval, resume approved workflows, persist execution metadata, and expose operational metrics.

RedPA is designed as a reusable platform rather than a single-purpose chatbot.

Typical use cases include:

- internal knowledge assistants;
- document-aware copilots;
- developer assistants;
- customer-support automation;
- enterprise workflow automation;
- tool-using agents;
- human-supervised AI systems;
- future research, SQL, MCP, memory, and multi-agent workflows.

## Why RedPA Is More Than a Chatbot

A basic chatbot usually follows:

```text
User message → LLM → Response
```

RedPA uses a controlled workflow:

```text
User Request
    ↓
Authentication and Conversation Context
    ↓
Planner and Deterministic Safety Checks
    ↓
┌───────────────┬───────────────┬────────────────┬──────────────────┐
│ Chat Workflow │ RAG Workflow  │ Tool Runtime   │ Human Review     │
│ Local LLM     │ Qdrant        │ Tool Registry  │ Pause / Resume   │
└───────────────┴───────────────┴────────────────┴──────────────────┘
    ↓
Persisted Response, Metadata, Logs, and Metrics
```

Clear requests such as calculations and current-time lookups are routed directly to deterministic tools. Sensitive actions can be blocked until a human approves them.

## Current Status

RedPA AI is under active development.

### Implemented

- JWT authentication
- User, conversation, and message persistence
- Chat API and streaming workflow support
- LangGraph orchestration
- LLM planner
- Deterministic routing and rule-based fallback
- Planner confidence, reasoning, and signals
- RAG document pipeline
- PDF, TXT, Markdown, and DOCX extraction
- Chunking and embeddings
- Qdrant vector storage and retrieval
- Tool registry and tool service
- Safe calculator tool
- DateTime tool with IANA time zones
- Human review queue
- Approve and reject decisions
- Approved-workflow resume
- PostgreSQL and Alembic migrations
- Docker Compose
- Prometheus metrics endpoint
- Grafana service
- GitHub Actions CI
- Request IDs and processing-time headers
- Improved Ollama stream handling

### Planned

- Tool-specific Prometheus metrics
- Grafana tool dashboards
- Research agent
- Read-only SQL agent
- MCP client and server
- Agent-to-agent communication
- Long-running durable workflows
- Short-term and long-term memory
- Fine-grained permissions
- Audit policies
- Web frontend

## Routes

| Route | Status | Purpose |
|---|---:|---|
| `chat` | Implemented | General explanations and conversations |
| `rag` | Implemented | Answers grounded in uploaded documents |
| `tool` | Implemented | Registered tool execution |
| `human_review` | Implemented | Human approval for sensitive actions |
| `research` | Planned | External-source research |
| `sql` | Planned | Controlled database querying |

## Tool Runtime

```text
Planner
   ↓ route=tool
Tool Node
   ↓
Tool Registry
   ↓
Tool Service
   ↓
Registered Tool
   ↓
Structured Tool Result
```

### Calculator Tool

The calculator:

- supports basic arithmetic, parentheses, modulo, floor division, and powers;
- uses Python AST parsing;
- does not use `eval`;
- rejects imports, function calls, attribute access, and arbitrary code;
- limits expression length, exponent size, and result magnitude.

Example:

```text
Calculate 25 * 18
```

Response:

```text
The result of 25 * 18 is 450.
```

A malicious request such as:

```text
Calculate __import__('os').system('dir')
```

is rejected without executing a command.

### DateTime Tool

The DateTime tool:

- returns the current date and time;
- supports IANA time zones;
- supports aliases such as Berlin, Germany, Passau, Tehran, Tokyo, London, and New York;
- returns date, time, weekday, ISO datetime, and UTC offset.

Example:

```text
What time is it in Berlin?
```

The request is routed directly to the `datetime` tool instead of asking the LLM to guess.

## RAG Pipeline

```mermaid
flowchart LR
    Upload --> Extract
    Extract --> Chunk
    Chunk --> Embed
    Embed --> Store[(Qdrant)]

    Question --> QueryEmbedding
    QueryEmbedding --> Search
    Store --> Search
    Search --> ContextBuilder
    ContextBuilder --> LLM
    LLM --> Answer
```

Supported formats:

- PDF
- TXT
- Markdown
- DOCX

The pipeline includes file validation, text extraction, chunk creation, embedding generation through Ollama, vector storage in Qdrant, similarity search, source metadata, user and conversation filtering, and grounded answer generation.

## Human-in-the-Loop

Sensitive requests can be paused before execution.

```text
User Request
    ↓
Deterministic Safety Gate
    ↓
Human Review Created
    ↓
Approve or Reject
    ↓
Resume Approved Workflow
```

The review system stores the reason, requested action, original request, action payload, reviewer, decision, feedback, timestamps, and resume metadata.

## Local AI

Current chat model:

```text
qwen2.5:7b
```

Current embedding model:

```text
nomic-embed-text:latest
```

Ollama integration supports normal chat, streaming chat, structured response formats, configurable temperature, health checks, error handling, and graceful handling when content is received without a final stream frame.

## Architecture

```mermaid
flowchart TB
    Client[Client / Swagger / Future Frontend]

    subgraph API[FastAPI API]
        Auth[Authentication]
        Chat[Chat API]
        Documents[Documents API]
        Reviews[Human Reviews API]
        Metrics[Metrics Endpoint]
    end

    subgraph Runtime[Agent Runtime]
        Planner[Planner]
        Router[Conditional Router]
        Graph[LangGraph]
        ChatNode[Chat Node]
        RAGNode[RAG Node]
        ToolNode[Tool Node]
        ReviewNode[Human Review Node]
    end

    subgraph Tools[Tool Runtime]
        Registry[Tool Registry]
        ToolService[Tool Service]
        Calculator[Calculator]
        DateTime[DateTime]
    end

    subgraph Data[Data Layer]
        PostgreSQL[(PostgreSQL)]
        Qdrant[(Qdrant)]
        Storage[(Document Storage)]
    end

    subgraph AI[AI Services]
        Ollama[Ollama]
    end

    subgraph Obs[Observability]
        Prometheus[Prometheus]
        Grafana[Grafana]
    end

    Client --> API
    Chat --> Planner
    Planner --> Router
    Router --> Graph
    Graph --> ChatNode
    Graph --> RAGNode
    Graph --> ToolNode
    Graph --> ReviewNode
    ToolNode --> ToolService
    ToolService --> Registry
    Registry --> Calculator
    Registry --> DateTime
    ChatNode --> Ollama
    RAGNode --> Qdrant
    RAGNode --> Ollama
    API --> PostgreSQL
    Metrics --> Prometheus
    Prometheus --> Grafana
```

## Technology Stack

### Backend
- Python
- FastAPI
- Pydantic
- SQLAlchemy Async
- Alembic
- LangGraph

### AI and Retrieval
- Ollama
- Qwen 2.5 7B
- Nomic Embed Text
- Qdrant
- RAG

### Infrastructure
- PostgreSQL
- Docker
- Docker Compose
- Prometheus
- Grafana
- GitHub Actions

## Project Structure

```text
redpa-ai/
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── agents/
│   │   ├── api/v1/
│   │   ├── clients/
│   │   ├── core/
│   │   ├── database/
│   │   ├── middleware/
│   │   ├── models/
│   │   ├── monitoring/
│   │   ├── prompts/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── tools/
│   │   └── main.py
│   ├── tests/
│   └── alembic.ini
├── docs/
├── monitoring/
├── .github/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── LICENSE
└── README.md
```

## Quick Start

### Prerequisites

- Docker Desktop
- Git
- Ollama

Recommended: at least 16 GB RAM and GPU acceleration when available.

### Clone

```bash
git clone https://github.com/saeidkh96/redpa-ai.git
cd redpa-ai
```

### Pull Models

```bash
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

### Environment

At minimum:

```env
JWT_SECRET_KEY=replace-with-a-long-random-secret
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/redpa_ai
QDRANT_URL=http://qdrant:6333
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen2.5:7b
```

Never commit real secrets.

### Start

```bash
docker compose up -d --build
```

### Migrations

```bash
docker compose exec backend alembic -c alembic.ini upgrade head
```

### Services

| Service | URL |
|---|---|
| Swagger | `http://localhost:8000/docs` |
| OpenAPI | `http://localhost:8000/openapi.json` |
| Prometheus | `http://localhost:9090` |
| Grafana | `http://localhost:3000` |
| Qdrant | `http://localhost:6333` |

## Development Commands

```bash
python -m compileall backend/app
docker compose up -d --build backend
docker compose logs -f backend
docker compose exec backend python -m compileall app
docker compose exec backend alembic -c alembic.ini upgrade head
```

## Example Requests

### Chat

```text
Explain what Python decorators are.
```

### Calculator

```text
Calculate 25 * 18
```

### Security Validation

```text
Calculate __import__('os').system('dir')
```

### DateTime

```text
What time is it in Berlin?
```

### RAG

```text
Search my uploaded documents for information about LangGraph.
```

### Human Review

```text
Send an email to the project manager.
```

## Security Principles

- no production secrets in source control;
- JWT authentication;
- user-scoped resources;
- deterministic approval gates;
- safe calculator parsing without `eval`;
- no arbitrary shell tool;
- structured tool registration;
- controlled workflow resume;
- file type and size validation;
- environment-based service configuration.

Before production, add HTTPS, rate limiting, strict CORS, secret management, backups, centralized logs, fine-grained authorization, dependency scanning, and container scanning.

## Testing Checklist

Before pushing major changes, verify:

- general chat;
- calculator;
- malicious calculator input;
- DateTime;
- document upload and RAG;
- human review;
- approve or reject;
- workflow resume;
- Docker health;
- database migrations.

## Documentation

- [Architecture](docs/architecture.md)
- [Workflows](docs/workflows.md)
- [Tool System](docs/tools.md)
- [Deployment and Troubleshooting](docs/operations.md)
- [Roadmap](docs/roadmap.md)

## Roadmap

### V1 — Foundation
- [x] FastAPI
- [x] PostgreSQL
- [x] JWT
- [x] Conversations and messages
- [x] LangGraph
- [x] Ollama
- [x] RAG
- [x] Docker Compose

### V2 — Planning and Tools
- [x] Structured planner
- [x] Deterministic routing
- [x] Tool registry
- [x] Safe calculator
- [x] DateTime tool
- [ ] Tool metrics
- [ ] Tool discovery endpoint

### V3 — Human Supervision
- [x] Human review persistence
- [x] Approve and reject
- [x] Workflow resume
- [ ] Review dashboard
- [ ] Approval policies
- [ ] Audit timeline

### V4 — Advanced Agents
- [ ] Research agent
- [ ] SQL agent
- [ ] Report agent
- [ ] Memory
- [ ] Long-running workflows

### V5 — Interoperability
- [ ] MCP server
- [ ] MCP client
- [ ] Agent-to-agent communication

### V6 — Production Hardening
- [ ] Fine-grained authorization
- [ ] Rate limiting
- [ ] Distributed tracing
- [ ] Centralized logs
- [ ] Load testing
- [ ] Web frontend

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Licensed under the MIT License.

## Author

**Saeid Khalilian**  
AI & Python Developer  
Master's student in Computer Science at the University of Passau

GitHub: [saeidkh96](https://github.com/saeidkh96)

## Vision

RedPA AI aims to become a reusable open-source foundation for production-oriented agentic applications with planning, retrieval, tools, human supervision, memory, interoperability, and observability.

The goal is not to build another chatbot. The goal is to build an extensible runtime for trustworthy AI workflows.
