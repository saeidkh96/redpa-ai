# 🚀 RedPA AI

![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Production-009688?logo=fastapi)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_AI-purple)
![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791?logo=postgresql)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-DC244C)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?logo=docker)
![License](https://img.shields.io/badge/License-MIT-green)

**RedPA AI** is an open-source, production-oriented Agentic AI platform
for building intelligent assistants with Retrieval-Augmented Generation
(RAG), document understanding, conversational memory (planned), and
multi-agent workflows.

------------------------------------------------------------------------

# Features

-   JWT Authentication
-   Conversation Management
-   Persistent Chat History
-   LangGraph Agent Workflow
-   Planner-based Routing
-   Conversational RAG
-   Document Upload
-   Text Extraction
-   Intelligent Chunking
-   Embedding Generation
-   Semantic Retrieval
-   Qdrant Vector Database
-   Ollama Local Models
-   PostgreSQL Persistence
-   Async FastAPI API
-   Docker Ready
-   Swagger Documentation

------------------------------------------------------------------------

# Architecture

``` text
Client
   │
   ▼
FastAPI API
   │
   ▼
Chat Service
   │
   ▼
Orchestrator
   │
   ▼
LangGraph
 ├── Chat Node
 ├── RAG Node
 └── Response Node
        │
        ▼
Retriever
        │
        ▼
Qdrant
        │
        ▼
Context Builder
        │
        ▼
Ollama
```

------------------------------------------------------------------------

# RAG Pipeline

``` text
Upload Document
      │
      ▼
Extract Text
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
User Question
      │
      ▼
Retriever
      │
      ▼
Context Builder
      │
      ▼
Ollama
      │
      ▼
Grounded Response + Sources
```

------------------------------------------------------------------------

# Tech Stack

## Backend

-   FastAPI
-   SQLAlchemy
-   Alembic
-   Pydantic
-   AsyncIO

## AI

-   LangGraph
-   Ollama
-   qwen2.5:7b
-   nomic-embed-text
-   RAG

## Database

-   PostgreSQL
-   Qdrant

## DevOps

-   Docker
-   Docker Compose

------------------------------------------------------------------------

# Project Structure

``` text
backend/
 ├── app/
 │   ├── agents/
 │   ├── api/
 │   ├── clients/
 │   ├── core/
 │   ├── database/
 │   ├── models/
 │   ├── prompts/
 │   ├── repositories/
 │   ├── schemas/
 │   └── services/
 ├── alembic/
 ├── storage/
 └── tests/
```

------------------------------------------------------------------------

# Installation

``` bash
git clone https://github.com/saeidkh96/redpa-ai.git
cd redpa-ai

python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

Run infrastructure:

``` bash
docker compose up -d
```

Start Ollama:

``` bash
ollama serve

ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

Run API:

``` bash
uvicorn app.main:app --reload
```

Swagger:

    http://127.0.0.1:8000/docs

------------------------------------------------------------------------

# Current Capabilities

-   Authentication
-   Conversations
-   Persistent Chat
-   Document Upload
-   Document Parsing
-   Chunking
-   Embeddings
-   Qdrant Integration
-   Retriever Service
-   Context Builder
-   Conversational RAG
-   LangGraph Routing
-   Source Attribution

------------------------------------------------------------------------

# Roadmap

## Completed

-   Authentication
-   Chat API
-   LangGraph
-   Planner Agent
-   RAG
-   Retriever
-   Context Builder
-   Source Citation

## Planned

-   Streaming Responses
-   Conversation Memory
-   Tool Calling
-   SQL Agent
-   Research Agent
-   Human Review
-   Monitoring
-   GitHub Actions
-   MCP Integration
-   A2A Protocol

------------------------------------------------------------------------

# Why RedPA AI?

RedPA AI is designed as a portfolio-quality project demonstrating modern
backend engineering, retrieval-augmented generation, production-ready
API design, and agent orchestration. The architecture emphasizes modular
services, clear separation of concerns, and extensibility for future
enterprise AI capabilities.

------------------------------------------------------------------------

# License

MIT License

Copyright (c) 2026 Saeid Khalilian
