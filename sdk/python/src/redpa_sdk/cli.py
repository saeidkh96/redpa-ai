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
workflows_app = typer.Typer(help="Operate durable distributed workflows.")
reviews_app = typer.Typer(help="Operate human-review requests.")
mcp_app = typer.Typer(help="Inspect and execute MCP tools.")

app.add_typer(agents_app, name="agents")
app.add_typer(models_app, name="models")
app.add_typer(tools_app, name="tools")
app.add_typer(quality_app, name="quality")
app.add_typer(reliability_app, name="reliability")
app.add_typer(workflows_app, name="workflows")
app.add_typer(reviews_app, name="reviews")
app.add_typer(mcp_app, name="mcp")


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


@workflows_app.command("list")
def workflows_list(
    limit: int = typer.Option(50, min=1, max=200),
    api_url: str | None = typer.Option(None, "--api-url"),
    token: str | None = typer.Option(None, "--token"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    def execute() -> None:
        with RedPA(_config(api_url, token)) as client:
            _print(client.workflows(limit=limit), json_output=json_output)
    _run(execute)


@workflows_app.command("get")
def workflow_get(
    workflow_id: str,
    api_url: str | None = typer.Option(None, "--api-url"),
    token: str | None = typer.Option(None, "--token"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    def execute() -> None:
        with RedPA(_config(api_url, token)) as client:
            _print(client.workflow(workflow_id), json_output=json_output)
    _run(execute)


@workflows_app.command("create")
def workflow_create(
    request: str = typer.Option(..., "--request"),
    max_parallelism: int = typer.Option(4, min=1, max=10),
    timeout_seconds: float = typer.Option(120.0, min=1.0, max=900.0),
    approval_granted: bool = typer.Option(False, "--approval-granted"),
    api_url: str | None = typer.Option(None, "--api-url"),
    token: str | None = typer.Option(None, "--token"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    def execute() -> None:
        with RedPA(_config(api_url, token)) as client:
            _print(
                client.create_workflow(
                    request=request,
                    max_parallelism=max_parallelism,
                    timeout_seconds=timeout_seconds,
                    approval_granted=approval_granted,
                ),
                json_output=json_output,
            )
    _run(execute)


@workflows_app.command("resume")
def workflow_resume(
    workflow_id: str,
    approval_granted: bool = typer.Option(False, "--approval-granted"),
    retry_failed: bool = typer.Option(True, "--retry-failed/--no-retry-failed"),
    retry_running: bool = typer.Option(True, "--retry-running/--no-retry-running"),
    api_url: str | None = typer.Option(None, "--api-url"),
    token: str | None = typer.Option(None, "--token"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    def execute() -> None:
        with RedPA(_config(api_url, token)) as client:
            _print(
                client.resume_workflow(
                    workflow_id,
                    approval_granted=approval_granted,
                    retry_failed=retry_failed,
                    retry_running=retry_running,
                ),
                json_output=json_output,
            )
    _run(execute)


@reviews_app.command("list")
def reviews_list(
    status: str | None = typer.Option(None, "--status"),
    limit: int = typer.Option(20, min=1, max=100),
    offset: int = typer.Option(0, min=0),
    api_url: str | None = typer.Option(None, "--api-url"),
    token: str | None = typer.Option(None, "--token"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    def execute() -> None:
        with RedPA(_config(api_url, token)) as client:
            _print(client.reviews(status=status, limit=limit, offset=offset), json_output=json_output)
    _run(execute)


@reviews_app.command("get")
def review_get(
    review_id: str,
    api_url: str | None = typer.Option(None, "--api-url"),
    token: str | None = typer.Option(None, "--token"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    def execute() -> None:
        with RedPA(_config(api_url, token)) as client:
            _print(client.review(review_id), json_output=json_output)
    _run(execute)


@reviews_app.command("approve")
def review_approve(
    review_id: str,
    feedback: str | None = typer.Option(None, "--feedback"),
    api_url: str | None = typer.Option(None, "--api-url"),
    token: str | None = typer.Option(None, "--token"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    def execute() -> None:
        with RedPA(_config(api_url, token)) as client:
            _print(client.approve_review(review_id, feedback=feedback), json_output=json_output)
    _run(execute)


@reviews_app.command("reject")
def review_reject(
    review_id: str,
    feedback: str | None = typer.Option(None, "--feedback"),
    api_url: str | None = typer.Option(None, "--api-url"),
    token: str | None = typer.Option(None, "--token"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    def execute() -> None:
        with RedPA(_config(api_url, token)) as client:
            _print(client.reject_review(review_id, feedback=feedback), json_output=json_output)
    _run(execute)


@reviews_app.command("resume")
def review_resume(
    review_id: str,
    api_url: str | None = typer.Option(None, "--api-url"),
    token: str | None = typer.Option(None, "--token"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    def execute() -> None:
        with RedPA(_config(api_url, token)) as client:
            _print(client.resume_review(review_id), json_output=json_output)
    _run(execute)


@mcp_app.command("servers")
def mcp_servers(
    api_url: str | None = typer.Option(None, "--api-url"),
    token: str | None = typer.Option(None, "--token"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    def execute() -> None:
        with RedPA(_config(api_url, token)) as client:
            _print(client.mcp_servers(), json_output=json_output)
    _run(execute)


@mcp_app.command("health")
def mcp_health(
    api_url: str | None = typer.Option(None, "--api-url"),
    token: str | None = typer.Option(None, "--token"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    def execute() -> None:
        with RedPA(_config(api_url, token)) as client:
            _print(client.mcp_health(), json_output=json_output)
    _run(execute)


@mcp_app.command("tools")
def mcp_tools(
    refresh: bool = typer.Option(False, "--refresh"),
    api_url: str | None = typer.Option(None, "--api-url"),
    token: str | None = typer.Option(None, "--token"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    def execute() -> None:
        with RedPA(_config(api_url, token)) as client:
            _print(client.mcp_tools(refresh=refresh), json_output=json_output)
    _run(execute)


@mcp_app.command("execute")
def mcp_execute(
    qualified_name: str,
    arguments: str = typer.Option("{}", "--arguments", help="JSON object with tool arguments."),
    approval_granted: bool = typer.Option(False, "--approval-granted"),
    api_url: str | None = typer.Option(None, "--api-url"),
    token: str | None = typer.Option(None, "--token"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    def execute() -> None:
        try:
            parsed = json.loads(arguments)
        except json.JSONDecodeError as exc:
            typer.echo(f"Error: --arguments must be valid JSON: {exc}", err=True)
            raise typer.Exit(code=2) from exc
        if not isinstance(parsed, dict):
            typer.echo("Error: --arguments must decode to a JSON object.", err=True)
            raise typer.Exit(code=2)
        with RedPA(_config(api_url, token)) as client:
            _print(
                client.execute_mcp_tool(
                    qualified_name,
                    arguments=parsed,
                    approval_granted=approval_granted,
                ),
                json_output=json_output,
            )
    _run(execute)


if __name__ == "__main__":
    app()
