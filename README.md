
![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Production-009688?logo=fastapi)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_AI-purple)
![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791?logo=postgresql)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-DC244C)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?logo=docker)
![License](https://img.shields.io/badge/License-MIT-green)

# RedPA AI

**RedPA AI** is an open-source, production-oriented Agentic AI platform built with FastAPI, LangGraph, PostgreSQL, Ollama, and modern asynchronous Python.

The project provides a scalable foundation for building AI assistants capable of planning requests, retrieving knowledge, streaming generated responses, managing conversations, and requesting human approval before executing sensitive actions.

RedPA AI is designed as a portfolio and research project demonstrating practical backend engineering, agent orchestration, retrieval-augmented generation, local LLM integration, authentication, persistence, and Human-in-the-Loop workflows.

---

## Project Status

RedPA AI is under active development.

The current version includes:

- FastAPI backend
- PostgreSQL database
- Async SQLAlchemy
- Alembic migrations
- JWT authentication
- User registration and login
- Conversation management
- Persistent chat messages
- Ollama LLM integration
- LangGraph agent orchestration
- Planner-based routing
- Standard chat workflow
- Retrieval-Augmented Generation workflow
- Server-Sent Events streaming
- Token-by-token LLM streaming
- Human review detection
- Human review database model
- Human review database migration
- API documentation with Swagger UI
- Request ID and processing-time headers
- CORS configuration
- Structured project architecture

Human-in-the-Loop is fully implemented for the core workflow, including:

- Human review persistence
- Review listing and retrieval APIs
- Approve and reject APIs
- Workflow resume after approval
- Duplicate resume protection

Future work includes reviewer dashboards, advanced authorization, and additional audit capabilities.

---

## Why RedPA AI?

Many AI demos only send a prompt to a language model and return a response.

RedPA AI is designed differently. It focuses on the complete engineering workflow required for real AI applications:

1. Authenticate the user.
2. Store conversations and messages.
3. Analyze the request using a planner.
4. Select the appropriate agent capability.
5. Retrieve external knowledge when required.
6. Stream generated tokens to the client.
7. Detect sensitive or high-risk actions.
8. Escalate sensitive requests for human review.
9. Persist application and workflow state.
10. Extend the system with tools, memory, monitoring, and long-running workflows.

---

## Architecture

```text
Client
  |
  v
FastAPI API
  |
  +-----------------------+
  | Authentication        |
  | Conversations         |
  | Messages              |
  | Chat                  |
  | Streaming             |
  | Human Reviews         |
  +-----------------------+
  |
  v
LangGraph Orchestrator
  |
  v
Planner Agent
  |
  +--------------------+---------------------+----------------------+
  |                    |                     |                      |
  v                    v                     v                      v
Chat Node           RAG Node         Human Review Node     Capability Unavailable
  |                    |                     |                      |
  +--------------------+---------------------+----------------------+
                               |
                               v
                         Response Node
                               |
                               v
                         FastAPI Response
```

---

## Agent Workflow

A request enters the LangGraph workflow through the planner.

The planner determines the most suitable route:

```text
START
  |
  v
Planner
  |
  +--> Chat
  |
  +--> RAG
  |
  +--> Human Review
  |
  +--> Capability Unavailable
  |
  v
Response
  |
  v
END
```

### Chat route

Used for general questions and requests that can be answered directly by the configured language model.

### RAG route

Used when the response should be grounded in indexed documents and retrieved context.

### Human Review route

Used when the request contains a potentially sensitive or high-risk action, such as:

- Sending an email
- Transferring money
- Processing a payment
- Approving an invoice
- Issuing a refund
- Deleting data
- Creating calendar events
- Creating external issues
- Purchasing products
- Performing destructive database operations

The current implementation creates the foundation for persisting these review requests in PostgreSQL.

### Capability Unavailable route

Used when the requested capability is not yet available in the system.

---

## Human-in-the-Loop Design

RedPA AI includes a persistent Human-in-the-Loop foundation.

A human review record can contain:

- Review ID
- User ID
- Conversation ID
- Message ID
- Review status
- Review reason
- Requested action
- Original request content
- Structured action payload
- Reviewer feedback
- Reviewer ID
- Review timestamp
- Creation timestamp
- Update timestamp

Supported review statuses:

```text
pending
approved
rejected
cancelled
```

Implemented Human-in-the-Loop capabilities:

- List reviews
- Retrieve individual reviews
- Approve requests
- Reject requests
- Reviewer feedback
- Prevent duplicate workflow resumes
- Resume approved workflows

Future enhancements:

- Human Review Dashboard
- Reviewer roles and permissions
- Extended audit logging

---

## Streaming

RedPA AI supports real token-by-token streaming through Server-Sent Events.

The backend streams workflow and token events such as:

```text
workflow_started
route_selected
node_completed
token
token_stream_completed
workflow_completed
```

This allows frontend clients to display generated responses while the language model is still producing them.

---

## Technology Stack

### Backend

- Python
- FastAPI
- Pydantic
- Uvicorn

### Agentic AI

- LangGraph
- LangChain
- Planner-based routing
- Human-in-the-Loop architecture
- Retrieval-Augmented Generation

### Language Model

- Ollama
- Qwen 2.5
- Local LLM inference
- Async token streaming

### Database

- PostgreSQL
- SQLAlchemy 2
- Async SQLAlchemy
- Alembic
- UUID primary keys

### Authentication

- OAuth2 password flow
- JWT access tokens
- Password hashing
- Protected API endpoints

### Development and Deployment

- Git
- GitHub
- Docker
- Docker Compose
- Environment-based configuration

---

## Project Structure

```text
redpa-ai/
|
+-- backend/
|   |
|   +-- alembic/
|   |   +-- versions/
|   |
|   +-- app/
|   |   |
|   |   +-- agents/
|   |   |   +-- nodes/
|   |   |   |   +-- capability_unavailable.py
|   |   |   |   +-- chat.py
|   |   |   |   +-- human_review.py
|   |   |   |   +-- planner.py
|   |   |   |   +-- rag.py
|   |   |   |   +-- response.py
|   |   |   |
|   |   |   +-- graph.py
|   |   |   +-- orchestrator.py
|   |   |   +-- router.py
|   |   |   +-- state.py
|   |   |
|   |   +-- api/
|   |   |   +-- v1/
|   |   |
|   |   +-- core/
|   |   |
|   |   +-- database/
|   |   |   +-- base.py
|   |   |
|   |   +-- models/
|   |   |   +-- conversation.py
|   |   |   +-- document.py
|   |   |   +-- document_chunk.py
|   |   |   +-- document_content.py
|   |   |   +-- human_review.py
|   |   |   +-- message.py
|   |   |   +-- user.py
|   |   |
|   |   +-- schemas/
|   |   +-- services/
|   |   +-- main.py
|   |
|   +-- tests/
|   +-- .env
|   +-- alembic.ini
|   +-- requirements.txt
|
+-- README.md
+-- LICENSE
+-- .gitignore
```

The exact structure may evolve as new agents, tools, APIs, and services are added.

---

## Requirements

Before running the project, install:

- Python 3.12 or newer
- PostgreSQL
- Ollama
- Git

Python 3.14 is currently used during development.

For the most predictable dependency compatibility, a stable Python release supported by all project dependencies is recommended.

---

## Local Installation

### 1. Clone the repository

```bash
git clone https://github.com/saeidkh96/redpa-ai.git
cd redpa-ai
```

### 2. Open the backend directory

```bash
cd backend
```

### 3. Create a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Environment Configuration

Create a `.env` file inside the `backend` directory.

Example configuration:

```env
APP_NAME=RedPA AI
APP_ENV=development
DEBUG=true

API_V1_PREFIX=/api/v1

DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/redpa_ai

SECRET_KEY=replace_this_with_a_long_random_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b

CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

Use the exact variable names defined in the project settings module when configuring the application.

Never commit a real `.env` file, database password, or JWT secret to GitHub.

---

## PostgreSQL Setup

Create a PostgreSQL database:

```sql
CREATE DATABASE redpa_ai;
```

Update `DATABASE_URL` in the `.env` file with the correct:

- Username
- Password
- Host
- Port
- Database name

Example:

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/redpa_ai
```

---

## Database Migrations

Run all Alembic migrations:

```bash
alembic upgrade head
```

Check the current migration revision:

```bash
alembic current
```

Create a new migration after changing SQLAlchemy models:

```bash
alembic revision --autogenerate -m "describe migration"
```

Rollback one migration:

```bash
alembic downgrade -1
```

---

## Ollama Setup

Start the Ollama server:

```bash
ollama serve
```

Download the configured model:

```bash
ollama pull qwen2.5:7b
```

Check installed models:

```bash
ollama list
```

Test Ollama directly:

```bash
ollama run qwen2.5:7b
```

The Ollama server normally runs at:

```text
http://localhost:11434
```

---

## Running the Backend

From the `backend` directory:

```bash
fastapi dev app/main.py
```

Alternatively:

```bash
uvicorn app.main:app --reload
```

The API will normally be available at:

```text
http://127.0.0.1:8000
```

---

## API Documentation

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

OpenAPI schema:

```text
http://127.0.0.1:8000/openapi.json
```

---

## Main API Capabilities

### Health

Health endpoints can be used to check whether the backend is running.

```text
GET /api/v1/health
```

### Authentication

The authentication module supports an OAuth2 password flow and JWT access tokens.

Typical operations include:

```text
Register
Login
Get current user
Logout
```

### Conversations

Users can create and retrieve their own conversations.

Typical operations include:

```text
Create conversation
List conversations
Retrieve conversation
Update conversation
Delete conversation
```

### Messages

Messages are persisted using the following roles:

```text
user
assistant
system
tool
```

Message processing statuses include:

```text
pending
processing
completed
failed
```

### Chat

The standard chat endpoint executes the LangGraph workflow and returns the final assistant response.

```text
POST /api/v1/chat/send
```

### Streaming Chat

The streaming endpoint emits Server-Sent Events while the workflow is running.

```text
POST /api/v1/chat/stream
```

The client should send:

```http
Accept: text/event-stream
```

---

## Example Authentication Request

OAuth2 login requests commonly use form data:

```bash
curl -X POST \
  "http://127.0.0.1:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=your_password"
```

Example response:

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

Use the token for protected endpoints:

```http
Authorization: Bearer jwt-token
```

---

## Example Chat Request

```bash
curl -X POST \
  "http://127.0.0.1:8000/api/v1/chat/send" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "YOUR_CONVERSATION_ID",
    "message": "Explain three practical uses of agentic AI."
  }'
```

Request and response field names should follow the schemas exposed in Swagger UI.

---

## Example Streaming Request

```bash
curl -N -X POST \
  "http://127.0.0.1:8000/api/v1/chat/stream" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "YOUR_CONVERSATION_ID",
    "message": "Explain agentic AI in automotive software development."
  }'
```

A streaming response may contain events similar to:

```text
event: workflow_started
data: {...}

event: route_selected
data: {...}

event: token
data: {...}

event: token_stream_completed
data: {...}

event: workflow_completed
data: {...}
```

---

## Database Models

### User

Represents an authenticated platform user.

### Conversation

Represents a user-owned chat session.

Main fields include:

```text
id
user_id
title
created_at
updated_at
```

### Message

Represents a persisted conversation message.

Main fields include:

```text
id
conversation_id
role
content
status
agent_name
tool_name
extra_data
created_at
```

### Human Review

Represents an action waiting for a human decision.

Main fields include:

```text
id
conversation_id
user_id
message_id
status
reason
requested_action
request_content
action_payload
reviewer_feedback
reviewed_by
reviewed_at
created_at
updated_at
```

### Document

Represents a document registered for knowledge retrieval.

### Document Content

Stores document content and extracted information.

### Document Chunk

Stores smaller searchable sections used by the RAG pipeline.

---

## Security Considerations

RedPA AI is being designed with the following security principles:

- Passwords must be securely hashed.
- JWT secrets must not be committed.
- Protected resources must verify user ownership.
- Database operations must use parameterized ORM queries.
- Sensitive actions must require human approval.
- Review decisions must be auditable.
- Destructive actions must not execute automatically.
- CORS origins must be explicitly configured.
- Production deployments must use HTTPS.
- Production deployments must use secure secret management.
- Error responses must not expose internal credentials or stack traces.

The current project is still under development and must be reviewed before use in production.

---

## Current Development Roadmap

### Version 1 — Core Platform

- [x] FastAPI application
- [x] PostgreSQL integration
- [x] Async SQLAlchemy
- [x] Alembic migrations
- [x] JWT authentication
- [x] Conversation persistence
- [x] Message persistence
- [x] Ollama integration
- [x] LangGraph workflow
- [x] Planner routing
- [x] Chat node
- [x] RAG node foundation
- [x] SSE response streaming
- [x] Token-level LLM streaming
- [ ] Automated backend test coverage
- [ ] Production Docker Compose

### Version 2 — Human-in-the-Loop

- [x] Sensitive-action detection
- [x] Human review routing
- [x] Human review node
- [x] Human review SQLAlchemy model
- [x] Human review Alembic migration
- [x] Human review PostgreSQL table
- [ ] Review schemas
- [ ] Review repository
- [x] Review service
- [x] List reviews API
- [x] Review details API
- [x] Approve API
- [x] Reject API
- [ ] Reviewer authorization
- [x] Workflow resume after approval
- [ ] Audit log

### Version 3 — Specialized Agents

- [ ] Planner Agent
- [ ] Research Agent
- [ ] Tool Agent
- [ ] SQL Agent
- [ ] Report Agent
- [ ] Agent result evaluation
- [ ] Retry and fallback policies

### Version 4 — Tools and MCP

- [ ] Tool registry
- [ ] MCP server
- [ ] MCP client
- [ ] External tool permissions
- [ ] Tool execution audit logs
- [ ] Sandboxed tool execution

### Version 5 — Agent Communication

- [ ] Agent-to-Agent protocol
- [ ] Multi-agent communication
- [ ] Agent task delegation
- [ ] Shared agent context
- [ ] Multi-agent workflow monitoring

### Version 6 — Long-Running Workflows

- [ ] Persistent workflow checkpoints
- [ ] Pause and resume
- [ ] Scheduled continuation
- [ ] Wait for external data
- [ ] Background task processing
- [ ] Workflow cancellation
- [ ] Workflow timeout handling

### Version 7 — Agent Memory

- [ ] Short-term memory
- [ ] Long-term memory
- [ ] Semantic memory
- [ ] User preferences
- [ ] Memory retrieval
- [ ] Memory deletion
- [ ] Privacy controls

### Version 8 — Observability and Delivery

- [ ] Structured logging
- [ ] Metrics
- [ ] Prometheus
- [ ] Grafana dashboards
- [ ] Distributed tracing
- [ ] Langfuse integration
- [ ] GitHub Actions
- [ ] GitLab CI
- [ ] Automated tests
- [ ] Security scanning
- [ ] Deployment pipelines

### Version 9 — Frontend

- [ ] Web application
- [ ] Authentication UI
- [ ] Conversation interface
- [ ] Streaming chat interface
- [ ] Human review dashboard
- [ ] Approve and reject controls
- [ ] Document management
- [ ] Agent workflow visualization
- [ ] Monitoring dashboard

---

## Planned Human Review API

The following endpoints are planned:

```text
GET  /api/v1/reviews
GET  /api/v1/reviews/{review_id}
POST /api/v1/reviews/{review_id}/approve
POST /api/v1/reviews/{review_id}/reject
POST /api/v1/reviews/{review_id}/resume
```

Expected behavior:

- Only authorized users can access reviews.
- Users can only access permitted review records.
- Pending reviews can be approved or rejected once.
- Decisions include reviewer identity and timestamp.
- Feedback can be attached to decisions.
- Approved workflows can be resumed.
- Rejected workflows must not execute the requested action.

---

## Testing Strategy

The project is intended to include:

### Unit tests

- Planner routing
- High-risk action detection
- Authentication helpers
- Review state transitions
- Service-layer behavior
- Schema validation

### Integration tests

- Authentication API
- Conversation API
- Chat API
- Streaming API
- Review API
- PostgreSQL persistence
- Alembic migrations

### Workflow tests

- Chat route
- RAG route
- Human review route
- Unsupported capability route
- Approved workflow continuation
- Rejected workflow termination

### Security tests

- Unauthorized access
- Cross-user resource access
- Invalid JWT
- Expired JWT
- Duplicate review decisions
- Unsafe action execution
- Malformed request payloads

---

## Development Principles

RedPA AI follows these engineering principles:

- Clear separation of concerns
- Async-first backend design
- Typed Python
- Modular agent nodes
- Explicit workflow routing
- Persistent domain models
- API versioning
- Database migrations
- Secure authentication
- Human approval for risky operations
- Observable workflow events
- Local-first LLM support
- Extensible agent architecture

---

## Contributing

Contributions, suggestions, and issue reports are welcome.

A typical contribution workflow:

1. Fork the repository.
2. Create a feature branch.
3. Implement the change.
4. Add or update tests.
5. Run formatting and tests.
6. Commit the change.
7. Push the branch.
8. Open a pull request.

Example:

```bash
git checkout -b feature/human-review-api
git add .
git commit -m "feat: add human review API"
git push origin feature/human-review-api
```

---

## Git Commit Convention

Recommended commit types:

```text
feat:     new feature
fix:      bug fix
docs:     documentation
refactor: code restructuring
test:     tests
chore:    maintenance
build:    build or dependency changes
ci:       CI/CD configuration
```

Examples:

```text
feat: add token streaming
feat: add human review persistence
fix: handle Ollama connection errors
docs: update project setup
refactor: separate agent routing logic
test: add planner routing tests
```

---

## Troubleshooting

### PostgreSQL connection timeout

Check that PostgreSQL is running and verify:

```text
host
port
database
username
password
```

Also verify the `DATABASE_URL` value.

### Alembic cannot detect models

Make sure all SQLAlchemy models are imported before Alembic reads `Base.metadata`.

The models package should export newly created models.

### Ollama port is already in use

Check whether Ollama is already running.

On Windows:

```powershell
netstat -ano | findstr :11434
```

Do not start a second Ollama server if one is already active.

### Model is unavailable

Install the configured model:

```bash
ollama pull qwen2.5:7b
```

Then verify:

```bash
ollama list
```

### PowerShell blocks virtual environment activation

Run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Unauthorized response in Swagger UI

Use the **Authorize** button in Swagger UI and provide valid login credentials or a valid bearer token according to the configured OAuth2 flow.

---

## Disclaimer

RedPA AI is an experimental open-source project under active development.

It is not currently intended for unsupervised use in financial, legal, medical, security-critical, or other high-risk production environments.

All external side effects and sensitive operations should require appropriate authorization, validation, logging, and human approval.

---

## License

This project is licensed under the MIT License.

See the `LICENSE` file for details.

---

## Author

**Saeid Khalilian**

AI and Python Developer  
Master's student in Computer Science at the University of Passau

Areas of interest:

- Agentic AI
- Generative AI
- Large Language Models
- Backend Development
- Retrieval-Augmented Generation
- AI Agents
- Human-in-the-Loop Systems
- Machine Learning
- Production AI Engineering

GitHub:

```text
https://github.com/saeidkh96
```

Project repository:

```text
https://github.com/saeidkh96/redpa-ai
```

---

## Acknowledgements

RedPA AI is built using open-source technologies including:

- FastAPI
- LangGraph
- LangChain
- Ollama
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic
- Uvicorn

Thanks to the open-source community for making modern AI application development accessible.
