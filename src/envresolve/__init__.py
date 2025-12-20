"""Resolve env vars from secret stores."""

from envresolve.api import (
    EnvResolver,
    load_env,
    register_azure_kv_provider,
    resolve_os_environ,
    resolve_secret,
    set_logger,
)
from envresolve.application.expanders import DotEnvExpander, EnvExpander
from envresolve.exceptions import (
    CircularReferenceError,
    EnvironmentVariableResolutionError,
    EnvResolveError,
    InvalidVariableNameError,
    MutuallyExclusiveArgumentsError,
    ProviderRegistrationError,
    SecretResolutionError,
    URIParseError,
    VariableNotFoundError,
)
from envresolve.services.expansion import expand_variables

__version__ = "0.1.11"

__all__ = [
    "CircularReferenceError",
    "DotEnvExpander",
    "EnvExpander",
    "EnvResolveError",
    "EnvResolver",
    "EnvironmentVariableResolutionError",
    "InvalidVariableNameError",
    "MutuallyExclusiveArgumentsError",
    "ProviderRegistrationError",
    "SecretResolutionError",
    "URIParseError",
    "VariableNotFoundError",
    "expand_variables",
    "load_env",
    "register_azure_kv_provider",
    "resolve_os_environ",
    "resolve_secret",
    "set_logger",
]
