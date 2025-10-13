"""Secret resolution orchestration.

This module coordinates the resolution process:
1. Variable expansion
2. URI parsing
3. Provider selection
4. Secret retrieval
"""

import os
from typing import TYPE_CHECKING

from envresolve.exceptions import SecretResolutionError
from envresolve.services.expansion import expand_variables
from envresolve.services.reference import is_secret_uri, parse_secret_uri

if TYPE_CHECKING:
    from envresolve.models import ParsedURI
    from envresolve.providers.base import SecretProvider


class SecretResolver:
    """Orchestrates secret resolution with variable expansion."""

    def __init__(self, providers: dict[str, "SecretProvider"]) -> None:
        """Initialize resolver with provider registry.

        Args:
            providers: Dictionary mapping URI schemes to provider instances
        """
        self._providers = providers

    def resolve(self, uri: str, env: dict[str, str] | None = None) -> str:
        """Resolve a URI to its secret value.

        This method performs the following steps:
        1. Expand variables in the URI using the provided environment
        2. Check if the expanded string is a secret URI
        3. Parse the URI if it's a secret URI
        4. Get the appropriate provider for the scheme
        5. Resolve the secret using the provider

        Args:
            uri: The URI to resolve (may contain variables)
            env: Environment dict for variable expansion (defaults to os.environ)

        Returns:
            Resolved secret value, or the original string if not a secret URI

        Raises:
            SecretResolutionError: If no provider is registered for the scheme
            URIParseError: If the URI format is invalid
            VariableNotFoundError: If a referenced variable is not found
            CircularReferenceError: If a circular reference is detected
        """
        if env is None:
            env = dict(os.environ)

        # Step 1: Expand variables
        expanded = expand_variables(uri, env)

        # Step 2: Check if it's a secret URI
        if not is_secret_uri(expanded):
            # Not a secret URI - return as-is (idempotent)
            return expanded

        # Step 3: Parse URI
        parsed_uri = parse_secret_uri(expanded)

        # Step 4: Get provider and resolve
        provider = self._get_provider(parsed_uri)
        return provider.resolve(parsed_uri)

    def _get_provider(self, parsed_uri: "ParsedURI") -> "SecretProvider":
        """Get provider for the given URI scheme.

        Args:
            parsed_uri: Parsed URI containing the scheme

        Returns:
            Provider instance for the scheme

        Raises:
            SecretResolutionError: If no provider is registered for the scheme
        """
        scheme = parsed_uri["scheme"]
        if scheme not in self._providers:
            msg = f"No provider registered for scheme '{scheme}'"
            uri = f"{scheme}://..."
            raise SecretResolutionError(msg, uri=uri)
        return self._providers[scheme]
