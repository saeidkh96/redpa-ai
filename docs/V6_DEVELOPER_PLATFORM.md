# RedPA AI V6.0 — Developer Platform

## Goal

V6 moves RedPA from a repository-centric platform toward an externally usable developer platform.

## Batch 1: Python SDK and CLI

Implemented:

- standalone installable Python package under `sdk/python`;
- `RedPA` API client with environment-based configuration;
- bearer-token support;
- typed responses for core health, provider, tool, reliability, and release-gate operations;
- structured `RedPAError` with HTTP status and API detail;
- `redpa` CLI entry point;
- `redpa status`;
- `redpa doctor`;
- agent list and discovery commands;
- model-provider inspection;
- unified-tool catalog inspection;
- provider reliability scorecard;
- persisted release quality-gate execution;
- release candidate report retrieval.

### Package

```text
sdk/python/
├── pyproject.toml
├── README.md
└── src/redpa_sdk/
    ├── __init__.py
    ├── cli.py
    ├── client.py
    ├── config.py
    └── models.py
```

### Install

```bash
pip install -e sdk/python
```

### Environment

```text
REDPA_API_URL
REDPA_TOKEN
REDPA_TIMEOUT_SECONDS
```

### Design boundary

The SDK is an API client. It does not duplicate agent orchestration, model routing, tool execution, evaluation, or reliability logic. Those remain server-side RedPA capabilities.

Batch 1 intentionally exposes only API surfaces that are already implemented in the repository.


### Batch 1.1 — SDK hardening

- network/connection failures are converted to `RedPAError` instead of exposing an HTTPX traceback;
- CLI errors show a concise message and actionable hint;
- `redpa doctor` explains missing `REDPA_TOKEN` for authenticated model-gateway endpoints;
- `redpa doctor` warns when a `404` suggests that the running Docker backend image is older than the checked-out source.

When backend source changes are not bind-mounted into the container, rebuild the service:

```bash
docker compose up -d --build backend
```


## V6.0 Complete Developer Surface

The completed V6.0 developer layer includes:

- synchronous `RedPA` client;
- asynchronous `AsyncRedPA` client;
- installable CLI entry point;
- platform health and doctor diagnostics;
- agent registry and capability discovery;
- provider and unified-tool inspection;
- durable workflow list/get/create/resume;
- human-review list/get/approve/reject/resume;
- MCP server/health/tool discovery and qualified-tool execution;
- provider reliability inspection;
- release quality-gate execution and candidate reports;
- benchmark-suite and reliability-history API access;
- actionable connection/authentication diagnostics;
- local examples and dedicated SDK CI across Python 3.11, 3.12 and 3.13;
- wheel/sdist package build support.

V6.0 remains a client/developer layer over implemented RedPA APIs. It does not move orchestration or policy logic into the SDK.
