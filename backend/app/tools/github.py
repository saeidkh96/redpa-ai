from __future__ import annotations

import os
import re
from time import perf_counter
from typing import Any

from app.tools.http_base import BaseHTTPTool
from app.tools.schemas import ToolExecutionResult, ToolMetadata


REPOSITORY_PATTERN = re.compile(
    r"^[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}$"
)


class GitHubTool(BaseHTTPTool):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="github",
            description=(
                "Returns public metadata for a GitHub repository."
            ),
            version="1.0.0",
            requires_approval=False,
        )

    async def execute(
        self,
        arguments: dict[str, Any],
    ) -> ToolExecutionResult:
        started_at = perf_counter()

        try:
            repository = self.required_string(
                arguments,
                "repository",
                max_length=201,
            )

            repository = repository.removeprefix(
                "https://github.com/"
            ).strip("/")

            if not REPOSITORY_PATTERN.fullmatch(repository):
                raise ValueError(
                    "'repository' must use the owner/name format."
                )

            headers = {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }

            token = os.getenv("GITHUB_TOKEN", "").strip()
            if token:
                headers["Authorization"] = f"Bearer {token}"

            response = await self.http_client.get_json(
                url=f"https://api.github.com/repos/{repository}",
                headers=headers,
                allowed_hosts={"api.github.com"},
            )

            if not isinstance(response.data, dict):
                raise ValueError(
                    "GitHub returned an invalid repository response."
                )

            data = response.data

            result = {
                "full_name": data.get("full_name"),
                "description": data.get("description"),
                "html_url": data.get("html_url"),
                "default_branch": data.get("default_branch"),
                "language": data.get("language"),
                "topics": data.get("topics", []),
                "stars": data.get("stargazers_count"),
                "forks": data.get("forks_count"),
                "open_issues": data.get("open_issues_count"),
                "watchers": data.get("subscribers_count"),
                "is_private": data.get("private"),
                "is_archived": data.get("archived"),
                "license": (
                    data.get("license", {}).get("spdx_id")
                    if isinstance(data.get("license"), dict)
                    else None
                ),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
                "pushed_at": data.get("pushed_at"),
                "provider": "GitHub",
            }

            return ToolExecutionResult(
                tool_name=self.metadata.name,
                success=True,
                result=result,
                error=None,
                execution_time_ms=self._elapsed_ms(started_at),
                metadata={
                    "provider": "github",
                    "authenticated": bool(token),
                },
            )

        except Exception as exception:
            return ToolExecutionResult(
                tool_name=self.metadata.name,
                success=False,
                result=None,
                error=f"{type(exception).__name__}: {exception}"[:1000],
                execution_time_ms=self._elapsed_ms(started_at),
                metadata={
                    "error_type": type(exception).__name__,
                },
            )

    @staticmethod
    def _elapsed_ms(started_at: float) -> float:
        return round((perf_counter() - started_at) * 1000, 2)
