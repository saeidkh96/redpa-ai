# Changelog

All notable changes to RedPA AI are documented in this file.

## [Unreleased]

### Planned

- persisted Remote Agent Registry;
- independent specialist A2A services;
- streaming A2A execution;
- durable workflows;
- agent memory;
- production deployment.

## [0.5.0] - 2026-08-03

### Added

- Agent Registry and typed Agent Cards;
- official Google A2A Python SDK integration;
- A2A Protocol 1.0 server and public Agent Card;
- RedPA Coordinator Agent;
- Remote Agent Registry and Agent Card resolution;
- remote task delegation over JSON-RPC;
- Chat integration through the `a2a` LangGraph route;
- automatic capability-based Agent Selection;
- automatic Coordinator bootstrap;
- parallel Multi-Agent subtask execution;
- result aggregation and partial-failure reporting;
- Human Approval Gate for distributed workflows;
- A2A and Multi-Agent Prometheus metrics.

### Changed

- deterministic A2A intent is evaluated before MCP tool selection;
- planner routes now include `a2a`;
- Chat metadata records Remote Agent, selected skill, score, task ID, context ID, latency, and success state;
- application version advanced to `0.5.0`.

### Security

- bounded remote-delegation timeouts;
- validated Agent Card discovery;
- no sensitive Multi-Agent execution before approval;
- protobuf dependency constrained for SDK compatibility.

## [0.4.0] - 2026-08-03

### Added

- MCP platform foundation;
- Filesystem, GitHub, PostgreSQL, and Docker MCP servers;
- dynamic MCP selection;
- MCP health, catalog, permissions, formatters, and security tests.

## [0.3.0]

- research workflow and ranked evidence pipeline.

## [0.2.0]

- Human Review, workflow resume, Prometheus, Grafana, and Docker Compose.

## [0.1.0]

- FastAPI, JWT, users, conversations, messages, LangGraph, Ollama, PostgreSQL, Qdrant, and initial RAG.
