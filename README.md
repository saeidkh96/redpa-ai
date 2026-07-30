# RedPA AI

```{=html}
<p align="center">
```
**Production-ready Agentic AI Backend built with FastAPI, LangGraph and
Ollama**

A modular backend demonstrating how modern AI systems combine LLMs,
workflow orchestration, retrieval, human approval, monitoring and
production engineering practices.

```{=html}
</p>
```

------------------------------------------------------------------------

## Highlights

-   🤖 Agentic AI workflows with **LangGraph**
-   🧠 Structured LLM planner using **JSON Schema**
-   💬 Multi-conversation chat API
-   🔎 Retrieval-Augmented Generation (RAG)
-   👤 Human-in-the-loop approval
-   ⚡ Streaming responses
-   🔐 JWT Authentication
-   🐳 Docker Compose deployment
-   📊 Prometheus + Grafana monitoring
-   🗄️ PostgreSQL + Qdrant

------------------------------------------------------------------------

## Architecture

``` text
                Client
                   │
                   ▼
              FastAPI API
                   │
             LangGraph Router
                   │
     ┌─────────────┼─────────────┐
     ▼             ▼             ▼
 Planner        Chat Agent     RAG Agent
     │             │             │
     ├────► Tool Agent           │
     ├────► SQL Agent            │
     ├────► Research Agent       │
     └────► Human Review         │
                   │
          Ollama (Qwen2.5)
                   │
     PostgreSQL • Qdrant • Metrics
                   │
     Prometheus → Grafana
```

------------------------------------------------------------------------

## Features

### AI

-   LangGraph orchestration
-   Structured planner
-   Deterministic fallback
-   Streaming generation
-   Multi-workflow routing

### Backend

-   FastAPI
-   Async SQLAlchemy
-   Alembic migrations
-   REST API
-   JWT authentication

### Infrastructure

-   Docker
-   Docker Compose
-   PostgreSQL
-   Qdrant
-   Prometheus
-   Grafana
-   GitHub Actions

------------------------------------------------------------------------

## Tech Stack

  Category     Technologies
  ------------ ------------------------------
  Backend      Python, FastAPI
  AI           LangGraph, LangChain, Ollama
  Model        Qwen2.5 7B
  Database     PostgreSQL
  Vector DB    Qdrant
  Monitoring   Prometheus, Grafana
  DevOps       Docker, GitHub Actions

------------------------------------------------------------------------

## Project Structure

``` text
redpa-ai
├── backend
│   ├── app
│   ├── alembic
│   ├── tests
│   └── Dockerfile
├── monitoring
├── docker-compose.yml
├── .env.example
└── README.md
```

------------------------------------------------------------------------

## Quick Start

``` bash
git clone https://github.com/<your-user>/redpa-ai.git
cd redpa-ai

cp .env.example .env

docker compose up -d --build
```

Swagger:

    http://localhost:8000/docs

------------------------------------------------------------------------

## Planner

The planner classifies each request into one workflow.

Supported routes:

-   chat
-   rag
-   research
-   tool
-   sql
-   human_review

Example:

``` json
{
  "route":"chat",
  "confidence":0.95,
  "planner_provider":"ollama"
}
```

If structured generation fails, a deterministic rule-based planner is
used automatically.

------------------------------------------------------------------------

## Monitoring

Metrics include:

-   Request count
-   Request latency
-   Planner latency
-   Planner fallback count
-   Route usage
-   Human review events

Visualized in Grafana.

------------------------------------------------------------------------

## Roadmap

-   External research agent
-   SQL execution agent
-   MCP integration
-   Long-term memory
-   Agent-to-agent communication
-   Frontend dashboard
-   Kubernetes deployment

------------------------------------------------------------------------

## License

MIT License

------------------------------------------------------------------------

## Author

**Saeid Khalilian**

AI & Python Developer

Master's Student -- Computer Science

University of Passau
