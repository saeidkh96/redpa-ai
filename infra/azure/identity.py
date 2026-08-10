from __future__ import annotations
import uuid
from pulumi_azure_native import authorization, managedidentity
from config import AzureSettings
from foundation import Foundation
from naming import resource_name
from tags import standard_tags

ACR_PULL_ROLE_ID = '7f951dda-4ed3-4680-a7ca-43fe172d538d'
KEY_VAULT_SECRETS_USER_ROLE_ID = '4633458b-17de-408a-b874-0445c86b69e6'

def _guid(value: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, value))

class Identity:
    def __init__(self, settings: AzureSettings, foundation: Foundation) -> None:
        tags = standard_tags(project=settings.project_name, environment=settings.environment)
        self.app_identity = managedidentity.UserAssignedIdentity('container-app-identity', resource_name_=resource_name(settings.project_name, settings.environment, 'identity'), resource_group_name=foundation.resource_group.name, location=foundation.resource_group.location, tags=tags)
        acr_role = foundation.client.subscription_id.apply(lambda sid: f'/subscriptions/{sid}/providers/Microsoft.Authorization/roleDefinitions/{ACR_PULL_ROLE_ID}')
        kv_role = foundation.client.subscription_id.apply(lambda sid: f'/subscriptions/{sid}/providers/Microsoft.Authorization/roleDefinitions/{KEY_VAULT_SECRETS_USER_ROLE_ID}')
        self.acr_pull = authorization.RoleAssignment('acr-pull-role', role_assignment_name=_guid(f'{settings.project_name}:{settings.environment}:acr-pull'), scope=foundation.registry.id, principal_id=self.app_identity.principal_id, principal_type='ServicePrincipal', role_definition_id=acr_role)
        self.key_vault_secrets_user = authorization.RoleAssignment('key-vault-secrets-user-role', role_assignment_name=_guid(f'{settings.project_name}:{settings.environment}:kv-secrets-user'), scope=foundation.key_vault.id, principal_id=self.app_identity.principal_id, principal_type='ServicePrincipal', role_definition_id=kv_role)
        self.identity_map = self.app_identity.id.apply(lambda rid: {rid: {}})
