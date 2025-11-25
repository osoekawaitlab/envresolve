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
