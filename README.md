![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116-009688?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791?logo=postgresql)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-DC244C)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent_Workflows-4B32C3)
![Ollama](https://img.shields.io/badge/Ollama-qwen2.5:7b-black)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?logo=docker)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-success)

![GitHub stars](https://img.shields.io/github/stars/SaeedKhalilian/redpa-ai?style=social)
![GitHub forks](https://img.shields.io/github/forks/SaeedKhalilian/redpa-ai?style=social)
![GitHub issues](https://img.shields.io/github/issues/SaeedKhalilian/redpa-ai)
![GitHub last commit](https://img.shields.io/github/last-commit/SaeedKhalilian/redpa-ai)

# 🚀 RedPA AI

> An enterprise-ready Agentic AI Platform built with FastAPI, LangGraph, Ollama, PostgreSQL and Qdrant.

RedPA AI is an open-source platform for building production-grade AI assistants capable of understanding documents, retrieving relevant knowledge using Retrieval-Augmented Generation (RAG), and orchestrating intelligent workflows through AI agents.

---

## ✨ Features

- 🔐 JWT Authentication
- 💬 Persistent AI Conversations
- 📄 Document Upload
- 📑 PDF, DOCX, TXT & Markdown Support
- 🔍 Automatic Text Extraction
- ✂️ Smart Document Chunking
- 🧠 Local Embeddings with Ollama
- ⚡ Vector Search using Qdrant
- 📚 Retrieval-Augmented Generation (RAG)
- 🤖 LangGraph Agent Workflow
- 🐳 Docker Support
- 📖 Interactive Swagger API
- ⚡ Async FastAPI Backend

---

# 🏗 Architecture

```
                +----------------------+
                |      FastAPI API     |
                +----------+-----------+
                           |
             +-------------+-------------+
             |                           |
             ▼                           ▼
      PostgreSQL                  LangGraph Agent
             |                           |
             ▼                           ▼
     Document Metadata           Ollama LLM
             |
             ▼
     Document Extraction
             |
             ▼
      Chunking Service
             |
             ▼
    Ollama Embeddings
             |
             ▼
         Qdrant Vector DB
             |
             ▼
      Semantic Retrieval
```

---

# 📄 Document Processing Pipeline

```
Upload Document
        │
        ▼
Store File
        │
        ▼
Extract Text
        │
        ▼
Save Content
        │
        ▼
Chunk Document
        │
        ▼
Generate Embeddings
        │
        ▼
Store in Qdrant
        │
        ▼
READY
```

---

# 🛠 Tech Stack

## Backend

- FastAPI
- SQLAlchemy
- Alembic
- Pydantic
- AsyncIO

## AI

- LangGraph
- Ollama
- Local Embeddings
- RAG

## Database

- PostgreSQL
- Qdrant Vector Database

## DevOps

- Docker
- Docker Compose

---

# 📂 Project Structure

```
backend/
│
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   ├── agents/
│   └── utils/
│
├── storage/
├── alembic/
└── tests/
```

---

# 🚀 Running the Project

## Clone

```bash
git clone https://github.com/YOUR_USERNAME/redpa-ai.git
cd redpa-ai
```

---

## Install

```bash
python -m venv .venv
```

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

---

## Start PostgreSQL & Qdrant

```bash
docker compose up -d
```

---

## Start Ollama

```bash
ollama serve
```

Pull required models

```bash
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

---

## Run FastAPI

```bash
uvicorn app.main:app --reload
```

Swagger

```
http://127.0.0.1:8000/docs
```

---

# 📚 Current Capabilities

- User authentication
- Conversation management
- AI chat
- Document upload
- Automatic document parsing
- Semantic chunking
- Local embedding generation
- Vector indexing
- Semantic search
- RAG-ready architecture

---

# 🚧 Roadmap

### ✅ Completed

- Authentication
- Chat API
- LangGraph Integration
- Document Processing
- Chunking
- Embeddings
- Qdrant Integration

### 🚀 In Progress

- Retriever Service
- Context Builder
- RAG Pipeline
- Source Citation

### 🔜 Planned

- Multi-Agent System
- Tool Calling
- SQL Agent
- Research Agent
- Human-in-the-Loop
- Long-term Memory
- MCP Integration
- A2A Communication
- Monitoring Dashboard
- GitHub Actions CI/CD

---

# 📷 Screenshots

Coming soon.

---

# 🤝 Contributing

Pull requests are welcome.

For major changes, please open an issue first.

---

# 📄 License

MIT License

Copyright (c) 2026 Saeed Khalilian

---

# ⭐ Support

If you find this project useful, consider giving it a ⭐ on GitHub.