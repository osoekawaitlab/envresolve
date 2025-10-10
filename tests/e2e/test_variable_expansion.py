"""E2E tests for variable expansion functionality."""

import pytest

from envresolve.exceptions import CircularReferenceError
from envresolve.services.expansion import VariableExpander


def test_simple_variable_expansion_with_curly_braces() -> None:
    """Test ${VAR} syntax for variable expansion in a simple case."""
    expander = VariableExpander()
    env = {"VAULT_NAME": "my-vault"}

    result = expander.expand("${VAULT_NAME}", env)

    assert result == "my-vault"


def test_simple_variable_expansion_without_curly_braces() -> None:
    """Test $VAR syntax for variable expansion in a simple case."""
    expander = VariableExpander()
    env = {"VAULT_NAME": "my-vault"}

    result = expander.expand("$VAULT_NAME", env)

    assert result == "my-vault"


def test_circular_reference_detection() -> None:
    """Test that circular references are detected and raise errors."""
    expander = VariableExpander()
    env = {"A": "${B}", "B": "${A}"}

    with pytest.raises(CircularReferenceError, match=r"[Cc]ircular"):
        expander.expand(env["A"], env)
