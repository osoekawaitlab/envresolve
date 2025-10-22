"""Public API for envresolve."""

import importlib
import os
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import dotenv_values, find_dotenv

from envresolve.application.resolver import SecretResolver
from envresolve.exceptions import (
    MutuallyExclusiveArgumentsError,
    ProviderRegistrationError,
    SecretResolutionError,
    VariableNotFoundError,
)

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

    def register_azure_kv_provider(
        self, provider: "SecretProvider | None" = None
    ) -> None:
        """Register Azure Key Vault provider for akv:// scheme.

        This method is safe to call multiple times (idempotent).

        Args:
            provider: Optional custom provider. If None, uses default AzureKVProvider.

        Raises:
            ProviderRegistrationError: If azure-identity or azure-keyvault-secrets
                is not installed (only when provider is None)
        """
        if provider is None:
            try:
                # Dynamically import the provider module
                provider_module = importlib.import_module(
                    "envresolve.providers.azure_kv"
                )
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
        dotenv_path: str | Path | None = None,
        *,
        export: bool = True,
        override: bool = False,
        stop_on_expansion_error: bool = True,
        stop_on_resolution_error: bool = True,
    ) -> dict[str, str]:
        """Load environment variables from a .env file and resolve secret URIs.

        This function:
        1. Loads variables from the .env file
        2. Expands variable references within values
        3. Resolves secret URIs (akv://) to actual secret values
        4. Optionally exports to os.environ

        Args:
            dotenv_path: Path to .env file. If None, searches for .env in
                current directory. Mimics python-dotenv's load_dotenv() behavior.
                (default: None)
            export: If True, export resolved variables to os.environ
            override: If True, override existing os.environ variables
            stop_on_expansion_error: If False, skip variables with expansion errors
                (e.g., VariableNotFoundError). CircularReferenceError is always
                raised as it indicates a configuration error. (default: True)
            stop_on_resolution_error: If False, skip variables with resolution errors
                (e.g., SecretResolutionError). Useful for resilience against transient
                secret store failures. (default: True)

        Returns:
            Dictionary of resolved environment variables

        Raises:
            URIParseError: If a URI format is invalid
            SecretResolutionError: If secret resolution fails
                (when stop_on_resolution_error=True)
            VariableNotFoundError: If a referenced variable is not found
                (when stop_on_expansion_error=True)
            CircularReferenceError: If a circular variable reference is detected
        """
        # Load .env file
        # When dotenv_path is None, use find_dotenv with usecwd=True
        if dotenv_path is None:
            dotenv_path = find_dotenv(usecwd=True)
        # Use interpolate=False to prevent python-dotenv from expanding variables
        # We handle expansion ourselves in resolve_with_env
        env_dict = {
            k: v
            for k, v in dotenv_values(dotenv_path, interpolate=False).items()
            if v is not None
        }

        # Build complete environment (for variable expansion)
        complete_env = dict(os.environ)
        complete_env.update(env_dict)

        # Resolve each variable
        resolved: dict[str, str] = {}
        for key, value in env_dict.items():
            try:
                resolved[key] = self.resolve_with_env(value, complete_env)
            except VariableNotFoundError:
                if stop_on_expansion_error:
                    raise
                # Skip this variable on expansion error
                continue
            except SecretResolutionError:
                if stop_on_resolution_error:
                    raise
                # Skip this variable on resolution error
                continue
            # CircularReferenceError is always raised (configuration error)

        # Export to os.environ if requested
        if export:
            for key, value in resolved.items():
                if override or key not in os.environ:
                    os.environ[key] = value

        return resolved

    def resolve_os_environ(  # noqa: C901
        self,
        keys: list[str] | None = None,
        prefix: str | None = None,
        *,
        overwrite: bool = True,
        stop_on_expansion_error: bool = True,
        stop_on_resolution_error: bool = True,
    ) -> dict[str, str]:
        """Resolve secret URIs in os.environ.

        Args:
            keys: List of specific keys to resolve. If None, scan all keys.
                Mutually exclusive with prefix.
            prefix: Only process keys with this prefix, strip prefix from output.
                Mutually exclusive with keys.
            overwrite: If True, update os.environ with resolved values.
            stop_on_expansion_error: If False, skip variables with expansion errors
                (e.g., VariableNotFoundError). CircularReferenceError is always
                raised as it indicates a configuration error. (default: True)
            stop_on_resolution_error: If False, skip variables with resolution errors
                (e.g., SecretResolutionError). Useful for resilience against transient
                secret store failures. (default: True)

        Returns:
            Dictionary of resolved values

        Raises:
            MutuallyExclusiveArgumentsError: If both keys and prefix are specified
            VariableNotFoundError: If a referenced variable is not found
                (when stop_on_expansion_error=True)
            CircularReferenceError: If a circular variable reference is detected
            SecretResolutionError: If secret resolution fails
                (when stop_on_resolution_error=True)
        """
        # Check mutually exclusive arguments
        if keys is not None and prefix is not None:
            arg1 = "keys"
            arg2 = "prefix"
            raise MutuallyExclusiveArgumentsError(arg1, arg2)

        # Determine which keys to process
        if keys is not None:
            keys_to_process = keys
        elif prefix is not None:
            keys_to_process = [k for k in os.environ if k.startswith(prefix)]
        else:
            keys_to_process = list(os.environ)

        # Resolve each key
        resolved: dict[str, str] = {}
        for key in keys_to_process:
            if key not in os.environ:
                continue

            value = os.environ[key]

            # Resolve the value
            try:
                resolved_value = self.resolve_with_env(value, dict(os.environ))
            except VariableNotFoundError:
                if stop_on_expansion_error:
                    raise
                # Skip this key on expansion error
                continue
            except SecretResolutionError:
                if stop_on_resolution_error:
                    raise
                # Skip this key on resolution error
                continue
            # CircularReferenceError is always raised (configuration error)

            # Determine output key (strip prefix if specified)
            output_key = (
                key[len(prefix) :] if prefix and key.startswith(prefix) else key
            )

            resolved[output_key] = resolved_value

            # Update os.environ if requested
            if overwrite:
                os.environ[output_key] = resolved_value
                # If prefix stripping occurred, remove the old key
                if prefix and key.startswith(prefix) and output_key != key:
                    del os.environ[key]

        return resolved


# Default instance for module-level API
_default_resolver = EnvResolver()


def register_azure_kv_provider(provider: "SecretProvider | None" = None) -> None:
    """Register Azure Key Vault provider for akv:// scheme.

    This function should be called before attempting to resolve secrets
    from Azure Key Vault. It is safe to call multiple times (idempotent).

    Args:
        provider: Optional custom provider. If None, uses default AzureKVProvider.

    Raises:
        ProviderRegistrationError: If azure-identity or azure-keyvault-secrets
            is not installed (only when provider is None)

    Examples:
        >>> import envresolve
        >>> # Default behavior
        >>> envresolve.register_azure_kv_provider()
        >>> # Custom provider (requires Azure SDK imports)
        >>> # from envresolve.providers.azure_kv import AzureKVProvider
        >>> # from azure.identity import ManagedIdentityCredential
        >>> # custom = AzureKVProvider(credential=ManagedIdentityCredential())
        >>> # envresolve.register_azure_kv_provider(provider=custom)
        >>> # Now you can resolve secrets (requires Azure authentication)
        >>> # secret = envresolve.resolve_secret("akv://my-vault/db-password")
    """
    _default_resolver.register_azure_kv_provider(provider=provider)


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
    dotenv_path: str | Path | None = None,
    *,
    export: bool = True,
    override: bool = False,
    stop_on_expansion_error: bool = True,
    stop_on_resolution_error: bool = True,
) -> dict[str, str]:
    """Load environment variables from a .env file and resolve secret URIs.

    This function:
    1. Loads variables from the .env file
    2. Expands variable references within values
    3. Resolves secret URIs (akv://) to actual secret values
    4. Optionally exports to os.environ

    Args:
        dotenv_path: Path to .env file. If None, searches for .env in current directory.
            Mimics python-dotenv's load_dotenv() behavior. (default: None)
        export: If True, export resolved variables to os.environ (default: True)
        override: If True, override existing os.environ variables (default: False)
        stop_on_expansion_error: If False, skip variables with expansion errors
            (e.g., VariableNotFoundError). CircularReferenceError is always
            raised as it indicates a configuration error. (default: True)
        stop_on_resolution_error: If False, skip variables with resolution errors
            (e.g., SecretResolutionError). Useful for resilience against transient
            secret store failures. (default: True)

    Returns:
        Dictionary of resolved environment variables

    Raises:
        URIParseError: If a URI format is invalid
        SecretResolutionError: If secret resolution fails
            (when stop_on_resolution_error=True)
        VariableNotFoundError: If a referenced variable is not found
            (when stop_on_expansion_error=True)
        CircularReferenceError: If a circular variable reference is detected

    Examples:
        >>> import envresolve
        >>> envresolve.register_azure_kv_provider()
        >>> # Load and export to os.environ (searches for .env in cwd)
        >>> resolved = envresolve.load_env(export=True)  # doctest: +SKIP
        >>> # Load specific file without exporting
        >>> resolved = envresolve.load_env("custom.env", export=False)  # doctest: +SKIP
    """
    return _default_resolver.load_env(
        dotenv_path,
        export=export,
        override=override,
        stop_on_expansion_error=stop_on_expansion_error,
        stop_on_resolution_error=stop_on_resolution_error,
    )


def resolve_os_environ(
    keys: list[str] | None = None,
    prefix: str | None = None,
    *,
    overwrite: bool = True,
    stop_on_expansion_error: bool = True,
    stop_on_resolution_error: bool = True,
) -> dict[str, str]:
    """Resolve secret URIs in os.environ.

    This function resolves secret URIs that are already set in environment variables,
    useful when values are passed from parent shells or container orchestrators.

    Args:
        keys: List of specific keys to resolve. If None, scan all keys.
            Mutually exclusive with prefix.
        prefix: Only process keys with this prefix, strip prefix from output.
            Mutually exclusive with keys.
        overwrite: If True, update os.environ with resolved values (default: True).
        stop_on_expansion_error: If False, skip variables with expansion errors
            (e.g., VariableNotFoundError). CircularReferenceError is always
            raised as it indicates a configuration error. (default: False)
        stop_on_resolution_error: If False, skip variables with resolution errors
            (e.g., SecretResolutionError). Useful for resilience against transient
            secret store failures. (default: True)

    Returns:
        Dictionary of resolved values

    Raises:
        MutuallyExclusiveArgumentsError: If both keys and prefix are specified
        URIParseError: If the URI format is invalid
        VariableNotFoundError: If a referenced variable is not found
            (when stop_on_expansion_error=True)
        CircularReferenceError: If a circular variable reference is detected
        SecretResolutionError: If secret resolution fails
            (when stop_on_resolution_error=True)

    Examples:
        >>> import envresolve
        >>> import os
        >>> envresolve.register_azure_kv_provider()
        >>> # Resolve all environment variables
        >>> resolved = envresolve.resolve_os_environ()  # doctest: +SKIP
        >>> # Resolve specific keys only
        >>> resolved = envresolve.resolve_os_environ(keys=["API_KEY"])  # doctest: +SKIP
    """
    return _default_resolver.resolve_os_environ(
        keys=keys,
        prefix=prefix,
        overwrite=overwrite,
        stop_on_expansion_error=stop_on_expansion_error,
        stop_on_resolution_error=stop_on_resolution_error,
    )
