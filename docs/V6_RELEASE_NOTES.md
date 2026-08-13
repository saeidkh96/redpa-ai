# RedPA AI v6.0.0

RedPA AI v6.0.0 turns the existing agentic platform into a developer-facing platform without moving orchestration logic out of the server.

## Highlights

- installable Python SDK with synchronous and asynchronous clients;
- `redpa` CLI for health, agents, workflows, reviews, MCP, reliability, and release-quality operations;
- durable workflow create/list/get/resume developer operations;
- Human Review list/get/approve/reject/resume operations;
- MCP server/tool discovery and qualified tool execution;
- model-provider and reliability inspection;
- benchmark/release quality-gate developer access;
- actionable API connection and authentication diagnostics;
- SDK examples and dedicated SDK CI;
- release version alignment across backend, Docker Compose, frontend, and SDK.

## Existing platform capabilities included in this release

V6.0 builds on the repository's existing multi-agent runtime, retrieval/RAG services, MCP and A2A integration, durable workflows, human approval, agent memory, model gateway, evaluation/reliability, persistence, runtime caching/background jobs, Control Plane, and distributed observability.

## Validation

Before tagging the release, run the release checklist in `docs/V6_RELEASE_CHECKLIST.md`.

The pre-hardening V6 checkout was validated with 298 passing Python tests, a passing secret scan, successful SDK 6.0.0 package build/install, and registered CLI command groups. The release-hardening changes must be validated again before tagging.

## Deployment note

Kubernetes/Helm and Azure/Pulumi assets are deployment/reference architecture surfaces. This release does not claim that RedPA is currently operated as a hosted production service.
