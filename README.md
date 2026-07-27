# RedPA AI

Enterprise-grade AI platform built with FastAPI for intelligent automation, multi-agent workflows, Retrieval-Augmented Generation (RAG), and enterprise integrations.

## Overview

RedPA AI is a production-oriented backend platform designed to demonstrate modern AI engineering and backend development practices.

The project focuses on building scalable AI systems with clean architecture, robust APIs, observability, authentication, and multi-agent orchestration.

## Current Features

- FastAPI backend
- Environment-based configuration
- Structured logging
- Request ID middleware
- Global exception handling
- OpenAPI / Swagger documentation
- ReDoc documentation

## Planned Features

- JWT Authentication
- User Management
- PostgreSQL
- SQLAlchemy
- Alembic Migrations
- Redis
- LangGraph Multi-Agent System
- Retrieval-Augmented Generation (RAG)
- Vector Database (ChromaDB)
- Role-Based Access Control (RBAC)
- Docker & Docker Compose
- GitHub Actions CI/CD
- Prometheus & Grafana Monitoring
- React Dashboard

## Tech Stack

### Backend

- Python 3.14
- FastAPI
- Pydantic v2

### AI

- LangGraph
- LangChain
- Ollama
- OpenAI API

### Database

- PostgreSQL
- Redis
- ChromaDB

### DevOps

- Docker
- GitHub Actions
- Prometheus
- Grafana

## Project Structure

```text
backend/
├── app/
│   ├── api/
│   ├── agents/
│   ├── core/
│   ├── database/
│   ├── middleware/
│   ├── exceptions/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── main.py
└── tests/
```

## API Documentation

After running the project:

Swagger UI

```
http://127.0.0.1:8000/docs
```

ReDoc

```
http://127.0.0.1:8000/redoc
```

## Development Status

This project is under active development.
New features are added incrementally following production-grade engineering practices.

## License

MIT