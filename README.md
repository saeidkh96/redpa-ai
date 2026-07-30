# 🤖 RedPA AI

> A production-inspired Agentic AI platform built with FastAPI, LangGraph, PostgreSQL, Qdrant, JWT Authentication, Prometheus, and Grafana.

![Python](https://img.shields.io/badge/Python-3.14-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-REST-green)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic-orange)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)
![License](https://img.shields.io/badge/License-MIT-black)

---

## Overview

RedPA AI is an agentic AI backend designed using production-oriented software engineering practices.

The project demonstrates how modern AI applications can combine LLM workflows, Retrieval-Augmented Generation (RAG), authentication, monitoring, and human review into a scalable architecture.

Instead of being a simple chatbot, RedPA AI provides a complete backend platform for building intelligent AI services.

---

# Features

- JWT Authentication
- FastAPI REST API
- PostgreSQL
- Qdrant Vector Database
- LangGraph Agent Workflow
- Retrieval-Augmented Generation (RAG)
- Human Review Workflow
- Conversation Management
- Message History
- Docker & Docker Compose
- GitHub Actions CI
- Prometheus Monitoring
- Grafana Dashboard
- Structured Project Architecture

---

# Tech Stack

| Category | Technology |
|----------|------------|
| Backend | FastAPI |
| Language | Python 3.14 |
| AI Workflow | LangGraph |
| LLM | Ollama |
| Vector Database | Qdrant |
| Database | PostgreSQL |
| Authentication | JWT |
| Monitoring | Prometheus + Grafana |
| Containerization | Docker Compose |
| CI/CD | GitHub Actions |

---

# Project Structure

```text
backend/
monitoring/
docker/
.github/
docs/
```

---

# Monitoring

The project includes built-in observability using Prometheus and Grafana.

Metrics include:

- API Request Rate
- Total Requests
- Requests by Endpoint
- Status Code Monitoring
- Response Time Metrics

---

# Running the Project

```bash
git clone https://github.com/<YOUR_USERNAME>/redpa-ai.git

cd redpa-ai

docker compose up --build
```

Backend:

```
http://localhost:8000
```

Swagger:

```
http://localhost:8000/docs
```

Grafana:

```
http://localhost:3000
```

Prometheus:

```
http://localhost:9090
```

---

# CI/CD

GitHub Actions automatically:

- Install dependencies
- Run tests
- Validate the project
- Build Docker images

---

# Roadmap

- Agent Memory
- Planner Agent
- Research Agent
- SQL Agent
- MCP Integration
- Multi-Agent Collaboration
- Long-running Workflows

---

# License

MIT License

---

Built by **Saeid Khalilian**