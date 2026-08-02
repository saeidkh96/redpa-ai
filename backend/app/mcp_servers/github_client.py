from __future__ import annotations

import os
import re
from typing import Any

import httpx


class GitHubMCPError(RuntimeError):
    """Raised when the GitHub API cannot complete a request."""


REPOSITORY_PATTERN = re.compile(
    r"^[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}$"
)


class GitHubAPIClient:
    """Small read-only GitHub REST API client."""

    def __init__(
        self,
        *,
        token: str | None = None,
        timeout_seconds: float = 20.0,
    ) -> None:
        self.token = (
            token
            if token is not None
            else os.getenv(
                "GITHUB_TOKEN",
                "",
            ).strip()
        )

        self.timeout_seconds = max(
            1.0,
            min(
                float(timeout_seconds),
                60.0,
            ),
        )

    async def get_repository(
        self,
        repository: str,
    ) -> dict[str, Any]:
        owner, name = self.parse_repository(
            repository,
        )

        return await self._get_json(
            f"/repos/{owner}/{name}",
        )

    async def list_branches(
        self,
        repository: str,
        *,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        owner, name = self.parse_repository(
            repository,
        )

        payload = await self._get_json(
            f"/repos/{owner}/{name}/branches",
            params={
                "per_page": self._normalize_limit(
                    limit,
                    maximum=100,
                ),
            },
        )

        return self._require_list(
            payload,
        )

    async def list_commits(
        self,
        repository: str,
        *,
        branch: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        owner, name = self.parse_repository(
            repository,
        )

        params: dict[str, Any] = {
            "per_page": self._normalize_limit(
                limit,
                maximum=100,
            ),
        }

        if branch:
            params["sha"] = branch.strip()

        payload = await self._get_json(
            f"/repos/{owner}/{name}/commits",
            params=params,
        )

        return self._require_list(
            payload,
        )

    async def list_issues(
        self,
        repository: str,
        *,
        state: str = "open",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        owner, name = self.parse_repository(
            repository,
        )

        normalized_state = state.casefold().strip()

        if normalized_state not in {
            "open",
            "closed",
            "all",
        }:
            raise ValueError(
                "Issue state must be open, closed, or all."
            )

        payload = await self._get_json(
            f"/repos/{owner}/{name}/issues",
            params={
                "state": normalized_state,
                "per_page": self._normalize_limit(
                    limit,
                    maximum=100,
                ),
            },
        )

        issues = self._require_list(
            payload,
        )

        return [
            item
            for item in issues
            if "pull_request" not in item
        ]

    async def list_pull_requests(
        self,
        repository: str,
        *,
        state: str = "open",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        owner, name = self.parse_repository(
            repository,
        )

        normalized_state = state.casefold().strip()

        if normalized_state not in {
            "open",
            "closed",
            "all",
        }:
            raise ValueError(
                "Pull-request state must be open, closed, or all."
            )

        payload = await self._get_json(
            f"/repos/{owner}/{name}/pulls",
            params={
                "state": normalized_state,
                "per_page": self._normalize_limit(
                    limit,
                    maximum=100,
                ),
            },
        )

        return self._require_list(
            payload,
        )

    async def _get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "redpa-github-mcp/1.0",
        }

        if self.token:
            headers["Authorization"] = (
                f"Bearer {self.token}"
            )

        try:
            async with httpx.AsyncClient(
                base_url="https://api.github.com",
                headers=headers,
                timeout=httpx.Timeout(
                    self.timeout_seconds,
                ),
                follow_redirects=True,
            ) as client:
                response = await client.get(
                    path,
                    params=params,
                )

        except httpx.TimeoutException as exception:
            raise GitHubMCPError(
                "GitHub API request timed out."
            ) from exception

        except httpx.HTTPError as exception:
            raise GitHubMCPError(
                f"GitHub API connection failed: {exception}"
            ) from exception

        if response.status_code == 404:
            raise GitHubMCPError(
                "GitHub repository or resource was not found."
            )

        if response.status_code == 403:
            remaining = response.headers.get(
                "X-RateLimit-Remaining",
                "unknown",
            )

            raise GitHubMCPError(
                "GitHub API rejected the request. "
                f"Remaining rate limit: {remaining}."
            )

        if response.status_code >= 400:
            detail = self._extract_error_detail(
                response,
            )

            raise GitHubMCPError(
                f"GitHub API returned HTTP "
                f"{response.status_code}: {detail}"
            )

        try:
            return response.json()
        except ValueError as exception:
            raise GitHubMCPError(
                "GitHub API returned invalid JSON."
            ) from exception

    @staticmethod
    def parse_repository(
        repository: str,
    ) -> tuple[str, str]:
        normalized = str(
            repository
            or "",
        ).strip()

        normalized = normalized.removeprefix(
            "https://github.com/",
        ).removesuffix(
            "/",
        )

        if not REPOSITORY_PATTERN.fullmatch(
            normalized,
        ):
            raise ValueError(
                "Repository must use the owner/name format."
            )

        owner, name = normalized.split(
            "/",
            1,
        )

        return (
            owner,
            name,
        )

    @staticmethod
    def _normalize_limit(
        value: int,
        *,
        maximum: int,
    ) -> int:
        return max(
            1,
            min(
                int(value),
                maximum,
            ),
        )

    @staticmethod
    def _require_list(
        payload: Any,
    ) -> list[dict[str, Any]]:
        if not isinstance(
            payload,
            list,
        ):
            raise GitHubMCPError(
                "GitHub API returned an unexpected response."
            )

        return [
            item
            for item in payload
            if isinstance(
                item,
                dict,
            )
        ]

    @staticmethod
    def _extract_error_detail(
        response: httpx.Response,
    ) -> str:
        try:
            payload = response.json()
        except ValueError:
            return (
                response.text.strip()
                or "Unknown GitHub API error."
            )[:500]

        if isinstance(
            payload,
            dict,
        ):
            message = payload.get(
                "message",
            )

            if message:
                return str(
                    message,
                )[:500]

        return "Unknown GitHub API error."
