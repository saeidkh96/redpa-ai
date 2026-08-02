# Contributing to RedPA AI

Thank you for considering a contribution.

## Development Principles

Contributions should preserve the following properties:

- explicit security boundaries;
- deterministic behavior where practical;
- typed schemas;
- test coverage;
- async compatibility;
- clear service separation;
- no hidden mutation in read-only tools;
- observable execution.

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

Run tests:

```bash
python -m pytest tests -v
```

Compile backend modules:

```bash
python -m compileall backend/app
```

Validate Compose:

```bash
docker compose config
```

## Branches

Use focused branches:

```text
feat/<name>
fix/<name>
docs/<name>
test/<name>
refactor/<name>
```

## Commit Style

Examples:

```text
feat(mcp): add read-only Docker server
fix(planner): detect running container requests
test(postgres): cover unsafe SQL functions
docs(readme): document MCP architecture
```

## Pull Requests

A pull request should include:

- a clear summary;
- motivation;
- relevant design notes;
- tests;
- migration instructions when applicable;
- security impact;
- documentation updates.

## Security-Sensitive Changes

Changes involving authentication, SQL, filesystem access, Docker, MCP permissions, or human approval require focused tests and explicit review.
