"""Unit tests for Azure Key Vault provider."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from azure.core.exceptions import ResourceNotFoundError
from pytest_mock import MockFixture

from envresolve.exceptions import SecretResolutionError
from envresolve.providers.azure_kv import AzureKVProvider

if TYPE_CHECKING:
    from envresolve.models import ParsedURI

# Mark all tests in this file as requiring Azure
pytestmark = pytest.mark.azure


class AzureProviderMocks:
    """Type-safe mock container for Azure provider unit tests."""

    def __init__(self) -> None:
        """Initialize mock objects with proper specs."""
        self.credential: MagicMock = MagicMock(spec=["get_token"])
        self.secret_client_class: MagicMock = MagicMock()
        self.secret_client: MagicMock = MagicMock(spec=["get_secret"])
        self.secret: MagicMock = MagicMock(spec=["value", "name", "properties"])

        # Configure default behavior
        self.secret_client_class.return_value = self.secret_client

    def set_secret_value(self, value: str) -> None:
        """Configure mock to return a secret with the given value."""
        self.secret.value = value
        self.secret_client.get_secret.return_value = self.secret

    def raise_not_found(self) -> None:
        """Configure mock to raise ResourceNotFoundError."""
        self.secret_client.get_secret.side_effect = ResourceNotFoundError("Not found")

    def create_provider(self) -> AzureKVProvider:
        """Create an AzureKVProvider instance with mocked dependencies."""
        return AzureKVProvider(credential=self.credential)


@pytest.fixture
def azure_provider_mocks(mocker: MockFixture) -> AzureProviderMocks:
    """Fixture providing configured Azure provider mocks.

    Returns:
        AzureProviderMocks: Container with credential and client mocks
    """
    mocks = AzureProviderMocks()

    # Patch Azure SDK imports
    mocker.patch(
        "envresolve.providers.azure_kv.DefaultAzureCredential",
        return_value=mocks.credential,
    )
    mocker.patch(
        "envresolve.providers.azure_kv.SecretClient",
        mocks.secret_client_class,
    )

    return mocks


def test_azure_kv_provider_exists() -> None:
    """Test that AzureKVProvider class exists."""
    assert AzureKVProvider is not None


def test_azure_kv_provider_resolve_simple(
    azure_provider_mocks: AzureProviderMocks,
) -> None:
    """Test resolving a simple secret without version."""
    azure_provider_mocks.set_secret_value("secret-value-123")
    provider = azure_provider_mocks.create_provider()

    parsed_uri: ParsedURI = {
        "scheme": "akv",
        "vault": "my-vault",
        "secret": "db-password",
        "version": None,
    }
    result = provider.resolve(parsed_uri)

    assert result == "secret-value-123"
    azure_provider_mocks.secret_client.get_secret.assert_called_once_with(
        "db-password", version=None
    )


def test_azure_kv_provider_resolve_with_version(
    azure_provider_mocks: AzureProviderMocks,
) -> None:
    """Test resolving a secret with specific version."""
    azure_provider_mocks.set_secret_value("secret-v2")
    provider = azure_provider_mocks.create_provider()

    parsed_uri: ParsedURI = {
        "scheme": "akv",
        "vault": "vault",
        "secret": "api-key",
        "version": "abc123",
    }
    result = provider.resolve(parsed_uri)

    assert result == "secret-v2"
    azure_provider_mocks.secret_client.get_secret.assert_called_once_with(
        "api-key", version="abc123"
    )


def test_azure_kv_provider_raises_on_not_found(
    azure_provider_mocks: AzureProviderMocks,
) -> None:
    """Test that provider raises SecretResolutionError when secret not found."""
    azure_provider_mocks.raise_not_found()
    provider = azure_provider_mocks.create_provider()

    parsed_uri: ParsedURI = {
        "scheme": "akv",
        "vault": "vault",
        "secret": "nonexistent",
        "version": None,
    }

    with pytest.raises(SecretResolutionError) as exc:
        provider.resolve(parsed_uri)

    assert "nonexistent" in str(exc.value) or "not found" in str(exc.value).lower()
    assert exc.value.original_error is not None


def test_azure_kv_provider_caches_clients(
    azure_provider_mocks: AzureProviderMocks,
) -> None:
    """Test that provider caches SecretClient instances per vault."""
    azure_provider_mocks.set_secret_value("value")
    provider = azure_provider_mocks.create_provider()

    # Resolve multiple secrets from same vault
    vault1_secret1: ParsedURI = {
        "scheme": "akv",
        "vault": "vault1",
        "secret": "secret1",
        "version": None,
    }
    vault1_secret2: ParsedURI = {
        "scheme": "akv",
        "vault": "vault1",
        "secret": "secret2",
        "version": None,
    }

    provider.resolve(vault1_secret1)
    provider.resolve(vault1_secret2)

    # SecretClient should be created only once for vault1
    assert azure_provider_mocks.secret_client_class.call_count == 1


def test_azure_kv_provider_creates_clients_per_vault(
    azure_provider_mocks: AzureProviderMocks,
) -> None:
    """Test that provider creates separate SecretClient for each vault."""
    azure_provider_mocks.set_secret_value("value")
    provider = azure_provider_mocks.create_provider()

    # Resolve secrets from different vaults
    vault1_secret: ParsedURI = {
        "scheme": "akv",
        "vault": "vault1",
        "secret": "secret1",
        "version": None,
    }
    vault2_secret: ParsedURI = {
        "scheme": "akv",
        "vault": "vault2",
        "secret": "secret2",
        "version": None,
    }

    provider.resolve(vault1_secret)
    provider.resolve(vault2_secret)

    # SecretClient should be created twice (once per vault)
    expected_client_count = 2
    assert azure_provider_mocks.secret_client_class.call_count == expected_client_count
