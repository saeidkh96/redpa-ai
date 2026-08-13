from __future__ import annotations

import asyncio
import os
import re
from typing import Any

import docker
from docker.errors import (
    DockerException,
    NotFound,
)

from app.specialist_agents.runtime import (
    build_specialist_agent_card,
    create_specialist_application,
    run_specialist,
)


SAFE_CONTAINER_REFERENCE = re.compile(
    r"^[A-Za-z0-9_.-]{1,128}$"
)

LIST_CONTAINER_PATTERNS = (
    r"\bshow\s+(?:docker\s+)?containers?\b",
    r"\blist\s+(?:docker\s+)?containers?\b",
    r"\brunning\s+containers?\b",
    r"\bdocker\s+ps\b",
    r"\bcontainer\s+list\b",
)

LIST_IMAGE_PATTERNS = (
    r"\bshow\s+(?:docker\s+)?images?\b",
    r"\blist\s+(?:docker\s+)?images?\b",
    r"\bdocker\s+images\b",
    r"\bimage\s+list\b",
)

LOG_PATTERNS = (
    r"\blogs?\s+(?:for|of)\s+([A-Za-z0-9_.-]+)",
    r"\bshow\s+logs?\s+(?:for|of)\s+([A-Za-z0-9_.-]+)",
    r"\bcontainer\s+logs?\s+([A-Za-z0-9_.-]+)",
)

INSPECT_PATTERNS = (
    r"\binspect\s+(?:docker\s+)?container\s+([A-Za-z0-9_.-]+)",
    r"\binspect\s+([A-Za-z0-9_.-]+)",
    r"\bcontainer\s+([A-Za-z0-9_.-]+)\s+(?:details?|info|status)\b",
)


def _matches_any(
    request: str,
    patterns: tuple[str, ...],
) -> bool:
    return any(
        re.search(
            pattern,
            request,
            flags=re.IGNORECASE,
        )
        is not None
        for pattern in patterns
    )


def _validate_container_reference(
    value: str,
) -> str:
    normalized = str(
        value
        or "",
    ).strip()

    if not SAFE_CONTAINER_REFERENCE.fullmatch(
        normalized,
    ):
        raise ValueError(
            "Unsafe Docker container reference."
        )

    return normalized


def _extract_with_patterns(
    request: str,
    patterns: tuple[str, ...],
) -> str | None:
    for pattern in patterns:
        match = re.search(
            pattern,
            request,
            flags=re.IGNORECASE,
        )

        if match is not None:
            return _validate_container_reference(
                match.group(1),
            )

    return None


def _list_containers_sync() -> dict[str, Any]:
    client = docker.from_env()

    try:
        containers = client.containers.list(
            all=True,
        )

        return {
            "success": True,
            "operation": "list_containers",
            "containers": [
                {
                    "id": container.short_id,
                    "name": container.name,
                    "status": container.status,
                    "image": (
                        container.attrs.get(
                            "Config",
                            {},
                        ).get(
                            "Image",
                        )
                        or container.attrs.get(
                            "Image",
                        )
                        or "unknown"
                    ),
                }
                for container in containers[:100]
            ],
            "count": min(
                len(
                    containers,
                ),
                100,
            ),
            "read_only": True,
        }

    finally:
        client.close()


def _list_images_sync() -> dict[str, Any]:
    client = docker.from_env()

    try:
        images = client.images.list()

        return {
            "success": True,
            "operation": "list_images",
            "images": [
                {
                    "id": image.short_id,
                    "tags": image.tags,
                }
                for image in images[:100]
            ],
            "count": min(
                len(
                    images,
                ),
                100,
            ),
            "read_only": True,
        }

    finally:
        client.close()


def _inspect_container_sync(
    container_name: str,
) -> dict[str, Any]:
    client = docker.from_env()

    try:
        container = client.containers.get(
            container_name,
        )

        attrs = container.attrs

        return {
            "success": True,
            "operation": "inspect_container",
            "container": container.name,
            "id": container.short_id,
            "status": container.status,
            "image": attrs.get(
                "Config",
                {},
            ).get(
                "Image",
            ),
            "created": attrs.get(
                "Created",
            ),
            "ports": attrs.get(
                "NetworkSettings",
                {},
            ).get(
                "Ports",
            ),
            "read_only": True,
        }

    finally:
        client.close()


def _container_logs_sync(
    container_name: str,
) -> dict[str, Any]:
    client = docker.from_env()

    try:
        container = client.containers.get(
            container_name,
        )

        logs = container.logs(
            tail=100,
            timestamps=True,
        ).decode(
            "utf-8",
            errors="replace",
        )

        return {
            "success": True,
            "operation": "container_logs",
            "container": container.name,
            "logs": logs,
            "read_only": True,
        }

    finally:
        client.close()


async def handle_docker_request(
    request: str,
) -> dict[str, Any]:
    normalized = str(
        request
        or "",
    ).strip()

    try:
        if _matches_any(
            normalized,
            LIST_CONTAINER_PATTERNS,
        ):
            return await asyncio.to_thread(
                _list_containers_sync,
            )

        if _matches_any(
            normalized,
            LIST_IMAGE_PATTERNS,
        ):
            return await asyncio.to_thread(
                _list_images_sync,
            )

        log_target = _extract_with_patterns(
            normalized,
            LOG_PATTERNS,
        )

        if log_target is not None:
            return await asyncio.to_thread(
                _container_logs_sync,
                log_target,
            )

        inspect_target = _extract_with_patterns(
            normalized,
            INSPECT_PATTERNS,
        )

        if inspect_target is not None:
            return await asyncio.to_thread(
                _inspect_container_sync,
                inspect_target,
            )

        return {
            "success": False,
            "request": normalized,
            "error": (
                "Docker request was not recognized. "
                "Use list containers, list images, "
                "inspect container <name>, or logs for <name>."
            ),
        }

    except NotFound as exception:
        raise ValueError(
            "Docker container or resource was not found."
        ) from exception

    except DockerException as exception:
        raise RuntimeError(
            f"Docker Engine communication failed: {exception}"
        ) from exception


PUBLIC_URL = os.getenv(
    "DOCKER_AGENT_PUBLIC_URL",
    "http://docker-agent:8063",
)

CARD = build_specialist_agent_card(
    name="RedPA Docker Agent",
    description=(
        "A read-only remote specialist for Docker container "
        "inspection, logs, images, and container listing."
    ),
    public_url=PUBLIC_URL,
    version="0.6.1",
    skill_id="docker_inspection",
    skill_name="Docker Inspection",
    skill_description=(
        "List containers, inspect safe metadata, read logs, "
        "and list images."
    ),
    tags=[
        "docker",
        "containers",
        "logs",
        "images",
        "infrastructure",
    ],
    examples=[
        "Show Docker containers.",
        "List running containers.",
        "Inspect container redpa-backend.",
        "Show logs for redpa-backend.",
        "List Docker images.",
    ],
)

app = create_specialist_application(
    service_name="RedPA Docker Agent",
    version="0.6.1",
    card=CARD,
    handler=handle_docker_request,
    capabilities=[
        "docker_inspection",
        "container_listing",
        "container_logs",
        "image_listing",
    ],
)


def main() -> None:
    run_specialist(
        module_path=(
            "app.specialist_agents.docker_agent:app"
        ),
        host_env="DOCKER_AGENT_HOST",
        port_env="DOCKER_AGENT_PORT",
        default_port=8063,
    )


if __name__ == "__main__":
    main()
