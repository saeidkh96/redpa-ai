from __future__ import annotations
from pulumi_azure_native import authorization, containerregistry, keyvault, operationalinsights, resources
from config import AzureSettings
from naming import acr_name, resource_name
from tags import standard_tags

class Foundation:
    def __init__(self, settings: AzureSettings) -> None:
        tags = standard_tags(project=settings.project_name, environment=settings.environment)
        self.resource_group = resources.ResourceGroup('resource-group', resource_group_name=resource_name(settings.project_name, settings.environment, 'rg'), location=settings.location, tags=tags)
        self.log_workspace = operationalinsights.Workspace('log-analytics', workspace_name=resource_name(settings.project_name, settings.environment, 'logs'), resource_group_name=self.resource_group.name, location=self.resource_group.location, retention_in_days=settings.log_retention_days, sku=operationalinsights.WorkspaceSkuArgs(name='PerGB2018'), tags=tags)
        self.log_shared_keys = operationalinsights.get_shared_keys_output(resource_group_name=self.resource_group.name, workspace_name=self.log_workspace.name)
        self.registry = containerregistry.Registry('container-registry', registry_name=acr_name(settings.project_name, settings.environment), resource_group_name=self.resource_group.name, location=self.resource_group.location, admin_user_enabled=False, sku=containerregistry.SkuArgs(name='Basic'), tags=tags)
        self.client = authorization.get_client_config_output()
        self.key_vault = keyvault.Vault('key-vault', vault_name=resource_name(settings.project_name, settings.environment, 'kv', max_length=24), resource_group_name=self.resource_group.name, location=self.resource_group.location, properties=keyvault.VaultPropertiesArgs(tenant_id=self.client.tenant_id, enable_rbac_authorization=True, enable_soft_delete=True, soft_delete_retention_in_days=7, public_network_access='Enabled', sku=keyvault.SkuArgs(family='A', name='standard')), tags=tags)
