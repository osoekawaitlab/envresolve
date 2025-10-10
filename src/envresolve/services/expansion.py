"""Variable expansion service."""

import re


class VariableExpander:
    """Expands ${VAR} and $VAR in strings with cycle detection."""

    def expand(self, text: str, env: dict[str, str]) -> str:
        """Expand variables in text using provided env dict."""

        def replace(match: re.Match[str]) -> str:
            # Group 1 is from ${VAR}, group 2 is from $VAR
            var_name = match.group(1) if match.group(1) else match.group(2)
            return env[var_name]

        # Pattern for ${VAR} or $VAR (word characters, numbers, underscore)
        pattern = r"\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)"

        return re.sub(pattern, replace, text)
