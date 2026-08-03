from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "backend/app/api/v1/router.py"


def main() -> None:
    text = ROUTER.read_text(
        encoding="utf-8",
    )

    import_line = (
        "from app.api.v1.durable_workflows "
        "import router as durable_workflows_router\n"
    )

    include_line = (
        "api_router.include_router("
        "durable_workflows_router"
        ")\n"
    )

    if import_line not in text:
        text = (
            import_line
            + text
        )

    if include_line not in text:
        marker = "api_router = APIRouter()"
        index = text.find(
            marker,
        )

        if index == -1:
            raise SystemExit(
                "Could not find api_router = APIRouter()."
            )

        line_end = text.find(
            "\n",
            index,
        )

        if line_end == -1:
            line_end = len(
                text,
            )

        text = (
            text[:line_end + 1]
            + include_line
            + text[line_end + 1:]
        )

    ROUTER.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "Phase 6.6 durable workflow routes installed."
    )


if __name__ == "__main__":
    main()
