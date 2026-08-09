from __future__ import annotations

from dataclasses import dataclass

import pulumi


@dataclass(frozen=True, slots=True)
class AzureSettings:
    environment: str
    location: str
    project_name: str
    backend_image: str
    frontend_image: str
    policy_image: str
    postgres_admin: str
    postgres_password: pulumi.Output[str]
    redis_url: pulumi.Output[str] | None
    qdrant_url: pulumi.Output[str] | None
    ollama_base_url: pulumi.Output[str] | None
    min_replicas: int
    max_replicas: int


def _optional_secret(
    config: pulumi.Config,
    key: str,
) -> pulumi.Output[str] | None:
    value = config.get_secret(key)
    return value


def load_settings() -> AzureSettings:
    cfg = pulumi.Config("redpa")

    environment = cfg.get("environment") or "dev"
    location = cfg.get("location") or "westeurope"
    project_name = cfg.get("projectName") or "redpa"

    backend_image = (
        cfg.get("backendImage")
        or "ghcr.io/saeidkh96/redpa-ai-backend:latest"
    )
    frontend_image = (
        cfg.get("frontendImage")
        or "ghcr.io/saeidkh96/redpa-ai-frontend:latest"
    )
    policy_image = (
        cfg.get("policyImage")
        or "ghcr.io/saeidkh96/redpa-ai-policy-service:latest"
    )

    postgres_admin = cfg.get("postgresAdmin") or "redpaadmin"
    postgres_password = cfg.require_secret("postgresPassword")

    min_replicas = cfg.get_int("minReplicas") or 1
    max_replicas = cfg.get_int("maxReplicas") or 2

    if min_replicas < 0:
        raise ValueError("redpa:minReplicas cannot be negative.")
    if max_replicas < max(min_replicas, 1):
        raise ValueError(
            "redpa:maxReplicas must be at least minReplicas and >= 1."
        )

    return AzureSettings(
        environment=environment,
        location=location,
        project_name=project_name,
        backend_image=backend_image,
        frontend_image=frontend_image,
        policy_image=policy_image,
        postgres_admin=postgres_admin,
        postgres_password=postgres_password,
        redis_url=_optional_secret(cfg, "redisUrl"),
        qdrant_url=_optional_secret(cfg, "qdrantUrl"),
        ollama_base_url=_optional_secret(cfg, "ollamaBaseUrl"),
        min_replicas=min_replicas,
        max_replicas=max_replicas,
    )
