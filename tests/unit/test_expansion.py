"""Unit tests for variable expansion."""

import pytest

from envresolve.exceptions import CircularReferenceError
from envresolve.services.expansion import VariableExpander


def test_variable_expander_exists() -> None:
    """Test that VariableExpander class can be imported."""
    assert VariableExpander is not None


def test_expand_method_exists() -> None:
    """Test that VariableExpander has expand method."""
    expander = VariableExpander()
    assert hasattr(expander, "expand")
    assert callable(expander.expand)


def test_expand_simple_curly_braces() -> None:
    """Test expanding ${VAR} pattern."""
    expander = VariableExpander()
    result = expander.expand("${VAULT}", {"VAULT": "my-vault"})

    assert result == "my-vault"


def test_expand_simple_without_curly_braces() -> None:
    """Test expanding $VAR pattern."""
    expander = VariableExpander()
    result = expander.expand("$VAULT", {"VAULT": "my-vault"})

    assert result == "my-vault"


def test_circular_reference_raises_error() -> None:
    """Test that circular reference raises CircularReferenceError."""
    expander = VariableExpander()
    env = {"A": "${B}", "B": "${A}"}

    with pytest.raises(CircularReferenceError):
        expander.expand(env["A"], env)
