"""E2E tests for variable expansion functionality."""

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
