from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "docker-compose.yml"

SERVICES = """
  postgres-agent:
    build:
      context: .
      dockerfile: Dockerfile
    image: redpa-ai-backend
    container_name: redpa-postgres-agent
    command: ["python", "-m", "app.specialist_agents.postgres_agent"]
    working_dir: /app/backend
    environment:
      PYTHONPATH: /app/backend
      POSTGRES_AGENT_HOST: 0.0.0.0
      POSTGRES_AGENT_PORT: 8062
      POSTGRES_AGENT_PUBLIC_URL: http://postgres-agent:8062
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/redpa_ai
    ports:
      - "8062:8062"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - redpa-network
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8062/health', timeout=5)"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 10s

  docker-agent:
    build:
      context: .
      dockerfile: Dockerfile
    image: redpa-ai-backend
    container_name: redpa-docker-agent
    command: ["python", "-m", "app.specialist_agents.docker_agent"]
    working_dir: /app/backend
    environment:
      PYTHONPATH: /app/backend
      DOCKER_AGENT_HOST: 0.0.0.0
      DOCKER_AGENT_PORT: 8063
      DOCKER_AGENT_PUBLIC_URL: http://docker-agent:8063
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    ports:
      - "8063:8063"
    networks:
      - redpa-network
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8063/health', timeout=5)"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 10s

  filesystem-agent:
    build:
      context: .
      dockerfile: Dockerfile
    image: redpa-ai-backend
    container_name: redpa-filesystem-agent
    command: ["python", "-m", "app.specialist_agents.filesystem_agent"]
    working_dir: /app/backend
    environment:
      PYTHONPATH: /app/backend
      FILESYSTEM_AGENT_HOST: 0.0.0.0
      FILESYSTEM_AGENT_PORT: 8064
      FILESYSTEM_AGENT_PUBLIC_URL: http://filesystem-agent:8064
      FILESYSTEM_AGENT_ROOT: /app
    ports:
      - "8064:8064"
    networks:
      - redpa-network
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8064/health', timeout=5)"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 10s

  github-agent:
    build:
      context: .
      dockerfile: Dockerfile
    image: redpa-ai-backend
    container_name: redpa-github-agent
    command: ["python", "-m", "app.specialist_agents.github_agent"]
    working_dir: /app/backend
    environment:
      PYTHONPATH: /app/backend
      GITHUB_AGENT_HOST: 0.0.0.0
      GITHUB_AGENT_PORT: 8065
      GITHUB_AGENT_PUBLIC_URL: http://github-agent:8065
      GITHUB_TOKEN: ${GITHUB_TOKEN:-}
    ports:
      - "8065:8065"
    networks:
      - redpa-network
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8065/health', timeout=5)"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 10s

"""


def main() -> None:
    text = COMPOSE.read_text(encoding="utf-8")

    if "\n  postgres-agent:\n" in text:
        print("Specialist Agent services already exist.")
        return

    marker = "services:\n"
    if marker not in text:
        raise SystemExit("Could not find services: in docker-compose.yml.")

    COMPOSE.write_text(text.replace(marker, marker + SERVICES, 1), encoding="utf-8")
    print("Specialist Agent services added to Docker Compose.")


if __name__ == "__main__":
    main()
