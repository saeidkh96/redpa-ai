from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "docker-compose.yml"


def main() -> None:
    text = COMPOSE.read_text(encoding="utf-8")

    # The service reference alone does not define the top-level volume.
    lines = text.splitlines()

    volumes_index = None
    for index, line in enumerate(lines):
        if line == "volumes:":
            volumes_index = index
            break

    if volumes_index is None:
        lines.extend(
            [
                "",
                "volumes:",
                "  redpa-redis-data:",
            ]
        )
    else:
        block_end = len(lines)

        for index in range(volumes_index + 1, len(lines)):
            line = lines[index]

            if (
                line
                and not line.startswith(" ")
                and line.endswith(":")
            ):
                block_end = index
                break

        volume_definition_exists = any(
            line.strip() == "redpa-redis-data:"
            and line.startswith("  ")
            and not line.startswith("    ")
            for line in lines[
                volumes_index + 1:block_end
            ]
        )

        if not volume_definition_exists:
            lines.insert(
                volumes_index + 1,
                "  redpa-redis-data:",
            )

    COMPOSE.write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )

    print(
        "Top-level volume redpa-redis-data was added."
    )


if __name__ == "__main__":
    main()
