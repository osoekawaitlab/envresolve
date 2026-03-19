"""Unit tests for AWS Secrets Manager provider."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from envresolve.exceptions import SecretResolutionError
from envresolve.providers.aws_sm import AWSSecretsManagerProvider

if TYPE_CHECKING:
    from envresolve.models import ParsedURI

# Mark all tests in this file as requiring AWS
pytestmark = pytest.mark.aws


class AWSProviderMocks:
    """Type-safe mock container for AWS provider unit tests."""

    def __init__(self) -> None:
        """Initialize mock objects with proper specs."""
        self.session: MagicMock = MagicMock()
        self.client: MagicMock = MagicMock(spec=["get_secret_value"])

        # Configure default behavior
        self.session.client.return_value = self.client

    def set_secret_value(self, value: str) -> None:
        """Configure mock to return a secret with the given string value."""
        self.client.get_secret_value.return_value = {"SecretString": value}

    def raise_not_found(self) -> None:
        """Configure mock to raise ResourceNotFoundException."""
        error_response: dict[str, dict[str, str]] = {
            "Error": {"Code": "ResourceNotFoundException"}
        }
        self.client.get_secret_value.side_effect = ClientError(
            error_response,  # type: ignore[arg-type]
            "GetSecretValue",
        )

    def raise_access_denied(self) -> None:
        """Configure mock to raise AccessDeniedException."""
        error_response: dict[str, dict[str, str]] = {
            "Error": {"Code": "AccessDeniedException"}
        }
        self.client.get_secret_value.side_effect = ClientError(
            error_response,  # type: ignore[arg-type]
            "GetSecretValue",
        )

    def create_provider(self) -> AWSSecretsManagerProvider:
        """Create an AWSSecretsManagerProvider instance with mocked dependencies."""
        return AWSSecretsManagerProvider(session=self.session)


@pytest.fixture
def aws_provider_mocks() -> AWSProviderMocks:
    """Fixture providing configured AWS provider mocks.

    Returns:
        AWSProviderMocks: Container with session and client mocks
    """
    return AWSProviderMocks()


def test_aws_sm_provider_exists() -> None:
    """Test that AWSSecretsManagerProvider class exists."""
    assert AWSSecretsManagerProvider is not None


def test_aws_sm_provider_resolve_simple(
    aws_provider_mocks: AWSProviderMocks,
) -> None:
    """Test resolving a simple secret without version."""
    aws_provider_mocks.set_secret_value("secret-value-123")
    provider = aws_provider_mocks.create_provider()

    parsed_uri: ParsedURI = {
        "scheme": "asm",
        "vault": "my-secret",
        "secret": "value",
        "version": None,
    }
    result = provider.resolve(parsed_uri)

    assert result == "secret-value-123"
    aws_provider_mocks.client.get_secret_value.assert_called_once_with(
        SecretId="my-secret"
    )


def test_aws_sm_provider_resolve_with_version(
    aws_provider_mocks: AWSProviderMocks,
) -> None:
    """Test resolving a secret with specific version."""
    aws_provider_mocks.set_secret_value("secret-v2")
    provider = aws_provider_mocks.create_provider()

    parsed_uri: ParsedURI = {
        "scheme": "asm",
        "vault": "my-secret",
        "secret": "value",
        "version": "abc123",
    }
    result = provider.resolve(parsed_uri)

    assert result == "secret-v2"
    aws_provider_mocks.client.get_secret_value.assert_called_once_with(
        SecretId="my-secret", VersionId="abc123"
    )


def test_aws_sm_provider_raises_on_not_found(
    aws_provider_mocks: AWSProviderMocks,
) -> None:
    """Test that provider raises SecretResolutionError when secret not found."""
    aws_provider_mocks.raise_not_found()
    provider = aws_provider_mocks.create_provider()

    parsed_uri: ParsedURI = {
        "scheme": "asm",
        "vault": "nonexistent",
        "secret": "value",
        "version": None,
    }

    with pytest.raises(SecretResolutionError) as exc:
        provider.resolve(parsed_uri)

    assert "ResourceNotFoundException" in str(exc.value)
    assert exc.value.original_error is not None


def test_aws_sm_provider_raises_on_access_denied(
    aws_provider_mocks: AWSProviderMocks,
) -> None:
    """Test that provider raises SecretResolutionError when access denied."""
    aws_provider_mocks.raise_access_denied()
    provider = aws_provider_mocks.create_provider()

    parsed_uri: ParsedURI = {
        "scheme": "asm",
        "vault": "restricted-secret",
        "secret": "value",
        "version": None,
    }

    with pytest.raises(SecretResolutionError) as exc:
        provider.resolve(parsed_uri)

    assert "AccessDeniedException" in str(exc.value)
    assert exc.value.original_error is not None


def test_aws_sm_provider_caches_clients(
    aws_provider_mocks: AWSProviderMocks,
) -> None:
    """Test that provider caches client instances."""
    aws_provider_mocks.set_secret_value("value")
    provider = aws_provider_mocks.create_provider()

    # Resolve multiple secrets
    secret1: ParsedURI = {
        "scheme": "asm",
        "vault": "secret1",
        "secret": "value",
        "version": None,
    }
    secret2: ParsedURI = {
        "scheme": "asm",
        "vault": "secret2",
        "secret": "value",
        "version": None,
    }

    provider.resolve(secret1)
    provider.resolve(secret2)

    # Client should be created only once
    assert aws_provider_mocks.session.client.call_count == 1


def test_aws_sm_provider_raises_on_binary_secret(
    aws_provider_mocks: AWSProviderMocks,
) -> None:
    """Test that provider raises error for binary secrets."""
    aws_provider_mocks.client.get_secret_value.return_value = {
        "SecretBinary": b"binary-data"
    }
    provider = aws_provider_mocks.create_provider()

    parsed_uri: ParsedURI = {
        "scheme": "asm",
        "vault": "binary-secret",
        "secret": "value",
        "version": None,
    }

    with pytest.raises(SecretResolutionError) as exc:
        provider.resolve(parsed_uri)

    assert "binary" in str(exc.value).lower()
