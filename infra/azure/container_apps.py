from __future__ import annotations

import pulumi
from pulumi_azure_native import app

from config import AzureSettings
from database import Database
from foundation import Foundation
from naming import resource_name
from tags import standard_tags


def _env(
    name: str,
    value: pulumi.Input[str] | None,
) -> app.EnvironmentVarArgs | None:
    if value is None:
        return None
    return app.EnvironmentVarArgs(
        name=name,
        value=value,
    )


def _compact(values):
    return [value for value in values if value is not None]


class ContainerApps:
    def __init__(
        self,
        settings: AzureSettings,
        foundation: Foundation,
        database: Database,
    ) -> None:
        tags = standard_tags(
            project=settings.project_name,
            environment=settings.environment,
        )

        self.environment = app.ManagedEnvironment(
            "container-apps-environment",
            environment_name=resource_name(
                settings.project_name,
                settings.environment,
                "cae",
            ),
            resource_group_name=foundation.resource_group.name,
            location=foundation.resource_group.location,
            tags=tags,
        )

        database_url = pulumi.Output.all(
            host=database.host,
            password=settings.postgres_password,
        ).apply(
            lambda values: (
                "postgresql+asyncpg://"
                f"{settings.postgres_admin}:"
                f"{values['password']}@"
                f"{values['host']}:5432/redpa_ai"
            )
        )

        self.policy = app.ContainerApp(
            "policy-service",
            container_app_name=resource_name(
                settings.project_name,
                settings.environment,
                "policy",
            ),
            resource_group_name=foundation.resource_group.name,
            managed_environment_id=self.environment.id,
            location=foundation.resource_group.location,
            configuration=app.ConfigurationArgs(
                ingress=app.IngressArgs(
                    external=False,
                    target_port=8090,
                    transport="auto",
                ),
            ),
            template=app.TemplateArgs(
                containers=[
                    app.ContainerArgs(
                        name="policy-service",
                        image=settings.policy_image,
                        resources=app.ContainerResourcesArgs(
                            cpu=0.5,
                            memory="1Gi",
                        ),
                    )
                ],
                scale=app.ScaleArgs(
                    min_replicas=settings.min_replicas,
                    max_replicas=settings.max_replicas,
                ),
            ),
            tags=tags,
        )

        policy_url = self.policy.properties.apply(
            lambda props: (
                f"https://{props.configuration.ingress.fqdn}"
                if props
                and props.configuration
                and props.configuration.ingress
                and props.configuration.ingress.fqdn
                else ""
            )
        )

        backend_env = _compact(
            [
                _env("ENVIRONMENT", settings.environment),
                _env("DATABASE_URL", database_url),
                _env("POLICY_SERVICE_URL", policy_url),
                _env("REDIS_URL", settings.redis_url),
                _env("QDRANT_URL", settings.qdrant_url),
                _env("OLLAMA_BASE_URL", settings.ollama_base_url),
            ]
        )

        self.backend = app.ContainerApp(
            "backend",
            container_app_name=resource_name(
                settings.project_name,
                settings.environment,
                "backend",
            ),
            resource_group_name=foundation.resource_group.name,
            managed_environment_id=self.environment.id,
            location=foundation.resource_group.location,
            configuration=app.ConfigurationArgs(
                ingress=app.IngressArgs(
                    external=True,
                    target_port=8000,
                    transport="auto",
                ),
            ),
            template=app.TemplateArgs(
                containers=[
                    app.ContainerArgs(
                        name="backend",
                        image=settings.backend_image,
                        env=backend_env,
                        resources=app.ContainerResourcesArgs(
                            cpu=1.0,
                            memory="2Gi",
                        ),
                    )
                ],
                scale=app.ScaleArgs(
                    min_replicas=settings.min_replicas,
                    max_replicas=settings.max_replicas,
                ),
            ),
            tags=tags,
        )

        backend_url = self.backend.properties.apply(
            lambda props: (
                f"https://{props.configuration.ingress.fqdn}"
                if props
                and props.configuration
                and props.configuration.ingress
                and props.configuration.ingress.fqdn
                else ""
            )
        )

        self.frontend = app.ContainerApp(
            "frontend",
            container_app_name=resource_name(
                settings.project_name,
                settings.environment,
                "frontend",
            ),
            resource_group_name=foundation.resource_group.name,
            managed_environment_id=self.environment.id,
            location=foundation.resource_group.location,
            configuration=app.ConfigurationArgs(
                ingress=app.IngressArgs(
                    external=True,
                    target_port=3001,
                    transport="auto",
                ),
            ),
            template=app.TemplateArgs(
                containers=[
                    app.ContainerArgs(
                        name="frontend",
                        image=settings.frontend_image,
                        env=[
                            app.EnvironmentVarArgs(
                                name="NEXT_PUBLIC_API_BASE_URL",
                                value=backend_url.apply(
                                    lambda value: f"{value}/api/v1"
                                ),
                            )
                        ],
                        resources=app.ContainerResourcesArgs(
                            cpu=0.5,
                            memory="1Gi",
                        ),
                    )
                ],
                scale=app.ScaleArgs(
                    min_replicas=settings.min_replicas,
                    max_replicas=settings.max_replicas,
                ),
            ),
            tags=tags,
        )

        self.backend_url = backend_url
        self.frontend_url = self.frontend.properties.apply(
            lambda props: (
                f"https://{props.configuration.ingress.fqdn}"
                if props
                and props.configuration
                and props.configuration.ingress
                and props.configuration.ingress.fqdn
                else ""
            )
        )
        self.policy_url = policy_url
