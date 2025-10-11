"""Variable expansion service."""

import os
import re
from pathlib import Path

from dotenv import dotenv_values

from envresolve.exceptions import CircularReferenceError, VariableNotFoundError


def expand_variables(
    text: str, env: dict[str, str], visited: set[str] | None = None
) -> str:
    """Expand ${VAR} and $VAR in text using provided environment dictionary.

    Args:
        text: The text containing variables to expand
        env: Dictionary of variable name to value mappings
        visited: Set of variable names currently being resolved (for cycle detection)

    Returns:
        The text with all variables expanded

    Raises:
        CircularReferenceError: If a circular reference is detected
        VariableNotFoundError: If a referenced variable is not found

    Examples:
        >>> expand_variables("${VAULT}", {"VAULT": "my-vault"})
        'my-vault'
        >>> expand_variables("$VAULT", {"VAULT": "my-vault"})
        'my-vault'
    """
    if visited is None:
        visited = set()

    # Pattern for ${VAR} or $VAR (word characters, numbers, underscore)
    pattern = r"\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)"

    def replace(match: re.Match[str]) -> str:
        # Group 1 is from ${VAR}, group 2 is from $VAR
        var_name = match.group(1) if match.group(1) else match.group(2)

        # Check for circular reference
        if var_name in visited:
            raise CircularReferenceError(var_name)

        # Get the value and recursively expand it
        try:
            value = env[var_name]
        except KeyError as e:
            raise VariableNotFoundError(var_name) from e

        # Add to visited set before recursing
        new_visited = visited | {var_name}

        # Recursively expand the value
        return expand_variables(value, env, new_visited)

    return re.sub(pattern, replace, text)


class BaseExpander:
    """Base class for expanders with common expand logic."""

    def __init__(self) -> None:
        """Initialize with empty environment dictionary."""
        self.env: dict[str, str] = {}

    def expand(self, text: str) -> str:
        """Expand variables in text using the loaded environment.

        Args:
            text: The text containing variables to expand

        Returns:
            The text with all variables expanded

        Raises:
            CircularReferenceError: If a circular reference is detected
            VariableNotFoundError: If a referenced variable is not found
        """
        return expand_variables(text, self.env)


class EnvExpander(BaseExpander):
    """Convenience wrapper for expanding variables using os.environ."""

    def __init__(self) -> None:
        """Initialize expander with os.environ.

        Examples:
            >>> import os
            >>> os.environ["TEST_VAR"] = "test-value"
            >>> expander = EnvExpander()
            >>> expander.expand("${TEST_VAR}")
            'test-value'
        """
        super().__init__()
        self.env = dict(os.environ)


class DotEnvExpander(BaseExpander):
    """Convenience wrapper for expanding variables from a .env file."""

    def __init__(self, dotenv_path: Path | str = ".env") -> None:
        """Initialize expander with .env file.

        Args:
            dotenv_path: Path to the .env file (default: ".env")
        """
        super().__init__()
        self.env = {
            k: v for k, v in dotenv_values(dotenv_path).items() if v is not None
        }
