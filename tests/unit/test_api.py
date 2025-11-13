"""Unit tests for the public API layer."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pytest_mock import MockFixture

import envresolve
from envresolve.api import EnvResolver
from envresolve.exceptions import (
    EnvResolveError,
    MutuallyExclusiveArgumentsError,
    ProviderRegistrationError,
    SecretResolutionError,
    URIParseError,
)
from envresolve.models import ParsedURI


def test_expand_variables_is_exported() -> None:
    """Test that expand_variables is available from the envresolve module."""
    assert hasattr(envresolve, "expand_variables")
    assert callable(envresolve.expand_variables)


def test_env_expander_is_exported() -> None:
    """Test that EnvExpander is available from the envresolve module."""
    assert hasattr(envresolve, "EnvExpander")
    # Verify it's a class
    assert isinstance(envresolve.EnvExpander, type)


def test_dotenv_expander_is_exported() -> None:
    """Test that DotEnvExpander is available from the envresolve module."""
    assert hasattr(envresolve, "DotEnvExpander")
    # Verify it's a class
    assert isinstance(envresolve.DotEnvExpander, type)


class MockProvider:
    """Simple mock provider for testing."""

    def resolve(self, parsed_uri: ParsedURI) -> str:
        """Return a resolved value based on secret name."""
        return f"resolved-{parsed_uri['secret']}"


@pytest.fixture
def resolver_with_mock() -> EnvResolver:
    """Fixture providing EnvResolver with mock provider."""
    resolver = EnvResolver()
    resolver._providers["akv"] = MockProvider()  # noqa: SLF001
    return resolver


def test_resolve_os_environ_method_exists() -> None:
    """Test that EnvResolver has resolve_os_environ method."""
    resolver = EnvResolver()
    assert hasattr(resolver, "resolve_os_environ")
    assert callable(resolver.resolve_os_environ)


def test_resolve_os_environ_basic_functionality(
    resolver_with_mock: EnvResolver,
) -> None:
    """Test basic resolve_os_environ with all defaults."""
    with patch.dict(
        os.environ,
        {"API_KEY": "akv://vault/api-key", "PLAIN": "plain-value"},
        clear=True,
    ):
        result = resolver_with_mock.resolve_os_environ()

        assert result["API_KEY"] == "resolved-api-key"
        assert result["PLAIN"] == "plain-value"
        assert os.environ["API_KEY"] == "resolved-api-key"
        assert os.environ["PLAIN"] == "plain-value"


def test_resolve_os_environ_with_keys_filter(
    resolver_with_mock: EnvResolver,
) -> None:
    """Test resolve_os_environ with keys parameter."""
    with patch.dict(
        os.environ,
        {
            "API_KEY": "akv://vault/api-key",
            "DB_URL": "akv://vault/db-url",
            "OTHER": "value",
        },
        clear=True,
    ):
        result = resolver_with_mock.resolve_os_environ(keys=["API_KEY"])

        assert "API_KEY" in result
        assert result["API_KEY"] == "resolved-api-key"
        assert "DB_URL" not in result
        assert "OTHER" not in result
        assert os.environ["API_KEY"] == "resolved-api-key"
        assert os.environ["DB_URL"] == "akv://vault/db-url"  # Unchanged


def test_resolve_os_environ_keys_and_prefix_both_specified(
    resolver_with_mock: EnvResolver,
) -> None:
    """Test that specifying both keys and prefix raises an error."""
    with patch.dict(
        os.environ,
        {
            "DEV_API_KEY": "akv://vault/api-key",
            "DEV_DB_URL": "akv://vault/db-url",
            "PROD_SECRET": "akv://vault/secret",
        },
        clear=True,
    ):
        # When both keys and prefix are specified, should raise error
        with pytest.raises(MutuallyExclusiveArgumentsError) as exc_info:
            resolver_with_mock.resolve_os_environ(keys=["PROD_SECRET"], prefix="DEV_")

        # Check exception attributes
        assert exc_info.value.arg1 == "keys"
        assert exc_info.value.arg2 == "prefix"
        assert "mutually exclusive" in str(exc_info.value).lower()


def test_resolve_os_environ_with_prefix_filter(
    resolver_with_mock: EnvResolver,
) -> None:
    """Test resolve_os_environ with prefix parameter strips prefix."""
    with patch.dict(
        os.environ,
        {
            "DEV_API_KEY": "akv://vault/api-key",
            "DEV_DB_URL": "akv://vault/db-url",
            "PROD_SECRET": "akv://vault/secret",
        },
        clear=True,
    ):
        result = resolver_with_mock.resolve_os_environ(prefix="DEV_")

        # Should only process DEV_ prefixed keys and strip prefix
        assert "API_KEY" in result
        assert "DB_URL" in result
        assert result["API_KEY"] == "resolved-api-key"
        assert result["DB_URL"] == "resolved-db-url"
        assert "PROD_SECRET" not in result
        assert "DEV_API_KEY" not in result

        # os.environ should have stripped keys (new keys added)
        assert os.environ["API_KEY"] == "resolved-api-key"
        assert os.environ["DB_URL"] == "resolved-db-url"
        # Original prefixed keys should be deleted when prefix stripping occurred
        assert "DEV_API_KEY" not in os.environ
        assert "DEV_DB_URL" not in os.environ
        # Non-prefixed keys should be unchanged
        assert os.environ["PROD_SECRET"] == "akv://vault/secret"  # noqa: S105


def test_resolve_os_environ_with_overwrite_false(
    resolver_with_mock: EnvResolver,
) -> None:
    """Test resolve_os_environ with overwrite=False doesn't modify os.environ."""
    with patch.dict(
        os.environ,
        {"API_KEY": "akv://vault/api-key", "PLAIN": "plain-value"},
        clear=True,
    ):
        result = resolver_with_mock.resolve_os_environ(overwrite=False)

        # Result should contain resolved values
        assert result["API_KEY"] == "resolved-api-key"
        assert result["PLAIN"] == "plain-value"

        # But os.environ should be unchanged
        assert os.environ["API_KEY"] == "akv://vault/api-key"
        assert os.environ["PLAIN"] == "plain-value"


def test_resolve_os_environ_with_stop_on_error_false() -> None:
    """Test resolve_os_environ continues on errors.

    Tests that stop_on_resolution_error=False continues on errors.
    """

    # Create a provider that fails for specific secrets
    class FailingProvider:
        def resolve(self, parsed_uri: ParsedURI) -> str:
            if parsed_uri["secret"] == "failing-secret":  # noqa: S105
                uri = f"akv://{parsed_uri['vault']}/{parsed_uri['secret']}"
                msg = "Simulated resolution failure"
                raise SecretResolutionError(msg, uri)
            return f"resolved-{parsed_uri['secret']}"

    resolver = EnvResolver()
    resolver._providers["akv"] = FailingProvider()  # noqa: SLF001

    with patch.dict(
        os.environ,
        {
            "API_KEY": "akv://vault/api-key",
            "FAILING": "akv://vault/failing-secret",
            "DB_URL": "akv://vault/db-url",
        },
        clear=True,
    ):
        result = resolver.resolve_os_environ(stop_on_resolution_error=False)

        # Should have resolved successful keys
        assert result["API_KEY"] == "resolved-api-key"
        assert result["DB_URL"] == "resolved-db-url"

        # Failing key should not be in result (skipped on error)
        assert "FAILING" not in result

        # os.environ should reflect the same
        assert os.environ["API_KEY"] == "resolved-api-key"
        assert os.environ["DB_URL"] == "resolved-db-url"
        # Failing key remains unchanged (not overwritten)
        assert os.environ["FAILING"] == "akv://vault/failing-secret"


def test_resolve_os_environ_with_stop_on_error_true() -> None:
    """Test resolve_os_environ with stop_on_resolution_error=True raises on errors."""

    # Create a provider that fails for specific secrets
    class FailingProvider:
        def resolve(self, parsed_uri: ParsedURI) -> str:
            if parsed_uri["secret"] == "failing-secret":  # noqa: S105
                uri = f"akv://{parsed_uri['vault']}/{parsed_uri['secret']}"
                msg = "Simulated resolution failure"
                raise SecretResolutionError(msg, uri)
            return f"resolved-{parsed_uri['secret']}"

    resolver = EnvResolver()
    resolver._providers["akv"] = FailingProvider()  # noqa: SLF001

    with (
        patch.dict(
            os.environ,
            {
                "API_KEY": "akv://vault/api-key",
                "FAILING": "akv://vault/failing-secret",
            },
            clear=True,
        ),
        pytest.raises(SecretResolutionError),
    ):
        resolver.resolve_os_environ(stop_on_resolution_error=True)


def test_resolve_os_environ_with_empty_environ(
    resolver_with_mock: EnvResolver,
) -> None:
    """Test resolve_os_environ with empty os.environ."""
    with patch.dict(os.environ, {}, clear=True):
        result = resolver_with_mock.resolve_os_environ()

        assert result == {}


def test_resolve_os_environ_with_nonexistent_keys(
    resolver_with_mock: EnvResolver,
) -> None:
    """Test resolve_os_environ with keys that don't exist in os.environ."""
    with patch.dict(
        os.environ,
        {"API_KEY": "akv://vault/api-key"},
        clear=True,
    ):
        # Request keys that don't exist
        result = resolver_with_mock.resolve_os_environ(
            keys=["NONEXISTENT1", "NONEXISTENT2"]
        )

        # Should return empty result
        assert result == {}


def test_resolve_os_environ_propagates_unexpected_errors() -> None:
    """Test that unexpected errors are always raised.

    Tests that unexpected errors are always raised regardless of the
    stop_on_resolution_error parameter.
    """

    # Create a provider that raises a non-domain error
    class UnexpectedErrorProvider:
        def resolve(self, parsed_uri: ParsedURI) -> str:
            mesg = "Unexpected internal error for {}".format(parsed_uri["secret"])
            raise ValueError(mesg)

    resolver = EnvResolver()
    resolver._providers["akv"] = UnexpectedErrorProvider()  # noqa: SLF001

    with (
        patch.dict(
            os.environ,
            {"API_KEY": "akv://vault/api-key"},
            clear=True,
        ),
        pytest.raises(ValueError, match="Unexpected internal error"),
    ):
        # stop_on_resolution_error=False should not suppress
        # non-EnvResolveError exceptions
        resolver.resolve_os_environ(stop_on_resolution_error=False)


def test_resolve_os_environ_with_empty_keys_list(
    resolver_with_mock: EnvResolver,
) -> None:
    """Test resolve_os_environ with empty keys list."""
    with patch.dict(
        os.environ,
        {"API_KEY": "akv://vault/api-key", "DB_URL": "akv://vault/db-url"},
        clear=True,
    ):
        result = resolver_with_mock.resolve_os_environ(keys=[])

        # Should return empty result (no keys specified)
        assert result == {}


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


def test_resolve_os_environ_with_ignore_keys(mocker: MockFixture) -> None:
    """Test that ignore_keys skips expansion for specified keys."""
    resolver = EnvResolver()

    mocker.patch.dict(
        os.environ,
        {
            "CONFIG": "${UNDEFINED_VAR}",  # Would cause VariableNotFoundError
            "VALID": "hello",
        },
        clear=True,
    )

    result = resolver.resolve_os_environ(ignore_keys=["CONFIG"])

    # CONFIG should be unchanged (not expanded)
    assert result["CONFIG"] == "${UNDEFINED_VAR}"
    # VALID should be processed normally
    assert result["VALID"] == "hello"


def test_resolve_os_environ_with_empty_ignore_keys(mocker: MockFixture) -> None:
    """Test that empty ignore_keys list processes all variables normally."""
    resolver = EnvResolver()

    mocker.patch.dict(
        os.environ,
        {"VAR1": "value1", "VAR2": "value2"},
        clear=True,
    )

    result = resolver.resolve_os_environ(ignore_keys=[])

    assert result == {"VAR1": "value1", "VAR2": "value2"}


def test_resolve_os_environ_with_nonexistent_ignore_keys(
    mocker: MockFixture,
) -> None:
    """Test that nonexistent keys in ignore_keys are silently skipped."""
    resolver = EnvResolver()

    mocker.patch.dict(
        os.environ,
        {"VAR1": "value1", "VAR2": "value2"},
        clear=True,
    )

    result = resolver.resolve_os_environ(ignore_keys=["NONEXISTENT", "VAR1"])

    # Only VAR1 should be in result (VAR2 is not ignored)
    assert "VAR1" in result
    assert "VAR2" in result
    # NONEXISTENT should not appear (doesn't exist in os.environ)
    assert "NONEXISTENT" not in result
