"""Unit tests for expand_variables function."""

import logging
from unittest.mock import MagicMock

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

    with pytest.raises(CircularReferenceError) as exc:
        expand_variables("${A}", env)

    assert exc.value.chain == ["A", "B", "A"]
    assert str(exc.value) == "Circular reference detected: A -> B -> A"


def test_missing_variable_raises_error() -> None:
    """Test that missing variable raises VariableNotFoundError."""
    with pytest.raises(VariableNotFoundError, match=r"MISSING"):
        expand_variables("${MISSING}", {"A": "value"})


def test_expand_multiple_variables() -> None:
    """Test expanding multiple variables in a single string."""
    env = {"VAULT": "my-vault", "SECRET": "db-password"}
    result = expand_variables("akv://${VAULT}/${SECRET}", env)

    assert result == "akv://my-vault/db-password"


def test_expand_nested_variables() -> None:
    """Test expanding nested variable references."""
    env = {"C": "3", "B": "2${C}", "A": "1${B}"}
    result = expand_variables("${A}", env)

    assert result == "123"


def test_expand_text_without_variables() -> None:
    """Test that text without variables is returned unchanged."""
    result = expand_variables("plain text", {"VAR": "value"})

    assert result == "plain text"


def test_expand_empty_string() -> None:
    """Test expanding empty string."""
    result = expand_variables("", {"VAR": "value"})

    assert result == ""


def test_expand_dollar_sign_alone() -> None:
    """Test that lone dollar sign is preserved."""
    result = expand_variables("price: $100", {"VAR": "value"})

    assert result == "price: $100"


def test_expand_nested_curly_braces() -> None:
    """Test that nested curly braces are expanded correctly."""
    env = {"NESTED": "BAR", "VAR_BAR": "value"}
    result = expand_variables("${VAR_${NESTED}}", env)
    assert result == "value"


def test_expand_variables_accepts_logger_parameter() -> None:
    """Test that expand_variables accepts optional logger parameter."""
    logger = MagicMock(spec=logging.Logger)

    result = expand_variables("${FOO}", {"FOO": "bar"}, logger=logger)

    assert result == "bar"
    # Logger should have been called to log the expansion
    logger.debug.assert_called()
