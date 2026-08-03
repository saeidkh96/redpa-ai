# Contributing to RedPA AI

Thank you for considering a contribution.

## Development Principles

Contributions should preserve:

- explicit security boundaries;
- deterministic behavior where practical;
- typed schemas;
- async compatibility;
- clear service separation;
- no hidden mutation in read-only tools;
- observable execution;
- test coverage;
- backward-compatible APIs when possible.

## Setup

```bash
git clone https://github.com/saeidkh96/redpa-ai.git
cd redpa-ai
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Validation

Run the full test suite:

```bash
python -m pytest tests -v
```

Compile backend modules:

```bash
python -m compileall backend/app
```

Validate Docker Compose:

```bash
docker compose config
```

Check services:

```bash
docker compose ps
```

## Branches

Use focused branches:

```text
feat/<name>
fix/<name>
docs/<name>
test/<name>
refactor/<name>
security/<name>
```

## Commit Style

Use Conventional Commit-style messages.

Examples:

```text
feat(a2a): add Remote Agent selection
feat(mcp): add read-only Docker server
fix(planner): prioritize A2A discovery intent
fix(a2a): constrain protobuf compatibility
test(postgres): cover unsafe SQL functions
docs(readme): document Multi-Agent workflow
security(a2a): validate Remote Agent URLs
```

## Pull Requests

A pull request should include:

- a clear summary;
- motivation;
- relevant design notes;
- migration instructions;
- tests;
- documentation updates;
- security impact;
- API impact;
- screenshots or logs when helpful.

## Component Guidelines

### Planner

- preserve deterministic safety checks;
- avoid route ambiguity;
- add tests for conflicting intents;
- document route-priority changes.

### MCP

- keep capability surfaces minimal;
- prefer read-only operations;
- validate all inputs;
- add server and planner tests;
- never introduce a generic infrastructure proxy.

### A2A

- validate Remote Agent URLs;
- resolve and inspect Agent Cards;
- bound timeouts;
- preserve task and context metadata;
- add selection tests;
- document trust assumptions;
- stop sensitive workflows before delegation.

### Human Review

- never bypass persisted approval state;
- avoid duplicate reviews after resume;
- keep decisions auditable;
- test approve, reject, and resume paths.

### Metrics

- use stable metric names;
- keep label cardinality bounded;
- document every new metric;
- avoid labels containing raw user content.

## Documentation

Update relevant files under `docs/` when changing:

- architecture;
- APIs;
- MCP;
- A2A;
- Human Review;
- deployment;
- monitoring;
- roadmap.

## Security-Sensitive Changes

Changes involving authentication, SQL, filesystems, Docker, MCP permissions, A2A delegation, or Human Review require focused tests and explicit review.
