from __future__ import annotations

import os
from typing import Any

from mcp.server import MCPServer
from mcp.server.transport_security import (
    TransportSecuritySettings,
)

from app.mcp_servers.github_client import (
    GitHubAPIClient,
)


SERVER_HOST = os.getenv(
    "GITHUB_MCP_HOST",
    "0.0.0.0",
)

SERVER_PORT = int(
    os.getenv(
        "GITHUB_MCP_PORT",
        "8020",
    )
)

client = GitHubAPIClient(
    timeout_seconds=float(
        os.getenv(
            "GITHUB_MCP_TIMEOUT_SECONDS",
            "20",
        )
    )
)

mcp = MCPServer(
    "RedPA GitHub",
    instructions=(
        "Read-only access to public GitHub repository metadata, "
        "branches, commits, issues, and pull requests. "
        "No repository mutation operations are exposed."
    ),
)


TRANSPORT_SECURITY = TransportSecuritySettings(
    allowed_hosts=[
        "github-mcp",
        "github-mcp:*",
        "redpa-github-mcp",
        "redpa-github-mcp:*",
        "127.0.0.1",
        "127.0.0.1:*",
        "localhost",
        "localhost:*",
    ],
    allowed_origins=[],
)


@mcp.tool()
async def repository(
    repository: str,
) -> dict[str, Any]:
    """
    Return public metadata for a GitHub repository.

    Args:
        repository: GitHub repository in owner/name format.
    """

    payload = await client.get_repository(
        repository,
    )

    license_payload = payload.get(
        "license",
    )

    return {
        "repository": payload.get(
            "full_name",
        ),
        "description": payload.get(
            "description",
        ),
        "html_url": payload.get(
            "html_url",
        ),
        "homepage": payload.get(
            "homepage",
        ),
        "default_branch": payload.get(
            "default_branch",
        ),
        "language": payload.get(
            "language",
        ),
        "stars": payload.get(
            "stargazers_count",
            0,
        ),
        "forks": payload.get(
            "forks_count",
            0,
        ),
        "open_issues": payload.get(
            "open_issues_count",
            0,
        ),
        "archived": payload.get(
            "archived",
            False,
        ),
        "visibility": payload.get(
            "visibility",
        ),
        "license": (
            license_payload.get(
                "spdx_id",
            )
            if isinstance(
                license_payload,
                dict,
            )
            else None
        ),
        "created_at": payload.get(
            "created_at",
        ),
        "updated_at": payload.get(
            "updated_at",
        ),
        "pushed_at": payload.get(
            "pushed_at",
        ),
        "read_only": True,
    }


@mcp.tool()
async def branches(
    repository: str,
    limit: int = 20,
) -> dict[str, Any]:
    """
    List branches of a public GitHub repository.

    Args:
        repository: GitHub repository in owner/name format.
        limit: Maximum number of branches, from 1 to 100.
    """

    payload = await client.list_branches(
        repository,
        limit=limit,
    )

    items = [
        {
            "name": item.get(
                "name",
            ),
            "protected": item.get(
                "protected",
                False,
            ),
            "commit_sha": (
                item.get(
                    "commit",
                    {},
                ).get(
                    "sha",
                )
                if isinstance(
                    item.get(
                        "commit",
                    {},
                ),
                    dict,
                )
                else None
            ),
        }
        for item in payload
    ]

    return {
        "repository": repository,
        "branches": items,
        "count": len(
            items,
        ),
        "read_only": True,
    }


@mcp.tool()
async def commits(
    repository: str,
    branch: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """
    List recent commits of a public GitHub repository.

    Args:
        repository: GitHub repository in owner/name format.
        branch: Optional branch or Git reference.
        limit: Maximum number of commits, from 1 to 100.
    """

    payload = await client.list_commits(
        repository,
        branch=branch,
        limit=limit,
    )

    items: list[dict[str, Any]] = []

    for item in payload:
        commit_payload = item.get(
            "commit",
            {},
        )

        author_payload = (
            commit_payload.get(
                "author",
                {},
            )
            if isinstance(
                commit_payload,
                dict,
            )
            else {}
        )

        message = (
            commit_payload.get(
                "message",
                "",
            )
            if isinstance(
                commit_payload,
                dict,
            )
            else ""
        )

        items.append(
            {
                "sha": str(
                    item.get(
                        "sha",
                        "",
                    )
                )[:12],
                "message": str(
                    message,
                ).splitlines()[0],
                "author": (
                    author_payload.get(
                        "name",
                    )
                    if isinstance(
                        author_payload,
                        dict,
                    )
                    else None
                ),
                "date": (
                    author_payload.get(
                        "date",
                    )
                    if isinstance(
                        author_payload,
                        dict,
                    )
                    else None
                ),
                "html_url": item.get(
                    "html_url",
                ),
            }
        )

    return {
        "repository": repository,
        "branch": branch,
        "commits": items,
        "count": len(
            items,
        ),
        "read_only": True,
    }


@mcp.tool()
async def issues(
    repository: str,
    state: str = "open",
    limit: int = 20,
) -> dict[str, Any]:
    """
    List issues of a public GitHub repository.

    Pull requests are excluded from this tool.

    Args:
        repository: GitHub repository in owner/name format.
        state: open, closed, or all.
        limit: Maximum number of issues, from 1 to 100.
    """

    payload = await client.list_issues(
        repository,
        state=state,
        limit=limit,
    )

    items = [
        {
            "number": item.get(
                "number",
            ),
            "title": item.get(
                "title",
            ),
            "state": item.get(
                "state",
            ),
            "author": (
                item.get(
                    "user",
                    {},
                ).get(
                    "login",
                )
                if isinstance(
                    item.get(
                        "user",
                        {},
                    ),
                    dict,
                )
                else None
            ),
            "comments": item.get(
                "comments",
                0,
            ),
            "created_at": item.get(
                "created_at",
            ),
            "updated_at": item.get(
                "updated_at",
            ),
            "html_url": item.get(
                "html_url",
            ),
        }
        for item in payload
    ]

    return {
        "repository": repository,
        "state": state,
        "issues": items,
        "count": len(
            items,
        ),
        "read_only": True,
    }


@mcp.tool()
async def pull_requests(
    repository: str,
    state: str = "open",
    limit: int = 20,
) -> dict[str, Any]:
    """
    List pull requests of a public GitHub repository.

    Args:
        repository: GitHub repository in owner/name format.
        state: open, closed, or all.
        limit: Maximum number of pull requests, from 1 to 100.
    """

    payload = await client.list_pull_requests(
        repository,
        state=state,
        limit=limit,
    )

    items = [
        {
            "number": item.get(
                "number",
            ),
            "title": item.get(
                "title",
            ),
            "state": item.get(
                "state",
            ),
            "draft": item.get(
                "draft",
                False,
            ),
            "author": (
                item.get(
                    "user",
                    {},
                ).get(
                    "login",
                )
                if isinstance(
                    item.get(
                        "user",
                        {},
                    ),
                    dict,
                )
                else None
            ),
            "base_branch": (
                item.get(
                    "base",
                    {},
                ).get(
                    "ref",
                )
                if isinstance(
                    item.get(
                        "base",
                        {},
                    ),
                    dict,
                )
                else None
            ),
            "head_branch": (
                item.get(
                    "head",
                    {},
                ).get(
                    "ref",
                )
                if isinstance(
                    item.get(
                        "head",
                        {},
                    ),
                    dict,
                )
                else None
            ),
            "created_at": item.get(
                "created_at",
            ),
            "updated_at": item.get(
                "updated_at",
            ),
            "html_url": item.get(
                "html_url",
            ),
        }
        for item in payload
    ]

    return {
        "repository": repository,
        "state": state,
        "pull_requests": items,
        "count": len(
            items,
        ),
        "read_only": True,
    }


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host=SERVER_HOST,
        port=SERVER_PORT,
        streamable_http_path="/mcp",
        stateless_http=True,
        json_response=True,
        transport_security=TRANSPORT_SECURITY,
    )
