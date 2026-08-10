from __future__ import annotations
from dataclasses import dataclass
import pulumi
from pulumi_azure_native import keyvault
from config import AzureSettings
from foundation import Foundation

@dataclass(frozen=True, slots=True)
class SecretReferences:
    postgres_password_url: pulumi.Output[str]
    secret_key_url: pulumi.Output[str]
    api_key_pepper_url: pulumi.Output[str]
    redis_url: pulumi.Output[str] | None
    qdrant_url: pulumi.Output[str] | None
    ollama_base_url: pulumi.Output[str] | None

def _url(vault_name, secret_name: str):
    return pulumi.Output.from_input(vault_name).apply(lambda n: f'https://{n}.vault.azure.net/secrets/{secret_name}')

class Secrets:
    def __init__(self, settings: AzureSettings, foundation: Foundation) -> None:
        def create(logical: str, secret_name: str, value):
            return keyvault.Secret(logical, resource_group_name=foundation.resource_group.name, vault_name=foundation.key_vault.name, secret_name=secret_name, properties=keyvault.SecretPropertiesArgs(value=value))
        self.postgres_password = create('postgres-password-secret', 'postgres-password', settings.postgres_password)
        self.secret_key = create('app-secret-key-secret', 'app-secret-key', settings.secret_key)
        self.api_key_pepper = create('api-key-pepper-secret', 'api-key-pepper', settings.api_key_pepper)
        self.redis = create('redis-url-secret', 'redis-url', settings.redis_url) if settings.redis_url is not None else None
        self.qdrant = create('qdrant-url-secret', 'qdrant-url', settings.qdrant_url) if settings.qdrant_url is not None else None
        self.ollama = create('ollama-url-secret', 'ollama-base-url', settings.ollama_base_url) if settings.ollama_base_url is not None else None
        self.refs = SecretReferences(_url(foundation.key_vault.name, 'postgres-password'), _url(foundation.key_vault.name, 'app-secret-key'), _url(foundation.key_vault.name, 'api-key-pepper'), _url(foundation.key_vault.name, 'redis-url') if self.redis else None, _url(foundation.key_vault.name, 'qdrant-url') if self.qdrant else None, _url(foundation.key_vault.name, 'ollama-base-url') if self.ollama else None)
