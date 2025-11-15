"""Public API for envresolve."""

import fnmatch
import importlib
import os
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import dotenv_values, find_dotenv

from envresolve.application.resolver import SecretResolver
from envresolve.exceptions import (
    EnvironmentVariableResolutionError,
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
            self._providers["akv"] = provider_class()
        else:
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

    def load_env(  # noqa: PLR0913
        self,
        dotenv_path: str | Path | None = None,
        *,
        export: bool = True,
        override: bool = False,
        stop_on_expansion_error: bool = True,
        stop_on_resolution_error: bool = True,
        ignore_keys: list[str] | None = None,
        ignore_patterns: list[str] | None = None,
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
            ignore_keys: List of keys to skip expansion for. These keys are included
                in the result as-is without variable expansion or secret resolution.
                (default: None)
            ignore_patterns: List of glob patterns to match keys for skipping expansion.
                Keys matching any pattern are included as-is without variable expansion
                or secret resolution. Supports wildcards: *, ?, [seq]. (default: None)

        Returns:
            Dictionary of resolved environment variables

        Raises:
            EnvironmentVariableResolutionError: If a variable resolution error occurs
                (wraps VariableNotFoundError or SecretResolutionError with context)
            URIParseError: If a URI format is invalid
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
            # Skip expansion for ignored keys or patterns
            if self._should_ignore_key(key, ignore_keys, ignore_patterns):
                resolved[key] = value
                continue

            try:
                resolved_value = self._resolve_variable(
                    value,
                    complete_env,
                    stop_on_expansion_error=stop_on_expansion_error,
                    stop_on_resolution_error=stop_on_resolution_error,
                )
            except (VariableNotFoundError, SecretResolutionError) as e:
                msg = f"Failed to resolve environment variable '{key}': {e}"
                raise EnvironmentVariableResolutionError(
                    msg,
                    context_key=key,
                    original_error=e,
                ) from e
            if resolved_value is None:
                continue

            resolved[key] = resolved_value

        # Export to os.environ if requested
        if export:
            for key, value in resolved.items():
                if override or key not in os.environ:
                    os.environ[key] = value

        return resolved

    def _get_target_environ(
        self, keys: list[str] | None, prefix: str | None
    ) -> dict[str, str]:
        """Get the target environment variables to process."""
        if keys is not None:
            return {k: os.environ[k] for k in keys if k in os.environ}
        if prefix is not None:
            return {k: v for k, v in os.environ.items() if k.startswith(prefix)}
        return dict(os.environ)

    def _should_ignore_key(
        self, key: str, ignore_keys: list[str] | None, ignore_patterns: list[str] | None
    ) -> bool:
        """Check if a key should be ignored based on exact match or pattern match.

        Args:
            key: Environment variable key to check
            ignore_keys: List of keys for exact matching
            ignore_patterns: List of glob patterns for pattern matching

        Returns:
            True if the key should be ignored, False otherwise
        """
        # Check exact match
        if ignore_keys and key in ignore_keys:
            return True

        # Check pattern match
        return bool(
            ignore_patterns
            and any(fnmatch.fnmatch(key, pattern) for pattern in ignore_patterns)
        )

    def _resolve_variable(
        self,
        value: str,
        env: dict[str, str] | None = None,
        *,
        stop_on_expansion_error: bool,
        stop_on_resolution_error: bool,
    ) -> str | None:
        """Resolve a single variable, handling errors granularly.

        Args:
            value: Value to resolve (may contain variables or be a secret URI)
            env: Environment dict for variable expansion. If None, uses os.environ.
            stop_on_expansion_error: If False, return None on VariableNotFoundError
            stop_on_resolution_error: If False, return None on SecretResolutionError

        Returns:
            Resolved value, or None if error occurred and corresponding flag is False
        """
        if env is None:
            env = dict(os.environ)
        try:
            return self.resolve_with_env(value, env)
        except VariableNotFoundError:
            if stop_on_expansion_error:
                raise
            return None
        except SecretResolutionError:
            if stop_on_resolution_error:
                raise
            return None
        # CircularReferenceError is always raised as it's a configuration error.

    def resolve_os_environ(  # noqa: PLR0913
        self,
        keys: list[str] | None = None,
        prefix: str | None = None,
        *,
        overwrite: bool = True,
        stop_on_expansion_error: bool = True,
        stop_on_resolution_error: bool = True,
        ignore_keys: list[str] | None = None,
        ignore_patterns: list[str] | None = None,
    ) -> dict[str, str]:
        """Resolve secret URIs in os.environ.

        Raises:
            EnvironmentVariableResolutionError: If a variable resolution error occurs
                (wraps VariableNotFoundError or SecretResolutionError with context)
            MutuallyExclusiveArgumentsError: If both keys and prefix are specified
            URIParseError: If the URI format is invalid
            CircularReferenceError: If a circular variable reference is detected
        """
        if keys is not None and prefix is not None:
            arg1 = "keys"
            arg2 = "prefix"
            raise MutuallyExclusiveArgumentsError(arg1, arg2)

        target_env = self._get_target_environ(keys, prefix)
        resolved: dict[str, str] = {}

        for key, value in target_env.items():
            # Skip expansion for ignored keys or patterns
            if self._should_ignore_key(key, ignore_keys, ignore_patterns):
                resolved[key] = value
                if overwrite:
                    os.environ[key] = value
                continue

            try:
                resolved_value = self._resolve_variable(
                    value,
                    stop_on_expansion_error=stop_on_expansion_error,
                    stop_on_resolution_error=stop_on_resolution_error,
                )
            except (VariableNotFoundError, SecretResolutionError) as e:
                msg = f"Failed to resolve environment variable '{key}': {e}"
                raise EnvironmentVariableResolutionError(
                    msg,
                    context_key=key,
                    original_error=e,
                ) from e
            if resolved_value is None:
                continue

            output_key = (
                key[len(prefix) :] if prefix and key.startswith(prefix) else key
            )
            resolved[output_key] = resolved_value

            if overwrite:
                os.environ[output_key] = resolved_value
                if prefix and key != output_key:
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


def load_env(  # noqa: PLR0913
    dotenv_path: str | Path | None = None,
    *,
    export: bool = True,
    override: bool = False,
    stop_on_expansion_error: bool = True,
    stop_on_resolution_error: bool = True,
    ignore_keys: list[str] | None = None,
    ignore_patterns: list[str] | None = None,
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
        ignore_keys: List of keys to skip expansion for. These keys are included
            in the result as-is without variable expansion or secret resolution.
            (default: None)
        ignore_patterns: List of glob patterns to match keys for skipping expansion.
            Keys matching any pattern are included as-is without variable expansion
            or secret resolution. Supports wildcards: *, ?, [seq]. (default: None)

    Returns:
        Dictionary of resolved environment variables

    Raises:
        EnvironmentVariableResolutionError: If a variable resolution error occurs
            (wraps VariableNotFoundError or SecretResolutionError with context)
        URIParseError: If a URI format is invalid
        CircularReferenceError: If a circular variable reference is detected

    Examples:
        >>> import envresolve
        >>> envresolve.register_azure_kv_provider()
        >>> # Load and export to os.environ (searches for .env in cwd)
        >>> resolved = envresolve.load_env(export=True)  # doctest: +SKIP
        >>> # Load specific file without exporting
        >>> resolved = envresolve.load_env("custom.env", export=False)  # doctest: +SKIP
        >>> # Skip expansion for system variables
        >>> resolved = envresolve.load_env(ignore_keys=["PS1"])  # doctest: +SKIP
    """
    return _default_resolver.load_env(
        dotenv_path,
        export=export,
        override=override,
        stop_on_expansion_error=stop_on_expansion_error,
        stop_on_resolution_error=stop_on_resolution_error,
        ignore_keys=ignore_keys,
        ignore_patterns=ignore_patterns,
    )


def resolve_os_environ(  # noqa: PLR0913
    keys: list[str] | None = None,
    prefix: str | None = None,
    *,
    overwrite: bool = True,
    stop_on_expansion_error: bool = True,
    stop_on_resolution_error: bool = True,
    ignore_keys: list[str] | None = None,
    ignore_patterns: list[str] | None = None,
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
            raised as it indicates a configuration error. (default: True)
        stop_on_resolution_error: If False, skip variables with resolution errors
            (e.g., SecretResolutionError). Useful for resilience against transient
            secret store failures. (default: True)
        ignore_keys: List of keys to skip expansion for. These keys are included
            in the result as-is without variable expansion or secret resolution.
            (default: None)
        ignore_patterns: List of glob patterns to match keys for skipping expansion.
            Keys matching any pattern are included as-is without variable expansion
            or secret resolution. Supports wildcards: *, ?, [seq]. (default: None)

    Returns:
        Dictionary of resolved values

    Raises:
        EnvironmentVariableResolutionError: If a variable resolution error occurs
            (wraps VariableNotFoundError or SecretResolutionError with context)
        MutuallyExclusiveArgumentsError: If both keys and prefix are specified
        URIParseError: If the URI format is invalid
        CircularReferenceError: If a circular variable reference is detected

    Examples:
        >>> import envresolve
        >>> import os
        >>> envresolve.register_azure_kv_provider()
        >>> # Resolve all environment variables
        >>> resolved = envresolve.resolve_os_environ()  # doctest: +SKIP
        >>> # Resolve specific keys only
        >>> resolved = envresolve.resolve_os_environ(keys=["API_KEY"])  # doctest: +SKIP
        >>> # Skip expansion for system variables
        >>> resolved = envresolve.resolve_os_environ(
        ...     ignore_keys=["PS1"]
        ... )  # doctest: +SKIP
    """
    return _default_resolver.resolve_os_environ(
        keys=keys,
        prefix=prefix,
        overwrite=overwrite,
        stop_on_expansion_error=stop_on_expansion_error,
        stop_on_resolution_error=stop_on_resolution_error,
        ignore_keys=ignore_keys,
        ignore_patterns=ignore_patterns,
    )
