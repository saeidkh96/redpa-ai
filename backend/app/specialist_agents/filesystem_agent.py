from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from app.specialist_agents.runtime import (
    build_specialist_agent_card,
    create_specialist_application,
    run_specialist,
)

PROJECT_ROOT = Path(os.getenv("FILESYSTEM_AGENT_ROOT", "/app")).resolve()
ALLOWED_ROOTS = ((PROJECT_ROOT / "backend").resolve(), (PROJECT_ROOT / "docs").resolve())
BLOCKED_NAMES = {
    ".env", ".env.local", ".env.production",
    "id_rsa", "id_ed25519", "credentials.json", "secrets.json",
}


def _resolve_safe_path(value: str) -> Path:
    normalized = str(value or "").strip().replace("\\", "/")
    if normalized.startswith("/"):
        raise ValueError("Absolute paths are not allowed.")

    candidate = (PROJECT_ROOT / normalized).resolve()

    if candidate.name.casefold() in BLOCKED_NAMES:
        raise ValueError("The requested file is blocked.")

    if not any(candidate == allowed or allowed in candidate.parents for allowed in ALLOWED_ROOTS):
        raise ValueError("Path is outside the read-only sandbox.")

    return candidate


def _extract_path(request: str) -> str:
    match = re.search(
        r"\b(?:read|show|list|inspect)\s+(?:file|files|directory|folder)?\s*([A-Za-z0-9_./\\-]+)",
        request,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(1)

    fallback = re.search(
        r"\b(backend|docs)(?:/[A-Za-z0-9_.-]+)+",
        request,
        flags=re.IGNORECASE,
    )
    return fallback.group(0) if fallback else "backend"


async def handle_filesystem_request(request: str) -> dict[str, Any]:
    relative_path = _extract_path(request)
    target = _resolve_safe_path(relative_path)

    if not target.exists():
        raise FileNotFoundError(f"Path was not found: {relative_path}")

    if target.is_dir():
        entries = []
        for child in sorted(target.iterdir(), key=lambda item: (not item.is_dir(), item.name.casefold()))[:200]:
            entries.append({
                "name": child.name,
                "path": str(child.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "type": "directory" if child.is_dir() else "file",
            })
        return {
            "success": True,
            "operation": "list",
            "path": relative_path,
            "entries": entries,
            "count": len(entries),
            "read_only": True,
        }

    if target.stat().st_size > 200_000:
        raise ValueError("File is too large for the specialist response.")

    content = target.read_text(encoding="utf-8")
    return {
        "success": True,
        "operation": "read",
        "path": relative_path,
        "content": content[:20_000],
        "truncated": len(content) > 20_000,
        "read_only": True,
    }


CARD = build_specialist_agent_card(
    name="RedPA Filesystem Agent",
    description="A sandboxed read-only specialist for RedPA backend and documentation files.",
    public_url=os.getenv("FILESYSTEM_AGENT_PUBLIC_URL", "http://filesystem-agent:8064"),
    version="0.6.0",
    skill_id="filesystem_read",
    skill_name="Filesystem Read",
    skill_description="List or read safe RedPA project files.",
    tags=["filesystem", "files", "read", "backend", "docs"],
    examples=["List backend/app.", "Read backend/app/main.py."],
)

app = create_specialist_application(
    service_name="RedPA Filesystem Agent",
    version="0.6.0",
    card=CARD,
    handler=handle_filesystem_request,
    capabilities=["filesystem_read", "directory_listing"],
)


def main() -> None:
    run_specialist(
        module_path="app.specialist_agents.filesystem_agent:app",
        host_env="FILESYSTEM_AGENT_HOST",
        port_env="FILESYSTEM_AGENT_PORT",
        default_port=8064,
    )


if __name__ == "__main__":
    main()
