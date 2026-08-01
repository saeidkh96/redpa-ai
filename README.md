# RedPA AI

> A production-oriented Agentic AI Platform for secure, observable, tool-using, and human-supervised AI workflows.

**FastAPI · LangGraph · PostgreSQL · Qdrant · Ollama · Docker · Prometheus · Grafana**

## Overview

RedPA AI is an extensible backend platform for building agentic applications. It supports:

- structured planning and deterministic routing;
- conversational AI through Ollama;
- retrieval-augmented generation over uploaded documents;
- safe internal and external tools;
- human review and workflow resume;
- persistent users, conversations, messages, and reviews;
- Prometheus metrics and Grafana dashboards;
- Docker-based local deployment.

RedPA is designed as a reusable agent platform rather than a single-purpose chatbot.

## Current Capabilities

- JWT authentication
- User management
- Conversations and messages
- LangGraph workflow orchestration
- LLM planner with deterministic fallback
- Chat workflow
- RAG document pipeline
- Human review queue
- Approve, reject, and resume
- Tool registry
- Tool discovery API
- Safe calculator
- DateTime tool
- Weather tool
- Currency tool
- GitHub repository tool
- Hacker News tool
- Brave web-search tool
- External HTTP client
- Retry and timeout handling
- Tool response formatters
- HTTP and tool metrics
- Prometheus
- Grafana
- Docker Compose
- GitHub Actions CI

## Why RedPA Is More Than a Chatbot

```text
User Request
    ↓
Authentication and Conversation Context
    ↓
Planner and Deterministic Safety Rules
    ↓
┌──────────────┬──────────────┬───────────────┬─────────────────┐
│ Chat         │ RAG          │ Tool Runtime  │ Human Review    │
│ Ollama       │ Qdrant       │ Registry      │ Pause / Resume  │
└──────────────┴──────────────┴───────────────┴─────────────────┘
    ↓
Persisted Response, Metadata, Logs, and Metrics
```

## Built-in Tools

| Tool | Purpose |
|---|---|
| Calculator | Safe arithmetic without `eval` |
| DateTime | Time-zone-aware current date and time |
| Weather | Current weather through Open-Meteo |
| Currency | Currency conversion through Frankfurter |
| GitHub | Public repository metadata |
| News | Latest Hacker News stories |
| Web Search | Brave Search integration |

## Tool Request Examples

```text
Calculate 25 * 18
What time is it in Berlin?
What is the weather in Munich?
Convert 100 USD to EUR
Show GitHub repository saeidkh96/redpa-ai
Show the latest Hacker News stories
Search the web for LangGraph durable execution
```

## Technology Stack

### Backend

- Python 3.13
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
- Retrieval-Augmented Generation

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
│   │   ├── formatters/
│   │   ├── middleware/
│   │   ├── models/
│   │   ├── monitoring/
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

- Git
- Docker Desktop
- Ollama

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

### Configure Environment

```bash
cp .env.example .env
```

Set at least:

```env
JWT_SECRET_KEY=replace-with-a-long-random-secret
BRAVE_SEARCH_API_KEY=
GITHUB_TOKEN=
```

### Start the Stack

```bash
docker compose up -d --build
```

### Apply Migrations

```bash
docker compose exec backend alembic -c alembic.ini upgrade head
```

## Services

| Service | URL |
|---|---|
| Swagger UI | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |
| OpenAPI | `http://localhost:8000/openapi.json` |
| Prometheus | `http://localhost:9090` |
| Grafana | `http://localhost:3000` |
| Qdrant | `http://localhost:6333` |

## Documentation

- [Architecture](docs/architecture.md)
- [API](docs/api.md)
- [Agent Workflows](docs/workflows.md)
- [RAG](docs/rag.md)
- [Tool System](docs/tools.md)
- [Human Review](docs/human-review.md)
- [Monitoring](docs/monitoring.md)
- [Deployment](docs/deployment.md)
- [Development](docs/development.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Roadmap](docs/roadmap.md)

## Roadmap

### Completed

- [x] FastAPI backend
- [x] PostgreSQL persistence
- [x] JWT authentication
- [x] LangGraph orchestration
- [x] Ollama integration
- [x] RAG
- [x] Human review
- [x] Workflow resume
- [x] Tool registry
- [x] Tool discovery API
- [x] Internal tools
- [x] External tools
- [x] Tool response formatters
- [x] Prometheus and Grafana
- [x] Docker Compose

### Planned

- [ ] Research agent
- [ ] Read-only SQL agent
- [ ] MCP client
- [ ] MCP server
- [ ] Agent memory
- [ ] A2A workflows
- [ ] Web frontend
- [ ] Production hardening

## Security

RedPA currently includes:

- JWT authentication;
- user-scoped resources;
- safe calculator parsing;
- deterministic approval gates;
- structured tools;
- blocked private-network HTTP targets;
- environment-based secrets;
- no arbitrary shell-execution tool.

See [SECURITY.md](SECURITY.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Author

**Saeid Khalilian**  
AI & Python Developer  
Master's student in Computer Science at the University of Passau

GitHub: https://github.com/saeidkh96

## License

MIT License
