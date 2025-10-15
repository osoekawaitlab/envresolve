"""Unit tests for public API functions."""

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockFixture

import envresolve
from envresolve.exceptions import (
    EnvResolveError,
    ProviderRegistrationError,
    SecretResolutionError,
    URIParseError,
)


def test_resolve_secret_exported() -> None:
    """Test that resolve_secret is exported."""
    assert hasattr(envresolve, "resolve_secret")
    assert callable(envresolve.resolve_secret)


def test_load_env_exported() -> None:
    """Test that load_env is exported."""
    assert hasattr(envresolve, "load_env")
    assert callable(envresolve.load_env)


def test_register_azure_kv_provider_exported() -> None:
    """Test that register_azure_kv_provider is exported."""
    assert hasattr(envresolve, "register_azure_kv_provider")
    assert callable(envresolve.register_azure_kv_provider)


def test_uri_parse_error_exported() -> None:
    """Test that URIParseError is exported."""
    assert hasattr(envresolve, "URIParseError")
    assert envresolve.URIParseError is URIParseError


def test_secret_resolution_error_exported() -> None:
    """Test that SecretResolutionError is exported."""
    assert hasattr(envresolve, "SecretResolutionError")
    assert envresolve.SecretResolutionError is SecretResolutionError


def test_provider_registration_error_exported() -> None:
    """Test that ProviderRegistrationError is exported."""
    assert hasattr(envresolve, "ProviderRegistrationError")
    assert envresolve.ProviderRegistrationError is ProviderRegistrationError


def test_env_resolve_error_exported() -> None:
    """Test that EnvResolveError base exception is exported."""
    assert hasattr(envresolve, "EnvResolveError")
    assert envresolve.EnvResolveError is EnvResolveError


def test_resolve_secret_with_plain_string() -> None:
    """Test that resolve_secret passes through non-URI strings (idempotent)."""
    result = envresolve.resolve_secret("just-a-plain-string")
    assert result == "just-a-plain-string"


def test_resolve_secret_with_non_target_uri() -> None:
    """Test that resolve_secret passes through non-target URIs."""
    result = envresolve.resolve_secret("postgres://localhost:5432/db")
    assert result == "postgres://localhost:5432/db"


@pytest.mark.azure
def test_resolve_secret_with_variable_expansion(mocker: MockFixture) -> None:
    """Test that resolve_secret expands variables before resolving."""
    # Mock environment
    mocker.patch.dict("os.environ", {"VAULT_NAME": "my-vault"})

    # Mock Azure SDK
    mock_credential = MagicMock()
    mock_secret_client = MagicMock()
    mock_secret = MagicMock()
    mock_secret.value = "resolved-value"
    mock_secret_client.get_secret.return_value = mock_secret

    mocker.patch(
        "envresolve.providers.azure_kv.DefaultAzureCredential",
        return_value=mock_credential,
    )
    mocker.patch(
        "envresolve.providers.azure_kv.SecretClient",
        return_value=mock_secret_client,
    )

    # Register provider
    envresolve.register_azure_kv_provider()

    result = envresolve.resolve_secret("akv://${VAULT_NAME}/secret")

    # Should expand variable and resolve
    assert result == "resolved-value"
    # Verify the expanded vault name was used
    mock_secret_client.get_secret.assert_called_once_with("secret", version=None)


def test_load_env_returns_dict(tmp_path: Path) -> None:
    """Test that load_env returns a dictionary."""
    env_file = tmp_path / ".env"
    env_file.write_text("KEY=value\n")

    result = envresolve.load_env(str(env_file), export=False)

    assert isinstance(result, dict)
    assert "KEY" in result


def test_load_env_with_export_false(tmp_path: Path, mocker: MockFixture) -> None:
    """Test that load_env with export=False doesn't modify os.environ."""
    env_file = tmp_path / ".env"
    env_file.write_text("TEST_KEY=test_value\n")

    # Track os.environ modifications
    mocker.patch.dict("os.environ", {})

    result = envresolve.load_env(str(env_file), export=False)

    assert result["TEST_KEY"] == "test_value"
    # os.environ should not be modified
    assert "TEST_KEY" not in os.environ


@pytest.mark.azure
def test_register_azure_kv_provider_idempotent() -> None:
    """Test that registering provider multiple times is safe."""
    # Should not raise
    envresolve.register_azure_kv_provider()
    envresolve.register_azure_kv_provider()
