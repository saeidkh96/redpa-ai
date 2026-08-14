# RedPA AI Python SDK

The RedPA AI V8 SDK is the developer-facing client for the implemented RedPA `/api/v1` platform.

## Install

From the repository:

```bash
pip install -e sdk/python
```

Build a wheel:

```bash
python -m build sdk/python
```

## Configuration

```text
REDPA_API_URL=http://localhost:8000
REDPA_TOKEN=<access-token>
REDPA_TIMEOUT_SECONDS=30
```

PowerShell:

```powershell
$env:REDPA_API_URL="http://localhost:8000"
$env:REDPA_TOKEN="<access-token>"
```

## Sync Python client

```python
from redpa_sdk import RedPA

with RedPA() as client:
    print(client.health())
    print(client.agents())
    print(client.providers())
```

## Async Python client

```python
import asyncio
from redpa_sdk import AsyncRedPA

async def main():
    async with AsyncRedPA() as client:
        print(await client.health())
        print(await client.workflows(limit=10))

asyncio.run(main())
```

## CLI

```text
redpa status
redpa doctor

redpa agents list
redpa agents discover "web research"

redpa models providers
redpa tools list

redpa workflows list
redpa workflows get <workflow-uuid>
redpa workflows create --request "Research a topic"
redpa workflows resume <workflow-uuid>

redpa reviews list --status pending
redpa reviews get <review-uuid>
redpa reviews approve <review-uuid> --feedback "Approved"
redpa reviews reject <review-uuid> --feedback "Rejected"
redpa reviews resume <review-uuid>

redpa mcp servers
redpa mcp health
redpa mcp tools
redpa mcp execute mcp:redpa-filesystem:read_file --arguments "{\"path\":\"README.md\"}"

redpa reliability scorecard

redpa quality gate --baseline <uuid> --candidate <uuid> --release-label candidate
redpa quality report --candidate <uuid>
```

Authenticated endpoints require `REDPA_TOKEN` or `--token`.

## SDK scope

The SDK is intentionally thin. Agent orchestration, durable workflow execution, MCP permissions, human review, model routing, evaluation, and reliability remain server-side RedPA capabilities. The SDK only exposes APIs that are implemented by the repository.


## V7 Enterprise Research

```bash
redpa research start --query "Compare enterprise AI agent platforms"
redpa research list
redpa research get <run-uuid>
```

Python:

```python
from redpa_sdk import RedPA

with RedPA() as client:
    run = client.start_research(
        "Compare enterprise AI agent platforms",
        max_results=8,
        minimum_quality_score=0.65,
    )
    print(run["id"])
```


## V8 Operations

```bash
redpa analytics catalog
redpa analytics query --metric research.quality --aggregation weighted_avg --group-by workspace
redpa connectors list
redpa operations slo-demo
```

The SDK also exposes `ingest_analytics`, `query_kpi`, connector create/execute operations and SLO evaluation in synchronous and asynchronous clients.
