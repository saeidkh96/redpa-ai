# RedPA AI

<p align="center">
  <strong>A production-oriented Agentic AI Platform for building secure, observable, human-supervised AI applications.</strong>
</p>

<p align="center">
  FastAPI · LangGraph · PostgreSQL · Qdrant · Ollama · Docker · Prometheus · Grafana
</p>

---

## Overview

RedPA AI is an open-source backend platform for building agentic AI applications with:

- authenticated conversations and message persistence;
- planner-based routing between direct chat and multi-step workflows;
- retrieval-augmented generation over uploaded documents;
- resumable LangGraph workflows;
- human-in-the-loop approval and rejection;
- local LLM execution through Ollama;
- PostgreSQL persistence and Qdrant vector search;
- Prometheus metrics, Grafana dashboards, structured logging, and request tracing;
- containerized local development and CI automation.

The project is designed as a reusable platform rather than a single-purpose chatbot. Customer support, research assistants, knowledge systems, SQL agents, reporting agents, and tool-using workflows can be implemented on top of the same foundation.

## Current Status

RedPA AI is under active development.

Implemented foundation:

- JWT authentication
- User, conversation, and message persistence
- Chat and streaming APIs
- Planner and orchestration services
- LangGraph workflow execution
- Document upload and extraction
- Chunking, embeddings, and Qdrant retrieval
- Human review workflow
- Workflow resume support
- Docker Compose
- GitHub Actions CI
- Prometheus metrics
- Provisioned Grafana dashboard
- Request ID and processing-time headers

Planned platform capabilities are documented in [docs/roadmap.md](docs/roadmap.md).

## Architecture

```mermaid
flowchart TD
    Client[Client / API Consumer] --> API[FastAPI API]
    API --> Auth[JWT Authentication]
    API --> Chat[Chat Service]
    API --> Docs[Document Service]
    API --> Review[Human Review API]

    Chat --> Planner[Planner Service]
    Planner --> Orchestrator[Agent Orchestrator]
    Orchestrator --> Graph[LangGraph Workflow]

    Graph --> LLM[Ollama / Local LLM]
    Graph --> RAG[RAG Pipeline]
    Graph --> HITL[Human-in-the-Loop]

    RAG --> Extract[Document Extraction]
    Extract --> Chunk[Chunking]
    Chunk --> Embed[Embedding Service]
    Embed --> Qdrant[(Qdrant)]

    Auth --> Postgres[(PostgreSQL)]
    Chat --> Postgres
    Docs --> Postgres
    Review --> Postgres

    API --> Metrics[Prometheus Metrics]
    Metrics --> Prometheus[Prometheus]
    Prometheus --> Grafana[Grafana]
```

See [docs/architecture.md](docs/architecture.md) for a detailed description.

## Agent Workflow

```mermaid
flowchart LR
    Start([Request]) --> Planner
    Planner -->|Direct chat| Generate[Generate Response]
    Planner -->|Knowledge required| Retrieve[Retrieve Context]
    Planner -->|Multi-step task| Execute[Execute Workflow]

    Retrieve --> Generate
    Execute --> Evaluate{Human review required?}
    Generate --> Evaluate

    Evaluate -->|No| Persist[Persist Result]
    Evaluate -->|Yes| Pause[Pause Workflow]
    Pause --> Decision{Approve / Reject / Retry}
    Decision --> Resume[Resume Workflow]
    Resume --> Persist
    Persist --> End([Response])
```

## Technology Stack

| Area | Technology |
|---|---|
| API | FastAPI |
| Agent orchestration | LangGraph |
| LLM runtime | Ollama |
| Default local model | `qwen2.5:7b` |
| Relational database | PostgreSQL |
| ORM / migrations | SQLAlchemy, Alembic |
| Vector database | Qdrant |
| Authentication | JWT Bearer tokens |
| Observability | Prometheus, Grafana |
| Containers | Docker, Docker Compose |
| CI | GitHub Actions |

## Repository Layout

```text
redpa-ai/
├── .github/workflows/       # CI pipeline
├── backend/
│   ├── alembic/             # Database migrations
│   ├── app/
│   │   ├── api/             # FastAPI routes and dependencies
│   │   ├── agents/          # Agent and workflow logic
│   │   ├── core/            # Configuration and security
│   │   ├── db/              # Database session and base classes
│   │   ├── middleware/      # Logging, metrics, request tracing
│   │   ├── models/          # SQLAlchemy models
│   │   ├── monitoring/      # Application metrics
│   │   ├── prompts/         # Prompt templates
│   │   ├── repositories/    # Persistence abstractions
│   │   ├── schemas/         # Pydantic request/response models
│   │   └── services/        # Application and domain services
│   └── storage/uploads/     # Local upload storage
├── monitoring/
│   ├── prometheus/          # Prometheus configuration
│   └── grafana/             # Provisioning and dashboards
├── tests/
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

Generated virtual environments and uploaded user files should not be committed.

## Quick Start with Docker

### Prerequisites

- Docker Desktop or Docker Engine with Compose
- Ollama running on the host
- The configured local model

Pull the default model:

```bash
ollama pull qwen2.5:7b
```

Start Ollama:

```bash
ollama serve
```

Copy environment configuration:

```bash
cp .env.example .env
```

Start the platform:

```bash
docker compose up --build
```

Services:

| Service | URL |
|---|---|
| API | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/docs` |
| OpenAPI JSON | `http://localhost:8000/openapi.json` |
| Qdrant | `http://localhost:6333` |
| Prometheus | `http://localhost:9090` |
| Grafana | `http://localhost:3000` |

Default local Grafana credentials from the current Compose configuration:

```text
username: admin
password: admin
```

Change all development credentials before any non-local deployment.

## Local Development

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start PostgreSQL and Qdrant:

```bash
docker compose up -d postgres qdrant
```

Run migrations from the backend directory:

```bash
alembic upgrade head
```

Start the API:

```bash
uvicorn backend.app.main:app --reload
```

Use the actual import path defined by the repository if it differs.

## Configuration

Important settings include:

```env
APP_NAME=RedPA AI
APP_VERSION=0.1.0
ENVIRONMENT=development
DEBUG=true

API_V1_PREFIX=/api/v1
JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/redpa_ai
QDRANT_URL=http://localhost:6333

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
```

Do not commit `.env`. Use `.env.example` only for safe placeholders.

## API Usage

The authoritative endpoint list is generated by FastAPI and is available in Swagger UI after startup.

Typical flow:

1. Register or authenticate a user.
2. Obtain an access token.
3. Create a conversation.
4. Send a message or start a workflow.
5. Upload documents when retrieval is required.
6. Review pending human-review items.
7. Resume approved, rejected, or retried workflows.

Bearer authentication:

```http
Authorization: Bearer <access-token>
```

Example health check:

```bash
curl http://localhost:8000/api/v1/health
```

Endpoint names may evolve while the project is under active development. Prefer `/docs` over copied endpoint lists.

## Retrieval-Augmented Generation

The RAG subsystem separates document processing from response generation:

```mermaid
flowchart LR
    Upload --> Extract --> Chunk --> Embed --> Store[(Qdrant)]
    Query --> QueryEmbed[Query Embedding] --> Search[Similarity Search]
    Store --> Search
    Search --> Context[Context Builder]
    Context --> LLM[LLM Generation]
    LLM --> Answer
```

Main responsibilities are split across document, extraction, chunking, embedding, vector-store, retrieval, context-building, and RAG services.

## Human-in-the-Loop

Workflows can pause when a decision should not be made automatically. A reviewer can:

- approve the generated result;
- reject it;
- provide a corrected decision or response;
- request retry;
- resume the paused workflow.

This design supports accountable automation and prevents high-risk actions from being silently executed.

## Observability

RedPA AI includes:

- Prometheus-compatible metrics;
- request counts and latency tracking;
- error monitoring;
- request IDs;
- `X-Process-Time-Ms` response headers;
- Grafana provisioning;
- an API overview dashboard.

See [docs/monitoring.md](docs/monitoring.md).

## Documentation

- [Architecture](docs/architecture.md)
- [API Guide](docs/api.md)
- [Agent Workflows](docs/workflows.md)
- [RAG](docs/rag.md)
- [Human Review](docs/human-review.md)
- [Deployment](docs/deployment.md)
- [Monitoring](docs/monitoring.md)
- [Development](docs/development.md)
- [Roadmap](docs/roadmap.md)
- [Troubleshooting](docs/troubleshooting.md)

## Security Notes

The checked-in Docker Compose configuration is suitable for local development, not production. Before deployment:

- replace JWT, database, and Grafana credentials;
- use a secrets manager;
- disable debug mode;
- restrict CORS;
- remove public database and vector-store ports when unnecessary;
- terminate TLS at a trusted reverse proxy;
- pin container image versions;
- establish backups and retention policies;
- define authentication and authorization for human-review operations.

See [SECURITY.md](SECURITY.md).

## Contributing

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a pull request.

## License

This project is intended to be released under the MIT License. Add the repository's final `LICENSE` file before publishing a release.

## Author

**Saeed Khalilian**

RedPA AI is developed as a portfolio-grade, production-oriented Agentic AI engineering project.
