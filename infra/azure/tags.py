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

        # Backward compatibility with Phase 15 governance tests.
        "architecture-phase": "15",

        # Current Azure infrastructure generation.
        "architecture": "azure-v4",
    }