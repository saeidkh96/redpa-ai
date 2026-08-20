from __future__ import annotations

import os
import re
import threading
from typing import Any

import docker
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


app = FastAPI(title='RedPA Ops Agent', version='19.3.0')

_client = docker.from_env()

_ALLOWED = re.compile(r'^redpa-[a-z0-9-]+$')
_STATEFUL_DENY = {'redpa-postgres','redpa-qdrant','redpa-redis'}

_VALIDATION_FAILURE_ENABLED = (
    os.getenv("OPS_VALIDATION_FAILURE_INJECTION", "false")
    .strip()
    .lower()
    in {"1", "true", "yes", "on"}
)

_VALIDATION_FAILURE_MARKER = "stage6-force-recovery-failure"

# Validation-only in-memory state.
# When a restart request carries the explicit marker and injection is enabled,
# subsequent diagnose calls report an unhealthy state for this target.
_forced_unhealthy: set[str] = set()
_forced_unhealthy_lock = threading.Lock()


class RestartRequest(BaseModel):
    approved: bool = False
    reason: str = Field(min_length=8, max_length=500)


def _container(name: str):
    if not _ALLOWED.fullmatch(name):
        raise HTTPException(
            status_code=400,
            detail='Target is outside the RedPA container allowlist.',
        )

    try:
        return _client.containers.get(name)
    except docker.errors.NotFound as exc:
        raise HTTPException(
            status_code=404,
            detail='Container not found.',
        ) from exc


def _validation_failure_requested(reason: str) -> bool:
    return (
        _VALIDATION_FAILURE_ENABLED
        and _VALIDATION_FAILURE_MARKER in reason.casefold()
    )


def _is_forced_unhealthy(name: str) -> bool:
    with _forced_unhealthy_lock:
        return name in _forced_unhealthy


def _mark_forced_unhealthy(name: str) -> None:
    with _forced_unhealthy_lock:
        _forced_unhealthy.add(name)


@app.get('/health')
def health() -> dict[str, str]:
    _client.ping()

    return {
        'status':'healthy',
        'service':'RedPA Ops Agent',
        'version':'19.3.0',
    }


@app.get('/containers/{name}/diagnose')
def diagnose(name: str) -> dict[str, Any]:
    container = _container(name)

    container.reload()

    state = container.attrs.get('State', {})
    health = state.get('Health', {}).get('Status')

    logs = (
        container.logs(
            tail=25,
            timestamps=True,
        )
        .decode(
            'utf-8',
            'replace',
        )
        .splitlines()
    )

    running = state.get('Status') == 'running'
    restart_allowed = name not in _STATEFUL_DENY

    validation_failure = _is_forced_unhealthy(name)

    # Production-validation-only simulated recovery failure.
    #
    # The real container remains untouched/running, but the Ops Agent reports
    # the recovery as unhealthy so the backend's fail-closed verification path
    # can be exercised end-to-end.
    if validation_failure and running:
        health = 'unhealthy'

    if not running:
        recommendation = (
            'restart_container'
            if restart_allowed
            else 'manual_stateful_recovery'
        )
    elif health == 'unhealthy':
        recommendation = (
            'restart_container'
            if restart_allowed
            else 'inspect_stateful_service'
        )
    else:
        recommendation = 'observe'

    return {
        'container': name,
        'found': True,
        'state': state.get('Status'),
        'health': health,
        'restart_count': container.attrs.get(
            'RestartCount',
            0,
        ),
        'recent_logs': logs[-25:],
        'recommendation': recommendation,
        'restart_allowed': restart_allowed,
        'validation_failure_injected': validation_failure,
    }


@app.post('/containers/{name}/restart')
def restart(
    name: str,
    payload: RestartRequest,
) -> dict[str, Any]:
    if not payload.approved:
        raise HTTPException(
            status_code=403,
            detail='Human approval is required.',
        )

    if name in _STATEFUL_DENY:
        raise HTTPException(
            status_code=403,
            detail='Automatic restart is disabled for stateful data services.',
        )

    container = _container(name)

    # This is still a real restart.
    container.restart(timeout=10)
    container.reload()

    validation_failure = _validation_failure_requested(
        payload.reason
    )

    if validation_failure:
        _mark_forced_unhealthy(name)

    return {
        'status':'completed',
        'action':'restart_container',
        'container':name,
        'state':container.attrs.get('State',{}).get('Status'),
        'reason':payload.reason,
        'validation_failure_injected':validation_failure,
    }


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        app,
        host='0.0.0.0',
        port=int(
            os.getenv(
                'OPS_AGENT_PORT',
                '8070',
            )
        ),
    )
