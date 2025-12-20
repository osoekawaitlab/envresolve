"""Unit tests for expand_variables function."""

import logging
from unittest.mock import MagicMock

import pytest

from envresolve.exceptions import CircularReferenceError, VariableNotFoundError
from envresolve.services.expansion import _parse_variable_spec, expand_variables


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


def test_expand_variables_logs_completion_on_success() -> None:
    """Test that successful expansion logs completion message."""
    logger = MagicMock(spec=logging.Logger)

    expand_variables("${FOO}", {"FOO": "bar"}, logger=logger)

    # Verify debug log was called with completion message
    logger.debug.assert_called_once_with("Variable expansion completed")


def test_expand_variables_logs_error_on_variable_not_found() -> None:
    """Test that VariableNotFoundError logs error message."""
    logger = MagicMock(spec=logging.Logger)

    with pytest.raises(VariableNotFoundError):
        expand_variables("${MISSING}", {}, logger=logger)

    # Verify error log was called with error message
    logger.error.assert_called_once_with(
        "Variable expansion failed: variable not found"
    )


def test_expand_variables_logs_error_on_circular_reference() -> None:
    """Test that CircularReferenceError logs error message."""
    logger = MagicMock(spec=logging.Logger)
    env = {"A": "${B}", "B": "${A}"}

    with pytest.raises(CircularReferenceError):
        expand_variables("${A}", env, logger=logger)

    # Verify error log was called with error message
    logger.error.assert_called_once_with(
        "Variable expansion failed: circular reference detected"
    )


def test_expand_variables_does_not_log_when_logger_is_none() -> None:
    """Test that no logging occurs when logger is None."""
    # Should not raise any errors even though logger is None
    result = expand_variables("${FOO}", {"FOO": "bar"}, logger=None)

    assert result == "bar"


def test_expand_variables_does_not_log_variable_names() -> None:
    """Test that variable names are not included in log messages."""
    logger = MagicMock(spec=logging.Logger)

    expand_variables("${SECRET_KEY}", {"SECRET_KEY": "value"}, logger=logger)

    # Verify that variable names are not in any log calls
    for call in logger.debug.call_args_list:
        args = call[0]
        assert "SECRET_KEY" not in str(args)

    for call in logger.error.call_args_list:
        args = call[0]
        assert "SECRET_KEY" not in str(args)


def test_expand_variables_does_not_log_variable_values() -> None:
    """Test that variable values are not included in log messages."""
    logger = MagicMock(spec=logging.Logger)

    expand_variables("${FOO}", {"FOO": "secret-value"}, logger=logger)

    # Verify that variable values are not in any log calls
    for call in logger.debug.call_args_list:
        args = call[0]
        assert "secret-value" not in str(args)

    for call in logger.error.call_args_list:
        args = call[0]
        assert "secret-value" not in str(args)


# Phase 1: Core Parsing Logic Tests


def test_parse_variable_spec_without_default() -> None:
    """Test parsing variable spec without default value."""
    var_name, default_value = _parse_variable_spec("VAR")

    assert var_name == "VAR"
    assert default_value is None


def test_parse_variable_spec_with_default() -> None:
    """Test parsing variable spec with default value."""
    var_name, default_value = _parse_variable_spec("VAR:-default")

    assert var_name == "VAR"
    assert default_value == "default"


def test_parse_variable_spec_with_empty_default() -> None:
    """Test parsing variable spec with empty default value."""
    var_name, default_value = _parse_variable_spec("VAR:-")

    assert var_name == "VAR"
    assert default_value == ""


def test_parse_variable_spec_with_colon_in_default() -> None:
    """Test parsing variable spec with colon in default value."""
    var_name, default_value = _parse_variable_spec("VAR:-http://example.com:8080")

    assert var_name == "VAR"
    assert default_value == "http://example.com:8080"


def test_parse_variable_spec_with_multiple_delimiters() -> None:
    """Test parsing variable spec with multiple :- in default value."""
    var_name, default_value = _parse_variable_spec("VAR:-default:-backup")

    assert var_name == "VAR"
    assert default_value == "default:-backup"


def test_parse_variable_spec_with_empty_var_name_raises_error() -> None:
    """Test that empty variable name raises VariableNotFoundError."""
    with pytest.raises(VariableNotFoundError) as exc:
        _parse_variable_spec(":-default")

    assert exc.value.variable_name == ""


# Phase 2: Resolution with Default Values Tests


def test_expand_undefined_variable_with_default() -> None:
    """Test that undefined variable uses default value."""
    result = expand_variables("${VAR:-fallback}", {})

    assert result == "fallback"


def test_expand_empty_variable_with_default() -> None:
    """Test that empty variable uses default value."""
    result = expand_variables("${VAR:-fallback}", {"VAR": ""})

    assert result == "fallback"


def test_expand_defined_variable_ignores_default() -> None:
    """Test that defined variable ignores default value."""
    result = expand_variables("${VAR:-fallback}", {"VAR": "actual"})

    assert result == "actual"


# Phase 3: Nested Default Values Tests


def test_expand_nested_variable_in_default() -> None:
    """Test that default value can contain nested variables."""
    result = expand_variables("${VAR:-${OTHER}}", {"OTHER": "backup"})

    assert result == "backup"


def test_expand_multiple_default_levels() -> None:
    """Test multiple levels of default values."""
    result = expand_variables("${A:-${B:-${C}}}", {"C": "deep"})

    assert result == "deep"


def test_expand_default_with_multiple_vars() -> None:
    """Test default value with multiple variables."""
    result = expand_variables("${VAR:-prefix-${OTHER}-suffix}", {"OTHER": "mid"})

    assert result == "prefix-mid-suffix"


# Phase 4: Circular Reference Handling Tests


def test_circular_reference_in_default_value() -> None:
    """Test that circular reference through default is detected."""
    env = {"A": "${B:-${A}}", "B": ""}

    with pytest.raises(CircularReferenceError) as exc:
        expand_variables("${A}", env)

    # A is expanded, contains ${B:-${A}}, innermost ${A} processed first
    assert exc.value.chain == ["A", "A"]


def test_circular_reference_chain_with_default() -> None:
    """Test complex circular reference involving defaults."""
    env = {"A": "${C}", "C": "${B:-${A}}"}

    with pytest.raises(CircularReferenceError) as exc:
        expand_variables("${A}", env)

    # A -> C -> B (empty, uses default ${A}) -> circular
    assert "A" in exc.value.chain
    assert "C" in exc.value.chain


def test_default_with_undefined_nested_variable() -> None:
    """Test default value containing undefined variable raises error."""
    with pytest.raises(VariableNotFoundError) as exc:
        expand_variables("${VAR:-${UNDEFINED}}", {})

    assert exc.value.variable_name == "UNDEFINED"


def test_non_circular_complex_default() -> None:
    """Test non-circular complex default value."""
    env = {"B": "${C}", "C": "value"}
    result = expand_variables("${A:-${B}}", env)

    assert result == "value"


# Phase 5: Edge Case Tests


def test_empty_default_value() -> None:
    """Test that empty default value returns empty string."""
    result = expand_variables("${VAR:-}", {})

    assert result == ""


def test_default_with_special_characters() -> None:
    """Test default value with special characters."""
    result = expand_variables("${VAR:-url:port}", {})

    assert result == "url:port"


def test_default_with_whitespace() -> None:
    """Test that whitespace in default value is preserved."""
    result = expand_variables("${VAR:-  spaces  }", {})

    assert result == "  spaces  "


def test_default_with_dollar_sign() -> None:
    """Test default value containing dollar sign."""
    result = expand_variables("${VAR:-price is $100}", {})

    assert result == "price is $100"


def test_multiple_variables_with_defaults() -> None:
    """Test multiple variables with default values in one string."""
    result = expand_variables("${A:-x}/${B:-y}", {"A": "1"})

    assert result == "1/y"


# Phase 6: Integration Tests


def test_simple_var_with_default_syntax() -> None:
    """Test simple variable syntax combined with default syntax."""
    env = {"PREFIX": "start"}
    result = expand_variables("$PREFIX-${SUFFIX:-end}", env)

    assert result == "start-end"


def test_nested_curly_with_defaults() -> None:
    """Test nested curly braces with default values."""
    env = {"ENV": "dev", "VAR_dev": "value"}
    result = expand_variables("${VAR_${ENV:-prod}}", env)

    assert result == "value"
