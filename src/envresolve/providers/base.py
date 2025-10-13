"""Base provider protocol."""

from typing import Protocol

from envresolve.models import ParsedURI


class SecretProvider(Protocol):
    """Protocol for secret providers."""

    def resolve(self, parsed_uri: ParsedURI) -> str:
        """Resolve a secret from its provider.

        Args:
            parsed_uri: Parsed URI dictionary

        Returns:
            The secret value as a string

        Raises:
            SecretResolutionError: If the secret cannot be resolved
        """
        ...
