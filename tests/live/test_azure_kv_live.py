"""Live tests that exercise the real Azure Key Vault integration."""

from __future__ import annotations

import os
from dataclasses import dataclass

import pytest
from azure.core.exceptions import ResourceNotFoundError

import envresolve
from envresolve.exceptions import SecretResolutionError

pytest.importorskip("azure.identity")
pytest.importorskip("azure.keyvault.secrets")

pytestmark = [pytest.mark.azure, pytest.mark.live]

REQUIRED_ENV_VARS = {
    "ENVRESOLVE_LIVE_KEY_VAULT_NAME": "key_vault_name",
    "ENVRESOLVE_LIVE_SECRET_NAME": "secret_name",
    "ENVRESOLVE_LIVE_SECRET_VALUE": "secret_value",
}
OPTIONAL_ENV_VARS = {
    "ENVRESOLVE_LIVE_SECRET_VERSION": "secret_version",
}


@dataclass(frozen=True)
class LiveAzureSettings:
    """Container for live Azure Key Vault test configuration."""

    key_vault_name: str
    secret_name: str
    secret_value: str
    secret_version: str | None = None


@pytest.fixture(scope="module")
def live_settings() -> LiveAzureSettings:
    """Collect required environment variables for the live test suite."""
    missing = [env for env in REQUIRED_ENV_VARS if not os.getenv(env)]
    if missing:
        pytest.skip(
            "Azure live-test configuration is incomplete. Missing: "
            + ", ".join(sorted(missing))
        )

    envresolve.register_azure_kv_provider()

    # Build settings with explicit type checking
    return LiveAzureSettings(
        key_vault_name=os.environ["ENVRESOLVE_LIVE_KEY_VAULT_NAME"],
        secret_name=os.environ["ENVRESOLVE_LIVE_SECRET_NAME"],
        secret_value=os.environ["ENVRESOLVE_LIVE_SECRET_VALUE"],
        secret_version=os.getenv("ENVRESOLVE_LIVE_SECRET_VERSION"),
    )


def test_resolve_secret_value(live_settings: LiveAzureSettings) -> None:
    """Ensure a plain akv:// URI resolves to the expected secret value."""
    uri = f"akv://{live_settings.key_vault_name}/{live_settings.secret_name}"

    result = envresolve.resolve_secret(uri)

    assert result == live_settings.secret_value


def test_resolve_secret_with_version(live_settings: LiveAzureSettings) -> None:
    """Ensure akv:// URI with version query resolves correctly."""
    if live_settings.secret_version is None:
        pytest.skip("Secret version not provided in ENVRESOLVE_LIVE_SECRET_VERSION")

    uri = (
        f"akv://{live_settings.key_vault_name}/{live_settings.secret_name}"
        f"?version={live_settings.secret_version}"
    )

    result = envresolve.resolve_secret(uri)

    assert result == live_settings.secret_value


def test_resolve_nonexistent_secret_raises_error(
    live_settings: LiveAzureSettings,
) -> None:
    """Ensure resolving a nonexistent secret raises an appropriate exception."""
    uri = f"akv://{live_settings.key_vault_name}/nonexistent-secret-12345"

    with pytest.raises(SecretResolutionError) as exc_info:
        envresolve.resolve_secret(uri)

    # Verify the error message contains helpful information
    error_msg = str(exc_info.value).lower()
    assert "nonexistent-secret-12345" in error_msg or "not found" in error_msg

    # Verify the original error is ResourceNotFoundError
    assert exc_info.value.__cause__ is not None
    assert isinstance(exc_info.value.__cause__, ResourceNotFoundError)


def test_resolve_secret_with_variable_expansion(
    live_settings: LiveAzureSettings,
) -> None:
    """Ensure variable expansion works with real Azure Key Vault resolution."""
    # Set up environment variable for expansion
    os.environ["ENVRESOLVE_TEST_VAULT_NAME"] = live_settings.key_vault_name

    # URI with variable that needs expansion
    uri = f"akv://${{ENVRESOLVE_TEST_VAULT_NAME}}/{live_settings.secret_name}"

    result = envresolve.resolve_secret(uri)

    assert result == live_settings.secret_value

    # Clean up
    del os.environ["ENVRESOLVE_TEST_VAULT_NAME"]
