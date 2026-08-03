from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "docker-compose.yml"

SERVICE = r"""
  a2a-coordinator:
    build:
      context: .
      dockerfile: Dockerfile
    image: redpa-ai-backend
    container_name: redpa-a2a-coordinator
    restart: unless-stopped
    command:
      [
        "python",
        "-m",
        "app.a2a_protocol.server",
      ]
    environment:
      A2A_HOST: 0.0.0.0
      A2A_PORT: 8050
      A2A_PUBLIC_URL: http://localhost:8050
      DATABASE_URL: ${DATABASE_URL:-postgresql+asyncpg://postgres:postgres@postgres:5432/redpa_ai}
      QDRANT_URL: ${QDRANT_URL:-http://qdrant:6333}
      OLLAMA_BASE_URL: ${OLLAMA_BASE_URL:-http://host.docker.internal:11434}
    ports:
      - "8050:8050"
    depends_on:
      postgres:
        condition: service_healthy
      qdrant:
        condition: service_healthy
    healthcheck:
      test:
        [
          "CMD",
          "python",
          "-c",
          "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8050/health', timeout=3)",
        ]
      interval: 5s
      timeout: 5s
      retries: 15
      start_period: 10s
    networks:
      - redpa-network

"""


def main() -> None:
    text = COMPOSE.read_text(
        encoding="utf-8",
    )

    if "\n  a2a-coordinator:\n" in text:
        print("a2a-coordinator already exists.")
        return

    marker = "\n  backend:\n"

    if marker not in text:
        raise SystemExit(
            "Could not find the backend service in docker-compose.yml."
        )

    text = text.replace(
        marker,
        "\n" + SERVICE + "  backend:\n",
        1,
    )

    COMPOSE.write_text(
        text,
        encoding="utf-8",
    )

    print("Added a2a-coordinator to docker-compose.yml.")


if __name__ == "__main__":
    main()
