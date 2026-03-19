"""Live tests that exercise the real AWS Secrets Manager integration."""

from __future__ import annotations

import os
from dataclasses import dataclass

import pytest

import envresolve
from envresolve.exceptions import SecretResolutionError

pytest.importorskip("boto3")

pytestmark = [pytest.mark.aws, pytest.mark.live]

REQUIRED_ENV_VARS = {
    "ENVRESOLVE_LIVE_AWS_SECRET_NAME": "secret_name",
    "ENVRESOLVE_LIVE_AWS_SECRET_VALUE": "secret_value",
}
OPTIONAL_ENV_VARS = {
    "ENVRESOLVE_LIVE_AWS_SECRET_VERSION": "secret_version",
    "ENVRESOLVE_LIVE_AWS_REGION": "region",
}


@dataclass(frozen=True)
class LiveAWSSettings:
    """Container for live AWS Secrets Manager test configuration."""

    secret_name: str
    secret_value: str
    secret_version: str | None = None
    region: str | None = None


@pytest.fixture(scope="module")
def live_settings() -> LiveAWSSettings:
    """Collect required environment variables for the live test suite."""
    missing = [env for env in REQUIRED_ENV_VARS if not os.getenv(env)]
    if missing:
        pytest.skip(
            "AWS live-test configuration is incomplete. Missing: "
            + ", ".join(sorted(missing))
        )

    envresolve.register_aws_sm_provider()

    return LiveAWSSettings(
        secret_name=os.environ["ENVRESOLVE_LIVE_AWS_SECRET_NAME"],
        secret_value=os.environ["ENVRESOLVE_LIVE_AWS_SECRET_VALUE"],
        secret_version=os.getenv("ENVRESOLVE_LIVE_AWS_SECRET_VERSION"),
        region=os.getenv("ENVRESOLVE_LIVE_AWS_REGION"),
    )


def test_resolve_secret_value(live_settings: LiveAWSSettings) -> None:
    """Ensure a plain asm:// URI resolves to the expected secret value."""
    uri = f"asm://{live_settings.secret_name}/value"

    result = envresolve.resolve_secret(uri)

    assert result == live_settings.secret_value


def test_resolve_secret_with_version(live_settings: LiveAWSSettings) -> None:
    """Ensure asm:// URI with version query resolves correctly."""
    if live_settings.secret_version is None:
        pytest.skip("Secret version not provided in ENVRESOLVE_LIVE_AWS_SECRET_VERSION")

    uri = (
        f"asm://{live_settings.secret_name}/value"
        f"?version={live_settings.secret_version}"
    )

    result = envresolve.resolve_secret(uri)

    assert result == live_settings.secret_value


@pytest.mark.usefixtures("live_settings")
def test_resolve_nonexistent_secret_raises_error() -> None:
    """Ensure resolving a nonexistent secret raises an appropriate exception."""
    uri = "asm://nonexistent-secret-envresolve-12345/value"

    with pytest.raises(SecretResolutionError) as exc_info:
        envresolve.resolve_secret(uri)

    # Verify the error contains helpful information
    error_msg = str(exc_info.value).lower()
    assert "resourcenotfoundexception" in error_msg or "not found" in error_msg


def test_resolve_secret_with_variable_expansion(
    live_settings: LiveAWSSettings,
) -> None:
    """Ensure variable expansion works with real AWS Secrets Manager resolution."""
    # Set up environment variable for expansion
    os.environ["ENVRESOLVE_TEST_AWS_SECRET_NAME"] = live_settings.secret_name

    # URI with variable that needs expansion
    uri = "asm://${ENVRESOLVE_TEST_AWS_SECRET_NAME}/value"

    result = envresolve.resolve_secret(uri)

    assert result == live_settings.secret_value

    # Clean up
    del os.environ["ENVRESOLVE_TEST_AWS_SECRET_NAME"]
