from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROUTER_PATH = (
    PROJECT_ROOT
    / "backend"
    / "app"
    / "api"
    / "v1"
    / "router.py"
)

IMPORT_LINE = (
    "from app.api.v1.unified_tools import "
    "router as unified_tools_router"
)

INCLUDE_BLOCK = """api_router.include_router(
    unified_tools_router,
)
"""


def main() -> None:
    if not ROUTER_PATH.exists():
        raise FileNotFoundError(
            f"Router file was not found: {ROUTER_PATH}"
        )

    content = ROUTER_PATH.read_text(
        encoding="utf-8",
    )

    changed = False

    if IMPORT_LINE not in content:
        lines = content.splitlines()

        insertion_index = 0

        for index, line in enumerate(lines):
            if line.startswith(
                "from app.api.v1."
            ):
                insertion_index = index + 1

        lines.insert(
            insertion_index,
            IMPORT_LINE,
        )

        content = "\n".join(lines) + "\n"
        changed = True

    if "unified_tools_router" not in _include_section(
        content,
    ):
        if not content.endswith("\n"):
            content += "\n"

        content += "\n" + INCLUDE_BLOCK
        changed = True

    if changed:
        ROUTER_PATH.write_text(
            content,
            encoding="utf-8",
        )
        print(
            f"Updated {ROUTER_PATH}"
        )
    else:
        print(
            "Router integration is already present."
        )


def _include_section(
    content: str,
) -> str:
    marker = "api_router = APIRouter()"

    marker_index = content.find(
        marker,
    )

    if marker_index == -1:
        return content

    return content[
        marker_index:
    ]


if __name__ == "__main__":
    main()
