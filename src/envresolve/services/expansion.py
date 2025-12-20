"""Variable expansion service."""

import logging
import re

from envresolve.exceptions import (
    CircularReferenceError,
    InvalidVariableNameError,
    VariableNotFoundError,
)

INNER_CURLY_PATTERN = re.compile(r"\$\{([^{}]+)\}")
SIMPLE_VAR_PATTERN = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)\b")
VAR_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _log_error(logger: logging.Logger | None, message: str) -> None:
    """Log an error message if logger is provided.

    Uses logger.error instead of logger.exception to avoid exposing
    sensitive information in tracebacks (ADR-0030).

    Args:
        logger: Optional logger instance
        message: Error message to log
    """
    if logger is not None:
        logger.error(message)


def _parse_variable_spec(spec: str) -> tuple[str, str | None]:
    """Parse variable specification into name and default value.

    Args:
        spec: Variable specification (e.g., "VAR" or "VAR:-default")

    Returns:
        Tuple of (variable_name, default_value or None)

    Raises:
        InvalidVariableNameError: If variable name does not match allowed pattern

    Examples:
        >>> _parse_variable_spec("VAR")
        ('VAR', None)
        >>> _parse_variable_spec("VAR:-default")
        ('VAR', 'default')
        >>> _parse_variable_spec("VAR:-http://example.com:8080")
        ('VAR', 'http://example.com:8080')
    """
    if ":-" not in spec:
        var_name, default_value = spec, None
    else:
        # Split on first :- only (allows :- in default value)
        parts = spec.split(":-", 1)
        var_name = parts[0]
        default_value = parts[1] if len(parts) > 1 else ""

    # Validate variable name (e.g., prevents ${:-default} or ${1VAR:-x})
    if not VAR_NAME_PATTERN.match(var_name):
        raise InvalidVariableNameError(var_name or "<empty>")

    return (var_name, default_value)


def expand_variables(
    text: str, env: dict[str, str], logger: logging.Logger | None = None
) -> str:
    """Expand ${VAR} and $VAR in text using provided environment dictionary.

    This function expands variables recursively to support nested variables and
    multiple variables in a single string. Circular references are detected by
    keeping track of the expansion stack and reporting the chain that caused the
    loop.

    Supports default values with ${VAR:-default} syntax. If VAR is undefined or
    empty, the default value is used. Default values are expanded recursively.

    Args:
        text: The text containing variables to expand
        env: Dictionary of variable name to value mappings
        logger: Optional logger for diagnostic messages

    Returns:
        The text with all variables expanded

    Raises:
        CircularReferenceError: If a circular reference is detected
        VariableNotFoundError: If a referenced variable is not found and no default
        InvalidVariableNameError: If a variable name is invalid

    Examples:
        >>> expand_variables("${VAULT}", {"VAULT": "my-vault"})
        'my-vault'
        >>> expand_variables("${VAR_${NESTED}}", {"NESTED": "BAR", "VAR_BAR": "value"})
        'value'
        >>> expand_variables("akv://${VAULT}/${SECRET}", {"VAULT": "v", "SECRET": "s"})
        'akv://v/s'
        >>> expand_variables("${HOST:-localhost}", {})
        'localhost'
        >>> expand_variables("${HOST:-localhost}", {"HOST": ""})
        'localhost'
        >>> expand_variables("${HOST:-localhost}", {"HOST": "example.com"})
        'example.com'
    """
    try:
        result = _expand_text(text, env, [], logger)
    except VariableNotFoundError:
        _log_error(logger, "Variable expansion failed: variable not found")
        raise
    except CircularReferenceError:
        _log_error(logger, "Variable expansion failed: circular reference detected")
        raise
    else:
        if logger is not None:
            logger.debug("Variable expansion completed")
        return result


def _resolve(
    var_name: str,
    env: dict[str, str],
    stack: list[str],
    logger: logging.Logger | None,
    default_value: str | None = None,
) -> str:
    """Resolve a variable, using default if provided and var not found/empty.

    Args:
        var_name: Variable name to resolve
        env: Environment dictionary
        stack: Expansion stack for circular reference detection
        logger: Optional logger
        default_value: Optional default value if variable is undefined/empty

    Returns:
        Resolved and expanded value

    Raises:
        CircularReferenceError: If circular reference detected
        VariableNotFoundError: If variable not found and no default provided
        InvalidVariableNameError: If variable name is invalid
    """
    if var_name in stack:
        cycle_start = stack.index(var_name)
        cycle = [*stack[cycle_start:], var_name]
        raise CircularReferenceError(var_name, cycle)

    # Check if variable is missing or empty
    if var_name not in env or env[var_name] == "":
        if default_value is not None:
            # Expand the default value recursively
            stack.append(var_name)
            try:
                return _expand_text(default_value, env, stack, logger)
            finally:
                stack.pop()
        # No default, raise error
        raise VariableNotFoundError(var_name)

    # Variable exists and is non-empty
    stack.append(var_name)
    try:
        return _expand_text(env[var_name], env, stack, logger)
    finally:
        stack.pop()


def _expand_text(
    value: str,
    env: dict[str, str],
    stack: list[str],
    logger: logging.Logger | None,
) -> str:
    current = value

    while True:
        curly_changed = False

        def replace_curly(match: re.Match[str]) -> str:
            nonlocal curly_changed
            curly_changed = True
            var_reference = match.group(1)

            # Parse variable spec to extract name and default
            var_name, default_value = _parse_variable_spec(var_reference)
            return _resolve(var_name, env, stack, logger, default_value)

        next_value = INNER_CURLY_PATTERN.sub(replace_curly, current)
        if curly_changed:
            current = next_value
            continue

        simple_changed = False

        def replace_simple(match: re.Match[str]) -> str:
            nonlocal simple_changed
            simple_changed = True
            return _resolve(match.group(1), env, stack, logger)

        next_value = SIMPLE_VAR_PATTERN.sub(replace_simple, current)
        if simple_changed:
            current = next_value
            continue

        unresolved_curly = INNER_CURLY_PATTERN.search(current)
        if unresolved_curly:
            raise VariableNotFoundError(unresolved_curly.group(1))

        unresolved_simple = SIMPLE_VAR_PATTERN.search(current)
        if unresolved_simple:
            raise VariableNotFoundError(unresolved_simple.group(1))

        return current
