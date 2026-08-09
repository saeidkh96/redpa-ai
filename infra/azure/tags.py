from __future__ import annotations


def standard_tags(
    *,
    project: str,
    environment: str,
) -> dict[str, str]:
    return {
        "project": project,
        "environment": environment,
        "managed-by": "pulumi",
        "platform": "redpa-ai",
        "architecture-phase": "15",
    }
