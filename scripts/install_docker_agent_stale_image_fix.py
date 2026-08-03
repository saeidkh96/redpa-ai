from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = (
    ROOT
    / "backend"
    / "app"
    / "specialist_agents"
    / "docker_agent.py"
)


OLD_BLOCK = """                {
                    "id": container.short_id,
                    "name": container.name,
                    "status": container.status,
                    "image": (
                        container.image.tags[0]
                        if container.image.tags
                        else container.image.short_id
                    ),
                }
"""

NEW_BLOCK = """                {
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
"""


def main() -> None:
    text = TARGET.read_text(
        encoding="utf-8",
    )

    if NEW_BLOCK in text:
        print(
            "Docker stale-image fix is already installed."
        )
        return

    if OLD_BLOCK not in text:
        raise SystemExit(
            "Could not find the Docker container image block."
        )

    text = text.replace(
        OLD_BLOCK,
        NEW_BLOCK,
        1,
    )

    TARGET.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "Docker stale-image fix installed."
    )


if __name__ == "__main__":
    main()
