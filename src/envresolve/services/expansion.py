"""Variable expansion service."""

import re

from envresolve.exceptions import CircularReferenceError, VariableNotFoundError

INNER_CURLY_PATTERN = re.compile(r"\$\{([^{}]+)\}")
SIMPLE_VAR_PATTERN = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)\b")


def expand_variables(text: str, env: dict[str, str]) -> str:
    """Expand ${VAR} and $VAR in text using provided environment dictionary.

    This function expands variables recursively to support nested variables and
    multiple variables in a single string. Circular references are detected by
    keeping track of the expansion stack and reporting the chain that caused the
    loop.

    Args:
        text: The text containing variables to expand
        env: Dictionary of variable name to value mappings

    Returns:
        The text with all variables expanded

    Raises:
        CircularReferenceError: If a circular reference is detected
        VariableNotFoundError: If a referenced variable is not found

    Examples:
        >>> expand_variables("${VAULT}", {"VAULT": "my-vault"})
        'my-vault'
        >>> expand_variables("${VAR_${NESTED}}", {"NESTED": "BAR", "VAR_BAR": "value"})
        'value'
        >>> expand_variables("akv://${VAULT}/${SECRET}", {"VAULT": "v", "SECRET": "s"})
        'akv://v/s'
    """
    return _expand_text(text, env, [])


def _resolve(var_name: str, env: dict[str, str], stack: list[str]) -> str:
    if var_name in stack:
        cycle_start = stack.index(var_name)
        cycle = [*stack[cycle_start:], var_name]
        raise CircularReferenceError(var_name, cycle)

    if var_name not in env:
        raise VariableNotFoundError(var_name)

    stack.append(var_name)
    try:
        return _expand_text(env[var_name], env, stack)
    finally:
        stack.pop()


def _expand_text(value: str, env: dict[str, str], stack: list[str]) -> str:
    current = value

    while True:
        curly_changed = False

        def replace_curly(match: re.Match[str]) -> str:
            nonlocal curly_changed
            curly_changed = True
            return _resolve(match.group(1), env, stack)

        next_value = INNER_CURLY_PATTERN.sub(replace_curly, current)
        if curly_changed:
            current = next_value
            continue

        simple_changed = False

        def replace_simple(match: re.Match[str]) -> str:
            nonlocal simple_changed
            simple_changed = True
            return _resolve(match.group(1), env, stack)

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
