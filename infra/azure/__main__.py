from __future__ import annotations

import pulumi

from config import load_settings
from container_apps import ContainerApps
from database import Database
from foundation import Foundation


settings = load_settings()
foundation = Foundation(settings)
database = Database(settings, foundation)
apps = ContainerApps(
    settings,
    foundation,
    database,
)

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
    "postgresHost",
    database.host,
)
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
