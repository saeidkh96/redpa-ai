from __future__ import annotations

from typing import Any

from google.protobuf.json_format import (
    MessageToDict,
)

from app.a2a_remote.client import (
    RemoteA2AClient,
)
from app.a2a_remote.registry import (
    RemoteAgentAlreadyRegisteredError,
    RemoteAgentNotFoundError,
    RemoteAgentRecord,
    remote_agent_registry,
)
from app.a2a_remote.schemas import (
    RemoteAgentCardResponse,
    RemoteAgentListResponse,
    RemoteAgentRegistrationRequest,
    RemoteAgentSummary,
    RemoteDelegationRequest,
    RemoteDelegationResponse,
)


class RemoteAgentService:
    @classmethod
    async def register(
        cls,
        request: RemoteAgentRegistrationRequest,
    ) -> RemoteAgentSummary:
        record = RemoteAgentRecord(
            name=request.name,
            base_url=RemoteA2AClient.validate_base_url(
                request.base_url,
            ),
            enabled=request.enabled,
            timeout_seconds=request.timeout_seconds,
        )

        await remote_agent_registry.register(
            record,
        )

        await RemoteA2AClient.resolve_card(
            record,
        )

        return cls.to_summary(
            record,
        )

    @classmethod
    async def list(
        cls,
    ) -> RemoteAgentListResponse:
        records = await remote_agent_registry.list()

        return RemoteAgentListResponse(
            items=[
                cls.to_summary(
                    record,
                )
                for record in records
            ],
            total=len(
                records,
            ),
        )

    @classmethod
    async def get_card(
        cls,
        name: str,
        *,
        refresh: bool = False,
    ) -> RemoteAgentCardResponse:
        record = await remote_agent_registry.get(
            name,
        )

        card = record.card

        if refresh or card is None:
            card = await RemoteA2AClient.resolve_card(
                record,
            )

        return RemoteAgentCardResponse(
            name=record.name,
            base_url=record.base_url,
            card=cls.card_to_dict(
                card,
            ),
        )

    @classmethod
    async def delegate(
        cls,
        name: str,
        request: RemoteDelegationRequest,
    ) -> RemoteDelegationResponse:
        record = await remote_agent_registry.get(
            name,
        )

        return await RemoteA2AClient.delegate(
            record,
            request.message,
            timeout_seconds=request.timeout_seconds,
        )

    @classmethod
    async def unregister(
        cls,
        name: str,
    ) -> None:
        await remote_agent_registry.unregister(
            name,
        )

    @staticmethod
    def card_to_dict(
        card: Any,
    ) -> dict[str, Any]:
        descriptor = getattr(
            card,
            "DESCRIPTOR",
            None,
        )

        if descriptor is not None:
            return MessageToDict(
                card,
                preserving_proto_field_name=True,
            )

        model_dump = getattr(
            card,
            "model_dump",
            None,
        )

        if callable(
            model_dump,
        ):
            result = model_dump(
                mode="json",
            )

            if isinstance(
                result,
                dict,
            ):
                return result

        return {
            "value": str(
                card,
            )
        }

    @classmethod
    def to_summary(
        cls,
        record: RemoteAgentRecord,
    ) -> RemoteAgentSummary:
        card = record.card

        agent_name = getattr(
            card,
            "name",
            None,
        )

        agent_version = getattr(
            card,
            "version",
            None,
        )

        interfaces = getattr(
            card,
            "supported_interfaces",
            [],
        ) or []

        protocol_bindings = [
            str(
                getattr(
                    interface,
                    "protocol_binding",
                    "",
                )
            )
            for interface in interfaces
            if getattr(
                interface,
                "protocol_binding",
                None,
            )
        ]

        skills = getattr(
            card,
            "skills",
            [],
        ) or []

        skill_ids = [
            str(
                getattr(
                    skill,
                    "id",
                    "",
                )
            )
            for skill in skills
            if getattr(
                skill,
                "id",
                None,
            )
        ]

        return RemoteAgentSummary(
            name=record.name,
            base_url=record.base_url,
            enabled=record.enabled,
            connected=record.connected,
            agent_name=agent_name,
            agent_version=agent_version,
            protocol_bindings=protocol_bindings,
            skills=skill_ids,
            last_checked_at=record.last_checked_at,
            error=record.error,
        )


__all__ = [
    "RemoteAgentAlreadyRegisteredError",
    "RemoteAgentNotFoundError",
    "RemoteAgentService",
]
