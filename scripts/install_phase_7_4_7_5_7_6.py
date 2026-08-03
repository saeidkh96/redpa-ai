from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "backend/app/api/v1/router.py"


def main() -> None:
    text = ROUTER.read_text(
        encoding="utf-8",
    )

    imports = [
        (
            "from app.api.v1.agent_memory_admin "
            "import router as agent_memory_admin_router\n"
        ),
        (
            "from app.agent_memory.dashboard "
            "import router as agent_memory_dashboard_router\n"
        ),
    ]

    includes = [
        (
            "api_router.include_router("
            "agent_memory_admin_router"
            ")\n"
        ),
        (
            "api_router.include_router("
            "agent_memory_dashboard_router"
            ")\n"
        ),
    ]

    for import_line in imports:
        if import_line not in text:
            text = import_line + text

    marker = "api_router = APIRouter()"
    index = text.find(marker)

    if index == -1:
        raise SystemExit(
            "Could not find api_router = APIRouter()."
        )

    line_end = text.find("\n", index)

    if line_end == -1:
        line_end = len(text)

    insertion = ""

    for include_line in includes:
        if include_line not in text:
            insertion += include_line

    if insertion:
        text = (
            text[:line_end + 1]
            + insertion
            + text[line_end + 1:]
        )

    ROUTER.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "Phase 7.4 + 7.5 + 7.6 installed."
    )


if __name__ == "__main__":
    main()
