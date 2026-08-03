from __future__ import annotations

import os
import re
from typing import Any

import httpx

from app.specialist_agents.runtime import (
    build_specialist_agent_card,
    create_specialist_application,
    run_specialist,
)


def _extract_repository(request: str) -> str:
    match = re.search(r"(?<![\w-])([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", request)
    if match is None:
        raise ValueError("A GitHub repository in owner/name format is required.")
    return match.group(1)


async def handle_github_request(request: str) -> dict[str, Any]:
    repository = _extract_repository(request)
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "redpa-github-agent",
    }
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers) as client:
        response = await client.get(f"https://api.github.com/repos/{repository}")
        response.raise_for_status()
        payload = response.json()

    return {
        "success": True,
        "repository": payload.get("full_name"),
        "description": payload.get("description"),
        "html_url": payload.get("html_url"),
        "default_branch": payload.get("default_branch"),
        "language": payload.get("language"),
        "stars": payload.get("stargazers_count"),
        "forks": payload.get("forks_count"),
        "open_issues": payload.get("open_issues_count"),
        "archived": payload.get("archived"),
        "visibility": payload.get("visibility"),
        "read_only": True,
    }


CARD = build_specialist_agent_card(
    name="RedPA GitHub Agent",
    description="A read-only remote specialist for public GitHub repository inspection.",
    public_url=os.getenv("GITHUB_AGENT_PUBLIC_URL", "http://github-agent:8065"),
    version="0.6.0",
    skill_id="github_repository",
    skill_name="GitHub Repository",
    skill_description="Inspect metadata for a public GitHub repository.",
    tags=["github", "repository", "commits", "issues", "source-code"],
    examples=["Show repository langchain-ai/langgraph.", "Inspect saeidkh96/redpa-ai."],
)

app = create_specialist_application(
    service_name="RedPA GitHub Agent",
    version="0.6.0",
    card=CARD,
    handler=handle_github_request,
    capabilities=["github_repository", "public_repository_metadata"],
)


def main() -> None:
    run_specialist(
        module_path="app.specialist_agents.github_agent:app",
        host_env="GITHUB_AGENT_HOST",
        port_env="GITHUB_AGENT_PORT",
        default_port=8065,
    )


if __name__ == "__main__":
    main()
