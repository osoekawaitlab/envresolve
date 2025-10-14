"""Resolve env vars from secret stores."""

from envresolve.api import load_env, register_azure_kv_provider, resolve_secret
from envresolve.application.expanders import DotEnvExpander, EnvExpander
from envresolve.exceptions import (
    CircularReferenceError,
    SecretResolutionError,
    URIParseError,
    VariableNotFoundError,
)
from envresolve.services.expansion import expand_variables

__version__ = "0.1.1"

__all__ = [
    "CircularReferenceError",
    "DotEnvExpander",
    "EnvExpander",
    "SecretResolutionError",
    "URIParseError",
    "VariableNotFoundError",
    "expand_variables",
    "load_env",
    "register_azure_kv_provider",
    "resolve_secret",
]
