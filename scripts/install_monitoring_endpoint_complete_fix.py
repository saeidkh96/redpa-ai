from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "backend/app/api/v1/router.py"


def main() -> None:
    text = ROUTER.read_text(
        encoding="utf-8",
    )

    import_line = (
        "from app.api.v1.monitoring import "
        "router as monitoring_router\n"
    )

    include_block = (
        "api_router.include_router(\n"
        "    monitoring_router,\n"
        ")\n"
    )

    if import_line not in text:
        anchor = (
            "from app.api.v1.llm import "
            "router as llm_router\n"
        )

        if anchor in text:
            text = text.replace(
                anchor,
                anchor + import_line,
                1,
            )
        else:
            text = import_line + text

    if include_block not in text:
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
            + include_block
            + text[line_end + 1:]
        )

    ROUTER.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "Monitoring endpoint and router registration installed."
    )


if __name__ == "__main__":
    main()
