from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "backend/app/main.py"


def main() -> None:
    text = MAIN.read_text(
        encoding="utf-8",
    )

    import_line = (
        "from app.core.application_setup import "
        "configure_application_runtime\n"
    )

    if import_line not in text:
        anchor = (
            "from app.core.config import settings\n"
        )

        if anchor in text:
            text = text.replace(
                anchor,
                anchor + import_line,
                1,
            )
        else:
            text = import_line + text

    call = (
        "\n    configure_application_runtime("
        "application"
        ")\n"
    )

    if (
        "configure_application_runtime("
        "application"
        ")"
        not in text
    ):
        marker = (
            "    application.include_router("
        )

        index = text.find(
            marker,
        )

        if index == -1:
            marker = (
                "    return application"
            )

            index = text.find(
                marker,
            )

            if index == -1:
                raise SystemExit(
                    "Could not locate create_application body."
                )

            text = (
                text[:index]
                + call
                + text[index:]
            )
        else:
            text = (
                text[:index]
                + call
                + text[index:]
            )

    MAIN.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "Phase 9.1 + 9.2 + 9.3 installed."
    )


if __name__ == "__main__":
    main()
