"""Application-level expander classes for environment and .env file integration."""

import logging
import os
from pathlib import Path

from dotenv import dotenv_values

from envresolve.services.expansion import expand_variables


class BaseExpander:
    """Base class for expanders with common expand logic."""

    def __init__(self) -> None:
        """Initialize with empty environment dictionary."""
        self.env: dict[str, str] = {}

    def expand(self, text: str, logger: logging.Logger | None = None) -> str:
        """Expand variables in text using the loaded environment.

        Args:
            text: The text containing variables to expand
            logger: Optional logger for diagnostic messages

        Returns:
            The text with all variables expanded

        Raises:
            CircularReferenceError: If a circular reference is detected
            VariableNotFoundError: If a referenced variable is not found
            InvalidVariableNameError: If a variable name is invalid
        """
        return expand_variables(text, self.env, logger=logger)


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
