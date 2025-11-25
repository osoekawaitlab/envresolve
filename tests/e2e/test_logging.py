"""E2E tests for logging functionality.

Tests verify acceptance criteria from issue #40:
- EnvResolver accepts optional logger parameter in constructor
- Global facade provides set_logger() function for default logger
"""

import logging

import envresolve
from envresolve.api import EnvResolver


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

    # load_env should accept logger parameter
    # (Will test with actual .env file later when logging is implemented)

    # resolve_os_environ should accept logger parameter
    # (Will test with actual environment variables later when logging is implemented)


def test_env_resolver_methods_accept_logger_parameter() -> None:
    """Test that EnvResolver methods accept optional logger parameter.

    The logger parameter in methods should override the constructor logger.
    """
    constructor_logger = logging.getLogger("constructor")
    method_logger = logging.getLogger("method")

    resolver = EnvResolver(logger=constructor_logger)

    # resolve_secret should accept logger parameter
    secret_result = resolver.resolve_secret("plain-string", logger=method_logger)
    assert secret_result == "plain-string"  # noqa: S105

    # Should work without logger parameter (uses constructor logger)
    secret_result = resolver.resolve_secret("plain-string")
    assert secret_result == "plain-string"  # noqa: S105

    # load_env should accept logger parameter
    # (basic smoke test - actual logging will be tested when implementation is complete)
    env_result = resolver.load_env(dotenv_path=None, logger=method_logger)
    assert isinstance(env_result, dict)

    # resolve_os_environ should accept logger parameter
    # (basic smoke test - actual logging will be tested when implementation is complete)
    os_result = resolver.resolve_os_environ(logger=method_logger)
    assert isinstance(os_result, dict)
