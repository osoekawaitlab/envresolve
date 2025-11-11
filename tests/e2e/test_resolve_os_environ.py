"""E2E tests for resolve_os_environ API."""

import importlib
import os
from collections.abc import Callable
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockFixture

import envresolve

if TYPE_CHECKING:
    from azure.keyvault.secrets import KeyVaultSecret

# Mark all tests in this file as requiring Azure
pytestmark = pytest.mark.azure


class ResolveOsEnvironMocks:
    """Type-safe mock container for resolve_os_environ tests."""

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
def resolve_mocks(mocker: MockFixture) -> ResolveOsEnvironMocks:
    """Fixture providing configured mocks for resolve_os_environ tests.

    Returns:
        ResolveOsEnvironMocks: Container with credential and secret_client mocks
    """
    mocks = ResolveOsEnvironMocks()

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
def test_resolve_os_environ_basic(
    resolve_mocks: ResolveOsEnvironMocks, mocker: MockFixture
) -> None:
    """Test basic resolve_os_environ functionality.

    Acceptance criteria:
    - resolve_os_environ() resolves secret URIs in os.environ
    - Updates os.environ with resolved values by default
    """
    resolve_mocks.set_secret_value("resolved-api-key-value")
    mocker.patch.dict(os.environ, {"API_KEY": "akv://test-vault/api-key"}, clear=True)

    result = envresolve.resolve_os_environ()

    assert result == {"API_KEY": "resolved-api-key-value"}
    assert os.environ["API_KEY"] == "resolved-api-key-value"


@pytest.mark.e2e
def test_resolve_os_environ_with_keys_parameter(
    resolve_mocks: ResolveOsEnvironMocks, mocker: MockFixture
) -> None:
    """Test resolve_os_environ with keys parameter.

    Acceptance criteria:
    - Support keys parameter to filter specific environment variables
    """

    def get_secret_by_name(name: str, version: str | None = None) -> MagicMock:
        mock = MagicMock()
        mock.value = f"resolved-{name}" + (f"-{version}" if version else "")
        return mock

    resolve_mocks.set_secret_getter(get_secret_by_name)
    mocker.patch.dict(
        os.environ,
        {
            "API_KEY": "akv://test-vault/api-key",
            "DB_URL": "akv://test-vault/db-url",
            "PLAIN_VAR": "plain-value",
        },
        clear=True,
    )

    result = envresolve.resolve_os_environ(keys=["API_KEY"])

    assert result == {"API_KEY": "resolved-api-key"}
    assert os.environ["API_KEY"] == "resolved-api-key"
    assert os.environ["DB_URL"] == "akv://test-vault/db-url"  # Unchanged
    assert os.environ["PLAIN_VAR"] == "plain-value"  # Unchanged


@pytest.mark.e2e
def test_resolve_os_environ_preserves_non_target_values(
    resolve_mocks: ResolveOsEnvironMocks, mocker: MockFixture
) -> None:
    """Test that non-target values pass through unchanged.

    Acceptance criteria:
    - Preserve non-target values (plain strings, non-secret URIs) unchanged
    """

    def get_secret_by_name(name: str, version: str | None = None) -> MagicMock:
        mock = MagicMock()
        mock.value = f"resolved-{name}" + (f"-{version}" if version else "")
        return mock

    resolve_mocks.set_secret_getter(get_secret_by_name)
    mocker.patch.dict(
        os.environ,
        {
            "SECRET": "akv://test-vault/secret",
            "PLAIN": "plain-value",
            "POSTGRES_URL": "postgres://localhost/db",
        },
        clear=True,
    )

    result = envresolve.resolve_os_environ()

    assert result["SECRET"] == "resolved-secret"  # noqa: S105
    assert result["PLAIN"] == "plain-value"
    assert result["POSTGRES_URL"] == "postgres://localhost/db"


@pytest.mark.e2e
def test_resolve_os_environ_with_variable_expansion(
    resolve_mocks: ResolveOsEnvironMocks, mocker: MockFixture
) -> None:
    """Test resolve_os_environ with variable expansion.

    Acceptance criteria:
    - Support variable expansion in values (e.g., akv://${VAULT}/secret)
    """

    def get_secret_by_name(name: str, version: str | None = None) -> MagicMock:
        mock = MagicMock()
        mock.value = f"resolved-my-vault-{name}" + (f"-{version}" if version else "")
        return mock

    resolve_mocks.set_secret_getter(get_secret_by_name)
    mocker.patch.dict(
        os.environ,
        {
            "VAULT_NAME": "my-vault",
            "API_KEY": "akv://${VAULT_NAME}/api-key",
        },
        clear=True,
    )

    result = envresolve.resolve_os_environ()

    assert result["API_KEY"] == "resolved-my-vault-api-key"
    assert result["VAULT_NAME"] == "my-vault"


@pytest.mark.e2e
def test_resolve_os_environ_with_prefix_parameter(
    resolve_mocks: ResolveOsEnvironMocks, mocker: MockFixture
) -> None:
    """Test resolve_os_environ with prefix parameter.

    Acceptance criteria:
    - Support prefix parameter to filter and strip prefixed keys
    """

    def get_secret_by_name(name: str, version: str | None = None) -> MagicMock:
        mock = MagicMock()
        mock.value = f"resolved-{name}" + (f"-{version}" if version else "")
        return mock

    resolve_mocks.set_secret_getter(get_secret_by_name)
    mocker.patch.dict(
        os.environ,
        {
            "DEV_API_KEY": "akv://test-vault/api-key",
            "DEV_DB_URL": "akv://test-vault/db-url",
            "PROD_API_KEY": "akv://prod-vault/api-key",
            "PROD_DB_URL": "akv://prod-vault/db-url",
            "OTHER_VAR": "akv://test-vault/other",
        },
        clear=True,
    )

    result = envresolve.resolve_os_environ(prefix="DEV_")

    assert "API_KEY" in result  # Prefix stripped
    assert "DB_URL" in result  # Prefix stripped
    assert "OTHER_VAR" not in result  # Not prefixed, not included

    assert os.environ["API_KEY"] == "resolved-api-key"
    assert os.environ["DB_URL"] == "resolved-db-url"
    assert "DEV_API_KEY" not in os.environ  # Old key removed
    assert "DEV_DB_URL" not in os.environ  # Old key removed
    assert os.environ["OTHER_VAR"] == "akv://test-vault/other"  # Unchanged
    assert os.environ["PROD_API_KEY"] == "akv://prod-vault/api-key"  # Unchanged
    assert os.environ["PROD_DB_URL"] == "akv://prod-vault/db-url"  # Unchanged


@pytest.mark.e2e
def test_resolve_os_environ_with_overwrite_false(
    resolve_mocks: ResolveOsEnvironMocks, mocker: MockFixture
) -> None:
    """Test resolve_os_environ with overwrite=False.

    Acceptance criteria:
    - Support overwrite parameter to control os.environ updates
    """
    resolve_mocks.set_secret_value("resolved-api-key-value")
    mocker.patch.dict(os.environ, {"API_KEY": "akv://test-vault/api-key"}, clear=True)

    result = envresolve.resolve_os_environ(overwrite=False)

    assert result == {"API_KEY": "resolved-api-key-value"}
    assert os.environ["API_KEY"] == "akv://test-vault/api-key"  # Unchanged


@pytest.mark.e2e
@pytest.mark.usefixtures("resolve_mocks")
def test_resolve_os_environ_expansion_error_raised_by_default(
    mocker: MockFixture,
) -> None:
    """Test resolve_os_environ raises VariableNotFoundError by default.

    Acceptance criteria:
    - Raise VariableNotFoundError when referenced variable is not found
    """
    mocker.patch.dict(
        os.environ,
        {
            "VALID": "hello",
            "INVALID": "${NONEXISTENT}",
        },
        clear=True,
    )

    with pytest.raises(envresolve.VariableNotFoundError) as exc_info:
        envresolve.resolve_os_environ()

    assert "NONEXISTENT" in str(exc_info.value)


@pytest.mark.e2e
@pytest.mark.usefixtures("resolve_mocks")
def test_resolve_os_environ_expansion_error_suppressed(
    mocker: MockFixture,
) -> None:
    """Test resolve_os_environ skips expansion errors.

    Tests that stop_on_expansion_error=False skips expansion errors.

    Acceptance criteria:
    - Skip variables with expansion errors when stop_on_expansion_error=False
    """
    mocker.patch.dict(
        os.environ,
        {
            "VALID": "hello",
            "INVALID": "${NONEXISTENT}",
            "ALSO_VALID": "world",
        },
        clear=True,
    )

    result = envresolve.resolve_os_environ(stop_on_expansion_error=False)

    assert result == {"VALID": "hello", "ALSO_VALID": "world"}
    assert "INVALID" not in result


@pytest.mark.e2e
@pytest.mark.usefixtures("resolve_mocks")
def test_resolve_os_environ_circular_reference_error_raised_by_default(
    mocker: MockFixture,
) -> None:
    """Test resolve_os_environ raises CircularReferenceError by default.

    Acceptance criteria:
    - Raise CircularReferenceError when circular reference is detected
    """
    mocker.patch.dict(
        os.environ,
        {
            "A": "${B}",
            "B": "${A}",
        },
        clear=True,
    )

    with pytest.raises(envresolve.CircularReferenceError):
        envresolve.resolve_os_environ()


@pytest.mark.e2e
def test_resolve_os_environ_resolution_error_raised_by_default(
    resolve_mocks: ResolveOsEnvironMocks, mocker: MockFixture
) -> None:
    """Test resolve_os_environ raises SecretResolutionError by default.

    Acceptance criteria:
    - Raise SecretResolutionError when secret resolution fails
    """

    def get_secret_by_name_with_error(
        name: str,  # noqa: ARG001
        version: str | None = None,  # noqa: ARG001
    ) -> MagicMock:
        # Lazy import using importlib (ADR-0014 pattern)
        azure_exceptions = importlib.import_module("azure.core.exceptions")
        resource_not_found_error = azure_exceptions.ResourceNotFoundError

        msg = "Secret not found"
        raise resource_not_found_error(msg)

    resolve_mocks.set_secret_getter(get_secret_by_name_with_error)
    mocker.patch.dict(
        os.environ,
        {
            "VALID": "hello",
            "SECRET": "akv://test-vault/bad-secret",
        },
        clear=True,
    )

    with pytest.raises(envresolve.SecretResolutionError):
        envresolve.resolve_os_environ()


@pytest.mark.e2e
def test_resolve_os_environ_resolution_error_suppressed(
    resolve_mocks: ResolveOsEnvironMocks, mocker: MockFixture
) -> None:
    """Test resolve_os_environ skips resolution errors.

    Tests that stop_on_resolution_error=False skips resolution errors.

    Acceptance criteria:
    - Skip variables with resolution errors when stop_on_resolution_error=False
    """

    def get_secret_by_name_with_error(
        name: str,
        version: str | None = None,
    ) -> MagicMock:
        if name == "bad-secret":
            # Lazy import using importlib (ADR-0014 pattern)
            azure_exceptions = importlib.import_module("azure.core.exceptions")
            resource_not_found_error = azure_exceptions.ResourceNotFoundError

            msg = "Secret not found"
            raise resource_not_found_error(msg)
        mock = MagicMock()
        mock.value = f"resolved-{name}" + (f"-{version}" if version else "")
        return mock

    resolve_mocks.set_secret_getter(get_secret_by_name_with_error)
    mocker.patch.dict(
        os.environ,
        {
            "GOOD_KEY": "akv://test-vault/good-secret",
            "BAD_KEY": "akv://test-vault/bad-secret",
            "PLAIN": "plain-value",
        },
        clear=True,
    )

    result = envresolve.resolve_os_environ(stop_on_resolution_error=False)

    assert "GOOD_KEY" in result
    assert result["GOOD_KEY"] == "resolved-good-secret"
    assert "BAD_KEY" not in result  # Skipped due to error
    assert result["PLAIN"] == "plain-value"


@pytest.mark.e2e
def test_resolve_os_environ_both_errors_suppressed(
    resolve_mocks: ResolveOsEnvironMocks, mocker: MockFixture
) -> None:
    """Test resolve_os_environ with both error flags set to False.

    Verifies that VariableNotFoundError is suppressed,
    SecretResolutionError is suppressed, but CircularReferenceError
    is always raised (configuration error).
    """

    def get_secret_by_name_with_error(
        name: str,
        version: str | None = None,
    ) -> MagicMock:
        if name == "bad-secret":
            # Lazy import using importlib (ADR-0014 pattern)
            azure_exceptions = importlib.import_module("azure.core.exceptions")
            resource_not_found_error = azure_exceptions.ResourceNotFoundError

            msg = "Secret not found"
            raise resource_not_found_error(msg)
        mock = MagicMock()
        mock.value = f"resolved-{name}" + (f"-{version}" if version else "")
        return mock

    resolve_mocks.set_secret_getter(get_secret_by_name_with_error)
    mocker.patch.dict(
        os.environ,
        {
            "VALID": "hello",
            "EXPANSION_ERROR": "${NONEXISTENT}",
            "SECRET": "akv://test-vault/bad-secret",
            "CIRCULAR_A": "${CIRCULAR_B}",
            "CIRCULAR_B": "${CIRCULAR_A}",
            "GOOD_SECRET": "akv://test-vault/good-secret",
            "ALSO_VALID": "world",
        },
        clear=True,
    )

    # CircularReferenceError should still be raised
    with pytest.raises(envresolve.CircularReferenceError):
        envresolve.resolve_os_environ(
            stop_on_expansion_error=False, stop_on_resolution_error=False
        )


@pytest.mark.e2e
@pytest.mark.usefixtures("resolve_mocks")
def test_resolve_os_environ_both_errors_raised(
    mocker: MockFixture,
) -> None:
    """Test resolve_os_environ raises first error when both flags are True (default).

    Acceptance criteria:
    - Raise first error encountered when both flags are True
    """
    mocker.patch.dict(
        os.environ,
        {
            "EXPANSION_ERROR": "${NONEXISTENT}",
            "VALID": "hello",
        },
        clear=True,
    )

    # Should raise expansion error (first in environ)
    with pytest.raises(envresolve.VariableNotFoundError):
        envresolve.resolve_os_environ()


@pytest.mark.e2e
def test_resolve_os_environ_keys_and_prefix_both_specified(
    resolve_mocks: ResolveOsEnvironMocks, mocker: MockFixture
) -> None:
    """Test that specifying both keys and prefix raises an error.

    Acceptance criteria:
    - When both keys and prefix are specified, raise MutuallyExclusiveArgumentsError
    """

    def get_secret_by_name(name: str, version: str | None = None) -> MagicMock:
        mock = MagicMock()
        mock.value = f"resolved-{name}" + (f"-{version}" if version else "")
        return mock

    resolve_mocks.set_secret_getter(get_secret_by_name)
    mocker.patch.dict(
        os.environ,
        {
            "DEV_API_KEY": "akv://test-vault/api-key",
            "DEV_DB_URL": "akv://test-vault/db-url",
            "PROD_SECRET": "akv://test-vault/secret",
        },
        clear=True,
    )

    # When both keys and prefix are specified, should raise error
    with pytest.raises(envresolve.MutuallyExclusiveArgumentsError) as exc_info:
        envresolve.resolve_os_environ(keys=["PROD_SECRET"], prefix="DEV_")

    # Check exception attributes
    assert exc_info.value.arg1 == "keys"
    assert exc_info.value.arg2 == "prefix"
    assert "mutually exclusive" in str(exc_info.value).lower()
