"""End-to-end tests for AWS Secrets Manager resolution."""

import os
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

import envresolve
from envresolve.exceptions import SecretResolutionError

if TYPE_CHECKING:
    from envresolve.models import ParsedURI

pytestmark = pytest.mark.aws


@pytest.fixture
def mock_provider() -> MagicMock:
    """Create a mock AWS SM provider."""
    mock = MagicMock()

    def resolve_side_effect(
        parsed_uri: "ParsedURI",
        _logger: object = None,
    ) -> str:
        secret_name = parsed_uri["vault"]
        if secret_name == "my-secret":
            return "secret-value-123"
        if secret_name == "another-secret":
            return "another-value"
        if secret_name == "nested-secret":
            return "asm://my-secret/value"
        msg = f"Secret not found: {secret_name}"
        raise SecretResolutionError(msg, uri=f"asm://{secret_name}/value")

    mock.resolve.side_effect = resolve_side_effect
    return mock


def test_resolve_simple_asm_uri(mock_provider: MagicMock) -> None:
    """Test resolving a simple asm:// URI."""
    envresolve.register_aws_sm_provider(provider=mock_provider)

    result = envresolve.resolve_secret("asm://my-secret/value")

    assert result == "secret-value-123"


def test_resolve_asm_uri_with_version(mock_provider: MagicMock) -> None:
    """Test resolving an asm:// URI with version query parameter."""
    envresolve.register_aws_sm_provider(provider=mock_provider)

    result = envresolve.resolve_secret("asm://my-secret/value?version=abc123")

    assert result == "secret-value-123"
    # Verify version was passed to provider
    call_args = mock_provider.resolve.call_args[0][0]
    assert call_args["version"] == "abc123"


def test_resolve_with_variable_expansion(
    mock_provider: MagicMock,
    mocker: MockerFixture,
) -> None:
    """Test resolving asm:// URI with variable expansion."""
    envresolve.register_aws_sm_provider(provider=mock_provider)
    mocker.patch.dict(os.environ, {"SECRET_NAME": "my-secret"}, clear=True)

    result = envresolve.resolve_secret("asm://${SECRET_NAME}/value")

    assert result == "secret-value-123"


def test_missing_secret_raises_error(mock_provider: MagicMock) -> None:
    """Test that missing secret raises SecretResolutionError."""
    envresolve.register_aws_sm_provider(provider=mock_provider)

    with pytest.raises(SecretResolutionError):
        envresolve.resolve_secret("asm://nonexistent/value")


def test_non_target_uri_passthrough() -> None:
    """Test that non-asm URIs pass through unchanged."""
    result = envresolve.resolve_secret("postgres://localhost/db")

    assert result == "postgres://localhost/db"


def test_idempotent_resolution(mock_provider: MagicMock) -> None:
    """Test that plain strings pass through unchanged."""
    envresolve.register_aws_sm_provider(provider=mock_provider)

    result = envresolve.resolve_secret("plain-string-value")

    assert result == "plain-string-value"
    mock_provider.resolve.assert_not_called()


def test_load_env_with_asm_uris(
    mock_provider: MagicMock,
    tmp_path: object,
    mocker: MockerFixture,
) -> None:
    """Test loading .env file with asm:// URIs."""
    envresolve.register_aws_sm_provider(provider=mock_provider)

    # Create a temporary .env file
    env_file = tmp_path / ".env"  # type: ignore[operator]
    env_file.write_text("DB_PASSWORD=asm://my-secret/value\nPLAIN_VAR=plain")

    # Mock os.environ
    mocker.patch.dict(os.environ, {}, clear=True)

    result = envresolve.load_env(str(env_file), export=False)

    assert result["DB_PASSWORD"] == "secret-value-123"
    assert result["PLAIN_VAR"] == "plain"


def test_invalid_uri_raises_error() -> None:
    """Test that invalid asm:// URI raises URIParseError."""
    envresolve.register_aws_sm_provider(provider=MagicMock())

    with pytest.raises(envresolve.URIParseError):
        envresolve.resolve_secret("asm:///missing-secret-name")
