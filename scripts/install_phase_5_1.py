from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTER_PATH = ROOT / "backend" / "app" / "api" / "v1" / "router.py"


def main() -> None:
    if not ROUTER_PATH.exists():
        raise SystemExit(
            f"Router file was not found: {ROUTER_PATH}"
        )

    text = ROUTER_PATH.read_text(
        encoding="utf-8",
    )

    import_line = "from app.api.v1.agents import router as agents_router\n"

    if import_line not in text:
        insert_at = text.find(
            "\n\n",
        )

        if insert_at == -1:
            text = import_line + text
        else:
            text = (
                text[:insert_at + 2]
                + import_line
                + text[insert_at + 2:]
            )

    include_line = "api_router.include_router(agents_router)\n"

    if include_line not in text:
        marker = "api_router = APIRouter()"

        marker_index = text.find(
            marker,
        )

        if marker_index == -1:
            raise SystemExit(
                "Could not find 'api_router = APIRouter()' in router.py."
            )

        line_end = text.find(
            "\n",
            marker_index,
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

    ROUTER_PATH.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "Phase 5.1 route installed successfully."
    )


if __name__ == "__main__":
    main()
