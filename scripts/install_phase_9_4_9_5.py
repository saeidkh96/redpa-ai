from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "backend/app/api/v1/router.py"
MAIN = ROOT / "backend/app/main.py"
WORKER = ROOT / "backend/app/background_jobs/worker.py"
SCHEDULER = ROOT / "backend/app/background_jobs/scheduler.py"
COMPOSE = ROOT / "docker-compose.yml"


def patch_router() -> None:
    text = ROUTER.read_text(
        encoding="utf-8",
    )

    imports = [
        (
            "from app.api.v1.platform_health "
            "import router as platform_health_router\n"
        ),
        (
            "from app.api.v1.performance "
            "import router as performance_router\n"
        ),
    ]

    includes = [
        (
            "api_router.include_router(\n"
            "    platform_health_router,\n"
            ")\n"
        ),
        (
            "api_router.include_router(\n"
            "    performance_router,\n"
            ")\n"
        ),
    ]

    for import_line in imports:
        if import_line not in text:
            text = import_line + text

    marker = "api_router = APIRouter()"
    index = text.find(
        marker,
    )

    if index == -1:
        raise SystemExit(
            "Could not find api_router = APIRouter()."
        )

    line_end = text.find(
        "\n",
        index,
    )

    if line_end == -1:
        line_end = len(
            text,
        )

    insertion = ""

    for include_block in includes:
        if include_block not in text:
            insertion += include_block

    if insertion:
        text = (
            text[:line_end + 1]
            + insertion
            + text[line_end + 1:]
        )

    ROUTER.write_text(
        text,
        encoding="utf-8",
    )


def patch_main() -> None:
    text = MAIN.read_text(
        encoding="utf-8",
    )

    import_line = (
        "from app.performance import "
        "PerformanceMonitoringMiddleware, "
        "register_sql_performance_monitor\n"
    )

    if import_line not in text:
        anchor = (
            "from app.monitoring.metrics import "
            "PrometheusMetricsMiddleware\n"
        )

        if anchor in text:
            text = text.replace(
                anchor,
                anchor + import_line,
                1,
            )
        else:
            text = import_line + text

    middleware_block = (
        "    application.add_middleware(\n"
        "        PerformanceMonitoringMiddleware,\n"
        "    )\n\n"
    )

    if (
        "PerformanceMonitoringMiddleware"
        not in text.split(
            "def create_application",
            1,
        )[-1]
    ):
        marker = (
            "    application.add_middleware(\n"
            "        PrometheusMetricsMiddleware,"
        )

        index = text.find(
            marker,
        )

        if index == -1:
            marker = (
                "    application.include_router("
            )
            index = text.find(
                marker,
            )

        if index == -1:
            raise SystemExit(
                "Could not locate middleware insertion point."
            )

        text = (
            text[:index]
            + middleware_block
            + text[index:]
        )

    sql_call = (
        "\n    from app.database.session "
        "import engine as database_engine\n"
        "    register_sql_performance_monitor("
        "database_engine"
        ")\n"
    )

    if (
        "register_sql_performance_monitor("
        "database_engine"
        ")"
        not in text
    ):
        marker = (
            "    configure_tracing("
        )

        index = text.find(
            marker,
        )

        if index == -1:
            marker = (
                "    return application"
            )
            index = text.find(
                marker,
            )

        if index == -1:
            raise SystemExit(
                "Could not locate SQL monitor insertion point."
            )

        text = (
            text[:index]
            + sql_call
            + text[index:]
        )

    MAIN.write_text(
        text,
        encoding="utf-8",
    )


def patch_heartbeat(
    path: Path,
    *,
    kind: str,
) -> None:
    text = path.read_text(
        encoding="utf-8",
    )

    import_line = (
        "from app.background_jobs.heartbeat "
        "import BackgroundHeartbeat\n"
    )

    if import_line not in text:
        text = import_line + text

    call = (
        "            await "
        f"BackgroundHeartbeat.{kind}()\n"
    )

    if call not in text:
        marker = "        while True:\n"

        if marker not in text:
            raise SystemExit(
                f"Could not locate loop in {path}."
            )

        text = text.replace(
            marker,
            marker + call,
            1,
        )

    path.write_text(
        text,
        encoding="utf-8",
    )


def patch_compose() -> None:
    text = COMPOSE.read_text(
        encoding="utf-8",
    )

    if "13133:13133" not in text:
        marker = (
            '      - "4318:4318"\n'
        )

        if marker in text:
            text = text.replace(
                marker,
                marker
                + '      - "13133:13133"\n',
                1,
            )

    COMPOSE.write_text(
        text,
        encoding="utf-8",
    )


def main() -> None:
    patch_router()
    patch_main()

    patch_heartbeat(
        WORKER,
        kind="worker",
    )

    patch_heartbeat(
        SCHEDULER,
        kind="scheduler",
    )

    patch_compose()

    print(
        "Phase 9.4 + 9.5 installed."
    )


if __name__ == "__main__":
    main()
