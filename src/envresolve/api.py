"""Public API for envresolve."""

import importlib
import os
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import dotenv_values

from envresolve.application.resolver import SecretResolver
from envresolve.exceptions import ProviderRegistrationError

if TYPE_CHECKING:
    from envresolve.providers.base import SecretProvider


class EnvResolver:
    """Manages provider registration and secret resolution.

    This class encapsulates the provider registry and resolver instance,
    eliminating the need for module-level global variables.
    """

    def __init__(self) -> None:
        """Initialize an empty provider registry."""
        self._providers: dict[str, SecretProvider] = {}
        self._resolver: SecretResolver | None = None

    def _get_resolver(self) -> SecretResolver:
        """Get or create the resolver instance.

        Returns:
            SecretResolver instance configured with registered providers
        """
        if self._resolver is None:
            self._resolver = SecretResolver(self._providers)
        return self._resolver

    def register_azure_kv_provider(self) -> None:
        """Register Azure Key Vault provider for akv:// scheme.

        This method is safe to call multiple times (idempotent).

        Raises:
            ProviderRegistrationError: If azure-identity or azure-keyvault-secrets
                is not installed
        """
        try:
            # Dynamically import the provider module
            provider_module = importlib.import_module("envresolve.providers.azure_kv")
            provider_class = provider_module.AzureKVProvider
        except ImportError as e:
            # Check which dependency is missing
            missing_deps: list[str] = []
            try:
                importlib.import_module("azure.identity")
            except ImportError:
                missing_deps.append("azure-identity")

            try:
                importlib.import_module("azure.keyvault.secrets")
            except ImportError:
                missing_deps.append("azure-keyvault-secrets")

            if missing_deps:
                deps_str = ", ".join(missing_deps)
                msg = (
                    f"Azure Key Vault provider requires: {deps_str}. "
                    "Install with: pip install envresolve[azure]"
                )
            else:
                msg = f"Failed to import Azure Key Vault provider. Error: {e}"
            raise ProviderRegistrationError(msg, original_error=e) from e

        provider = provider_class()
        self._providers["akv"] = provider
        # Reset resolver to pick up new providers
        self._resolver = None

    def resolve_secret(self, uri: str) -> str:
        """Resolve a secret URI to its value.

        This function supports:
        - Variable expansion: ${VAR} and $VAR syntax using os.environ
        - Secret URI resolution: akv:// scheme
        - Idempotent resolution: Plain strings and non-target URIs pass through

        Args:
            uri: Secret URI or plain string to resolve

        Returns:
            Resolved secret value or the original string if not a secret URI

        Raises:
            URIParseError: If the URI format is invalid
            SecretResolutionError: If secret resolution fails
            VariableNotFoundError: If a referenced variable is not found
            CircularReferenceError: If a circular variable reference is detected
        """
        resolver = self._get_resolver()
        return resolver.resolve(uri)

    def resolve_with_env(self, value: str, env: dict[str, str]) -> str:
        """Expand variables and resolve secret URIs with custom environment.

        Args:
            value: Value to resolve (may contain variables or be a secret URI)
            env: Environment dict for variable expansion

        Returns:
            Resolved value
        """
        resolver = self._get_resolver()
        return resolver.resolve(value, env)

    def load_env(
        self,
        path: str | Path = ".env",
        *,
        export: bool = True,
        override: bool = False,
    ) -> dict[str, str]:
        """Load environment variables from a .env file and resolve secret URIs.

        This function:
        1. Loads variables from the .env file
        2. Expands variable references within values
        3. Resolves secret URIs (akv://) to actual secret values
        4. Optionally exports to os.environ

        Args:
            path: Path to .env file (default: ".env")
            export: If True, export resolved variables to os.environ
            override: If True, override existing os.environ variables

        Returns:
            Dictionary of resolved environment variables

        Raises:
            FileNotFoundError: If the .env file doesn't exist
            URIParseError: If a URI format is invalid
            SecretResolutionError: If secret resolution fails
            VariableNotFoundError: If a referenced variable is not found
            CircularReferenceError: If a circular variable reference is detected
        """
        # Load .env file
        env_dict = {k: v for k, v in dotenv_values(path).items() if v is not None}

        # Build complete environment (for variable expansion)
        complete_env = dict(os.environ)
        complete_env.update(env_dict)

        # Resolve each variable
        resolved: dict[str, str] = {}
        for key, value in env_dict.items():
            resolved[key] = self.resolve_with_env(value, complete_env)

        # Export to os.environ if requested
        if export:
            for key, value in resolved.items():
                if override or key not in os.environ:
                    os.environ[key] = value

        return resolved


# Default instance for module-level API
_default_resolver = EnvResolver()


def register_azure_kv_provider() -> None:
    """Register Azure Key Vault provider for akv:// scheme.

    This function should be called before attempting to resolve secrets
    from Azure Key Vault. It is safe to call multiple times (idempotent).

    Example:
        >>> import envresolve
        >>> envresolve.register_azure_kv_provider()
        >>> # Now you can resolve secrets (requires Azure authentication)
        >>> # secret = envresolve.resolve_secret("akv://my-vault/db-password")
    """
    _default_resolver.register_azure_kv_provider()


def resolve_secret(uri: str) -> str:
    """Resolve a secret URI to its value.

    This function supports:
    - Variable expansion: ${VAR} and $VAR syntax using os.environ
    - Secret URI resolution: akv:// scheme
    - Idempotent resolution: Plain strings and non-target URIs pass through unchanged

    Args:
        uri: Secret URI or plain string to resolve

    Returns:
        Resolved secret value or the original string if not a secret URI

    Raises:
        URIParseError: If the URI format is invalid
        SecretResolutionError: If secret resolution fails
        VariableNotFoundError: If a referenced variable is not found
        CircularReferenceError: If a circular variable reference is detected

    Examples:
        >>> import envresolve
        >>> # Idempotent - plain strings pass through
        >>> value = envresolve.resolve_secret("just-a-string")
        >>> value
        'just-a-string'
        >>> # Non-target URIs pass through unchanged
        >>> uri = envresolve.resolve_secret("postgres://localhost/db")
        >>> uri
        'postgres://localhost/db'
        >>> # Secret URIs require provider registration and authentication
        >>> # envresolve.register_azure_kv_provider()
        >>> # secret = envresolve.resolve_secret("akv://my-vault/db-password")
    """
    return _default_resolver.resolve_secret(uri)


def load_env(
    path: str | Path = ".env",
    *,
    export: bool = True,
    override: bool = False,
) -> dict[str, str]:
    """Load environment variables from a .env file and resolve secret URIs.

    This function:
    1. Loads variables from the .env file
    2. Expands variable references within values
    3. Resolves secret URIs (akv://) to actual secret values
    4. Optionally exports to os.environ

    Args:
        path: Path to .env file (default: ".env")
        export: If True, export resolved variables to os.environ (default: True)
        override: If True, override existing os.environ variables (default: False)

    Returns:
        Dictionary of resolved environment variables

    Raises:
        FileNotFoundError: If the .env file doesn't exist
        URIParseError: If a URI format is invalid
        SecretResolutionError: If secret resolution fails
        VariableNotFoundError: If a referenced variable is not found
        CircularReferenceError: If a circular variable reference is detected

    Examples:
        >>> import envresolve
        >>> envresolve.register_azure_kv_provider()
        >>> # Load and export to os.environ
        >>> resolved = envresolve.load_env(".env", export=True)  # doctest: +SKIP
        >>> # Load without exporting
        >>> resolved = envresolve.load_env(".env", export=False)  # doctest: +SKIP
    """
    return _default_resolver.load_env(path, export=export, override=override)
