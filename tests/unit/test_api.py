"""Unit tests for the public API layer."""

import envresolve


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
