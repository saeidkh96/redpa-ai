![Python](https://img.shields.io/badge/Python-3.14-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-blue)
![License](https://img.shields.io/badge/License-MIT-green)

# 🚀 RedPA AI

**Production-Ready Enterprise AI Platform** built with FastAPI, PostgreSQL, and modern AI technologies.

RedPA AI is an enterprise-grade backend designed for AI-powered support automation. The project combines secure authentication, scalable backend architecture, retrieval-augmented generation (RAG), and multi-agent workflows to automate customer support while keeping humans in the loop for complex cases.

---

## ✨ Current Features

- ✅ FastAPI Backend
- ✅ PostgreSQL Database
- ✅ SQLAlchemy 2.0 (Async)
- ✅ Alembic Database Migrations
- ✅ JWT Authentication
- ✅ User Registration & Login
- ✅ Password Hashing (Argon2)
- ✅ Protected API Endpoints
- ✅ Pydantic v2 Validation
- ✅ OpenAPI / Swagger Documentation
- ✅ Async Architecture
- ✅ Health Check Endpoint

---

# 🛠 Tech Stack

| Category | Technologies |
|-----------|--------------|
| Backend | FastAPI |
| Language | Python 3.14 |
| Database | PostgreSQL |
| ORM | SQLAlchemy Async |
| Migration | Alembic |
| Authentication | JWT |
| Password Hashing | Argon2 |
| Validation | Pydantic v2 |
| API Docs | Swagger / OpenAPI |

---

# 🏗 Architecture

```
                Client
                   │
                   ▼
            FastAPI Backend
                   │
      ┌────────────┴────────────┐
      ▼                         ▼
 Authentication          Business Logic
      │                         │
      └────────────┬────────────┘
                   ▼
             PostgreSQL Database
```

The project follows a modular architecture with clear separation of concerns to simplify maintenance and future scaling.

---

# 📂 Project Structure

```
backend/
│
├── alembic/
│
├── app/
│   ├── api/
│   ├── core/
│   ├── database/
│   ├── middleware/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── utils/
│   └── main.py
│
├── tests/
│
└── requirements.txt
```

---

# 🚀 Getting Started

## Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/redpa-ai.git
cd redpa-ai/backend
```

## Create virtual environment

```bash
python -m venv .venv
```

Activate

Windows

```powershell
.venv\Scripts\Activate.ps1
```

Linux / macOS

```bash
source .venv/bin/activate
```

## Install dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Environment

Create a `.env` file inside the backend directory.

Example:

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/redpa_ai

JWT_SECRET_KEY=YOUR_SECRET_KEY

JWT_ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## Database Migration

```bash
alembic upgrade head
```

---

## Run Development Server

```bash
fastapi dev app/main.py
```

Swagger UI

```
http://127.0.0.1:8000/docs
```

---

# 📌 Roadmap

## ✅ Completed

- Authentication
- PostgreSQL Integration
- Alembic Migrations
- JWT Security
- Health Monitoring

## 🚧 In Progress

- Ticket Management System
- Role-Based Authorization
- Refresh Tokens

## 🔜 Planned

- Multi-Agent AI Workflow
- LangGraph Integration
- RAG Pipeline
- ChromaDB
- Redis
- Background Workers
- Docker Compose
- GitHub Actions CI/CD
- Prometheus Monitoring
- Grafana Dashboards
- Human Review Dashboard
- Audit Logging
- AI Evaluation Pipeline

---

# 🎯 Project Vision

RedPA AI aims to become a production-ready enterprise AI platform capable of:

- Intelligent ticket classification
- AI-powered response generation
- Retrieval-Augmented Generation (RAG)
- Multi-agent orchestration
- Human-in-the-loop approval workflows
- Enterprise authentication and authorization
- Observability and monitoring
- Production deployment

---

# 📄 License

MIT License