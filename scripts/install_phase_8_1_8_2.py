from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "backend/app/api/v1/router.py"
MAIN = ROOT / "backend/app/main.py"
REQ = ROOT / "requirements.txt"
COMPOSE = ROOT / "docker-compose.yml"

def main():
    router = ROUTER.read_text(encoding="utf-8")
    imp = "from app.api.v1.background_jobs import router as background_jobs_router\n"
    inc = "api_router.include_router(background_jobs_router)\n"
    if imp not in router:
        router = imp + router
    if inc not in router:
        marker = "api_router = APIRouter()"
        pos = router.find("\n", router.find(marker))
        router = router[:pos+1] + inc + router[pos+1:]
    ROUTER.write_text(router, encoding="utf-8")

    main_text = MAIN.read_text(encoding="utf-8")
    imports = (
        "from app.middleware.idempotency import RedisIdempotencyMiddleware\n"
        "from app.middleware.rate_limit import RedisRateLimitMiddleware\n"
    )
    if "RedisRateLimitMiddleware" not in main_text:
        main_text = imports + main_text
    middleware = (
        "\napp.add_middleware(RedisRateLimitMiddleware)\n"
        "app.add_middleware(RedisIdempotencyMiddleware)\n"
    )
    if "app.add_middleware(RedisRateLimitMiddleware)" not in main_text:
        start = main_text.find("app = FastAPI(")
        end = main_text.find("\n)", start) + 2
        main_text = main_text[:end] + middleware + main_text[end:]
    MAIN.write_text(main_text, encoding="utf-8")

    requirements = REQ.read_text(encoding="utf-8").splitlines()
    if not any(line.lower().startswith("redis") for line in requirements):
        requirements.append("redis>=5,<6")
    REQ.write_text("\n".join(requirements) + "\n", encoding="utf-8")

    compose = COMPOSE.read_text(encoding="utf-8")
    services = """
  redis:
    image: redis:7-alpine
    container_name: redpa-redis
    command: ["redis-server", "--appendonly", "yes"]
    ports: ["6379:6379"]
    volumes: ["redpa-redis-data:/data"]
    networks: ["redpa-network"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 10

  background-worker:
    build:
      context: .
      dockerfile: Dockerfile
    image: redpa-ai-backend
    container_name: redpa-background-worker
    command: ["python", "-m", "app.background_jobs.worker"]
    working_dir: /app/backend
    environment:
      PYTHONPATH: /app/backend
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/redpa_ai
      REDIS_URL: redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks: ["redpa-network"]

  background-scheduler:
    build:
      context: .
      dockerfile: Dockerfile
    image: redpa-ai-backend
    container_name: redpa-background-scheduler
    command: ["python", "-m", "app.background_jobs.scheduler"]
    working_dir: /app/backend
    environment:
      PYTHONPATH: /app/backend
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/redpa_ai
      REDIS_URL: redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks: ["redpa-network"]

"""
    if "\n  redis:\n" not in compose:
        compose = compose.replace("services:\n", "services:\n" + services, 1)
    if "redpa-redis-data:" not in compose:
        if "volumes:\n" in compose:
            compose = compose.replace("volumes:\n", "volumes:\n  redpa-redis-data:\n", 1)
        else:
            compose += "\nvolumes:\n  redpa-redis-data:\n"
    COMPOSE.write_text(compose, encoding="utf-8")
    print("Phase 8.1 + 8.2 installed.")

if __name__ == "__main__":
    main()
