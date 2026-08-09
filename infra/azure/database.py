from __future__ import annotations

from pulumi_azure_native import dbforpostgresql

from config import AzureSettings
from foundation import Foundation
from naming import resource_name
from tags import standard_tags


class Database:
    def __init__(
        self,
        settings: AzureSettings,
        foundation: Foundation,
    ) -> None:
        tags = standard_tags(
            project=settings.project_name,
            environment=settings.environment,
        )

        self.server = dbforpostgresql.Server(
            "postgres-flex",
            server_name=resource_name(
                settings.project_name,
                settings.environment,
                "pg",
            ),
            resource_group_name=foundation.resource_group.name,
            location=foundation.resource_group.location,
            administrator_login=settings.postgres_admin,
            administrator_login_password=settings.postgres_password,
            version="16",
            sku=dbforpostgresql.SkuArgs(
                name="Standard_B1ms",
                tier="Burstable",
            ),
            storage=dbforpostgresql.StorageArgs(
                storage_size_gb=32,
            ),
            backup=dbforpostgresql.BackupArgs(
                backup_retention_days=7,
                geo_redundant_backup="Disabled",
            ),
            tags=tags,
        )

        self.database = dbforpostgresql.Database(
            "redpa-database",
            database_name="redpa_ai",
            resource_group_name=foundation.resource_group.name,
            server_name=self.server.name,
            charset="UTF8",
            collation="en_US.utf8",
        )

        self.host = self.server.fully_qualified_domain_name
