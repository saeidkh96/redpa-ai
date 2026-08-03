from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "backend/app/main.py"
REQ = ROOT / "requirements.txt"
COMPOSE = ROOT / "docker-compose.yml"

def patch_main():
    text = MAIN.read_text(encoding="utf-8")

    imports = (
        "from app.middleware.security_headers import SecurityHeadersMiddleware\n"
        "from app.middleware.trace_headers import TraceHeadersMiddleware\n"
        "from app.observability.tracing import configure_tracing\n"
        "from app.security_hardening.config import SecuritySettings\n"
    )

    if "configure_tracing" not in text:
        text = imports + text

    if "SecuritySettings.load()" not in text:
        marker = "app = FastAPI("
        start = text.find(marker)
        end = text.find("\n)", start) + 2
        insertion = (
            "\nsecurity_settings = SecuritySettings.load()\n"
            "app.add_middleware(\n"
            "    SecurityHeadersMiddleware,\n"
            "    require_https=security_settings.require_https,\n"
            ")\n"
            "app.add_middleware(TraceHeadersMiddleware)\n"
            "configure_tracing(\n"
            "    app,\n"
            "    service_name='redpa-backend',\n"
            "    service_version='0.8.5',\n"
            ")\n"
        )
        text = text[:end] + insertion + text[end:]

    MAIN.write_text(text, encoding="utf-8")

def patch_requirements():
    lines = REQ.read_text(encoding="utf-8").splitlines()
    additions = [
        "opentelemetry-api>=1.27,<2",
        "opentelemetry-sdk>=1.27,<2",
        "opentelemetry-exporter-otlp-proto-http>=1.27,<2",
        "opentelemetry-instrumentation-fastapi>=0.48b0,<1",
        "opentelemetry-instrumentation-httpx>=0.48b0,<1",
        "opentelemetry-instrumentation-logging>=0.48b0,<1",
        "opentelemetry-instrumentation-redis>=0.48b0,<1",
        "opentelemetry-instrumentation-asyncpg>=0.48b0,<1",
    ]

    names = {
        line.split("=", 1)[0].split("<", 1)[0].strip().lower()
        for line in lines
    }

    for item in additions:
        name = item.split("=", 1)[0].split("<", 1)[0].strip().lower()
        if name not in names:
            lines.append(item)

    REQ.write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )

def patch_compose():
    text = COMPOSE.read_text(encoding="utf-8")

    services = """
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    container_name: redpa-otel-collector
    command: ["--config=/etc/otelcol/config.yaml"]
    volumes:
      - ./observability/otel-collector-config.yaml:/etc/otelcol/config.yaml:ro
    ports:
      - "4317:4317"
      - "4318:4318"
    depends_on:
      - tempo
    networks:
      - redpa-network

  tempo:
    image: grafana/tempo:latest
    container_name: redpa-tempo
    command: ["-config.file=/etc/tempo.yaml"]
    volumes:
      - ./observability/tempo.yaml:/etc/tempo.yaml:ro
      - redpa-tempo-data:/var/tempo
    ports:
      - "3200:3200"
    networks:
      - redpa-network

"""

    if "\n  otel-collector:\n" not in text:
        text = text.replace(
            "services:\n",
            "services:\n" + services,
            1,
        )

    if "redpa-tempo-data:" not in text:
        if "volumes:\n" in text:
            text = text.replace(
                "volumes:\n",
                "volumes:\n  redpa-tempo-data:\n",
                1,
            )
        else:
            text += "\nvolumes:\n  redpa-tempo-data:\n"

    COMPOSE.write_text(text, encoding="utf-8")

def main():
    patch_main()
    patch_requirements()
    patch_compose()
    print("Phase 8.3 + 8.4 + 8.5 installed.")

if __name__ == "__main__":
    main()
