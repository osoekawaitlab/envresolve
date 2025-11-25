"""Azure Key Vault provider implementation."""

import logging
from typing import TYPE_CHECKING

from azure.core.exceptions import AzureError
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from envresolve.exceptions import SecretResolutionError
from envresolve.models import ParsedURI

if TYPE_CHECKING:
    from azure.core.credentials import TokenCredential


class AzureKVProvider:
    """Provider for resolving secrets from Azure Key Vault.

    Supports both akv:// and kv:// URI schemes.
    Uses DefaultAzureCredential for authentication.
    Caches SecretClient instances per vault for efficiency.
    """

    def __init__(self, credential: "TokenCredential | None" = None) -> None:
        """Initialize Azure Key Vault provider.

        Args:
            credential: Azure credential to use.
                If None, DefaultAzureCredential is used.
        """
        self.credential = credential or DefaultAzureCredential()
        self._clients: dict[str, SecretClient] = {}

    def _get_client(self, vault_name: str) -> SecretClient:
        """Get or create a SecretClient for the given vault.

        Args:
            vault_name: Name of the Key Vault

        Returns:
            SecretClient instance for the vault
        """
        if vault_name not in self._clients:
            vault_url = f"https://{vault_name}.vault.azure.net"
            self._clients[vault_name] = SecretClient(
                vault_url=vault_url, credential=self.credential
            )
        return self._clients[vault_name]

    def resolve(
        self,
        parsed_uri: ParsedURI,
        logger: logging.Logger | None = None,  # noqa: ARG002
    ) -> str:
        """Resolve a secret from Azure Key Vault.

        Args:
            parsed_uri: Parsed URI dictionary containing vault, secret,
                and optional version
            logger: Optional logger for diagnostic messages

        Returns:
            The secret value as a string

        Raises:
            SecretResolutionError: If the secret cannot be resolved
        """
        vault_name = parsed_uri["vault"]
        secret_name = parsed_uri["secret"]
        version = parsed_uri["version"]

        # Reconstruct URI for error messages
        uri = f"{parsed_uri['scheme']}://{vault_name}/{secret_name}"
        if version:
            uri = f"{uri}?version={version}"

        try:
            client = self._get_client(vault_name)
            secret = client.get_secret(secret_name, version=version)
        except AzureError as e:
            msg = "Failed to resolve secret from Azure Key Vault"
            raise SecretResolutionError(msg, uri=uri, original_error=e) from e
        else:
            if secret.value is None:
                msg = "Secret value is None"
                raise SecretResolutionError(msg, uri=uri)
            return secret.value
