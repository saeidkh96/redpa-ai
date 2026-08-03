from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "docker-compose.yml"


def find_service_block(
    lines: list[str],
    service_name: str,
) -> tuple[int, int]:
    marker = f"  {service_name}:"

    try:
        start = lines.index(marker)
    except ValueError as exception:
        raise SystemExit(
            f"Service '{service_name}' was not found."
        ) from exception

    end = len(lines)

    for index in range(start + 1, len(lines)):
        line = lines[index]

        if (
            line.startswith("  ")
            and not line.startswith("    ")
            and line.endswith(":")
        ):
            end = index
            break

    return start, end


def find_environment_block(
    lines: list[str],
    start: int,
    end: int,
) -> tuple[int, int]:
    environment_index = -1

    for index in range(start + 1, end):
        if lines[index] == "    environment:":
            environment_index = index
            break

    if environment_index == -1:
        raise SystemExit(
            "The backend environment block was not found."
        )

    block_end = end

    for index in range(
        environment_index + 1,
        end,
    ):
        line = lines[index]

        if (
            line.startswith("    ")
            and not line.startswith("      ")
            and line.strip()
        ):
            block_end = index
            break

    return environment_index, block_end


def deduplicate_mapping_entries(
    entries: list[str],
) -> list[str]:
    result: list[str] = []
    key_positions: dict[str, int] = {}

    for line in entries:
        stripped = line.strip()

        if (
            not stripped
            or stripped.startswith("#")
            or ":" not in stripped
            or not line.startswith("      ")
        ):
            result.append(line)
            continue

        key = stripped.split(
            ":",
            1,
        )[0].strip()

        if not key:
            result.append(line)
            continue

        if key in key_positions:
            old_position = key_positions[key]
            result[old_position] = line
            continue

        key_positions[key] = len(result)
        result.append(line)

    return result


def ensure_entry(
    entries: list[str],
    key: str,
    value: str,
) -> list[str]:
    replacement = f"      {key}: {value}"

    for index, line in enumerate(entries):
        stripped = line.strip()

        if stripped.startswith(
            f"{key}:"
        ):
            entries[index] = replacement
            return entries

    entries.append(
        replacement,
    )

    return entries


def main() -> None:
    text = COMPOSE.read_text(
        encoding="utf-8",
    )

    lines = text.splitlines()

    service_start, service_end = find_service_block(
        lines,
        "backend",
    )

    environment_start, environment_end = (
        find_environment_block(
            lines,
            service_start,
            service_end,
        )
    )

    entries = lines[
        environment_start + 1:
        environment_end
    ]

    entries = deduplicate_mapping_entries(
        entries,
    )

    required = {
        "ENVIRONMENT": "development",
        "REDIS_URL": "redis://redis:6379/0",
        "REQUIRE_HTTPS": '"false"',
        "ALLOWED_HOSTS": (
            "localhost,127.0.0.1,backend"
        ),
        "OTEL_ENABLED": '"true"',
        "OTEL_EXPORTER_OTLP_ENDPOINT": (
            "http://otel-collector:4318"
        ),
    }

    for key, value in required.items():
        entries = ensure_entry(
            entries,
            key,
            value,
        )

    lines[
        environment_start + 1:
        environment_end
    ] = entries

    COMPOSE.write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )

    print(
        "Duplicate backend environment keys were removed."
    )


if __name__ == "__main__":
    main()
