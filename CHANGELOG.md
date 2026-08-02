# Changelog

All notable changes to RedPA AI are documented in this file.

## [Unreleased]

### Planned

- Agent Registry
- Agent Cards
- Agent discovery
- Agent-to-Agent task delegation
- Coordinator Agent
- Multi-agent workflows
- Long-running workflows
- Agent memory

## [0.4.0] - 2026-08-03

### Added

- MCP platform foundation
- MCP server configuration and reload
- MCP health reporting
- MCP tool discovery
- qualified MCP tool names
- unified internal and MCP tool catalog
- dynamic MCP tool selection
- Filesystem MCP server
- GitHub MCP server
- PostgreSQL MCP server
- Docker MCP server
- MCP-specific formatters
- MCP planner integration
- MCP security tests
- MCP v2 compatibility tests

### Security

- filesystem sandbox restrictions
- PostgreSQL read-only SQL validation
- Docker GET-only capability surface
- MCP allowlists
- private-network validation
- approval-compatible tool permissions

## [0.3.0]

### Added

- research workflow
- ranked evidence pipeline
- source deduplication
- web search through DDGS
- research metadata and confidence handling

## [0.2.0]

### Added

- Human Review persistence
- approve and reject operations
- workflow resume after approval
- Prometheus metrics
- Grafana dashboards
- Docker Compose infrastructure

## [0.1.0]

### Added

- FastAPI application
- JWT authentication
- users
- conversations
- messages
- LangGraph orchestration
- Ollama chat
- PostgreSQL persistence
- Qdrant integration
- initial RAG pipeline
