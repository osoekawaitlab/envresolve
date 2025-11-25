"""Base provider protocol."""

import logging
from typing import Protocol

from envresolve.models import ParsedURI


class SecretProvider(Protocol):
    """Protocol for secret providers."""

    def resolve(
        self, parsed_uri: ParsedURI, logger: logging.Logger | None = None
    ) -> str:
        """Resolve a secret from its provider.

        Args:
            parsed_uri: Parsed URI dictionary
            logger: Optional logger for diagnostic messages

        Returns:
            The secret value as a string

        Raises:
            SecretResolutionError: If the secret cannot be resolved
        """
        ...
