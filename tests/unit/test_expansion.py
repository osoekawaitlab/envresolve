"""Unit tests for variable expansion."""

import pytest

from envresolve.exceptions import CircularReferenceError, VariableNotFoundError
from envresolve.services.expansion import expand_variables


def test_expand_variables_function_exists() -> None:
    """Test that expand_variables function can be imported."""
    assert expand_variables is not None
    assert callable(expand_variables)


def test_expand_simple_curly_braces() -> None:
    """Test expanding ${VAR} pattern."""
    result = expand_variables("${VAULT}", {"VAULT": "my-vault"})

    assert result == "my-vault"


def test_expand_simple_without_curly_braces() -> None:
    """Test expanding $VAR pattern."""
    result = expand_variables("$VAULT", {"VAULT": "my-vault"})

    assert result == "my-vault"


def test_circular_reference_raises_error() -> None:
    """Test that circular reference raises CircularReferenceError."""
    env = {"A": "${B}", "B": "${A}"}

    with pytest.raises(CircularReferenceError):
        expand_variables(env["A"], env)


def test_missing_variable_raises_error() -> None:
    """Test that missing variable raises VariableNotFoundError."""
    with pytest.raises(VariableNotFoundError, match=r"MISSING"):
        expand_variables("${MISSING}", {"A": "value"})
