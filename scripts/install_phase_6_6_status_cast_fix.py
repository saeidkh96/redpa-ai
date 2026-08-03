from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = (
    ROOT
    / "backend"
    / "app"
    / "distributed_durable"
    / "repository.py"
)


def main() -> None:
    text = REPOSITORY.read_text(
        encoding="utf-8",
    )

    old_status = "status = $2,"
    new_status = "status = $2::varchar,"

    old_case = (
        "WHEN $2 IN ('completed', 'partial', 'failed')"
    )
    new_case = (
        "WHEN $2::varchar IN "
        "('completed', 'partial', 'failed')"
    )

    if new_status not in text:
        if old_status not in text:
            raise SystemExit(
                "Could not find finalize_workflow status assignment."
            )

        text = text.replace(
            old_status,
            new_status,
            1,
        )

    if new_case not in text:
        if old_case not in text:
            raise SystemExit(
                "Could not find finalize_workflow CASE condition."
            )

        text = text.replace(
            old_case,
            new_case,
            1,
        )

    REPOSITORY.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "Phase 6.6 status parameter casts installed."
    )


if __name__ == "__main__":
    main()
