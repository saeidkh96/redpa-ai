from __future__ import annotations

import json
from typing import Any

import typer

from redpa_sdk.client import RedPA, RedPAError
from redpa_sdk.config import RedPAConfig


app = typer.Typer(help="RedPA AI developer CLI.", no_args_is_help=True)
agents_app = typer.Typer(help="Inspect RedPA agents.")
models_app = typer.Typer(help="Inspect model providers.")
tools_app = typer.Typer(help="Inspect the unified tool catalog.")
quality_app = typer.Typer(help="Run release quality operations.")
reliability_app = typer.Typer(help="Inspect provider reliability.")

app.add_typer(agents_app, name="agents")
app.add_typer(models_app, name="models")
app.add_typer(tools_app, name="tools")
app.add_typer(quality_app, name="quality")
app.add_typer(reliability_app, name="reliability")


def _config(api_url: str | None, token: str | None) -> RedPAConfig:
    env = RedPAConfig.from_env()
    return RedPAConfig(
        base_url=(api_url or env.base_url).rstrip("/"),
        token=token or env.token,
        timeout_seconds=env.timeout_seconds,
    )


def _print(payload: Any, *, json_output: bool) -> None:
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump(mode="json")
    elif isinstance(payload, list):
        payload = [
            item.model_dump(mode="json") if hasattr(item, "model_dump") else item
            for item in payload
        ]

    if json_output:
        typer.echo(json.dumps(payload, indent=2, default=str))
        return

    if isinstance(payload, dict):
        for key, value in payload.items():
            typer.echo(f"{key}: {value}")
    else:
        typer.echo(payload)


def _run(fn) -> None:
    try:
        fn()
    except RedPAError as exc:
        typer.echo(f"Error: {exc}", err=True)
        if isinstance(exc.detail, dict):
            hint = exc.detail.get("hint")
            if hint:
                typer.echo(f"Hint: {hint}", err=True)
            elif exc.detail:
                typer.echo(json.dumps(exc.detail, indent=2, default=str), err=True)
        elif exc.detail is not None:
            typer.echo(str(exc.detail), err=True)
        raise typer.Exit(code=1) from exc


@app.command()
def status(
    api_url: str | None = typer.Option(None, "--api-url"),
    token: str | None = typer.Option(None, "--token"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Show platform health."""
    def execute() -> None:
        with RedPA(_config(api_url, token)) as client:
            _print(client.health(), json_output=json_output)
    _run(execute)


@app.command()
def doctor(
    api_url: str | None = typer.Option(None, "--api-url"),
    token: str | None = typer.Option(None, "--token"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Check platform, agent registry, providers and reliability."""
    def execute() -> None:
        with RedPA(_config(api_url, token)) as client:
            result: dict[str, Any] = {"health": client.health().model_dump(mode="json")}
            try:
                result["agents"] = client.agents().model_dump(mode="json")
            except RedPAError as exc:
                result["agents_error"] = {"status_code": exc.status_code, "detail": exc.detail}
            try:
                result["providers"] = [item.model_dump(mode="json") for item in client.provider_health()]
            except RedPAError as exc:
                result["providers_error"] = {"status_code": exc.status_code, "detail": exc.detail}
                if exc.status_code == 401 and not client.config.token:
                    result["providers_hint"] = "Set REDPA_TOKEN to access authenticated model-gateway endpoints."
            try:
                result["reliability"] = client.reliability_scorecard().model_dump(mode="json")
            except RedPAError as exc:
                result["reliability_error"] = {"status_code": exc.status_code, "detail": exc.detail}
                if exc.status_code == 404:
                    result["reliability_hint"] = (
                        "The running backend may be older than the checked-out source. "
                        "Rebuild it with: docker compose up -d --build backend"
                    )
            _print(result, json_output=json_output)
    _run(execute)


@agents_app.command("list")
def list_agents(
    api_url: str | None = typer.Option(None, "--api-url"),
    token: str | None = typer.Option(None, "--token"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    def execute() -> None:
        with RedPA(_config(api_url, token)) as client:
            _print(client.agents(), json_output=json_output)
    _run(execute)


@agents_app.command("discover")
def discover_agents(
    query: str,
    limit: int = typer.Option(10, min=1, max=50),
    api_url: str | None = typer.Option(None, "--api-url"),
    token: str | None = typer.Option(None, "--token"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    def execute() -> None:
        with RedPA(_config(api_url, token)) as client:
            _print(client.discover_agents(query, limit=limit), json_output=json_output)
    _run(execute)


@models_app.command("providers")
def providers(
    api_url: str | None = typer.Option(None, "--api-url"),
    token: str | None = typer.Option(None, "--token"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    def execute() -> None:
        with RedPA(_config(api_url, token)) as client:
            _print(client.providers(), json_output=json_output)
    _run(execute)


@tools_app.command("list")
def tools(
    refresh: bool = typer.Option(False, "--refresh"),
    api_url: str | None = typer.Option(None, "--api-url"),
    token: str | None = typer.Option(None, "--token"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    def execute() -> None:
        with RedPA(_config(api_url, token)) as client:
            _print(client.tools(refresh=refresh), json_output=json_output)
    _run(execute)


@reliability_app.command("scorecard")
def reliability_scorecard(
    api_url: str | None = typer.Option(None, "--api-url"),
    token: str | None = typer.Option(None, "--token"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    def execute() -> None:
        with RedPA(_config(api_url, token)) as client:
            _print(client.reliability_scorecard(), json_output=json_output)
    _run(execute)


@quality_app.command("gate")
def quality_gate(
    baseline: str = typer.Option(..., "--baseline"),
    candidate: str = typer.Option(..., "--candidate"),
    release_label: str | None = typer.Option(None, "--release-label"),
    minimum_score: float = typer.Option(0.70, "--minimum-score", min=0.0, max=1.0),
    max_aggregate_drop: float = typer.Option(0.05, "--max-aggregate-drop", min=0.0, max=1.0),
    max_metric_drop: float = typer.Option(0.10, "--max-metric-drop", min=0.0, max=1.0),
    api_url: str | None = typer.Option(None, "--api-url"),
    token: str | None = typer.Option(None, "--token"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    def execute() -> None:
        with RedPA(_config(api_url, token)) as client:
            result = client.release_gate(
                baseline_run_id=baseline,
                candidate_run_id=candidate,
                release_label=release_label,
                minimum_candidate_score=minimum_score,
                max_aggregate_drop=max_aggregate_drop,
                max_metric_drop=max_metric_drop,
            )
            _print(result, json_output=json_output)
            if result.decision != "PASS":
                raise typer.Exit(code=1)
    _run(execute)


@quality_app.command("report")
def candidate_report(
    candidate: str = typer.Option(..., "--candidate"),
    api_url: str | None = typer.Option(None, "--api-url"),
    token: str | None = typer.Option(None, "--token"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    def execute() -> None:
        with RedPA(_config(api_url, token)) as client:
            _print(client.candidate_report(candidate), json_output=json_output)
    _run(execute)


if __name__ == "__main__":
    app()
