from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "docker-compose.yml"


SERVICE_BLOCK = '''
  research-agent:
    build:
      context: .
      dockerfile: Dockerfile
    image: redpa-ai-backend
    container_name: redpa-research-agent
    command:
      - python
      - -m
      - app.research_agent.server
    working_dir: /app/backend
    environment:
      RESEARCH_AGENT_HOST: 0.0.0.0
      RESEARCH_AGENT_PORT: 8061
      RESEARCH_AGENT_PUBLIC_URL: http://research-agent:8061
      PYTHONPATH: /app/backend
    ports:
      - "8061:8061"
    networks:
      - redpa-network
    healthcheck:
      test:
        - CMD
        - python
        - -c
        - >
          import urllib.request;
          urllib.request.urlopen(
              'http://localhost:8061/health',
              timeout=5
          )
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 10s

'''


def main() -> None:
    text = COMPOSE.read_text(
        encoding="utf-8",
    )

    if "\n  research-agent:\n" in text:
        print(
            "research-agent service already exists."
        )
        return

    services_marker = "services:\n"

    if services_marker not in text:
        raise SystemExit(
            "Could not find services: in docker-compose.yml."
        )

    text = text.replace(
        services_marker,
        services_marker + SERVICE_BLOCK,
        1,
    )

    COMPOSE.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "Research Agent service added to docker-compose.yml."
    )


if __name__ == "__main__":
    main()
