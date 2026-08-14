from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.connectors_v8.repository import ConnectorNotFoundError, ConnectorRepository
from app.connectors_v8.schemas import ConnectorCreate, ConnectorExecuteRequest, ConnectorExecuteResponse, ConnectorRecord
from app.connectors_v8.service import ConnectorApprovalRequiredError, ConnectorService

router = APIRouter(prefix="/connectors", tags=["V8 Enterprise Connectors"])


@router.post("", response_model=ConnectorRecord, status_code=status.HTTP_201_CREATED)
async def create_connector(payload: ConnectorCreate) -> ConnectorRecord:
    return await ConnectorRepository.create(payload)


@router.get("", response_model=list[ConnectorRecord])
async def list_connectors(limit: int = Query(default=100, ge=1, le=200)) -> list[ConnectorRecord]:
    return await ConnectorRepository.list(limit)


@router.get("/{connector_id}", response_model=ConnectorRecord)
async def get_connector(connector_id: UUID) -> ConnectorRecord:
    try:
        return await ConnectorRepository.get(connector_id)
    except ConnectorNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{connector_id}/execute", response_model=ConnectorExecuteResponse)
async def execute_connector(connector_id: UUID, payload: ConnectorExecuteRequest) -> ConnectorExecuteResponse:
    try:
        return await ConnectorService.execute(connector_id, payload)
    except ConnectorNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConnectorApprovalRequiredError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
