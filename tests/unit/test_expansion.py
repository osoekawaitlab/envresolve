"""Unit tests for variable expansion."""

import os
from pathlib import Path

import pytest

from envresolve.exceptions import CircularReferenceError, VariableNotFoundError
from envresolve.services.expansion import (
    BaseExpander,
    DotEnvExpander,
    EnvExpander,
    expand_variables,
)


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


# BaseExpander tests
def test_base_expander_init() -> None:
    """Test BaseExpander initializes with empty env dict."""
    expander = BaseExpander()

    assert expander.env == {}


def test_base_expander_expand() -> None:
    """Test BaseExpander.expand calls expand_variables with its env."""
    expander = BaseExpander()
    expander.env = {"VAR": "value"}
    result = expander.expand("${VAR}")

    assert result == "value"


# EnvExpander tests
def test_env_expander_init(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test EnvExpander initializes with os.environ."""
    monkeypatch.setenv("TEST_VAR", "test-value")
    expander = EnvExpander()

    assert "TEST_VAR" in expander.env
    assert expander.env["TEST_VAR"] == "test-value"


def test_env_expander_expand(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test EnvExpander.expand uses os.environ."""
    monkeypatch.setenv("TEST_VAR", "test-value")
    expander = EnvExpander()
    result = expander.expand("${TEST_VAR}")

    assert result == "test-value"


def test_env_expander_snapshot() -> None:
    """Test EnvExpander takes a snapshot of os.environ at init time."""
    # Set a value
    os.environ["SNAPSHOT_TEST"] = "initial"
    expander = EnvExpander()

    # Change the value after initialization
    os.environ["SNAPSHOT_TEST"] = "changed"

    # Expander should still have the initial value
    assert expander.env["SNAPSHOT_TEST"] == "initial"

    # Cleanup
    del os.environ["SNAPSHOT_TEST"]


# DotEnvExpander tests
def test_dotenv_expander_init(tmp_path: Path) -> None:
    """Test DotEnvExpander initializes by loading .env file."""
    env_file = tmp_path / ".env"
    env_file.write_text("VAR1=value1\nVAR2=value2\n")

    expander = DotEnvExpander(env_file)

    assert expander.env == {"VAR1": "value1", "VAR2": "value2"}


def test_dotenv_expander_filters_none_values(tmp_path: Path) -> None:
    """Test DotEnvExpander filters out None values from dotenv_values."""
    env_file = tmp_path / ".env"
    env_file.write_text("VAR1=value1\n# Comment line\nVAR2=\n")

    expander = DotEnvExpander(env_file)

    # VAR2 with empty value might be None or empty string, depending on dotenv
    # We test that None values are filtered
    assert "VAR1" in expander.env
    # If VAR2 is None, it should be filtered out
    # If VAR2 is empty string, it should be kept
    for value in expander.env.values():
        assert value is not None


def test_dotenv_expander_expand(tmp_path: Path) -> None:
    """Test DotEnvExpander.expand uses loaded .env values."""
    env_file = tmp_path / ".env"
    env_file.write_text("VAULT=my-vault\n")

    expander = DotEnvExpander(env_file)
    result = expander.expand("akv://${VAULT}/secret")

    assert result == "akv://my-vault/secret"


def test_dotenv_expander_default_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test DotEnvExpander uses .env as default path."""
    monkeypatch.chdir(tmp_path)
    env_file = tmp_path / ".env"
    env_file.write_text("VAR=value\n")

    expander = DotEnvExpander()

    assert expander.env == {"VAR": "value"}
