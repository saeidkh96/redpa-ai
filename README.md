![Python](https://img.shields.io/badge/Python-3.14-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-REST-green)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic-orange)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)
![License](https://img.shields.io/badge/License-MIT-black)

RedPA AI

RedPA AI is a production-style agentic AI backend built with FastAPI, LangGraph, PostgreSQL, Qdrant, Ollama, Docker, Prometheus, and Grafana.

The project demonstrates how an AI application can combine authentication, conversation management, structured planning, workflow routing, retrieval-augmented generation, human review, streaming, observability, and containerized deployment in one backend system.

Features

JWT authentication

Conversation and message management

LangGraph-based orchestration

Ollama integration

Structured planner output with JSON Schema

Deterministic planner fallback

Chat, RAG, research, tool, SQL, and human-review routing

Human-in-the-loop review workflow

Streaming language-model responses

PostgreSQL persistence

Qdrant vector storage

Request IDs and request timing

Prometheus metrics

Grafana dashboards

Docker Compose environment

GitHub Actions CI

Current Status

The following parts are currently implemented:

Authentication

Conversations and messages

Ollama chat generation

Structured planner

Chat routing

Rule-based planner fallback

RAG infrastructure

Human review

Streaming

PostgreSQL and Qdrant integration

Monitoring with Prometheus and Grafana

Docker-based local deployment

Some specialized routes, such as external research, tool execution, and SQL-agent execution, are still being expanded.

Architecture

Client
  |
  v
FastAPI API
  |
  v
LangGraph Orchestrator
  |
  +--> Planner
  |      |
  |      +--> Ollama structured output
  |      +--> Rule-based fallback
  |
  +--> Chat workflow
  +--> RAG workflow
  +--> Research workflow
  +--> Tool workflow
  +--> SQL workflow
  +--> Human review workflow
  |
  +--> PostgreSQL
  +--> Qdrant
  +--> Prometheus
  +--> Grafana

Technology Stack

Backend

Python

FastAPI

SQLAlchemy

Alembic

Pydantic

LangGraph

LangChain

AI and Retrieval

Ollama

Qwen 2.5

Qdrant

Embeddings

Retrieval-augmented generation

Infrastructure

PostgreSQL

Docker

Docker Compose

Prometheus

Grafana

GitHub Actions

Project Structure

redpa-ai/
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── agents/
│   │   ├── api/
│   │   ├── clients/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── monitoring/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── tests/
│   ├── alembic.ini
│   └── Dockerfile
├── monitoring/
├── docker-compose.yml
├── .env.example
└── README.md

Requirements

Docker Desktop

Docker Compose

Ollama

Git

For local development without Docker:

Python 3.13 or later

PostgreSQL

Qdrant

Ollama Setup

Install and start Ollama, then download the model:

ollama pull qwen2.5:7b
ollama serve

Verify the model:

ollama list

Environment Configuration

Create a .env file from the example:

cp .env.example .env

On PowerShell:

Copy-Item .env.example .env

Example configuration:

POSTGRES_DB=redpa_ai
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/redpa_ai

QDRANT_URL=http://qdrant:6333

OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen2.5:7b

JWT_SECRET_KEY=replace-this-with-a-secure-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

Do not commit the real .env file.

Run with Docker

Build and start all services:

docker compose up -d --build

Check service status:

docker compose ps

View backend logs:

docker compose logs -f backend

Stop the environment:

docker compose down

Rebuild the backend without cache:

docker compose build --no-cache backend
docker compose up -d

Services

Service

URL

FastAPI

http://localhost:8000

Swagger UI

http://localhost:8000/docs

OpenAPI

http://localhost:8000/openapi.json

Qdrant

http://localhost:6333

Prometheus

http://localhost:9090

Grafana

http://localhost:3000

Database Migrations

Run migrations inside the backend container:

docker compose exec backend alembic upgrade head

Create a new migration:

docker compose exec backend alembic revision --autogenerate -m "describe change"

API Workflow

A typical request follows this flow:

The user authenticates and receives a JWT access token.

The user creates or selects a conversation.

A message is sent to the chat endpoint.

The planner classifies the request.

LangGraph routes the request to the correct workflow.

The selected agent generates or retrieves the response.

The response and metadata are stored in PostgreSQL.

Metrics are exposed to Prometheus and visualized in Grafana.

Planner

The planner returns structured output:

{
  "route": "chat",
  "confidence": 0.95,
  "reasoning": "The request is a general knowledge question.",
  "signals": [
    "general explanation",
    "no external research required"
  ]
}

Supported routes:

chat

rag

research

tool

sql

human_review

If Ollama fails or returns an invalid response, RedPA AI uses a deterministic rule-based fallback.

Example Response Metadata

{
  "provider": "ollama",
  "model": "qwen2.5:7b",
  "workflow": "langgraph",
  "route": "chat",
  "planner_provider": "ollama",
  "planner_fallback": false,
  "planner_error": null,
  "requires_human_review": false
}

Monitoring

Prometheus collects application metrics from the backend.

Grafana can be used to visualize:

Request count

Request latency

Error count

Chat requests

Planner fallback usage

Agent route usage

Human-review activity

Testing

Run tests inside the backend container:

docker compose exec backend pytest

Run with verbose output:

docker compose exec backend pytest -v

Development Commands

Check the active planner implementation:

docker compose exec backend python -c "import inspect; from app.services.planner_service import PlannerService; print(inspect.getfile(PlannerService))"

Check the Ollama streaming client signature:

docker compose exec backend python -c "import inspect; from app.clients.ollama_client import OllamaClient; print(inspect.signature(OllamaClient.stream_chat))"

Roadmap

Complete external research agent

Add production tool registry

Add SQL agent execution

Add MCP server and client support

Add agent-to-agent communication

Add long-running workflows

Add short-term and long-term memory

Add frontend dashboard

Improve planner latency

Expand automated tests

Add deployment configuration

Security Notes

Never commit .env

Use a strong JWT secret in production

Restrict CORS origins

Rotate credentials regularly

Do not expose PostgreSQL publicly in production

Protect Grafana with a strong password

Validate every tool action before execution

Require human approval for sensitive operations

License

This project is licensed under the MIT License.

Author

Saeid Khalilian

AI and Python DeveloperMaster's student in Computer Science at the University of Passau