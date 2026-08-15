from __future__ import annotations

import os
import re
from typing import Any

import docker
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title='RedPA Ops Agent', version='9.0.0')
_client = docker.from_env()
_ALLOWED = re.compile(r'^redpa-[a-z0-9-]+$')
_STATEFUL_DENY = {'redpa-postgres','redpa-qdrant','redpa-redis'}


class RestartRequest(BaseModel):
    approved: bool = False
    reason: str = Field(min_length=8, max_length=500)


def _container(name: str):
    if not _ALLOWED.fullmatch(name):
        raise HTTPException(status_code=400, detail='Target is outside the RedPA container allowlist.')
    try:
        return _client.containers.get(name)
    except docker.errors.NotFound as exc:
        raise HTTPException(status_code=404, detail='Container not found.') from exc


@app.get('/health')
def health() -> dict[str, str]:
    _client.ping()
    return {'status':'healthy','service':'RedPA Ops Agent','version':'9.0.0'}


@app.get('/containers/{name}/diagnose')
def diagnose(name: str) -> dict[str, Any]:
    container = _container(name)
    container.reload()
    state = container.attrs.get('State',{})
    health = state.get('Health',{}).get('Status')
    logs = container.logs(tail=25, timestamps=True).decode('utf-8','replace').splitlines()
    running = state.get('Status') == 'running'
    restart_allowed = name not in _STATEFUL_DENY
    if not running:
        recommendation = 'restart_container' if restart_allowed else 'manual_stateful_recovery'
    elif health == 'unhealthy':
        recommendation = 'restart_container' if restart_allowed else 'inspect_stateful_service'
    else:
        recommendation = 'observe'
    return {
        'container':name,'found':True,'state':state.get('Status'),'health':health,
        'restart_count':container.attrs.get('RestartCount',0),'recent_logs':logs[-25:],
        'recommendation':recommendation,'restart_allowed':restart_allowed,
    }


@app.post('/containers/{name}/restart')
def restart(name: str, payload: RestartRequest) -> dict[str, Any]:
    if not payload.approved:
        raise HTTPException(status_code=403, detail='Human approval is required.')
    if name in _STATEFUL_DENY:
        raise HTTPException(status_code=403, detail='Automatic restart is disabled for stateful data services.')
    container = _container(name)
    container.restart(timeout=10)
    container.reload()
    return {
        'status':'completed','action':'restart_container','container':name,
        'state':container.attrs.get('State',{}).get('Status'),'reason':payload.reason,
    }


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=int(os.getenv('OPS_AGENT_PORT','8070')))
