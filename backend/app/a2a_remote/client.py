from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit

import httpx
from a2a.client import (
    A2ACardResolver,
    ClientConfig,
    create_client,
)
from a2a.helpers import new_text_message
from a2a.types import (
    Role,
    SendMessageRequest,
)
from google.protobuf.json_format import (
    MessageToDict,
)

from app.a2a_remote.registry import (
    RemoteAgentRecord,
)
from app.a2a_remote.schemas import (
    RemoteDelegationResponse,
)


class RemoteA2AError(RuntimeError):
    pass


class RemoteA2AClient:
    @staticmethod
    def validate_base_url(
        value: str,
    ) -> str:
        normalized = str(
            value
            or "",
        ).strip().rstrip(
            "/",
        )

        parts = urlsplit(
            normalized,
        )

        if parts.scheme not in {
            "http",
            "https",
        }:
            raise ValueError(
                "Remote A2A URL must use http or https."
            )

        if not parts.hostname:
            raise ValueError(
                "Remote A2A URL must include a hostname."
            )

        if parts.username or parts.password:
            raise ValueError(
                "Credentials must not be embedded in the remote URL."
            )

        return normalized

    @classmethod
    async def resolve_card(
        cls,
        record: RemoteAgentRecord,
    ) -> Any:
        base_url = cls.validate_base_url(
            record.base_url,
        )

        timeout = httpx.Timeout(
            record.timeout_seconds,
        )

        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
            ) as httpx_client:
                resolver = A2ACardResolver(
                    httpx_client=httpx_client,
                    base_url=base_url,
                )

                card = await resolver.get_agent_card()

        except Exception as exception:
            record.connected = False
            record.error = str(
                exception,
            )
            record.last_checked_at = datetime.now(
                timezone.utc,
            )

            raise RemoteA2AError(
                f"Could not resolve remote Agent Card: {exception}"
            ) from exception

        record.card = card
        record.connected = True
        record.error = None
        record.last_checked_at = datetime.now(
            timezone.utc,
        )

        return card

    @classmethod
    async def delegate(
        cls,
        record: RemoteAgentRecord,
        message: str,
        *,
        timeout_seconds: float,
    ) -> RemoteDelegationResponse:
        started = time.perf_counter()
        events: list[dict[str, Any]] = []

        if not record.enabled:
            raise RemoteA2AError(
                f"Remote agent '{record.name}' is disabled."
            )

        card = record.card

        if card is None:
            card = await cls.resolve_card(
                record,
            )

        config = ClientConfig(
            streaming=False,
        )

        client = await create_client(
            agent=card,
            client_config=config,
        )

        request = SendMessageRequest(
            message=new_text_message(
                message,
                role=Role.ROLE_USER,
            )
        )

        try:
            async with asyncio.timeout(
                timeout_seconds,
            ):
                async for chunk in client.send_message(
                    request,
                ):
                    events.append(
                        cls.protobuf_to_dict(
                            chunk,
                        )
                    )

        except TimeoutError as exception:
            raise RemoteA2AError(
                "Remote A2A delegation timed out."
            ) from exception

        except Exception as exception:
            raise RemoteA2AError(
                f"Remote A2A delegation failed: {exception}"
            ) from exception

        finally:
            await client.close()

        final_response = (
            events[-1]
            if events
            else None
        )

        return RemoteDelegationResponse(
            remote_agent=record.name,
            base_url=record.base_url,
            success=bool(
                events,
            ),
            final_response=final_response,
            events=events,
            event_count=len(
                events,
            ),
            execution_time_ms=round(
                (
                    time.perf_counter()
                    - started
                )
                * 1_000,
                2,
            ),
            error=None,
        )

    @staticmethod
    def protobuf_to_dict(
        value: Any,
    ) -> dict[str, Any]:
        descriptor = getattr(
            value,
            "DESCRIPTOR",
            None,
        )

        if descriptor is not None:
            return MessageToDict(
                value,
                preserving_proto_field_name=True,
            )

        model_dump = getattr(
            value,
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
                value,
            )
        }
