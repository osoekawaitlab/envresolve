"""Resolve env vars from secret stores."""

from envresolve.application.expanders import DotEnvExpander, EnvExpander
from envresolve.services.expansion import expand_variables

__version__ = "0.1.0"

__all__ = ["DotEnvExpander", "EnvExpander", "expand_variables"]
