from __future__ import annotations

from collections.abc import Sequence

import pulumi
from pulumi_azure_native import app

from config import AzureSettings
from database import Database
from foundation import Foundation
from identity import Identity
from naming import resource_name
from secrets import Secrets
from tags import standard_tags


def _env(
    name: str,
    value: pulumi.Input[str] | None = None,
    *,
    secret_ref: str | None = None,
) -> app.EnvironmentVarArgs:
    if secret_ref is not None:
        return app.EnvironmentVarArgs(
            name=name,
            secret_ref=secret_ref,
        )

    return app.EnvironmentVarArgs(
        name=name,
        value=value,
    )


def _url(
    container_app: app.ContainerApp,
) -> pulumi.Output[str]:
    return container_app.latest_revision_fqdn.apply(
        lambda fqdn: (
            f"https://{fqdn}"
            if fqdn
            else ""
        )
    )


def _identity_args(
    identity: Identity,
) -> app.ManagedServiceIdentityArgs:
    return app.ManagedServiceIdentityArgs(
        type="UserAssigned",
        user_assigned_identities=identity.identity_map,
    )


def _registry_credentials(
    foundation: Foundation,
    identity: Identity,
) -> list[app.RegistryCredentialsArgs]:
    return [
        app.RegistryCredentialsArgs(
            server=foundation.registry.login_server,
            identity=identity.app_identity.id,
        )
    ]


def _key_vault_secret(
    *,
    name: str,
    url: pulumi.Input[str],
    identity: Identity,
) -> app.SecretArgs:
    return app.SecretArgs(
        name=name,
        key_vault_url=url,
        identity=identity.app_identity.id,
    )


class ContainerApps:
    def __init__(
        self,
        settings: AzureSettings,
        foundation: Foundation,
        identity: Identity,
        secrets: Secrets,
        database: Database,
    ) -> None:
        tags = standard_tags(
            project=settings.project_name,
            environment=settings.environment,
        )

        #
        # Container Apps Environment belongs to the
        # foundation layer and is ALWAYS created.
        #
        self.environment = app.ManagedEnvironment(
            "container-apps-environment",
            environment_name=resource_name(
                settings.project_name,
                settings.environment,
                "cae",
            ),
            resource_group_name=(
                foundation.resource_group.name
            ),
            location=(
                foundation.resource_group.location
            ),
            app_logs_configuration=(
                app.AppLogsConfigurationArgs(
                    destination="log-analytics",
                    log_analytics_configuration=(
                        app.LogAnalyticsConfigurationArgs(
                            customer_id=(
                                foundation
                                .log_workspace
                                .customer_id
                            ),
                            shared_key=(
                                foundation
                                .log_shared_keys
                                .primary_shared_key
                            ),
                        )
                    ),
                )
            ),
            tags=tags,
        )

        #
        # Safe default outputs for foundation-only mode.
        #
        self.policy = None
        self.backend = None
        self.frontend = None

        self.background_worker = None
        self.background_scheduler = None
        self.research_agent = None
        self.a2a_coordinator = None

        self.policy_url = pulumi.Output.from_input("")
        self.backend_url = pulumi.Output.from_input("")
        self.frontend_url = pulumi.Output.from_input("")

        #
        # CRITICAL:
        # Foundation-only mode stops here.
        #
        if not settings.deploy_apps:
            pulumi.log.info(
                "redpa:deployApps=false — "
                "skipping all RedPA runtime Container Apps."
            )
            return

        common_secrets: list[app.SecretArgs] = [
            _key_vault_secret(
                name="postgres-password",
                url=secrets.refs.postgres_password_url,
                identity=identity,
            ),
            _key_vault_secret(
                name="app-secret-key",
                url=secrets.refs.secret_key_url,
                identity=identity,
            ),
            _key_vault_secret(
                name="api-key-pepper",
                url=secrets.refs.api_key_pepper_url,
                identity=identity,
            ),
        ]

        if secrets.refs.redis_url is not None:
            common_secrets.append(
                _key_vault_secret(
                    name="redis-url",
                    url=secrets.refs.redis_url,
                    identity=identity,
                )
            )

        if secrets.refs.qdrant_url is not None:
            common_secrets.append(
                _key_vault_secret(
                    name="qdrant-url",
                    url=secrets.refs.qdrant_url,
                    identity=identity,
                )
            )

        if secrets.refs.ollama_base_url is not None:
            common_secrets.append(
                _key_vault_secret(
                    name="ollama-base-url",
                    url=secrets.refs.ollama_base_url,
                    identity=identity,
                )
            )

        #
        # Policy Service
        #
        self.policy = self._container_app(
            logical_name="policy-service",
            app_name=resource_name(
                settings.project_name,
                settings.environment,
                "policy",
            ),
            image=settings.policy_image,
            foundation=foundation,
            identity=identity,
            tags=tags,
            external=False,
            target_port=8090,
            cpu=settings.policy_cpu,
            memory=settings.policy_memory,
            min_replicas=settings.min_replicas,
            max_replicas=settings.max_replicas,
            env=[],
            secrets=[],
        )

        self.policy_url = _url(
            self.policy
        )

        #
        # Backend environment
        #
        backend_env = [
            _env(
                "APP_NAME",
                "RedPA AI",
            ),
            _env(
                "ENVIRONMENT",
                settings.environment,
            ),
            _env(
                "DEBUG",
                "false",
            ),
            _env(
                "LOG_LEVEL",
                "INFO",
            ),
            _env(
                "JSON_LOGS",
                "true",
            ),
            _env(
                "API_V1_PREFIX",
                "/api/v1",
            ),
            _env(
                "HOST",
                "0.0.0.0",
            ),
            _env(
                "PORT",
                "8000",
            ),
            _env(
                "DATABASE_URL",
                database.database_url,
            ),
            _env(
                "SECRET_KEY",
                secret_ref="app-secret-key",
            ),
            _env(
                "API_KEY_PEPPER",
                secret_ref="api-key-pepper",
            ),
            _env(
                "POLICY_SERVICE_URL",
                self.policy_url,
            ),
            _env(
                "EXPOSE_ERROR_DETAILS",
                "false",
            ),
            _env(
                "REQUIRE_HTTPS",
                "true",
            ),
            _env(
                "RATE_LIMIT_REQUESTS",
                "120",
            ),
            _env(
                "RATE_LIMIT_WINDOW_SECONDS",
                "60",
            ),
            _env(
                "IDEMPOTENCY_TTL_SECONDS",
                "86400",
            ),
            _env(
                "BACKGROUND_WORKER_POLL_SECONDS",
                "2",
            ),
            _env(
                "BACKGROUND_WORKER_CONCURRENCY",
                "4",
            ),
            _env(
                "SLOW_REQUEST_THRESHOLD_MS",
                "1000",
            ),
            _env(
                "SLOW_QUERY_THRESHOLD_MS",
                "500",
            ),
            _env(
                "REQUEST_ID_HEADER",
                "X-Request-ID",
            ),
            _env(
                "CORRELATION_ID_HEADER",
                "X-Correlation-ID",
            ),
        ]

        if settings.redis_url is not None:
            backend_env.append(
                _env(
                    "REDIS_URL",
                    secret_ref="redis-url",
                )
            )

        if settings.qdrant_url is not None:
            backend_env.append(
                _env(
                    "QDRANT_URL",
                    secret_ref="qdrant-url",
                )
            )

        if settings.ollama_base_url is not None:
            backend_env.append(
                _env(
                    "OLLAMA_BASE_URL",
                    secret_ref="ollama-base-url",
                )
            )

        #
        # Backend
        #
        self.backend = self._container_app(
            logical_name="backend",
            app_name=resource_name(
                settings.project_name,
                settings.environment,
                "backend",
            ),
            image=settings.backend_image,
            foundation=foundation,
            identity=identity,
            tags=tags,
            external=True,
            target_port=8000,
            cpu=settings.backend_cpu,
            memory=settings.backend_memory,
            min_replicas=settings.min_replicas,
            max_replicas=settings.max_replicas,
            env=backend_env,
            secrets=common_secrets,
        )

        self.backend_url = _url(
            self.backend
        )

        #
        # Frontend
        #
        self.frontend = self._container_app(
            logical_name="frontend",
            app_name=resource_name(
                settings.project_name,
                settings.environment,
                "frontend",
            ),
            image=settings.frontend_image,
            foundation=foundation,
            identity=identity,
            tags=tags,
            external=True,
            target_port=3001,
            cpu=settings.frontend_cpu,
            memory=settings.frontend_memory,
            min_replicas=settings.min_replicas,
            max_replicas=settings.max_replicas,
            env=[
                _env(
                    "NEXT_PUBLIC_API_BASE_URL",
                    self.backend_url.apply(
                        lambda url: (
                            f"{url}/api/v1"
                        )
                    ),
                ),
            ],
            secrets=[],
        )

        self.frontend_url = _url(
            self.frontend
        )

        #
        # Background services
        #
        if settings.deploy_background_services:
            self.background_worker = (
                self._container_app(
                    logical_name="background-worker",
                    app_name=resource_name(
                        settings.project_name,
                        settings.environment,
                        "worker",
                    ),
                    image=settings.backend_image,
                    foundation=foundation,
                    identity=identity,
                    tags=tags,
                    external=False,
                    target_port=None,
                    cpu=0.5,
                    memory="1Gi",
                    min_replicas=(
                        settings.worker_min_replicas
                    ),
                    max_replicas=(
                        settings.worker_max_replicas
                    ),
                    env=backend_env,
                    secrets=common_secrets,
                    command=[
                        "python",
                    ],
                    args=[
                        "-m",
                        "app.background_jobs.worker",
                    ],
                )
            )

            self.background_scheduler = (
                self._container_app(
                    logical_name="background-scheduler",
                    app_name=resource_name(
                        settings.project_name,
                        settings.environment,
                        "scheduler",
                    ),
                    image=settings.backend_image,
                    foundation=foundation,
                    identity=identity,
                    tags=tags,
                    external=False,
                    target_port=None,
                    cpu=0.25,
                    memory="0.5Gi",
                    min_replicas=1,
                    max_replicas=1,
                    env=backend_env,
                    secrets=common_secrets,
                    command=[
                        "python",
                    ],
                    args=[
                        "-m",
                        "app.background_jobs.scheduler",
                    ],
                )
            )

        #
        # Research Agent
        #
        if settings.deploy_research_agent:
            self.research_agent = (
                self._container_app(
                    logical_name="research-agent",
                    app_name=resource_name(
                        settings.project_name,
                        settings.environment,
                        "research",
                    ),
                    image=settings.backend_image,
                    foundation=foundation,
                    identity=identity,
                    tags=tags,
                    external=False,
                    target_port=8061,
                    cpu=0.5,
                    memory="1Gi",
                    min_replicas=(
                        settings.worker_min_replicas
                    ),
                    max_replicas=(
                        settings.worker_max_replicas
                    ),
                    env=backend_env
                    + [
                        _env(
                            "RESEARCH_AGENT_HOST",
                            "0.0.0.0",
                        ),
                        _env(
                            "RESEARCH_AGENT_PORT",
                            "8061",
                        ),
                    ],
                    secrets=common_secrets,
                    command=[
                        "python",
                    ],
                    args=[
                        "-m",
                        "app.research_agent.server",
                    ],
                )
            )

        #
        # A2A Coordinator
        #
        if settings.deploy_a2a_coordinator:
            self.a2a_coordinator = (
                self._container_app(
                    logical_name="a2a-coordinator",
                    app_name=resource_name(
                        settings.project_name,
                        settings.environment,
                        "a2a",
                    ),
                    image=settings.backend_image,
                    foundation=foundation,
                    identity=identity,
                    tags=tags,
                    external=False,
                    target_port=8050,
                    cpu=0.5,
                    memory="1Gi",
                    min_replicas=(
                        settings.worker_min_replicas
                    ),
                    max_replicas=(
                        settings.worker_max_replicas
                    ),
                    env=backend_env,
                    secrets=common_secrets,
                    command=[
                        "python",
                    ],
                    args=[
                        "-m",
                        "app.a2a_protocol.server",
                    ],
                )
            )

    def _container_app(
        self,
        *,
        logical_name: str,
        app_name: str,
        image: pulumi.Input[str],
        foundation: Foundation,
        identity: Identity,
        tags: dict[str, str],
        external: bool,
        target_port: int | None,
        cpu: float,
        memory: str,
        min_replicas: int,
        max_replicas: int,
        env: Sequence[app.EnvironmentVarArgs],
        secrets: Sequence[app.SecretArgs],
        command: Sequence[str] | None = None,
        args: Sequence[str] | None = None,
    ) -> app.ContainerApp:
        ingress = None

        if target_port is not None:
            ingress = app.IngressArgs(
                external=external,
                target_port=target_port,
                transport="auto",
                allow_insecure=False,
            )

        container = app.ContainerArgs(
            name=logical_name,
            image=image,
            env=list(env),
            command=(
                list(command)
                if command
                else None
            ),
            args=(
                list(args)
                if args
                else None
            ),
            resources=app.ContainerResourcesArgs(
                cpu=cpu,
                memory=memory,
            ),
        )

        return app.ContainerApp(
            logical_name,
            container_app_name=app_name,
            resource_group_name=(
                foundation.resource_group.name
            ),
            environment_id=self.environment.id,
            location=(
                foundation.resource_group.location
            ),
            identity=_identity_args(
                identity
            ),
            configuration=app.ConfigurationArgs(
                active_revisions_mode="Single",
                ingress=ingress,
                registries=_registry_credentials(
                    foundation,
                    identity,
                ),
                secrets=(
                    list(secrets)
                    if secrets
                    else None
                ),
            ),
            template=app.TemplateArgs(
                containers=[
                    container,
                ],
                scale=app.ScaleArgs(
                    min_replicas=min_replicas,
                    max_replicas=max_replicas,
                ),
            ),
            tags=tags,
            opts=pulumi.ResourceOptions(
                depends_on=[
                    identity.acr_pull,
                    identity.key_vault_secrets_user,
                ],
            ),
        )