"""E2E tests for variable expansion functionality."""

import os
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

import envresolve
from envresolve.exceptions import CircularReferenceError, VariableNotFoundError


def test_simple_variable_expansion_with_curly_braces() -> None:
    """Test ${VAR} syntax for variable expansion in a simple case."""
    env = {"VAULT_NAME": "my-vault"}

    result = envresolve.expand_variables("${VAULT_NAME}", env)

    assert result == "my-vault"


def test_simple_variable_expansion_without_curly_braces() -> None:
    """Test $VAR syntax for variable expansion in a simple case."""
    env = {"VAULT_NAME": "my-vault"}

    result = envresolve.expand_variables("$VAULT_NAME", env)

    assert result == "my-vault"


def test_circular_reference_detection() -> None:
    """Test that circular references are detected and raise errors."""
    env = {"A": "${B}", "B": "${A}"}

    with pytest.raises(CircularReferenceError) as exc:
        envresolve.expand_variables(env["A"], env)

    assert exc.value.chain == ["B", "A", "B"]


def test_missing_variable_raises_error() -> None:
    """Test that missing variable raises VariableNotFoundError."""
    env = {"A": "${MISSING}"}

    with pytest.raises(VariableNotFoundError, match=r"MISSING"):
        envresolve.expand_variables(env["A"], env)


def test_multiple_variable_expansion() -> None:
    """Test that multiple variables in a single string are expanded."""
    env = {
        "VAULT_NAME": "my-vault",
        "SECRET_PATH": "db-password",
        "FULL_URI": "akv://${VAULT_NAME}/${SECRET_PATH}",
    }

    result = envresolve.expand_variables(env["FULL_URI"], env)

    assert result == "akv://my-vault/db-password"


def test_nested_variable_expansion() -> None:
    """Test that variable values can contain references to other variables."""
    env = {
        "C": "1",
        "B": "1${C}",  # B's value contains ${C}
        "A": "1${B}",  # A's value contains ${B}
    }

    result = envresolve.expand_variables(env["A"], env)

    assert result == "111"


def test_expansion_with_os_environ(mocker: MockerFixture) -> None:
    """Test that EnvExpander uses os.environ for expansion."""
    mocker.patch.dict(os.environ, {"TEST_VAULT_NAME": "prod-vault"})

    expander = envresolve.EnvExpander()
    result = expander.expand("akv://${TEST_VAULT_NAME}/db-password")

    assert result == "akv://prod-vault/db-password"


def test_expansion_with_dotenv_file(tmp_path: Path) -> None:
    """Test that expansion works when loading from a .env file."""
    # Create a .env file with variable references
    env_file = tmp_path / ".env"
    env_file.write_text(
        "VAULT_NAME=my-company-vault\n"
        "DB_PASSWORD=akv://${VAULT_NAME}/db-password\n"
        "API_KEY=akv://${VAULT_NAME}/api-key\n"
    )

    # Use DotEnvExpander to load and expand
    expander = envresolve.DotEnvExpander(env_file)
    db_result = expander.expand("akv://${VAULT_NAME}/db-password")
    api_result = expander.expand("akv://${VAULT_NAME}/api-key")

    assert db_result == "akv://my-company-vault/db-password"
    assert api_result == "akv://my-company-vault/api-key"
