from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "docker-compose.yml"


def find_service_block(
    lines: list[str],
    service_name: str,
) -> tuple[int, int]:
    service_line = f"  {service_name}:"

    try:
        start = lines.index(service_line)
    except ValueError as exception:
        raise SystemExit(
            f"Service '{service_name}' was not found in docker-compose.yml."
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


def ensure_environment_entry(
    lines: list[str],
    start: int,
    end: int,
    entry: str,
) -> tuple[list[str], int]:
    block = lines[start:end]

    if any(
        line.strip() == entry.strip()
        for line in block
    ):
        return lines, end

    environment_index = None

    for index in range(start + 1, end):
        if lines[index].strip() == "environment:":
            environment_index = index
            break

    if environment_index is None:
        insert_at = start + 1
        lines.insert(
            insert_at,
            "    environment:",
        )
        lines.insert(
            insert_at + 1,
            f"      {entry}",
        )
        return lines, end + 2

    insert_at = environment_index + 1

    while (
        insert_at < end
        and (
            not lines[insert_at].strip()
            or lines[insert_at].startswith("      ")
        )
    ):
        insert_at += 1

    lines.insert(
        insert_at,
        f"      {entry}",
    )

    return lines, end + 1


def ensure_depends_on_redis(
    lines: list[str],
    start: int,
    end: int,
) -> tuple[list[str], int]:
    block = lines[start:end]

    if any(
        line.strip() == "redis:"
        and line.startswith("      ")
        for line in block
    ):
        return lines, end

    depends_index = None

    for index in range(start + 1, end):
        if lines[index].strip() == "depends_on:":
            depends_index = index
            break

    redis_block = [
        "      redis:",
        "        condition: service_healthy",
    ]

    if depends_index is None:
        insert_at = end
        lines[insert_at:insert_at] = [
            "    depends_on:",
            *redis_block,
        ]
        return lines, end + 3

    insert_at = depends_index + 1

    while (
        insert_at < end
        and (
            not lines[insert_at].strip()
            or lines[insert_at].startswith("      ")
            or lines[insert_at].startswith("        ")
        )
    ):
        insert_at += 1

    lines[insert_at:insert_at] = redis_block

    return lines, end + 2


def main() -> None:
    text = COMPOSE.read_text(
        encoding="utf-8",
    )

    lines = text.splitlines()

    start, end = find_service_block(
        lines,
        "backend",
    )

    lines, end = ensure_environment_entry(
        lines,
        start,
        end,
        "REDIS_URL: redis://redis:6379/0",
    )

    lines, end = ensure_environment_entry(
        lines,
        start,
        end,
        'ENVIRONMENT: development',
    )

    lines, end = ensure_environment_entry(
        lines,
        start,
        end,
        'REQUIRE_HTTPS: "false"',
    )

    lines, end = ensure_environment_entry(
        lines,
        start,
        end,
        "ALLOWED_HOSTS: localhost,127.0.0.1,backend",
    )

    lines, end = ensure_environment_entry(
        lines,
        start,
        end,
        "OTEL_ENABLED: \"true\"",
    )

    lines, end = ensure_environment_entry(
        lines,
        start,
        end,
        "OTEL_EXPORTER_OTLP_ENDPOINT: http://otel-collector:4318",
    )

    lines, end = ensure_depends_on_redis(
        lines,
        start,
        end,
    )

    COMPOSE.write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )

    print(
        "Backend Redis and observability environment fixed."
    )


if __name__ == "__main__":
    main()
