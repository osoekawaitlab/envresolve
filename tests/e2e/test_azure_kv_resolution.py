"""E2E tests for Azure Key Vault secret resolution with mocked SDK.

These tests use mocked Azure SDK components to verify the integration
without requiring actual Azure resources.
"""

import os
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from azure.core.exceptions import ResourceNotFoundError
from pytest_mock import MockFixture

import envresolve

if TYPE_CHECKING:
    from azure.keyvault.secrets import KeyVaultSecret

# Mark all tests in this file as requiring Azure
pytestmark = pytest.mark.azure


class AzureSDKMocks:
    """Type-safe Azure SDK mock container."""

    def __init__(self) -> None:
        """Initialize mock objects."""
        self.credential: MagicMock = MagicMock(spec=["get_token"])
        self.secret_client: MagicMock = MagicMock(spec=["get_secret"])
        self.secret: MagicMock = MagicMock(spec=["value", "name", "properties"])

    def set_secret_value(self, value: str) -> None:
        """Set the mock secret value."""
        self.secret.value = value
        self.secret_client.get_secret.return_value = self.secret

    def set_secret_getter(
        self, getter: Callable[[str, str | None], "KeyVaultSecret"]
    ) -> None:
        """Set a custom secret getter function."""
        self.secret_client.get_secret.side_effect = getter

    def raise_not_found(self) -> None:
        """Configure mock to raise ResourceNotFoundError."""
        self.secret_client.get_secret.side_effect = ResourceNotFoundError(
            "Secret not found"
        )


@pytest.fixture
def azure_mocks(mocker: MockFixture) -> AzureSDKMocks:
    """Fixture providing configured Azure SDK mocks.

    Returns:
        AzureSDKMocks: Container with credential, secret_client, and secret mocks
    """
    mocks = AzureSDKMocks()

    # Patch Azure SDK imports
    mocker.patch(
        "envresolve.providers.azure_kv.DefaultAzureCredential",
        return_value=mocks.credential,
    )
    mocker.patch(
        "envresolve.providers.azure_kv.SecretClient",
        return_value=mocks.secret_client,
    )

    # Register provider after mocks are in place
    envresolve.register_azure_kv_provider()

    return mocks


@pytest.mark.e2e
def test_resolve_simple_akv_uri(azure_mocks: AzureSDKMocks) -> None:
    """Test resolving a simple akv:// URI."""
    azure_mocks.set_secret_value("secret-value-123")

    result = envresolve.resolve_secret("akv://my-vault/db-password")

    assert result == "secret-value-123"
    azure_mocks.secret_client.get_secret.assert_called_once_with(
        "db-password", version=None
    )


@pytest.mark.e2e
def test_resolve_akv_uri_with_version(azure_mocks: AzureSDKMocks) -> None:
    """Test resolving akv:// URI with specific version."""
    azure_mocks.set_secret_value("secret-v2")

    result = envresolve.resolve_secret("akv://my-vault/api-key?version=abc123")

    assert result == "secret-v2"
    azure_mocks.secret_client.get_secret.assert_called_once_with(
        "api-key", version="abc123"
    )


@pytest.mark.e2e
def test_resolve_with_variable_expansion(
    azure_mocks: AzureSDKMocks, mocker: MockFixture
) -> None:
    """Test resolving URI with variable expansion."""
    azure_mocks.set_secret_value("expanded-secret")
    mocker.patch.dict(os.environ, {"VAULT_NAME": "my-company-vault"})

    result = envresolve.resolve_secret("akv://${VAULT_NAME}/db-password")

    assert result == "expanded-secret"
    azure_mocks.secret_client.get_secret.assert_called_once_with(
        "db-password", version=None
    )


@pytest.mark.e2e
def test_load_env_with_akv_uris(azure_mocks: AzureSDKMocks, tmp_path: Path) -> None:
    """Test load_env() resolves akv:// URIs in .env file."""
    # Create .env file
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DB_PASSWORD=akv://vault/db-pass\n"
        "API_KEY=akv://vault/api-key\n"
        "PLAIN_VALUE=just-a-string\n"
    )

    # Configure mock to return different values based on secret name
    def get_secret_by_name(name: str, version: str | None = None) -> MagicMock:  # noqa: ARG001
        mock = MagicMock()
        secrets = {
            "db-pass": "resolved-db-password",
            "api-key": "resolved-api-key",
        }
        mock.value = secrets.get(name, "")
        return mock

    azure_mocks.set_secret_getter(get_secret_by_name)

    # Load and resolve
    result = envresolve.load_env(str(env_file), export=False)

    assert result["DB_PASSWORD"] == "resolved-db-password"
    assert result["API_KEY"] == "resolved-api-key"
    assert result["PLAIN_VALUE"] == "just-a-string"


@pytest.mark.e2e
def test_non_target_uri_passthrough() -> None:
    """Test that non-target URIs (e.g., postgres://) pass through unchanged."""
    # No Azure mocks needed - should not be called
    envresolve.register_azure_kv_provider()

    result = envresolve.resolve_secret("postgres://localhost:5432/mydb")

    assert result == "postgres://localhost:5432/mydb"


@pytest.mark.e2e
def test_idempotent_resolution() -> None:
    """Test that resolving an already-resolved value is idempotent."""
    envresolve.register_azure_kv_provider()

    plain = "already-resolved-value"
    result1 = envresolve.resolve_secret(plain)
    result2 = envresolve.resolve_secret(result1)

    assert result1 == plain
    assert result2 == plain


@pytest.mark.e2e
def test_invalid_uri_raises_error() -> None:
    """Test that invalid akv:// URI raises appropriate error."""
    envresolve.register_azure_kv_provider()

    # Invalid URI (missing secret name)
    with pytest.raises(envresolve.URIParseError) as exc:
        envresolve.resolve_secret("akv://vault/")

    assert "vault" in str(exc.value) or "secret" in str(exc.value).lower()


@pytest.mark.e2e
def test_missing_secret_raises_error(azure_mocks: AzureSDKMocks) -> None:
    """Test that missing secret in Key Vault raises appropriate error."""
    azure_mocks.raise_not_found()

    with pytest.raises(envresolve.SecretResolutionError) as exc:
        envresolve.resolve_secret("akv://vault/nonexistent")

    assert (
        "nonexistent" in str(exc.value).lower() or "not found" in str(exc.value).lower()
    )
