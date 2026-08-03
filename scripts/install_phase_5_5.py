from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANNER_SERVICE = (
    ROOT
    / "backend"
    / "app"
    / "services"
    / "planner_service.py"
)


def main() -> None:
    text = PLANNER_SERVICE.read_text(
        encoding="utf-8",
    )

    anchor = (
        '    r"\\bremote\\s+a2a\\b",\n'
        ')\n'
    )

    replacement = (
        '    r"\\bremote\\s+a2a\\b",\n'
        '    r"\\bwhich\\s+agent\\s+can\\b",\n'
        '    r"\\bwhat\\s+agent\\s+can\\b",\n'
        '    r"\\bfind\\s+(an|the)\\s+agent\\s+for\\b",\n'
        '    r"\\bfind\\s+(an|the)\\s+agent\\s+that\\b",\n'
        '    r"\\bwho\\s+can\\s+handle\\b",\n'
        '    r"\\bshow\\s+available\\s+agents\\b",\n'
        '    r"\\blist\\s+available\\s+agents\\b",\n'
        ')\n'
    )

    if replacement in text:
        print(
            "Automatic A2A patterns are already installed."
        )
        return

    if anchor not in text:
        raise SystemExit(
            "Could not find DETERMINISTIC_A2A_PATTERNS in "
            "planner_service.py."
        )

    PLANNER_SERVICE.write_text(
        text.replace(
            anchor,
            replacement,
            1,
        ),
        encoding="utf-8",
    )

    print(
        "Phase 5.5 installed successfully."
    )


if __name__ == "__main__":
    main()
