"""E2E tests for logging functionality.

Tests verify acceptance criteria from issue #40:
- EnvResolver accepts optional logger parameter in constructor
- Global facade provides set_logger() function for default logger
"""

import logging
import os

import pytest
from pytest_mock import MockerFixture

import envresolve
from envresolve import EnvResolver

from .helpers import MockProvider


def test_env_resolver_accepts_optional_logger_parameter() -> None:
    """Test that EnvResolver accepts an optional logger parameter in constructor.

    Acceptance criteria: EnvResolver accepts optional logger parameter in constructor
    """
    logger = logging.getLogger(__name__)

    # Should accept logger parameter
    resolver_with_logger = EnvResolver(logger=logger)
    assert resolver_with_logger is not None

    # Should work without logger parameter
    resolver_without_logger = EnvResolver()
    assert resolver_without_logger is not None


def test_global_facade_provides_set_logger_function() -> None:
    """Test that global facade provides set_logger() function.

    Acceptance criteria: Global facade provides set_logger() function for default logger
    """
    logger = logging.getLogger(__name__)

    # Should have set_logger function
    assert hasattr(envresolve, "set_logger")
    assert callable(envresolve.set_logger)

    # Should be able to call set_logger
    envresolve.set_logger(logger)

    # Should be able to call with None to clear
    envresolve.set_logger(None)


def test_global_facade_functions_accept_logger_parameter() -> None:
    """Test that global facade functions accept optional logger parameter.

    Acceptance criteria: Global facade functions accept optional logger parameter
    that overrides global default
    """
    logger = logging.getLogger(__name__)

    # resolve_secret should accept logger parameter
    result = envresolve.resolve_secret("plain-string", logger=logger)
    assert result == "plain-string"

    # load_env should accept logger parameter (logging is now implemented)
    env_result = envresolve.load_env(dotenv_path=None, logger=logger)
    assert isinstance(env_result, dict)

    # resolve_os_environ should accept logger parameter (logging is now implemented)
    os_result = envresolve.resolve_os_environ(logger=logger)
    assert isinstance(os_result, dict)


def test_env_resolver_methods_accept_logger_parameter() -> None:
    """Test that EnvResolver methods accept optional logger parameter.

    The logger parameter in methods should override the constructor logger.
    """
    constructor_logger = logging.getLogger("constructor")
    method_logger = logging.getLogger("method")

    resolver = EnvResolver(logger=constructor_logger)

    # resolve_secret should accept logger parameter
    secret_result = resolver.resolve_secret("plain-string", logger=method_logger)
    assert secret_result == "plain-string"

    # Should work without logger parameter (uses constructor logger)
    secret_result = resolver.resolve_secret("plain-string")
    assert secret_result == "plain-string"

    # load_env should accept logger parameter
    env_result = resolver.load_env(dotenv_path=None, logger=method_logger)
    assert isinstance(env_result, dict)

    # resolve_os_environ should accept logger parameter
    os_result = resolver.resolve_os_environ(logger=method_logger)
    assert isinstance(os_result, dict)


def test_variable_expansion_is_logged(
    caplog: pytest.LogCaptureFixture,
    mocker: MockerFixture,
) -> None:
    """Test that variable expansion is logged with operation type and status.

    Acceptance criteria: Operations are logged with type, status, and error category

    This test verifies that when resolve_secret() performs variable expansion
    (plain text without secret URI), the operation is logged at DEBUG level
    with operation type and status, but without exposing specific values
    (variable names, etc.) per ADR-0030.
    """
    logger = logging.getLogger("test_expansion")

    # Set up environment variables for expansion
    mocker.patch.dict(os.environ, {"FOO": "bar", "BAZ": "qux"}, clear=True)

    # Test variable expansion through resolve_secret (plain text, no URI)
    with caplog.at_level(logging.DEBUG, logger="test_expansion"):
        result = envresolve.resolve_secret("prefix-${FOO}-${BAZ}-suffix", logger=logger)

        # Result should have variables expanded
        assert result == "prefix-bar-qux-suffix"

        # Should have logged the variable expansion operation
        assert len(caplog.records) > 0

        # Verify operation-level logging (ADR-0030: operation type and status only)
        messages = [record.message.lower() for record in caplog.records]

        # Should log completion status
        assert any(
            "variable expansion" in msg and "completed" in msg for msg in messages
        )

        # Should NOT log specific variable names (ADR-0030)
        assert not any("FOO" in record.message for record in caplog.records)
        assert not any("BAZ" in record.message for record in caplog.records)

        # Verify they were logged at DEBUG level
        debug_records = [r for r in caplog.records if r.levelname == "DEBUG"]
        assert len(debug_records) > 0


def test_variable_expansion_error_is_logged(
    caplog: pytest.LogCaptureFixture,
    mocker: MockerFixture,
) -> None:
    """Test that variable expansion errors are logged with error category.

    Acceptance criteria: Operations are logged with type, status, and error category

    This test verifies that when variable expansion fails, the error is logged
    with the error category but without exposing specific values per ADR-0030.
    """
    logger = logging.getLogger("test_expansion_error")

    # Set up environment with missing variable
    mocker.patch.dict(os.environ, {}, clear=True)

    # Test variable expansion failure
    with caplog.at_level(logging.ERROR, logger="test_expansion_error"):
        # Expect VariableNotFoundError to be raised
        with pytest.raises(envresolve.VariableNotFoundError):
            envresolve.resolve_secret("${MISSING_VAR}", logger=logger)

        # Should have logged the error
        assert len(caplog.records) > 0

        # Verify error-level logging with category
        messages = [record.message.lower() for record in caplog.records]

        # Should log error category
        assert any(
            "variable expansion" in msg and "variable not found" in msg
            for msg in messages
        )

        # Should NOT log specific variable names (ADR-0030)
        assert not any("MISSING_VAR" in record.message for record in caplog.records)

        # Verify they were logged at ERROR level
        error_records = [r for r in caplog.records if r.levelname == "ERROR"]
        assert len(error_records) > 0


def test_secret_resolution_is_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that secret resolution is logged with operation type and status.

    Acceptance criteria: Operations are logged with type, status, and error category

    This test verifies that when resolve_secret() resolves a secret URI,
    the operation is logged at DEBUG level with operation type and status,
    but without exposing specific values (vault names, secret names, URIs)
    per ADR-0030.
    """
    logger = logging.getLogger("test_resolution")

    # Register mock provider
    envresolve.register_azure_kv_provider(provider=MockProvider())

    # Test secret resolution through resolve_secret
    with caplog.at_level(logging.DEBUG, logger="test_resolution"):
        result = envresolve.resolve_secret("akv://my-vault/db-password", logger=logger)

        # Result should be the mocked secret value
        assert result == "mock-secret-value"

        # Should have logged the secret resolution operation
        assert len(caplog.records) > 0

        # Verify operation-level logging (ADR-0030: operation type and status only)
        messages = [record.message.lower() for record in caplog.records]

        # Should log completion status
        assert any(
            "secret resolution" in msg and "completed" in msg for msg in messages
        )

        # Should NOT log specific values (ADR-0030)
        assert not any("my-vault" in record.message for record in caplog.records)
        assert not any("db-password" in record.message for record in caplog.records)
        assert not any("akv://" in record.message for record in caplog.records)

        # Verify they were logged at DEBUG level
        debug_records = [r for r in caplog.records if r.levelname == "DEBUG"]
        assert len(debug_records) > 0


def test_secret_resolution_error_is_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that secret resolution errors are logged with error category.

    Acceptance criteria: Operations are logged with type, status, and error category

    This test verifies that when secret resolution fails, the error is logged
    with the error category but without exposing specific values per ADR-0030.
    """
    logger = logging.getLogger("test_resolution_error")

    envresolve.register_azure_kv_provider(provider=MockProvider())

    # Test secret resolution failure (no provider registered)
    with caplog.at_level(logging.ERROR, logger="test_resolution_error"):
        # Expect SecretResolutionError to be raised
        with pytest.raises(envresolve.SecretResolutionError):
            envresolve.resolve_secret("akv://fake-vault/db-password", logger=logger)

        # Should have logged the error
        assert len(caplog.records) > 0

        # Verify error-level logging with category
        messages = [record.message.lower() for record in caplog.records]

        # Should log error category
        assert any(
            "secret resolution" in msg and "provider error" in msg for msg in messages
        )

        # Should NOT log specific values (ADR-0030)
        assert not any("fake-vault" in record.message for record in caplog.records)
        assert not any("db-password" in record.message for record in caplog.records)
        assert not any("akv://" in record.message for record in caplog.records)

        # Verify they were logged at ERROR level
        error_records = [r for r in caplog.records if r.levelname == "ERROR"]
        assert len(error_records) > 0
