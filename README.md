# 🚀 RedPA AI

![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116-009688?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791?logo=postgresql)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red?logo=sqlalchemy)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063)
![Ollama](https://img.shields.io/badge/Ollama-qwen2.5:7b-black)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-success)
![PRs](https://img.shields.io/badge/PRs-Welcome-brightgreen)


> An enterprise-ready Agentic AI platform for building intelligent AI assistants, multi-agent workflows, and production-grade autonomous systems.

RedPA AI is an open-source backend platform focused on modern AI engineering. It combines FastAPI, PostgreSQL, and local Large Language Models (LLMs) to provide a scalable foundation for conversational AI, persistent memory, and future multi-agent orchestration.

The project is designed with clean architecture principles and aims to evolve into a complete enterprise Agentic AI platform with LangGraph, Retrieval-Augmented Generation (RAG), MCP, and Human-in-the-Loop workflows.

---

# ✨ Current Features

## 🔐 Authentication

- JWT Authentication
- User Registration
- User Login
- Password Hashing
- Protected API Endpoints

---

## 💬 Conversation Management

- Persistent Conversations
- Conversation History
- Message Storage
- User / Assistant Roles
- Pagination Support

---

## 🤖 AI Integration

- Ollama Integration
- Local LLM Support
- Persistent Chat Memory
- Context-aware Conversations
- AI Chat Endpoint
- LLM Health Monitoring

---

## 🗄 Database

- PostgreSQL
- SQLAlchemy 2.0 (Async)
- Alembic Migrations
- UUID Primary Keys
- Async Database Sessions

---

## ⚡ API

- FastAPI
- RESTful Architecture
- OpenAPI Documentation
- Swagger UI
- Modular Routing

---

# 🏗 Architecture

```
                    Client
                       │
                       ▼
                FastAPI REST API
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
 Authentication              Conversation API
          │                         │
          └────────────┬────────────┘
                       ▼
                 Chat Service
                       │
                       ▼
                  Ollama Client
                       │
                       ▼
               Local LLM (Qwen)
                       │
                       ▼
                  PostgreSQL
```

---

# 🛠 Tech Stack

| Backend | AI | Database | Tools |
|---------|----|----------|-------|
| Python 3.14 | Ollama | PostgreSQL | Git |
| FastAPI | Qwen2.5 | SQLAlchemy Async | Docker (planned) |
| Pydantic v2 | Local LLM | Alembic | VS Code |
| HTTPX | Agentic AI | AsyncPG | Swagger |

---

# 📂 Project Structure

```
backend/
│
├── app/
│   ├── api/
│   ├── clients/
│   ├── core/
│   ├── database/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── main.py
│   └── ...
│
├── alembic/
├── requirements.txt
└── .env
```

---

# 🔌 Available API Endpoints

## Authentication

```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
```

---

## Users

```
GET    /api/v1/users/me
```

---

## Conversations

```
POST   /api/v1/conversations
GET    /api/v1/conversations
GET    /api/v1/conversations/{id}
```

---

## Messages

```
POST   /api/v1/conversations/{id}/messages
GET    /api/v1/conversations/{id}/messages
```

---

## Chat

```
POST   /api/v1/chat
```

---

## LLM

```
GET    /api/v1/llm/health
```

---

# 📸 Current Capabilities

✅ User authentication

✅ Persistent conversations

✅ Persistent AI chat history

✅ Local LLM integration

✅ Async database architecture

✅ OpenAPI documentation

✅ Conversation context

✅ Usage metadata collection

---

# 🚧 Roadmap

## Version 0.2

- LangGraph Integration
- State Management
- Agent Workflow
- Chat Orchestrator

---

## Version 0.3

- Retrieval-Augmented Generation (RAG)
- ChromaDB
- Document Upload
- Semantic Search

---

## Version 0.4

- Planner Agent
- Research Agent
- Tool Agent
- SQL Agent

---

## Version 0.5

- MCP Server
- MCP Client
- Tool Registry
- External Integrations

---

## Version 0.6

- Human-in-the-Loop
- Approval Workflows
- Background Tasks
- Long-running Agents

---

## Version 1.0

- Multi-Agent Platform
- Docker Compose
- Kubernetes Deployment
- Monitoring
- Grafana
- Prometheus
- GitHub Actions
- Production CI/CD

---

# 🎯 Project Goals

RedPA AI aims to become an enterprise-grade Agentic AI platform capable of:

- Building autonomous AI agents
- Long-term conversational memory
- Multi-agent collaboration
- Enterprise AI workflows
- Local and cloud LLM support
- Production deployment

---

# 🚀 Getting Started

Clone the repository

```bash
git clone https://github.com/<your-username>/redpa-ai.git
cd redpa-ai/backend
```

Create a virtual environment

```bash
python -m venv .venv
```

Activate

Windows

```bash
.venv\Scripts\activate
```

Linux / macOS

```bash
source .venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run PostgreSQL

Configure your `.env`

Run migrations

```bash
alembic upgrade head
```

Start Ollama

```bash
ollama serve
```

Pull the model

```bash
ollama pull qwen2.5:7b
```

Run the backend

```bash
fastapi dev app/main.py
```

Open Swagger

```
http://127.0.0.1:8000/docs
```

---

# 📈 Current Status

| Component | Status |
|------------|--------|
| Authentication | ✅ |
| PostgreSQL | ✅ |
| Async SQLAlchemy | ✅ |
| Alembic | ✅ |
| Conversations | ✅ |
| Messages | ✅ |
| Ollama Integration | ✅ |
| AI Chat | ✅ |
| Conversation Memory | ✅ |
| Swagger | ✅ |
| LangGraph | 🚧 |
| RAG | 🚧 |
| Multi-Agent | 🚧 |
| MCP | 🚧 |

---

# 📄 License

MIT License

---

# ⭐ Star the repository

If you find this project useful, consider giving it a ⭐ to support future development.