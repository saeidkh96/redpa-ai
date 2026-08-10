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
    postgres_version: str

    secret_key: pulumi.Output[str]
    api_key_pepper: pulumi.Output[str]

    redis_url: pulumi.Output[str] | None
    qdrant_url: pulumi.Output[str] | None
    ollama_base_url: pulumi.Output[str] | None

    min_replicas: int
    max_replicas: int
    worker_min_replicas: int
    worker_max_replicas: int

    log_retention_days: int

    deploy_apps: bool
    deploy_background_services: bool
    deploy_research_agent: bool
    deploy_a2a_coordinator: bool

    backend_cpu: float
    backend_memory: str

    frontend_cpu: float
    frontend_memory: str

    policy_cpu: float
    policy_memory: str


def _optional_secret(
    config: pulumi.Config,
    key: str,
) -> pulumi.Output[str] | None:
    return config.get_secret(key)


def _non_negative_int(
    config: pulumi.Config,
    key: str,
    default: int,
) -> int:
    value = config.get_int(key)

    if value is None:
        value = default

    if value < 0:
        raise ValueError(
            f"redpa:{key} cannot be negative."
        )

    return value


def _bool(
    config: pulumi.Config,
    key: str,
    default: bool,
) -> bool:
    value = config.get_bool(key)

    if value is None:
        return default

    return value


def load_settings() -> AzureSettings:
    cfg = pulumi.Config("redpa")

    environment = (
        cfg.get("environment")
        or "dev"
    )

    location = (
        cfg.get("location")
        or "francecentral"
    )

    project_name = (
        cfg.get("projectName")
        or "redpa"
    )

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

    postgres_admin = (
        cfg.get("postgresAdmin")
        or "redpaadmin"
    )

    postgres_version = (
        cfg.get("postgresVersion")
        or "16"
    )

    postgres_password = cfg.require_secret(
        "postgresPassword"
    )

    secret_key = cfg.require_secret(
        "secretKey"
    )

    api_key_pepper = cfg.require_secret(
        "apiKeyPepper"
    )

    min_replicas = _non_negative_int(
        cfg,
        "minReplicas",
        1,
    )

    max_replicas = _non_negative_int(
        cfg,
        "maxReplicas",
        1,
    )

    worker_min_replicas = _non_negative_int(
        cfg,
        "workerMinReplicas",
        1,
    )

    worker_max_replicas = _non_negative_int(
        cfg,
        "workerMaxReplicas",
        1,
    )

    if max_replicas < min_replicas:
        raise ValueError(
            "redpa:maxReplicas must be >= minReplicas."
        )

    if worker_max_replicas < worker_min_replicas:
        raise ValueError(
            "redpa:workerMaxReplicas must be "
            ">= workerMinReplicas."
        )

    log_retention_days = _non_negative_int(
        cfg,
        "logRetentionDays",
        30,
    )

    if log_retention_days < 30:
        raise ValueError(
            "redpa:logRetentionDays must be at least 30."
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
        postgres_version=postgres_version,

        secret_key=secret_key,
        api_key_pepper=api_key_pepper,

        redis_url=_optional_secret(
            cfg,
            "redisUrl",
        ),
        qdrant_url=_optional_secret(
            cfg,
            "qdrantUrl",
        ),
        ollama_base_url=_optional_secret(
            cfg,
            "ollamaBaseUrl",
        ),

        min_replicas=min_replicas,
        max_replicas=max_replicas,

        worker_min_replicas=worker_min_replicas,
        worker_max_replicas=worker_max_replicas,

        log_retention_days=log_retention_days,

        # Important:
        # Default is intentionally FALSE.
        # Foundation is deployed before runtime apps.
        deploy_apps=_bool(
            cfg,
            "deployApps",
            False,
        ),

        deploy_background_services=_bool(
            cfg,
            "deployBackgroundServices",
            False,
        ),

        deploy_research_agent=_bool(
            cfg,
            "deployResearchAgent",
            False,
        ),

        deploy_a2a_coordinator=_bool(
            cfg,
            "deployA2ACoordinator",
            False,
        ),

        backend_cpu=float(
            cfg.get("backendCpu")
            or "1.0"
        ),
        backend_memory=(
            cfg.get("backendMemory")
            or "2Gi"
        ),

        frontend_cpu=float(
            cfg.get("frontendCpu")
            or "0.5"
        ),
        frontend_memory=(
            cfg.get("frontendMemory")
            or "1Gi"
        ),

        policy_cpu=float(
            cfg.get("policyCpu")
            or "0.5"
        ),
        policy_memory=(
            cfg.get("policyMemory")
            or "1Gi"
        ),
    )