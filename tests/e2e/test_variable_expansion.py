"""E2E tests for variable expansion functionality."""

import os

import pytest

from envresolve.exceptions import CircularReferenceError, VariableNotFoundError
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


def test_missing_variable_raises_error() -> None:
    """Test that missing variable raises VariableNotFoundError."""
    expander = VariableExpander()
    env = {"A": "${MISSING}"}

    with pytest.raises(VariableNotFoundError, match=r"MISSING"):
        expander.expand(env["A"], env)


def test_multiple_variable_expansion() -> None:
    """Test that multiple variables in a single string are expanded."""
    expander = VariableExpander()
    env = {
        "VAULT_NAME": "my-vault",
        "SECRET_PATH": "db-password",
        "FULL_URI": "akv://${VAULT_NAME}/${SECRET_PATH}",
    }

    result = expander.expand(env["FULL_URI"], env)

    assert result == "akv://my-vault/db-password"


def test_nested_variable_expansion() -> None:
    """Test that variable values can contain references to other variables."""
    expander = VariableExpander()
    env = {
        "C": "1",
        "B": "1${C}",  # B's value contains ${C}
        "A": "1${B}",  # A's value contains ${B}
    }

    result = expander.expand(env["A"], env)

    assert result == "111"


def test_expansion_with_os_environ() -> None:
    """Test that expansion works with values from os.environ."""
    # Setup: Add test value to os.environ
    original_value = os.environ.get("TEST_VAULT_NAME")
    os.environ["TEST_VAULT_NAME"] = "prod-vault"

    try:
        expander = VariableExpander()
        # Combine os.environ with additional variables
        env = dict(os.environ)
        env["DB_URI"] = "akv://${TEST_VAULT_NAME}/db-password"

        result = expander.expand(env["DB_URI"], env)

        assert result == "akv://prod-vault/db-password"
    finally:
        # Cleanup
        if original_value is None:
            os.environ.pop("TEST_VAULT_NAME", None)
        else:
            os.environ["TEST_VAULT_NAME"] = original_value


def test_expansion_with_dotenv_style() -> None:
    """Test that expansion works with .env file style (simulated dict)."""
    expander = VariableExpander()
    # Simulate .env file content loaded into a dict
    env = {
        "VAULT_NAME": "my-company-vault",
        "DB_PASSWORD": "akv://${VAULT_NAME}/db-password",
        "API_KEY": "akv://${VAULT_NAME}/api-key",
    }

    db_result = expander.expand(env["DB_PASSWORD"], env)
    api_result = expander.expand(env["API_KEY"], env)

    assert db_result == "akv://my-company-vault/db-password"
    assert api_result == "akv://my-company-vault/api-key"


def test_circular_reference_error_message_includes_variable() -> None:
    """Test that circular reference error message clearly indicates the variable."""
    expander = VariableExpander()
    env = {"A": "${B}", "B": "${A}"}

    with pytest.raises(CircularReferenceError) as exc_info:
        expander.expand(env["A"], env)

    # Check that error message contains information about circular reference
    error_message = str(exc_info.value)
    assert "Circular" in error_message or "circular" in error_message
    # Check that a variable name involved in the cycle is in the error
    assert "A" in error_message or "B" in error_message
