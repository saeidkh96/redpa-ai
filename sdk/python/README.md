# RedPA AI Python SDK

V6.0 introduces the first installable developer-facing SDK for RedPA AI.

## Install locally

```bash
pip install -e sdk/python
```

## Configuration

```bash
export REDPA_API_URL=http://localhost:8000
export REDPA_TOKEN=<access-token>
```

PowerShell:

```powershell
$env:REDPA_API_URL="http://localhost:8000"
$env:REDPA_TOKEN="<access-token>"
```

## Python

```python
from redpa_sdk import RedPA

with RedPA() as client:
    print(client.health())
    print(client.providers())
    print(client.reliability_scorecard())
```

## CLI

```bash
redpa status
redpa doctor
redpa agents list
redpa agents discover research
redpa models providers
redpa tools list
redpa reliability scorecard
redpa quality gate --baseline <uuid> --candidate <uuid> --release-label candidate
redpa quality report --candidate <uuid>
```

The SDK calls existing RedPA `/api/v1` endpoints. It does not embed or duplicate the RedPA backend runtime.
