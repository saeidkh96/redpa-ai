from __future__ import annotations

import pulumi

from config import load_settings
from container_apps import ContainerApps
from database import Database
from foundation import Foundation
from identity import Identity
from observability import Observability
from secrets import Secrets


settings = load_settings()

foundation = Foundation(
    settings,
)

identity = Identity(
    settings,
    foundation,
)

secrets = Secrets(
    settings,
    foundation,
)

database = Database(
    settings,
    foundation,
)

observability = Observability(
    foundation,
)

apps = ContainerApps(
    settings=settings,
    foundation=foundation,
    identity=identity,
    secrets=secrets,
    database=database,
)


#
# Foundation outputs
#

pulumi.export(
    "resourceGroupName",
    foundation.resource_group.name,
)

pulumi.export(
    "containerRegistryLoginServer",
    foundation.registry.login_server,
)

pulumi.export(
    "keyVaultName",
    foundation.key_vault.name,
)

pulumi.export(
    "managedIdentityId",
    identity.app_identity.id,
)

pulumi.export(
    "postgresHost",
    database.host,
)

pulumi.export(
    "containerAppsEnvironmentName",
    apps.environment.name,
)

pulumi.export(
    "logAnalyticsWorkspaceName",
    observability.outputs.log_analytics_workspace_name,
)


#
# Runtime outputs
#
# Empty strings are expected while deployApps=false.
#

pulumi.export(
    "backendUrl",
    apps.backend_url,
)

pulumi.export(
    "frontendUrl",
    apps.frontend_url,
)

pulumi.export(
    "policyUrl",
    apps.policy_url,
)

pulumi.export(
    "runtimeAppsEnabled",
    settings.deploy_apps,
)