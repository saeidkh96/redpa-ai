from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements.txt"


def decode_requirements() -> list[str]:
    raw = REQUIREMENTS.read_bytes()

    for encoding in (
        "utf-8-sig",
        "utf-16",
        "utf-8",
    ):
        try:
            return raw.decode(
                encoding,
            ).splitlines()
        except UnicodeDecodeError:
            continue

    raise SystemExit(
        "Could not decode requirements.txt."
    )


def main() -> None:
    lines = decode_requirements()

    filtered = [
        line
        for line in lines
        if not line.strip().casefold().startswith(
            (
                "docker==",
                "docker>=",
                "docker<",
            )
        )
    ]

    filtered.append(
        "docker>=7,<8"
    )

    REQUIREMENTS.write_text(
        "\n".join(filtered).rstrip()
        + "\n",
        encoding="utf-8",
    )

    print(
        "requirements.txt updated with docker>=7,<8"
    )


if __name__ == "__main__":
    main()
