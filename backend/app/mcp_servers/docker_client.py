from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import httpx

from app.mcp_servers.docker_security import (
    normalize_log_tail,
    validate_container_reference,
)


class DockerMCPError(RuntimeError):
    """Raised when the Docker Engine API cannot complete a request."""


class ReadOnlyDockerClient:
    """
    Read-only Docker Engine API client over a Unix-domain socket.

    The client exposes only GET requests and does not include generic
    request methods for mutation endpoints.
    """

    def __init__(
        self,
        *,
        socket_path: str | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        self.socket_path = (
            socket_path
            or os.getenv(
                "DOCKER_SOCKET_PATH",
                "/var/run/docker.sock",
            )
        )

        self.timeout_seconds = max(
            1.0,
            min(
                float(timeout_seconds),
                60.0,
            ),
        )

    async def list_containers(
        self,
        *,
        all_containers: bool = True,
    ) -> list[dict[str, Any]]:
        payload = await self._get_json(
            "/containers/json",
            params={
                "all": (
                    "1"
                    if all_containers
                    else "0"
                ),
            },
        )

        if not isinstance(
            payload,
            list,
        ):
            raise DockerMCPError(
                "Docker returned an unexpected containers response."
            )

        return [
            self._format_container_summary(
                item,
            )
            for item in payload
            if isinstance(
                item,
                dict,
            )
        ]

    async def inspect_container(
        self,
        container: str,
    ) -> dict[str, Any]:
        reference = validate_container_reference(
            container,
        )

        payload = await self._get_json(
            "/containers/"
            + quote(
                reference,
                safe="",
            )
            + "/json",
        )

        if not isinstance(
            payload,
            dict,
        ):
            raise DockerMCPError(
                "Docker returned an unexpected inspect response."
            )

        state = payload.get(
            "State",
            {},
        )

        config = payload.get(
            "Config",
            {},
        )

        network_settings = payload.get(
            "NetworkSettings",
            {},
        )

        host_config = payload.get(
            "HostConfig",
            {},
        )

        return {
            "id": str(
                payload.get(
                    "Id",
                    "",
                )
            )[:12],
            "name": str(
                payload.get(
                    "Name",
                    "",
                )
            ).removeprefix(
                "/",
            ),
            "image": (
                config.get(
                    "Image",
                )
                if isinstance(
                    config,
                    dict,
                )
                else None
            ),
            "created": payload.get(
                "Created",
            ),
            "platform": payload.get(
                "Platform",
            ),
            "state": {
                "status": (
                    state.get(
                        "Status",
                    )
                    if isinstance(
                        state,
                        dict,
                    )
                    else None
                ),
                "running": (
                    state.get(
                        "Running",
                        False,
                    )
                    if isinstance(
                        state,
                        dict,
                    )
                    else False
                ),
                "paused": (
                    state.get(
                        "Paused",
                        False,
                    )
                    if isinstance(
                        state,
                        dict,
                    )
                    else False
                ),
                "restarting": (
                    state.get(
                        "Restarting",
                        False,
                    )
                    if isinstance(
                        state,
                        dict,
                    )
                    else False
                ),
                "exit_code": (
                    state.get(
                        "ExitCode",
                    )
                    if isinstance(
                        state,
                        dict,
                    )
                    else None
                ),
                "started_at": (
                    state.get(
                        "StartedAt",
                    )
                    if isinstance(
                        state,
                        dict,
                    )
                    else None
                ),
                "finished_at": (
                    state.get(
                        "FinishedAt",
                    )
                    if isinstance(
                        state,
                        dict,
                    )
                    else None
                ),
                "health": (
                    state.get(
                        "Health",
                        {},
                    ).get(
                        "Status",
                    )
                    if (
                        isinstance(
                            state,
                            dict,
                        )
                        and isinstance(
                            state.get(
                                "Health",
                                {},
                            ),
                            dict,
                        )
                    )
                    else None
                ),
            },
            "restart_policy": (
                host_config.get(
                    "RestartPolicy",
                    {},
                ).get(
                    "Name",
                )
                if (
                    isinstance(
                        host_config,
                        dict,
                    )
                    and isinstance(
                        host_config.get(
                            "RestartPolicy",
                            {},
                        ),
                        dict,
                    )
                )
                else None
            ),
            "ports": self._format_ports(
                network_settings.get(
                    "Ports",
                    {},
                )
                if isinstance(
                    network_settings,
                    dict,
                )
                else {}
            ),
            "networks": sorted(
                (
                    network_settings.get(
                        "Networks",
                        {},
                    )
                    if isinstance(
                        network_settings,
                        dict,
                    )
                    else {}
                ).keys()
            ),
            "labels": (
                config.get(
                    "Labels",
                    {},
                )
                if isinstance(
                    config,
                    dict,
                )
                else {}
            ),
            "read_only": True,
        }

    async def container_logs(
        self,
        container: str,
        *,
        tail: int = 100,
        timestamps: bool = True,
    ) -> dict[str, Any]:
        reference = validate_container_reference(
            container,
        )

        normalized_tail = normalize_log_tail(
            tail,
        )

        response = await self._get_response(
            "/containers/"
            + quote(
                reference,
                safe="",
            )
            + "/logs",
            params={
                "stdout": "1",
                "stderr": "1",
                "timestamps": (
                    "1"
                    if timestamps
                    else "0"
                ),
                "tail": str(
                    normalized_tail,
                ),
            },
        )

        content_type = response.headers.get(
            "content-type",
            "",
        ).casefold()

        raw_content = response.content

        if "application/vnd.docker.raw-stream" in content_type:
            raw_content = self._decode_multiplexed_stream(
                raw_content,
            )

        text = raw_content.decode(
            "utf-8",
            errors="replace",
        )

        lines = text.splitlines()

        return {
            "container": reference,
            "tail": normalized_tail,
            "timestamps": timestamps,
            "logs": lines,
            "line_count": len(
                lines,
            ),
            "read_only": True,
        }

    async def list_images(
        self,
        *,
        all_images: bool = False,
    ) -> list[dict[str, Any]]:
        payload = await self._get_json(
            "/images/json",
            params={
                "all": (
                    "1"
                    if all_images
                    else "0"
                ),
            },
        )

        if not isinstance(
            payload,
            list,
        ):
            raise DockerMCPError(
                "Docker returned an unexpected images response."
            )

        images: list[dict[str, Any]] = []

        for item in payload:
            if not isinstance(
                item,
                dict,
            ):
                continue

            created = item.get(
                "Created",
            )

            images.append(
                {
                    "id": str(
                        item.get(
                            "Id",
                            "",
                        )
                    ).removeprefix(
                        "sha256:",
                    )[:12],
                    "repository_tags": (
                        item.get(
                            "RepoTags",
                        )
                        or []
                    ),
                    "repository_digests": (
                        item.get(
                            "RepoDigests",
                        )
                        or []
                    ),
                    "size_bytes": item.get(
                        "Size",
                        0,
                    ),
                    "created_at": (
                        datetime.fromtimestamp(
                            int(
                                created,
                            ),
                            tz=timezone.utc,
                        ).isoformat()
                        if isinstance(
                            created,
                            (
                                int,
                                float,
                            ),
                        )
                        else None
                    ),
                    "labels": item.get(
                        "Labels",
                    )
                    or {},
                    "read_only": True,
                }
            )

        return images

    async def system_info(
        self,
    ) -> dict[str, Any]:
        payload = await self._get_json(
            "/info",
        )

        if not isinstance(
            payload,
            dict,
        ):
            raise DockerMCPError(
                "Docker returned an unexpected system-info response."
            )

        return {
            "name": payload.get(
                "Name",
            ),
            "server_version": payload.get(
                "ServerVersion",
            ),
            "operating_system": payload.get(
                "OperatingSystem",
            ),
            "os_type": payload.get(
                "OSType",
            ),
            "architecture": payload.get(
                "Architecture",
            ),
            "cpus": payload.get(
                "NCPU",
                0,
            ),
            "memory_bytes": payload.get(
                "MemTotal",
                0,
            ),
            "containers": payload.get(
                "Containers",
                0,
            ),
            "containers_running": payload.get(
                "ContainersRunning",
                0,
            ),
            "containers_paused": payload.get(
                "ContainersPaused",
                0,
            ),
            "containers_stopped": payload.get(
                "ContainersStopped",
                0,
            ),
            "images": payload.get(
                "Images",
                0,
            ),
            "docker_root_dir": payload.get(
                "DockerRootDir",
            ),
            "driver": payload.get(
                "Driver",
            ),
            "read_only": True,
        }

    async def _get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        response = await self._get_response(
            path,
            params=params,
        )

        try:
            return response.json()
        except json.JSONDecodeError as exception:
            raise DockerMCPError(
                "Docker Engine returned invalid JSON."
            ) from exception

    async def _get_response(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        transport = httpx.AsyncHTTPTransport(
            uds=self.socket_path,
        )

        try:
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://docker",
                timeout=httpx.Timeout(
                    self.timeout_seconds,
                ),
            ) as client:
                response = await client.get(
                    path,
                    params=params,
                )

        except httpx.TimeoutException as exception:
            raise DockerMCPError(
                "Docker Engine request timed out."
            ) from exception

        except httpx.HTTPError as exception:
            raise DockerMCPError(
                f"Could not connect to Docker Engine: {exception}"
            ) from exception

        if response.status_code == 404:
            raise DockerMCPError(
                "Docker container or resource was not found."
            )

        if response.status_code >= 400:
            detail = response.text.strip()

            raise DockerMCPError(
                f"Docker Engine returned HTTP "
                f"{response.status_code}: "
                f"{detail[:500] or 'Unknown Docker error.'}"
            )

        return response

    @staticmethod
    def _format_container_summary(
        item: dict[str, Any],
    ) -> dict[str, Any]:
        names = [
            str(
                name,
            ).removeprefix(
                "/",
            )
            for name in (
                item.get(
                    "Names",
                )
                or []
            )
        ]

        return {
            "id": str(
                item.get(
                    "Id",
                    "",
                )
            )[:12],
            "names": names,
            "image": item.get(
                "Image",
            ),
            "image_id": str(
                item.get(
                    "ImageID",
                    "",
                )
            ).removeprefix(
                "sha256:",
            )[:12],
            "command": item.get(
                "Command",
            ),
            "created": item.get(
                "Created",
            ),
            "state": item.get(
                "State",
            ),
            "status": item.get(
                "Status",
            ),
            "ports": item.get(
                "Ports",
            )
            or [],
            "labels": item.get(
                "Labels",
            )
            or {},
            "read_only": True,
        }

    @staticmethod
    def _format_ports(
        raw_ports: Any,
    ) -> list[dict[str, Any]]:
        if not isinstance(
            raw_ports,
            dict,
        ):
            return []

        ports: list[dict[str, Any]] = []

        for container_port, bindings in raw_ports.items():
            if not bindings:
                ports.append(
                    {
                        "container_port": container_port,
                        "host_ip": None,
                        "host_port": None,
                    }
                )
                continue

            if not isinstance(
                bindings,
                list,
            ):
                continue

            for binding in bindings:
                if not isinstance(
                    binding,
                    dict,
                ):
                    continue

                ports.append(
                    {
                        "container_port": container_port,
                        "host_ip": binding.get(
                            "HostIp",
                        ),
                        "host_port": binding.get(
                            "HostPort",
                        ),
                    }
                )

        return ports

    @staticmethod
    def _decode_multiplexed_stream(
        payload: bytes,
    ) -> bytes:
        output = bytearray()
        index = 0

        while index + 8 <= len(
            payload,
        ):
            frame_size = int.from_bytes(
                payload[
                    index + 4:
                    index + 8
                ],
                byteorder="big",
            )

            frame_start = index + 8
            frame_end = frame_start + frame_size

            if frame_end > len(
                payload,
            ):
                return payload

            output.extend(
                payload[
                    frame_start:
                    frame_end
                ]
            )

            index = frame_end

        return (
            bytes(
                output,
            )
            if output
            else payload
        )
