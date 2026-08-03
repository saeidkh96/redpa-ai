from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "backend" / "app" / "a2a_protocol" / "server.py"


def main() -> None:
    text = SERVER.read_text(encoding="utf-8")

    old_import = "from app.a2a_protocol.executor import RedPACoordinatorExecutor\n"
    new_import = (
        "from app.a2a_protocol.specialist_executor import "
        "RedPACoordinatorDelegatingExecutor\n"
    )

    if new_import not in text:
        if old_import not in text:
            raise SystemExit("Could not find the Coordinator executor import.")
        text = text.replace(old_import, new_import, 1)

    old_constructor = "agent_executor=RedPACoordinatorExecutor(),"
    new_constructor = "agent_executor=RedPACoordinatorDelegatingExecutor(),"

    if new_constructor not in text:
        if old_constructor not in text:
            raise SystemExit("Could not find the Coordinator executor constructor.")
        text = text.replace(old_constructor, new_constructor, 1)

    SERVER.write_text(text, encoding="utf-8")
    print("Coordinator specialist delegation installed.")


if __name__ == "__main__":
    main()
