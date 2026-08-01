from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(
    __file__,
).resolve().parents[1]

REQUIREMENTS_PATH = (
    PROJECT_ROOT
    / "requirements.txt"
)

DEPENDENCY = "ddgs==9.14.4"


def read_requirements(
    path: Path,
) -> tuple[str, str]:
    raw_bytes = path.read_bytes()

    if raw_bytes.startswith(
        b"\xff\xfe",
    ) or raw_bytes.startswith(
        b"\xfe\xff",
    ):
        return (
            raw_bytes.decode(
                "utf-16",
            ),
            "utf-16",
        )

    try:
        return (
            raw_bytes.decode(
                "utf-8-sig",
            ),
            "utf-8",
        )
    except UnicodeDecodeError:
        return (
            raw_bytes.decode(
                "utf-16",
            ),
            "utf-16",
        )


def main() -> None:
    if not REQUIREMENTS_PATH.exists():
        raise FileNotFoundError(
            "requirements.txt was not found at "
            f"{REQUIREMENTS_PATH}"
        )

    content, encoding = read_requirements(
        REQUIREMENTS_PATH,
    )

    normalized_lines = [
        line.strip()
        for line in content.splitlines()
        if line.strip()
    ]

    package_names = {
        line.split(
            "==",
            1,
        )[0]
        .split(
            ">=",
            1,
        )[0]
        .split(
            "<=",
            1,
        )[0]
        .strip()
        .casefold()
        for line in normalized_lines
    }

    if "ddgs" in package_names:
        print(
            "The ddgs dependency is already present."
        )
        return

    updated_content = content.rstrip(
        "\r\n",
    )

    updated_content += (
        "\r\n"
        if encoding == "utf-16"
        else "\n"
    )

    updated_content += DEPENDENCY

    updated_content += (
        "\r\n"
        if encoding == "utf-16"
        else "\n"
    )

    REQUIREMENTS_PATH.write_text(
        updated_content,
        encoding=encoding,
    )

    print(
        f"Added {DEPENDENCY} to "
        f"{REQUIREMENTS_PATH}"
    )


if __name__ == "__main__":
    main()
