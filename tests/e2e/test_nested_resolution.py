"""E2E tests for nested URI resolution and variable expansion.

These tests verify that the resolver can handle:
- URI that resolves to another URI
- Multiple levels of variable expansion and URI resolution
- Circular reference detection across resolution steps
"""

import os
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
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
def test_uri_resolves_to_another_uri(azure_mocks: AzureSDKMocks) -> None:
    """Test URI resolution when the result is another URI."""

    # Setup: vault1/indirect contains "akv://vault2/actual"
    def get_secret_by_name(name: str, version: str | None = None) -> MagicMock:  # noqa: ARG001
        mock = MagicMock()
        secrets = {
            "indirect": "akv://vault2/actual",
            "actual": "final-password",
        }
        mock.value = secrets.get(name, "")
        return mock

    azure_mocks.set_secret_getter(get_secret_by_name)

    result = envresolve.resolve_secret("akv://vault1/indirect")

    assert result == "final-password"
    # Should resolve twice
    expected_resolution_count = 2
    assert azure_mocks.secret_client.get_secret.call_count == expected_resolution_count


@pytest.mark.e2e
def test_variable_expansion_then_uri_resolution(
    azure_mocks: AzureSDKMocks, mocker: MockFixture
) -> None:
    """Test variable expansion followed by URI resolution."""
    azure_mocks.set_secret_value("resolved-password")
    mocker.patch.dict(os.environ, {"SECRET_NAME": "db-password"})

    result = envresolve.resolve_secret("akv://my-vault/${SECRET_NAME}")

    assert result == "resolved-password"
    azure_mocks.secret_client.get_secret.assert_called_once_with(
        "db-password", version=None
    )


@pytest.mark.e2e
def test_nested_variable_and_uri_resolution(
    azure_mocks: AzureSDKMocks, mocker: MockFixture
) -> None:
    """Test multiple levels of variable expansion and URI resolution."""
    # Setup environment
    mocker.patch.dict(
        os.environ,
        {
            "VAULT_NAME": "vault1",
            "SECRET_KEY": "indirect",
        },
    )

    # Setup secrets: vault1/indirect → "akv://vault2/${FINAL_KEY}"
    # Need FINAL_KEY in environment for second expansion
    mocker.patch.dict(os.environ, {"FINAL_KEY": "actual"}, clear=False)

    def get_secret_by_name(name: str, version: str | None = None) -> MagicMock:  # noqa: ARG001
        mock = MagicMock()
        secrets = {
            "indirect": "akv://vault2/${FINAL_KEY}",
            "actual": "final-value",
        }
        mock.value = secrets.get(name, "")
        return mock

    azure_mocks.set_secret_getter(get_secret_by_name)

    result = envresolve.resolve_secret("akv://${VAULT_NAME}/${SECRET_KEY}")

    assert result == "final-value"


@pytest.mark.e2e
def test_three_level_uri_chain(azure_mocks: AzureSDKMocks) -> None:
    """Test URI chain with three levels of resolution."""

    def get_secret_by_name(name: str, version: str | None = None) -> MagicMock:  # noqa: ARG001
        mock = MagicMock()
        secrets = {
            "level1": "akv://vault/level2",
            "level2": "akv://vault/level3",
            "level3": "final-secret",
        }
        mock.value = secrets.get(name, "")
        return mock

    azure_mocks.set_secret_getter(get_secret_by_name)

    result = envresolve.resolve_secret("akv://vault/level1")

    assert result == "final-secret"
    expected_resolution_count = 3
    assert azure_mocks.secret_client.get_secret.call_count == expected_resolution_count


@pytest.mark.e2e
def test_circular_reference_in_uri_chain(azure_mocks: AzureSDKMocks) -> None:
    """Test that circular URI references are detected."""

    def get_secret_by_name(name: str, version: str | None = None) -> MagicMock:  # noqa: ARG001
        mock = MagicMock()
        secrets = {
            "secret1": "akv://vault/secret2",
            "secret2": "akv://vault/secret1",  # Circular!
        }
        mock.value = secrets.get(name, "")
        return mock

    azure_mocks.set_secret_getter(get_secret_by_name)

    with pytest.raises(envresolve.CircularReferenceError) as exc:
        envresolve.resolve_secret("akv://vault/secret1")

    assert "secret1" in str(exc.value) or "circular" in str(exc.value).lower()


@pytest.mark.e2e
def test_idempotent_resolution_with_plain_value(
    azure_mocks: AzureSDKMocks,
) -> None:
    """Test that plain values (non-URI) stop resolution immediately."""
    azure_mocks.set_secret_value("just-a-plain-value")

    result = envresolve.resolve_secret("akv://vault/simple")

    assert result == "just-a-plain-value"
    # Should only resolve once since result is not a URI
    azure_mocks.secret_client.get_secret.assert_called_once()


@pytest.mark.e2e
def test_load_env_with_nested_resolution(
    azure_mocks: AzureSDKMocks, tmp_path: Path
) -> None:
    """Test load_env with nested URI resolution."""
    # Create .env file
    env_file = tmp_path / ".env"
    env_file.write_text("INDIRECT_URI=akv://vault/indirect\nDIRECT_VALUE=plain-text\n")

    # Configure mock
    def get_secret_by_name(name: str, version: str | None = None) -> MagicMock:  # noqa: ARG001
        mock = MagicMock()
        secrets = {
            "indirect": "akv://vault/actual",
            "actual": "final-password",
        }
        mock.value = secrets.get(name, "")
        return mock

    azure_mocks.set_secret_getter(get_secret_by_name)

    result = envresolve.load_env(str(env_file), export=False)

    assert result["INDIRECT_URI"] == "final-password"
    assert result["DIRECT_VALUE"] == "plain-text"
