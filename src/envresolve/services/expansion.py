"""Variable expansion service."""

import re

from envresolve.exceptions import CircularReferenceError, VariableNotFoundError


class VariableExpander:
    """Expands ${VAR} and $VAR in strings with cycle detection."""

    def expand(
        self, text: str, env: dict[str, str], visited: set[str] | None = None
    ) -> str:
        """Expand variables in text using provided env dict.

        Args:
            text: The text containing variables to expand
            env: Dictionary of variable name to value mappings
            visited: Set of variable names currently being resolved
                     (for cycle detection)

        Returns:
            The text with all variables expanded

        Raises:
            CircularReferenceError: If a circular reference is detected
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
            return self.expand(value, env, new_visited)

        return re.sub(pattern, replace, text)
